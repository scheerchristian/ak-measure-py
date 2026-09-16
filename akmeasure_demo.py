"""Python port of AKtools' AKmeasureDemo.m.

Measures impulse response(s) with an exponential sweep: generate the sweep,
optionally measure a reference and a level calibration, play/record,
deconvolve, post-process, plot and save.

Settings live in config/device.yaml (I/O device and channels, see also
akmeasure_io_setup.py), config/settings.yaml (measurement settings) and
config/meta.yaml (free-text info about the measurement).
"""

from datetime import datetime
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pyfar as pf
import sounddevice as sd

from akmeasure_config import load

device_cfg = load("device")
settings = load("settings")
meta = load("meta")

fs = settings["sampling_rate"]
sweep_cfg = settings["sweep"]
level_cfg = settings["level"]
ref_cfg = settings["reference"]
calib_cfg = settings["calibration"]
freq_range = sweep_cfg["frequency_range"]
regu_inside = 10 ** (-sweep_cfg["dynamic_db"] / 20)

device = (device_cfg["input_device"], device_cfg["output_device"])
out_channels = device_cfg["output_channels"]
in_channels = device_cfg["input_channels"]

out_dir = Path("measurements")
out_dir.mkdir(exist_ok=True)


def play_rec(signal, out_ch, in_ch, level_db, clip_reduction_db, average=1):
    """Play `signal` on out_ch, record in_ch, averaging with automatic level
    reduction on clipping (compensated afterwards), as in AKmeasureIR.m."""
    n_avg = 0
    n_clip = 0
    rec_sum = None
    while n_avg < average:
        gain = 10 ** (level_db / 20) * 10 ** (-n_clip * clip_reduction_db / 20)
        buf = sd.playrec(signal * gain, samplerate=fs, device=device,
                          output_mapping=out_ch, input_mapping=in_ch, blocking=True)
        if np.max(np.abs(buf)) >= 0.9999:
            print("clipping detected, reducing level...")
            n_clip += 1
            n_avg = 0
            rec_sum = None
            continue
        rec_sum = buf if rec_sum is None else rec_sum + buf
        n_avg += 1
    return rec_sum / average * 10 ** (n_clip * clip_reduction_db / 20)


# --------------------------------------------------------- 1. excitation signal
sweep = pf.signals.exponential_sweep_time(sweep_cfg["n_samples"], freq_range, sampling_rate=fs)
excitation = np.concatenate([
    np.zeros(int(sweep_cfg["t_start"] * fs)),
    sweep.time[0],
    np.zeros(int(sweep_cfg["t_gap"] * fs)),
])

# ------------------------------------------------------- 2. reference measurement
reference_signal = None
latency = 0

if ref_cfg["type"]:
    print(f"reference measurement ({ref_cfg['type']})...")
    if ref_cfg["type"] == "latency":
        impulse_offset = 64
        ref_excitation = np.zeros(fs)
        ref_excitation[impulse_offset] = 1.0
    elif ref_cfg["type"] == "complex":
        ref_excitation = excitation
    else:
        raise ValueError("reference.type must be false, 'latency' or 'complex'")

    rec = play_rec(ref_excitation, [ref_cfg["output_channel"]], [ref_cfg["input_channel"]],
                    ref_cfg["output_level_db"], ref_cfg["clip_reduction_db"])[:, 0]

    if ref_cfg["type"] == "complex":
        reference_signal = pf.Signal(rec, fs)
        latency_signal = pf.dsp.deconvolve(reference_signal, sweep, frequency_range=freq_range,
                                            regu_inside=regu_inside)
        latency_time = latency_signal.time[0]
    else:
        rec = np.roll(rec, -impulse_offset)
        reference_signal = pf.Signal(rec, fs)
        latency_time = rec

    latency = int(np.argmax(np.abs(latency_time[: int(0.5 * fs)])))
    print(f"latency: {latency} samples")

# ---------------------------------------------------------- 3. level calibration
calibrate_amplitude_per_pa = None
calibration_signal = None

if calib_cfg["mode"]:
    print(f"level calibration ({calib_cfg['mode']})...")
    if calib_cfg["mode"] == "measured":
        input("Apply calibrator to microphone and press Enter...")
        duration_samples = int(5 * fs)
        rec = sd.rec(duration_samples, samplerate=fs, mapping=[calib_cfg["input_channel"]],
                      device=device_cfg["input_device"], blocking=True)[:, 0]
        if np.max(np.abs(rec)) >= 0.9999:
            raise RuntimeError("Input signal clipped, decrease the calibration level")
        level_in = np.sqrt(np.mean(rec**2)) * np.sqrt(2)
        calibrate_amplitude_per_pa = level_in / (2e-5 * 10 ** (calib_cfg["level_db_spl"] / 20))
        calibration_signal = pf.Signal(rec, fs)
    elif calib_cfg["mode"] == "numeric":
        calibrate_amplitude_per_pa = 10 ** (calib_cfg["numeric_dbfs_per_pa"] / 20)
    else:
        raise ValueError("calibration.mode must be false, 'numeric' or 'measured'")

    # compensate for the frequency response of a 'complex' reference measurement
    if reference_signal is not None and ref_cfg["type"] == "complex":
        tf = pf.dsp.deconvolve(reference_signal, sweep, frequency_range=freq_range,
                                regu_inside=regu_inside)
        idx = np.argmin(np.abs(tf.frequencies - calib_cfg["frequency"]))
        calibrate_amplitude_per_pa /= np.abs(tf.freq[0, idx])

    print(f"sensitivity: {20 * np.log10(calibrate_amplitude_per_pa):.2f} dBFS per Pascal")

# ----------------------------------------------------------------- 4. measure IRs
channel_groups = [out_channels] if settings["channel_mode"] == "all" else [[ch] for ch in out_channels]
irs = []

for group in channel_groups:
    print(f"measuring output channel(s) {group}...")
    rec = play_rec(excitation, group, in_channels, level_cfg["output_db"],
                    level_cfg["clip_reduction_db"], level_cfg["average"])
    recorded = pf.Signal(rec.T, fs)

    if ref_cfg["type"] == "complex":
        ir = pf.dsp.deconvolve(recorded, reference_signal, frequency_range=freq_range,
                                regu_inside=regu_inside)
    else:
        ir = pf.dsp.deconvolve(recorded, sweep, frequency_range=freq_range, regu_inside=regu_inside)
        if ref_cfg["type"] == "latency":
            ir = pf.dsp.time_shift(ir, -latency, mode="cyclic")

    if calibrate_amplitude_per_pa:
        ir = ir / calibrate_amplitude_per_pa
    if settings["subsonic_filter"]:
        ir = pf.dsp.filter.butterworth(ir, N=4, frequency=20, btype="highpass")

    irs.append(ir)

ir = pf.Signal(np.concatenate([i.time for i in irs], axis=0), fs)

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

# --------------------------------------------------------------------- 5. plot
if settings["plot"]:
    pf.plot.time_freq(ir)
    plt.savefig(out_dir / f"measurement_{timestamp}_ir.png")
    plt.show()

# --------------------------------------------------------------------- 6. save
if not meta.get("soundcard"):
    meta["soundcard"] = f"out: {device_cfg['output_device']} / in: {device_cfg['input_device']}"

data = {"sweep": sweep, "ir": ir, **{k: v for k, v in meta.items() if v is not None}}
if reference_signal is not None:
    data["reference"] = reference_signal
if calibration_signal is not None:
    data["calibration"] = calibration_signal

file = out_dir / f"measurement_{timestamp}.far"
pf.io.write(file, **data)
print(f"saved to {file}")

"""Python port of AKtools' AKmeasureDemo.m.

Measures an impulse response (IR) with an exponential sweep: generate the
sweep, play it back while recording, deconvolve, and save the result.
Relies on pyfar for signal generation, deconvolution, filtering and file
I/O, and on sounddevice for playback/recording.
"""

from datetime import datetime
from pathlib import Path

import numpy as np
import pyfar as pf
import sounddevice as sd

# --------------------------------------------------------------- 1. settings
fs = 44100                     # sampling rate in Hz
out_dir = Path("measurements")
out_dir.mkdir(exist_ok=True)

sweep_n_samples = 2**18        # sweep length in samples
freq_range = [20, 20000]       # sweep frequency range in Hz
t_start = 0.06                 # silence before sweep in s
t_gap = 2.0                    # silence after sweep in s (> reverberation time)
dynamic = 40                   # deconvolution regularization dynamic in dB

ch_out = 1                     # output channel
ch_in = 1                      # input channel
level_out_db = -40             # playback level in dBFS
average = 1                    # number of averages

subsonic = True                # apply a 20 Hz high-pass to the IR
calibration_dbfs_per_pa = None # dBFS (peak) at 1 Pascal, or None to skip

# --------------------------------------------------------- 2. excitation signal
sweep = pf.signals.exponential_sweep_time(sweep_n_samples, freq_range, sampling_rate=fs)
excitation = np.concatenate([
    np.zeros(int(t_start * fs)),
    sweep.time[0] * 10 ** (level_out_db / 20),
    np.zeros(int(t_gap * fs)),
])

# ----------------------------------------------------------------- 3. measure
rec = np.zeros(len(excitation))
for _ in range(average):
    buf = sd.playrec(excitation, samplerate=fs, input_mapping=[ch_in],
                      output_mapping=[ch_out], blocking=True)[:, 0]
    if np.max(np.abs(buf)) >= 0.9999:
        print("warning: clipping detected, reduce level_out_db")
    rec += buf
rec /= average

recorded = pf.Signal(rec, fs)

# ------------------------------------------------------------ 4. deconvolution
ir = pf.dsp.deconvolve(recorded, pf.Signal(excitation, fs),
                        frequency_range=freq_range,
                        regu_inside=10 ** (-dynamic / 20))

# --------------------------------------------------------- 5. post-processing
if calibration_dbfs_per_pa is not None:
    ir = ir / 10 ** (calibration_dbfs_per_pa / 20)

if subsonic:
    ir = pf.dsp.filter.butterworth(ir, N=4, frequency=20, btype="highpass")

# ------------------------------------------------------------------- 6. save
meta = {
    "fs": fs, "ch_out": ch_out, "ch_in": ch_in,
    "level_out_db": level_out_db, "average": average, "dynamic": dynamic,
}
if calibration_dbfs_per_pa is not None:
    meta["calibration_dbfs_per_pa"] = calibration_dbfs_per_pa

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
file = out_dir / f"measurement_{timestamp}.far"
pf.io.write(file, sweep=sweep, recording=recorded, ir=ir, **meta)
print(f"saved to {file}")

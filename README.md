# ak-measure-py

Python port of AKtools' `AKmeasureDemo.m`: measure an impulse response with
an exponential sweep. Uses [pyfar](https://pyfar.org) for sweep generation,
deconvolution, filtering and file I/O, and `sounddevice` for playback and
recording.

## Setup

```
conda env create -f environment.yml
conda activate ak-measure-py
```

## Configuration

All settings live in `config/`:

- `device.yaml` - I/O device and channels. Set manually, or run
  `python3 akmeasure_io_setup.py` for a GUI to pick the output/input device
  and channels from the devices available on your system.
- `settings.yaml` - sweep, level, averaging, clipping, channel mode
  (`single`/`all`), reference measurement (`false`/`latency`/`complex`) and
  level calibration (`false`/`numeric`/`measured`).
- `meta.yaml` - free-text info about the measurement (room, mic, source,
  ...), saved alongside the data.

## Usage

```
python3 akmeasure_demo.py
```

The excitation sweep, the impulse response(s), and (if used) the reference
and calibration recordings are saved to
`measurements/measurement_<timestamp>.far` (pyfar's native format, readable
with `pyfar.io.read`), plus a plot as `measurement_<timestamp>_ir.png` if
`plot: true`.

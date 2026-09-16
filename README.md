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
  `python3 akmeasure/io_setup.py` for a GUI to pick the output/input device
  and channels from the devices available on your system.
- `settings.yaml` - sweep, level, averaging, clipping, channel mode
  (`single`/`all`), reference measurement (`false`/`latency`/`complex`) and
  level calibration (`false`/`numeric`/`measured`).
- `meta.yaml` - free-text info about the measurement (room, mic, source,
  ...), saved alongside the data.

## Usage

```
python3 measure.py
```

In `channel_mode: single`, each output channel (source) is measured on its
own and saved to its own file, `measurements/measurement_<timestamp>_src<n>.far`,
with the `ir` channels representing the input channels. In `channel_mode:
all`, all output channels play at once and everything is saved to a single
`measurements/measurement_<timestamp>.far`.

Each file is a pyfar native `.far` file (readable with `pyfar.io.read`)
containing the `ir` plus, depending on `settings.yaml`, the excitation
sweep, the raw (non-deconvolved) recording, and the reference/calibration
recordings. If `plot: true`, the excitation, reference and each IR are also
plotted and saved as PNGs next to the `.far` files.

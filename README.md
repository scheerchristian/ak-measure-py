# ak-measure-py

Python port of AKtools' `AKmeasureDemo.m`: measure an impulse response with
an exponential sweep. Uses [pyfar](https://pyfar.org) for sweep generation,
deconvolution, filtering and file I/O, and `sounddevice` for playback and
recording.

`akmeasure` is a regular, `pip install`-able Python package (`src/akmeasure/`),
so it can also be imported and reused, e.g.
`from akmeasure.measure import deconvolve, play_rec`.

## Setup

```
conda env create -f environment.yml
conda activate ak-measure-py
```

This installs `akmeasure` itself in editable mode (see `pyproject.toml`), so
`import akmeasure` and the `akmeasure`/`akmeasure-io-setup` commands below
are both available. Without conda, `pip install -e .` works the same way in
any Python >=3.10 environment.

## Configuration

Settings live in `./config`, relative to wherever you run the commands from
(so a different project gets its own `config/`, independent of where
`akmeasure` is installed):

- `device.yaml` - I/O device and channels. Set manually, or run
  `akmeasure-io-setup` for a GUI to pick the output/input device and
  channels from the devices available on your system.
- `settings.yaml` - sweep, level, averaging, clipping, channel mode
  (`single`/`all`), reference measurement (`false`/`latency`/`complex`) and
  level calibration (`false`/`numeric`/`measured`).
- `meta.yaml` - free-text info about the measurement (room, mic, source,
  ...), saved alongside the data.

### Using it in a new project

With `akmeasure` installed (into the environment that project uses), from
that project's directory:

```
akmeasure-init      # writes config/{device,settings,meta}.yaml from the package defaults
akmeasure-io-setup  # GUI to pick the audio device and channels -> config/device.yaml
```

Then edit `config/settings.yaml` and `config/meta.yaml` by hand as needed
(sweep length, levels, reference/calibration, contact/room/... info).

## Usage

```
akmeasure
```

(equivalently: `python3 -m akmeasure.measure`)

In `channel_mode: single`, each output channel (source) is measured on its
own and saved to its own file, `measurement_<timestamp>_src<n>.far`, with
the `ir` channels representing the input channels. In `channel_mode: all`,
all output channels play at once and everything is saved to a single
`measurement_<timestamp>.far`. These files land in `measurements/`, or in
`measurements/sessions/<session-timestamp>/` when a reference/calibration
session is involved (see below).

Each file is a pyfar native `.far` file (readable with `pyfar.io.read`)
containing the `ir` plus, depending on `settings.yaml`, the excitation
sweep and the raw (non-deconvolved) recording. If `plot: true`, the
excitation, reference and each IR are also plotted and saved as PNGs next
to the `.far` files.

### Sessions: reusing a reference/calibration across runs

Whenever `reference.type` and/or `calibration.mode` are enabled, that run's
*entire* output moves into `measurements/sessions/<timestamp>/` instead of
flat `measurements/` — the reference/calibration measurement itself
(`session.far`), the excitation/reference plots, and the measured `.far`
files and their `ir` plots. The session path is printed at the end of the
run. (With neither enabled, everything stays flat in `measurements/`, as
before.)

To reuse that reference/calibration for later runs without redoing the
physical measurement (e.g. the calibrator tone, or the reference sweep),
set it explicitly in `settings.yaml`:

```yaml
session: measurements/sessions/20260917_101607
```

While `session` is set, `akmeasure` loads the reference/calibration from
that folder instead of measuring them again, and each new run's `.far`
file (and its `ir` plot) is added into that same session folder alongside
the ones already there. Each measurement `.far` file also gets a `session`
field pointing at the folder it belongs to. Set `session` back to `null`
(or remove it) to measure and cache a fresh session instead.

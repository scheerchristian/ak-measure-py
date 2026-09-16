# ak-measure-py

Python port of AKtools' `AKmeasureDemo.m`: measure an impulse response with
an exponential sweep. Uses [pyfar](https://pyfar.org) for sweep generation,
deconvolution, filtering and file I/O, and `sounddevice` for playback and
recording.

## Setup

```
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

## Usage

Edit the settings at the top of `akmeasure_demo.py` (sampling rate, channels,
levels, ...) and run:

```
python3 akmeasure_demo.py
```

The excitation sweep, the raw recording and the deconvolved impulse response
are saved to `measurements/measurement_<timestamp>.far` (pyfar's native
format, readable with `pyfar.io.read`).

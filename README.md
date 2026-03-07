# material-qualification-demo

A demo repository for a materials qualification.

The demo focuses on **tungsten** and uses:

- **Inputs**
  - `dpa`
  - `irradiation_temperature_c`
  - `impurity_fraction`

- **Outputs**
  - `lower_yield_stress_mpa`
  - `hardness_gpa`
  - `thermal_diffusivity_mm2_s`

This repository contains:repos:
- Streamlit app
- simulator package
- tests
- notebook

## Experimental realism assumptions

The simulator now includes two practical constraints to mimic real experiments:

- **Measured DPA noise**: the achieved/measured DPA can differ from the requested value.
  The simulator records and returns the measured DPA, and this value is used in the app
  tables and plots.
- **Discrete impurity stock**: impurity fraction is selected from a finite set of available
  tungsten samples. For each request, the nearest available impurity fraction is used and
  recorded.

In the Streamlit app these effects are enabled by default (with a fixed random seed for
reproducibility). In the core simulator config, DPA noise defaults to `0.0` so unit tests
and scripted use remain deterministic unless explicitly enabled.

## Important note

This simulator is a **demonstrator**, not a validated materials model.  

It should **not** be used for engineering design decisions.

## Quick start

```bash
poetry install
poetry run streamlit run src/material_qualification_demo/app.py
```

or via the Poetry script entrypoint:

```bash
poetry run material-qualification-demo
```

## Repository layout

```text
material-qualification-demo/
├── assets/
│   └── digiLab logo.png
├── notebooks/
│   └── tungsten_simulator_walkthrough.ipynb
├── src/
│   └── material_qualification_demo/
│       ├── __init__.py
│       ├── app.py
│       ├── branding.py
│       └── simulators/
│           ├── __init__.py
│           ├── base.py
│           └── tungsten.py
├── tests/
│   └── test_tungsten_simulator.py
├── pyproject.toml
└── README.md
```

## Initial design of experiments

The app includes a very simple initial design of experiments using **two anchor points**:

1. the minimum corner of the domain
2. the maximum corner of the domain

So if the user specifies bounds for:
- `dpa`
- `irradiation_temperature_c`
- `impurity_fraction`

the initial DoE is:

```python
[
    [dpa_min, temp_min, impurity_min],
    [dpa_max, temp_max, impurity_max],
]
```

## Example usage

```python
from material_qualification_demo.simulators.tungsten import (
    TungstenQualificationConfig,
    TungstenQualificationSimulator,
)

config = TungstenQualificationConfig()
sim = TungstenQualificationSimulator(config)

X = [
    [0.0, 300.0, 0.001],
    [2.0, 900.0, 0.010],
]

outputs = sim.forward(X)
print(outputs[0])
```

## Suggested future extensions

- alloy family selector
- helium / hydrogen transmutation variables
- uncertainty model on outputs
- synthetic observation noise
- larger DOE options (LHS, Sobol, random)
- surrogate model fitting inside the app
- export of training dataframes

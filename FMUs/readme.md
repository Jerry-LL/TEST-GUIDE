# Functional mock-up units
## Source of FMU files:


 - **https://github.com/modelica/fmi-cross-check/**
    - BouncingBall.fmu: https://github.com/modelica/fmi-cross-check/blob/master/fmus/2.0/cs/win64/Test-FMUs/0.0.2/BouncingBall/BouncingBall.fmu
    

 - **TraceTronic**:
    - acc_test.fmu
    - MassSpringDamper.py (to be built with PythonFMU)
    - SimpleFMU.py (to be built with PythonFMU)

# Build your own FMUs with PythonFMU

https://github.com/NTNU-IHB/PythonFMU

## Requirements

`pip install pythonfmu`

## Generate FMU

```
cd C:\...\FMUs
python -m pythonfmu build -f SimpleFMU.py
```

## How it works

PythonFMU provides the binaries for Linux and Windows. These load the specified Python module dynamically
into the current process and execute the FMU logic defined in it. Therefore no compiler is
necessary.

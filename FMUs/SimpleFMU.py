from pythonfmu import Fmi2Variability, Fmi2Causality, Fmi2Slave, Boolean, Integer, Real, String
import math


class SimpleFMU(Fmi2Slave):
    author = 'MIL Team'
    description = 'This FMU'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.internalParameter = 0.25
        
        self.tunableParameter = 1.0
        self.register_variable(Real("tunableParameter", causality=Fmi2Causality.parameter, variability=Fmi2Variability.tunable))
        
        self.realIn = 1.0
        self.register_variable(Real("realIn", causality=Fmi2Causality.input))

        self.intOut = 1
        self.register_variable(Integer("intOut", causality=Fmi2Causality.output))

        self.realOut1 = 0.0
        self.register_variable(Real("realOut1", causality=Fmi2Causality.output))
        
        self.realOut2 = 0.0
        self.register_variable(Real("realOut2", causality=Fmi2Causality.output))


    def do_step(self, current_time, step_size):
        self.intOut = self.internalParameter * current_time * 1000
        self.realOut1 = math.sin(current_time)
        self.realOut2 = self.tunableParameter * self.realIn
        return True
from pythonfmu import Fmi2Variability, Fmi2Causality, Fmi2Slave, Boolean, Integer, Real, String
import math


class MassSpringDamper(Fmi2Slave):
    author = 'Paul'
    description = 'Simulation of Mass-Spring-Damper System'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # Model Parameters
        self.damping = 0.5  # Damping constant
        self.stiffness = 10 # Stiffness of the spring
        self.mass = 0.8     # Mass
        self.f1 = 0.0       # force on mass
        
        self.x0 = 0.0   # position of base
        self.v0 = 0.0   # velocity of base
        self.x1 = 0.0   # position of mass
        self.v1 = 0.0   # velocity of mass
        
        self.register_variable(Real("damping", causality=Fmi2Causality.parameter, variability=Fmi2Variability.tunable, description='Damping constant'))
        self.register_variable(Real("stiffness", causality=Fmi2Causality.parameter, variability=Fmi2Variability.fixed, description='Stiffness of the spring'))
        self.register_variable(Real("mass", causality=Fmi2Causality.parameter, variability=Fmi2Variability.fixed))
        
        self.register_variable(Real("f1", causality=Fmi2Causality.input))
        self.register_variable(Real("x0", causality=Fmi2Causality.input))
        self.register_variable(Real("v0", causality=Fmi2Causality.input))
        self.register_variable(Real("x1", causality=Fmi2Causality.output))
        self.register_variable(Real("v1", causality=Fmi2Causality.output))
        

    def do_step(self, current_time, step_size):
        self.v1 = self.v1+step_size* (self.damping*(self.v0-self.v1) + self.stiffness * (self.x0 - self.x1 - self.f1)) / self.mass
        self.x1 = self.x1 + self.v1*step_size
 
        return True
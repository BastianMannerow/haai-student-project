from simulation.Simulation import Simulation
from simulation.BastiTracer import BastiTracer

if __name__ == '__main__':
    # needed for BastiTracer
    interceptor = BastiTracer()

    # simulation
    simulation = Simulation(interceptor)
    simulation.run_simulation()
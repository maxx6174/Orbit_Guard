"""The simulated planet environment: communication window, obstruction, interference."""
import math


class Environment:
    def __init__(self):
        self.tick = 0
        self.obstruction = 1.0     # 1.0 = clear sky, small = planet in the way
        self.interference = 1.0    # 1.0 = clean, small = strong interference
        self.active = {}           # fault name -> tick at which it clears by itself

    def update(self, tick):
        self.tick = tick

    def window_quality(self):
        """A gentle ups-and-downs 'communication window' (0.88 .. 1.0)."""
        return 0.94 + 0.06 * math.sin(2 * math.pi * self.tick / 90)

    def path_factor(self):
        return self.window_quality() * self.obstruction * self.interference

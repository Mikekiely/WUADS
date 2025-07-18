import numpy as np


# Calculates atmospheric conditions and flight conditions with a given height and mach number
class FlightConditions:
    """
    Calculates atmospheric and flight conditions for a given altitude and Mach number.

    """
    pressure = 0
    temperature = 0
    rho0 = 0
    mu = 0
    a = 0
    velocity = 0
    mach = 0
    q = 0
    re = 0
    altitude = 0
    gamma = 1.4

    def __init__(self, altitude, mach):
        """
        Initializes the FlightConditions object with the specified altitude and Mach number.

        :param float altitude: altitude (ft)
        :param float mach: mach number
        """
        # Constants
        g = 32.2  # gravity
        t0 = 519  # Rankine
        p0 = 2116  # lb/ft^2
        rho0 = .0023769
        a0 = 1116  # ft/s
        L = 0.003575  # temp lapse rate (R/ft)
        R = 1716.5  # Gas Constant
        gamma = 1.4

        t = t0 - L * altitude
        theta = t / t0
        delta = theta ** (g / (L * R))
        p = delta * p0
        sigma = delta / theta

        # Stratosphere Correction
        if delta < 0.224:
            h0 = 36000  # Troposphere Ceiling
            beta = 20790
            dh = altitude - 36000
            theta = .752
            delta = theta ** (g / (L * R)) * np.exp(-dh / beta)
            sigma = delta / theta
            t = t0 * theta

        # Sutherland's law (calculates in metric, converts back to imperial
        c1 = 1.458e-6
        S = 110.4
        tref = t * 5 / 9  # Rankine to Kelvin
        self.mu = c1 * (tref ** 1.5) / (tref + S)
        self.mu *= .0208854  # metric to imperial

        self.temperature = t
        self.pressure = delta * p0
        self.rho = sigma * rho0
        self.a = np.sqrt(gamma * R * t)

        self.velocity = mach * self.a
        self.mach = mach
        self.q = .5 * self.rho * self.velocity ** 2
        self.altitude = altitude

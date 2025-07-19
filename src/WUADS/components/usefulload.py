

class UsefulLoad:
    """
    Contains weight properties all the whole useful load

    crew members, passengers, fuel, and cargo
    """
    weight = 0
    n_pilots = 0
    w_pilots = 0
    cg_pilots = [0, 0, 0]
    n_flight_attendants = 0
    w_flight_attendants = 0
    cg_flight_attendants = [0, 0, 0]
    n_passengers = 0
    w_passengers = 0
    cg_passengers = [0, 0, 0]
    w_fuel = 0
    cg_fuel = [0, 0, 0]
    w_cargo = 0
    cg_cargo = [0, 0, 0]

    cg = [0, 0, 0]
    inertia = [0, 0, 0]


    def __init__(self, params):
        """
        Initialize useful load and set all weights, centers of gravity (cg), and moments of inertia
        :param <dict> params: list of parameters to edit.
        """
        for variable_name, variable_value in params.items():
            if hasattr(self, variable_name.lower()):
                setattr(self, variable_name.lower(), variable_value)

    def set_weight(self, aircraft):
        """
        Intializes and updates the useful load's various weights like cargo and passengers, and uses these to calculate
        the total weight and center of gravity.

        """
        # Set passenger and crew weight
        self.w_passengers = self.n_passengers * 165
        self.w_flight_attendants = self.n_flight_attendants * 165
        self.w_pilots = self.n_pilots * 165
        self.inertia = [0, 0, 0]
        # Update moments of inertia
        if self.cg_passengers:
            self.inertia = [i + self.w_passengers * x for i, x in zip(self.inertia, self.cg_passengers)]

        if self.cg_cargo:
            self.inertia = [i + self.w_cargo * x for i, x in zip(self.inertia, self.cg_cargo)]

        if self.cg_fuel:
            self.inertia = [i + self.w_fuel * x for i, x in zip(self.inertia, self.cg_fuel)]

        if self.cg_pilots:
            self.inertia = [i + self.w_fuel * x for i, x in zip(self.inertia, self.cg_pilots)]

        if self.cg_flight_attendants:
            self.inertia = [i + self.w_fuel * x for i, x in zip(self.inertia, self.cg_flight_attendants)]

        self.w_fuel = aircraft.w_fuel

        self.weight = self.w_pilots + self.w_passengers + self.w_flight_attendants + self.w_fuel + self.w_cargo
        self.cg = [i / self.weight for i in self.inertia]
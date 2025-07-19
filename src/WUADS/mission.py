from src.WUADS.mission_profile import takeoff, climb, cruise, descent, landing

MISSION_KEYS = {
    'takeoff': takeoff,
    'climb': climb,
    'cruise': cruise,
    'descent': descent,
    'landing': landing
}

class Mission:
    """
    Class which contains information to the mission requirements and profile of an aircraft
    """
    # Default values
    w_fuel = 0
    n_passengers = 0
    n_pilots = 0
    n_flight_attendants = 0
    mach = 0
    max_mach = 0
    altitude = 0
    design_range = 0

    rho_fuel = 6.8
    ultimate_load = 0

    mission_profile = []

    def __init__(self, aircraft):

        self.aircraft = aircraft
        self.max_mach = self.mach * 1.025

        self.takeoff_data = None
        self.climb_data = None
        self.cruise_data = None
        self.descent_data = None
        self.landing_data = None


    def generate_mission_profile(self, params):

        # Note: this should only really run on initialization
        if not params:
            self.mission_profile = [
                takeoff(thrust_setting=75, time=30),
                climb(aircraft=self.aircraft, start_velocity=150, end_velocity=200, start_altitude=0, end_altitude=10000,
                      best_climb=False),
                cruise(aircraft=self.aircraft, mach=0.85, altitude=35000, find_range=True),
                descent(weight_fraction=0.95),
                landing(weight_fraction=0.9, reserve_fuel=0.1)
            ]
        else:
            for name, seg in params.items():
                seg_class = MISSION_KEYS.get(seg['segment_type'])
                print(seg)
                self.mission_profile.append(seg_class(aircraft=self.aircraft, title=name, **seg))


    def run_case_updated(self, aircraft):
        """
        Runs mission profile calculations using the user-defined mission profile.
        Assumes self.mission_profile is already populated with valid mission segments.
        """

        mission_profile = self.mission_profile  # use the existing mission profile defined by user

        wi = aircraft.weight_takeoff

        # Forward loop: compute weight fractions and range up to the find_range segment
        seg_findrange = None
        for i, seg in enumerate(mission_profile):
            if seg.find_range:
                indx_findrange = i
                seg_findrange = seg
                break
            else:
                seg.breguet_range(aircraft, wi)
                wi *= seg.weight_fraction

        # Backward loop: compute wi for segments after find_range
        wn = aircraft.weight_takeoff - aircraft.useful_load.w_fuel
        for seg in reversed(mission_profile):
            if seg.find_range:
                break
            else:
                seg.breguet_range(aircraft, wn)
                wn = seg.wi

        # Compute the range for the find_range segment
        if seg_findrange is not None:
            seg_findrange.set_range(aircraft, wi, wn)

        # Sum total mission range
        max_range = sum(seg.range for seg in mission_profile)

        aircraft.range = max_range
        self.mission_profile = mission_profile  # store updated mission profile

from .mission_segments import takeoff, climb, cruise, descent, landing, loiter, weight_drop
import logging

logger = logging.getLogger(__name__)

MISSION_KEYS = {
    'takeoff': takeoff,
    'climb': climb,
    'cruise': cruise,
    'descent': descent,
    'landing': landing,
    'loiter': loiter,
    'weight_drop': weight_drop
}

class Mission:
    """
    Class which contains information to the mission requirements and profile of an aircraft
    """

    def __init__(self, aircraft):

        # Default values
        self.w_fuel = 0
        self.n_passengers = 0
        self.n_pilots = 0
        self.n_flight_attendants = 0
        self.mach = 0
        self.max_mach = 0
        self.altitude = 0
        self.design_range = 0
        self.range = 0

        self.rho_fuel = 6.8
        self.ultimate_load = 0

        self.mission_profile = []

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
                self.mission_profile.append(seg_class(aircraft=self.aircraft, title=name, **seg))


    def run_case(self, mute_output=False):
        """
        Runs mission profile calculations using the user-defined mission profile.
        Assumes self.mission_profile is already populated with valid mission segments.
        """
        aircraft = self.aircraft
        mission_profile = self.mission_profile  # use the existing mission profile defined by user
        wi = aircraft.weight_takeoff

        if not mute_output:
            logger.info("Generating mission profile...")

        # Forward loop: compute weight fractions and range up to the find_range segment
        seg_findrange = None
        for i, seg in enumerate(mission_profile):
            if seg.find_range:
                indx_findrange = i
                seg_findrange = seg
                break
            else:
                if not mute_output:
                    logger.info(f"Analyzing conditions for mission segment {seg.title}")
                seg.breguet_range(aircraft, wi=wi)
                wi *= seg.weight_fraction

        if seg_findrange is None:
            pass
        else:
            # Backward loop: compute wi for segments after find_range
            wn = aircraft.weight_takeoff - aircraft.useful_load.w_fuel
            for seg in reversed(mission_profile):
                if seg.find_range:
                    break
                else:
                    if not mute_output:
                        logger.info(f"Analyzing conditions for mission segment {seg.title}")
                    seg.breguet_range(aircraft, wn=wn)
                    wn = seg.wi

            if not mute_output:
                logger.info(f"Finding maximum range")
            seg_findrange.set_range(aircraft, wi=wi, wn=wn)

        # Sum total mission range
        max_range = sum(seg.range for seg in mission_profile)
        if not mute_output:
            logger.info(f"Analysis complete, maximum range is {max_range}")
        aircraft.range = max_range
        self.mission_profile = mission_profile  # store updated mission profile
        self.range = max_range

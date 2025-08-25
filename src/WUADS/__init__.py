__version__ = "0.1.0"

# Expose core functionality at the package level
from .aircraft import Aircraft
from .mission import Mission
from .propulsion import turbofan, propeller
from .reports import weights_report, mission_profile_report

# Clean up namespace
__all__ = [
    "Aircraft",
    "Mission",
    "turbofan",
    "propeller",
    "weights_report",
    "mission_profile_report",
    "__version__"
]
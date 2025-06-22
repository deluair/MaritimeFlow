"""
AIS data ingestion and processing modules
"""

from .synthetic_generator import SyntheticDataGenerator

# Optional imports with error handling
try:
    from .ais_collectors import AISHubCollector, AISStreamCollector, MarinePlanCollector
    AIS_COLLECTORS_AVAILABLE = True
except ImportError:
    AIS_COLLECTORS_AVAILABLE = False

# Note: data_processor and validation modules don't exist yet
# from .data_processor import AISDataProcessor
# from .validation import AISDataValidator

__all__ = [
    "SyntheticDataGenerator"
]

if AIS_COLLECTORS_AVAILABLE:
    __all__.extend([
        "AISHubCollector",
        "AISStreamCollector", 
        "MarinePlanCollector"
    ]) 
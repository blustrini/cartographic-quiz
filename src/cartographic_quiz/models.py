from dataclasses import dataclass
from typing import Optional


@dataclass
class CartographicDate:
    """Represents a specific date tied to a geographic location with coordinates."""

    date_str: Optional[str]
    location_name: Optional[str]
    latitude: Optional[float] = None
    longitude: Optional[float] = None

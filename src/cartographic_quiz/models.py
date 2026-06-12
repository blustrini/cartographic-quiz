from dataclasses import dataclass
from typing import Optional


@dataclass
class CartographicDate:
    """Represents a specific date tied to a geographic location with coordinates."""

    date_str: Optional[str]
    location_name: Optional[str]
    latitude: Optional[float] = None
    longitude: Optional[float] = None


@dataclass
class BiographyData:
    url: str | None = None
    formatted_name: str | None = None
    birth_date: Optional[str] = None
    birth_place: Optional[str] = None
    birth_lat: Optional[float] = None
    birth_lon: Optional[float] = None
    birth_rad_m: Optional[float] = None
    death_date: Optional[str] = None
    death_place: Optional[str] = None
    death_lat: Optional[float] = None
    death_lon: Optional[float] = None
    death_rad_m: Optional[float] = None
    additional_places: Optional[list[str]] = None
    additional_places_coords: Optional[list[tuple[float, float]]] = None


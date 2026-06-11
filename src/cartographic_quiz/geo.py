from typing import Optional

import requests
from bs4 import BeautifulSoup
from geopy.geocoders import Nominatim

from cartographic_quiz.constants import REQUEST_TIMEOUT_SECONDS


HISTORICAL_POLITY_TERMS = (
    "empire",
    "kingdom",
    "dynasty",
    "caliphate",
    "sultanate",
    "khanate",
)


def _geocode_candidates(text: str) -> list[str]:
    cleaned = text.strip()
    if not cleaned:
        return []

    if "," not in cleaned:
        return [cleaned]

    parts = [part.strip() for part in cleaned.split(",") if part.strip()]
    if not parts:
        return [cleaned]

    base = parts[0]
    trailing = " ".join(parts[1:]).lower()
    prioritize_base = any(token in trailing for token in HISTORICAL_POLITY_TERMS)

    candidates = [base, cleaned] if prioritize_base else [cleaned, base]
    deduped: list[str] = []
    for candidate in candidates:
        if candidate and candidate not in deduped:
            deduped.append(candidate)
    return deduped


def fetch_html(url: str, headers: dict) -> Optional[str]:
    try:
        response = requests.get(url, headers=headers, timeout=REQUEST_TIMEOUT_SECONDS)
        response.raise_for_status()
    except requests.RequestException as exc:
        print(f"  [Debug] Failed request for {url}: {exc}")
        return None
    return response.text


def fetch_json(url: str, params: dict, headers: dict) -> Optional[dict]:
    try:
        response = requests.get(url, params=params, headers=headers, timeout=REQUEST_TIMEOUT_SECONDS)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as exc:
        print(f"  [Debug] Failed request for {url}: {exc}")
    except ValueError as exc:
        print(f"  [Debug] Failed decoding JSON from {url}: {exc}")
    return None


def get_coordinates_from_wikipedia_url(wiki_url: str, headers: dict) -> tuple[Optional[float], Optional[float]]:
    """Follows a Wikipedia hyperlink to scrape exact coordinate metadata.

    directly from the location's dedicated page.
    """
    html = fetch_html(wiki_url, headers)
    if not html:
        return None, None

    try:
        soup = BeautifulSoup(html, "html.parser")

        geo_span = soup.find("span", class_="geo")
        if geo_span:
            geo_text = geo_span.get_text().strip()
            if ";" in geo_text:
                lat_str, lon_str = geo_text.split(";")
                return float(lat_str.strip()), float(lon_str.strip())

        lat_span = soup.find("span", class_="latitude")
        lon_span = soup.find("span", class_="longitude")
        if lat_span and lon_span:
            return float(lat_span.get_text()), float(lon_span.get_text())

    except Exception as exc:
        print(f"  [Debug] Failed parsing coordinates from target page {wiki_url}: {exc}")

    return None, None


def geocode_fallback(text: str) -> tuple[Optional[float], Optional[float]]:
    """Fallback geocoder that trims historical tails if standard lookup fails."""
    geolocator = Nominatim(user_agent="history_proof_final_mapper")
    try:
        for candidate in _geocode_candidates(text):
            location = geolocator.geocode(candidate)
            if location:
                return location.latitude, location.longitude
    except Exception:
        pass
    return None, None

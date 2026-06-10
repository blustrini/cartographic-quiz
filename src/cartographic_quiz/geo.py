from typing import Optional

import requests
from bs4 import BeautifulSoup
from geopy.geocoders import Nominatim

from cartographic_quiz.constants import REQUEST_TIMEOUT_SECONDS


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
        location = geolocator.geocode(text)
        if not location and "," in text:
            clean_base = text.split(",")[0].strip()
            location = geolocator.geocode(clean_base)

        if location:
            return location.latitude, location.longitude
    except Exception:
        pass
    return None, None

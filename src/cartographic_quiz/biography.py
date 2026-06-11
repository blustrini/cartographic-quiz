import re
from dataclasses import dataclass
from typing import Optional

from bs4 import BeautifulSoup

from cartographic_quiz.constants import USER_AGENT, WIKIPEDIA_BASE_URL
from cartographic_quiz.geo import fetch_html, fetch_json, geocode_fallback, get_coordinates_from_wikipedia_url


MONTH_PATTERN = (
    r"(?:jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|jul(?:y)?|"
    r"aug(?:ust)?|sep(?:t(?:ember)?)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?)"
)
NON_PLACE_TERMS = (
    "murder",
    "assassination",
    "gunshot",
    "wound",
    "battle",
    "war",
    "execution",
    "disease",
    "syndrome",
    "cancer",
    "heart attack",
    "stroke",
    "suicide",
)
BIRTH_ALT_DATE_HEADERS = ("baptized", "baptised", "christened", "christening")
NON_PLACE_SINGLETONS = {"a", "an", "the", "c", "c.", "ca", "ca.", "circa", "ad", "bc", "bce", "ce"}
ROMAN_NUMERAL_TOKEN = re.compile(r"^[ivxlcdm]+$", flags=re.IGNORECASE)


def _normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def _extract_date_candidate(text: str) -> Optional[str]:
    cleaned = _normalize_text(re.sub(r"\(aged[^)]*\)", "", text, flags=re.IGNORECASE))
    if not cleaned:
        return None

    era_day_month_match = re.search(
        rf"\b\d{{1,2}}\s+{MONTH_PATTERN}\s+(?:ad|a\.d\.?)\s*\d{{1,4}}\b",
        cleaned,
        flags=re.IGNORECASE,
    )
    if era_day_month_match:
        raw = _normalize_text(era_day_month_match.group(0))
        return re.sub(r"a\.?\s*d\.?", "AD", raw, flags=re.IGNORECASE)

    era_prefix_match = re.search(
        r"\b(?:(?:c\.?|ca\.?|circa)\s+)?(?:ad|a\.d\.?|ce|c\.e\.?)\s*\d{1,4}(?:/\d{1,2})?\b",
        cleaned,
        flags=re.IGNORECASE,
    )
    if era_prefix_match:
        raw = _normalize_text(era_prefix_match.group(0))
        raw = re.sub(r"a\.?\s*d\.?", "AD", raw, flags=re.IGNORECASE)
        raw = re.sub(r"c\.?\s*e\.?", "CE", raw, flags=re.IGNORECASE)
        return raw

    bc_match = re.search(
        rf"\b(?:(?:c\.?|ca\.?|circa)\s*)?(?:(?:\d{{1,2}}\s+{MONTH_PATTERN}\s+)?\d{{1,4}}(?:/\d{{1,2}})?)\s*(?:bc|b\.c\.?|bce|b\.c\.e\.?)($|\W)",
        cleaned,
        flags=re.IGNORECASE,
    )
    if bc_match:
        raw = _normalize_text(bc_match.group(0)).rstrip(".,;:")
        raw = re.sub(r"b\.?\s*c\.?\s*e\.?", "BCE", raw, flags=re.IGNORECASE)
        raw = re.sub(r"b\.?\s*c\.?", "BC", raw, flags=re.IGNORECASE)
        return raw

    ad_year_match = re.search(r"\b\d{1,4}\s*(?:ad|a\.d\.?|ce|c\.e\.?)\b", cleaned, flags=re.IGNORECASE)
    if ad_year_match:
        raw = _normalize_text(ad_year_match.group(0))
        raw = re.sub(r"a\.?\s*d\.?", "AD", raw, flags=re.IGNORECASE)
        raw = re.sub(r"c\.?\s*e\.?", "CE", raw, flags=re.IGNORECASE)
        return raw

    patterns = (
        r"\b\d{4}-\d{2}-\d{2}\b",
        rf"\b\d{{1,2}}\s+{MONTH_PATTERN}\s+\d{{3,4}}\b",
        rf"\b{MONTH_PATTERN}\s+\d{{1,2}},?\s+\d{{3,4}}\b",
        rf"\b{MONTH_PATTERN}\s+\d{{3,4}}\b",
        r"\b(?:c\.?|ca\.?|circa)\s*\d{3,4}(?:/\d{1,2})?\b",
        r"\b\d{3,4}(?:/\d{1,2})?\b",
    )

    for pattern in patterns:
        match = re.search(pattern, cleaned, flags=re.IGNORECASE)
        if match:
            return _normalize_text(match.group(0))

    return None


def _is_valid_place_name(text: str) -> bool:
    normalized = _normalize_text(text).lower().strip(" ,.;:-")
    if not normalized:
        return False

    if normalized in NON_PLACE_SINGLETONS:
        return False

    if not re.search(r"[a-z]", normalized):
        return False

    letters_only = re.sub(r"[^a-z]", "", normalized)
    if len(letters_only) < 2:
        return False

    if ROMAN_NUMERAL_TOKEN.fullmatch(letters_only):
        return False

    if any(term in normalized for term in NON_PLACE_TERMS):
        return False

    if any(token in normalized for token in ("death cause", "cause of death", "born in", "died from")):
        return False

    if re.search(r"\d", normalized):
        return False

    date_candidate = _extract_date_candidate(normalized)
    if date_candidate and _normalize_text(date_candidate).lower() == normalized:
        return False

    return True


def _remember_place_links(td, seen_links: list[tuple[str, str]]) -> None:
    for link in td.find_all("a", href=lambda h: h and h.startswith("/wiki/") and "File:" not in h):
        text = _normalize_text(link.get_text())
        href = link.get("href", "")
        if not text or not href:
            continue
        if any(href.startswith(prefix) for prefix in ("/wiki/Help:", "/wiki/Template:", "/wiki/Category:")):
            continue
        if not _is_valid_place_name(text):
            continue
        seen_links.append((text.lower(), href))


def _find_previous_place_link(place_text: Optional[str], seen_links: list[tuple[str, str]]) -> Optional[str]:
    normalized = _normalize_text(place_text or "").lower()
    if not normalized:
        return None

    candidates = []
    if "," in normalized:
        head = _normalize_text(normalized.split(",", 1)[0]).lower()
        if head:
            candidates.append(head)
    candidates.append(normalized)

    for link_text, href in reversed(seen_links):
        if any(candidate == link_text for candidate in candidates):
            return href

    return None


def _prefer_previous_link_for_composite_place(
    place_text: Optional[str],
    current_href: Optional[str],
    seen_links: list[tuple[str, str]],
) -> Optional[str]:
    normalized = _normalize_text(place_text or "")
    if not normalized or "," not in normalized:
        return current_href

    previous_href = _find_previous_place_link(place_text, seen_links)
    if previous_href and previous_href != current_href:
        return previous_href

    return current_href


def _chunks_after_date(td, date_str: Optional[str]) -> list[str]:
    chunks = [_normalize_text(chunk) for chunk in td.stripped_strings if _normalize_text(chunk)]
    if not chunks:
        return []

    if not date_str:
        return chunks

    joined = " ".join(chunks)
    date_start = joined.lower().find(date_str.lower())
    if date_start == -1:
        return chunks

    date_end = date_start + len(date_str)
    selected: list[str] = []
    pos = 0
    for chunk in chunks:
        chunk_start = pos
        chunk_end = pos + len(chunk)
        if chunk_start >= date_end:
            selected.append(chunk)
        pos = chunk_end + 1

    return selected or chunks


def _extract_location_link(td, date_str: Optional[str] = None, place_text: Optional[str] = None) -> Optional[str]:
    preferred_chunks = _chunks_after_date(td, date_str)
    place_normalized = _normalize_text(place_text or "").lower()

    place_text_links = []
    preferred_links = []
    fallback_links = []
    for link in td.find_all("a", href=lambda h: h and h.startswith("/wiki/") and "File:" not in h):
        text = _normalize_text(link.get_text())
        href = link.get("href", "")
        if not text or not href:
            continue
        if any(href.startswith(prefix) for prefix in ("/wiki/Help:", "/wiki/Template:", "/wiki/Category:")):
            continue

        if not _is_valid_place_name(text):
            continue

        text_lower = text.lower()
        in_preferred_chunks = any(text_lower in chunk.lower() or chunk.lower() in text_lower for chunk in preferred_chunks)
        matches_place_text = bool(place_normalized) and (
            text_lower in place_normalized or place_normalized in text_lower
        )

        if matches_place_text:
            place_text_links.append(href)
        elif in_preferred_chunks:
            preferred_links.append(href)
        else:
            fallback_links.append(href)

    if place_text_links:
        return place_text_links[0]

    if preferred_links:
        return preferred_links[0]
    if fallback_links:
        return fallback_links[0]

    return None


def _extract_place_from_cell(td, date_str: Optional[str]) -> Optional[str]:
    for normalized in _chunks_after_date(td, date_str):
        if not normalized:
            continue
        if _is_valid_place_name(normalized):
            return normalized

    return None


def _is_cause_header(header: str) -> bool:
    return any(token in header for token in ("cause", "manner"))


def _extract_date_from_cell(cell: BeautifulSoup) -> Optional[str]:
    bday = cell.find(class_="bday")
    if bday:
        return bday.text.strip()

    deathdate = cell.find(class_=lambda c: c and "deathdate" in c)
    if deathdate:
        candidate = _extract_date_candidate(deathdate.get_text())
        if candidate:
            return candidate

    chunks = [chunk for chunk in cell.stripped_strings if chunk]
    joined_chunks = " ".join(chunks[:6])
    candidate = _extract_date_candidate(joined_chunks)
    if candidate:
        return candidate

    for chunk in chunks:
        candidate = _extract_date_candidate(chunk)
        if candidate:
            return candidate

    return None


def _clean_place_text(text: str, date_str: Optional[str]) -> str:
    raw_text = re.sub(r"\[\d+\]|\s*\([^)]*\)", "", text).strip()
    without_date = raw_text.replace(date_str or "", "")
    without_causes = re.sub(
        r"\b(?:cause of death|death cause|murder|assassination|gunshot wounds?|execution|battle)\b.*$",
        "",
        without_date,
        flags=re.IGNORECASE,
    )
    return re.sub(r"\s+", " ", without_causes).strip(" ,;")


def _extract_present_day_place(text: str) -> Optional[str]:
    match = re.search(r"present-day\s+([^)]+)", text, flags=re.IGNORECASE)
    if not match:
        return None

    segment = _normalize_text(match.group(1)).strip(" ,;.")
    if not segment:
        return None

    candidate = _normalize_text(segment.split(",", 1)[0]).strip(" ,;.")
    if _is_valid_place_name(candidate):
        return candidate

    return None


def _resolve_title(name: str) -> Optional[str]:
    headers = {"User-Agent": USER_AGENT}
    base_url = f"{WIKIPEDIA_BASE_URL}/w/api.php"
    for search_mode in ("title", "text"):
        params = {
            "action": "query",
            "list": "search",
            "srsearch": name,
            "srlimit": 5,
            "srnamespace": 0,
            "srwhat": search_mode,
            "format": "json",
        }
        data = fetch_json(base_url, params=params, headers=headers)
        if not data:
            continue

        results = data.get("query", {}).get("search", [])
        if results:
            return results[0].get("title")

    return None


@dataclass
class BiographyData:
    birth_date: Optional[str] = None
    birth_place: Optional[str] = None
    birth_lat: Optional[float] = None
    birth_lon: Optional[float] = None
    death_date: Optional[str] = None
    death_place: Optional[str] = None
    death_lat: Optional[float] = None
    death_lon: Optional[float] = None


def scrape_robust_biography(name: str, verbose: bool = True) -> Optional[BiographyData]:
    """Scrapes a biography infobox, following hyperlinks to extract robust geographical data."""
    resolved_title = _resolve_title(name)
    if not resolved_title:
        if verbose:
            print(f"Error: Couldn't find a Wikipedia title for '{name}'")
        return None

    formatted_name = resolved_title.strip().replace(" ", "_")
    url = f"{WIKIPEDIA_BASE_URL}/wiki/{formatted_name}"
    headers = {"User-Agent": USER_AGENT}

    html = fetch_html(url, headers)
    if not html:
        if verbose:
            print(f"Error: Couldn't fetch page for '{name}'")
        return None

    soup = BeautifulSoup(html, "html.parser")
    infobox = soup.find("table", class_=lambda x: x and "infobox" in x)
    if not infobox:
        if verbose:
            print(f"Error: No biography infobox panel found for '{name}'.")
        return None

    data = BiographyData()
    seen_place_links: list[tuple[str, str]] = []

    for row in infobox.find_all("tr"):
        th = row.find("th")
        td = row.find("td")
        if not th or not td:
            continue

        header = th.text.lower().strip()

        if _is_cause_header(header):
            continue

        is_birth = any(key in header for key in ("born", "birth"))
        is_birth_alt_date = any(key in header for key in BIRTH_ALT_DATE_HEADERS)
        is_death = any(key in header for key in ("died", "death"))

        if is_birth or is_birth_alt_date or is_death:
            prefix = "birth" if (is_birth or is_birth_alt_date) else "death"
            date_str = None

            if prefix == "birth":
                date_str = _extract_date_from_cell(td)
                if date_str and (is_birth or not data.birth_date):
                    data.birth_date = date_str
            else:
                date_str = _extract_date_from_cell(td)
                if date_str:
                    data.death_date = date_str

            present_day_place = _extract_present_day_place(td.get_text(" ", strip=True))
            cleaned_place = _clean_place_text(td.get_text(), date_str)
            extracted_place = _extract_place_from_cell(td, date_str)
            final_place = present_day_place or extracted_place or cleaned_place
            if final_place and not _is_valid_place_name(final_place):
                final_place = None

            if prefix == "birth":
                if final_place:
                    data.birth_place = final_place
            else:
                if final_place:
                    data.death_place = final_place

            location_href = _extract_location_link(td, date_str=date_str, place_text=final_place)
            if not location_href:
                location_href = _find_previous_place_link(final_place, seen_place_links)
            else:
                location_href = _prefer_previous_link_for_composite_place(final_place, location_href, seen_place_links)

            if location_href:
                target_url = WIKIPEDIA_BASE_URL + location_href
                if verbose:
                    print(f" -> Found link for {prefix} place. Checking: {target_url}")
                lat, lon = get_coordinates_from_wikipedia_url(target_url, headers)

                if lat is not None and lon is not None:
                    if prefix == "birth":
                        data.birth_lat = lat
                        data.birth_lon = lon
                    else:
                        data.death_lat = lat
                        data.death_lon = lon
                    if verbose:
                        print(f"    [Success] Coordinates pulled from Wikipedia page: ({lat}, {lon})")
                else:
                    place_text = _extract_place_from_cell(td, date_str) or ""
                    if _is_valid_place_name(place_text):
                        if verbose:
                            print(f"    [Fallback] No direct coordinates. Geocoding link text: '{place_text}'")
                        lat, lon = geocode_fallback(place_text)
                    else:
                        lat, lon = None, None
                    if prefix == "birth":
                        data.birth_lat, data.birth_lon = lat, lon
                    else:
                        data.death_lat, data.death_lon = lat, lon
            else:
                if prefix == "birth" and extracted_place:
                    data.birth_place = extracted_place
                if prefix == "death" and extracted_place:
                    data.death_place = extracted_place

            _remember_place_links(td, seen_place_links)

            if prefix == "birth":
                if data.birth_lat is None:
                    if data.birth_place and _is_valid_place_name(data.birth_place):
                        if verbose:
                            print(f"    [Fallback] Geocoding raw location text: '{data.birth_place}'")
                        data.birth_lat, data.birth_lon = geocode_fallback(data.birth_place)
            else:
                if data.death_lat is None:
                    if data.death_place and _is_valid_place_name(data.death_place):
                        if verbose:
                            print(f"    [Fallback] Geocoding raw location text: '{data.death_place}'")
                        data.death_lat, data.death_lon = geocode_fallback(data.death_place)

    if not data.birth_date or not data.death_date:
        if verbose:
            print("Error: Missing birth/death dates; skipping subject.")
        return None

    if data.birth_lat is None or data.death_lat is None:
        if verbose:
            print("Error: Missing birth/death coordinates; skipping subject.")
        return None

    return data

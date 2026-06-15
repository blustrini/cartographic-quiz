import json
import re
from typing import Sequence

import folium
from branca.element import Element

from cartographic_quiz.constants import (
    BIRTH_ICON_ANCHOR,
    DEATH_ICON_ANCHOR,
    DEFAULT_REPEATS_EACH_SIDE,
    ICON_SIZE,
)
from cartographic_quiz.models import CartographicDate
from cartographic_quiz.svg_markers import build_birth_marker_svg, build_death_marker_svg, _format_display_date


COUNTRY_LEVEL_NAMES = {
  "afghanistan",
  "albania",
  "algeria",
  "argentina",
  "armenia",
  "australia",
  "austria",
  "azerbaijan",
  "bangladesh",
  "belarus",
  "belgium",
  "brazil",
  "bulgaria",
  "canada",
  "chile",
  "china",
  "colombia",
  "croatia",
  "cuba",
  "czech republic",
  "denmark",
  "egypt",
  "england",
  "ethiopia",
  "finland",
  "france",
  "georgia",
  "germany",
  "ghana",
  "greece",
  "hungary",
  "india",
  "indonesia",
  "iceland",
  "icelandic commonwealth",
  "iran",
  "iraq",
  "ireland",
  "israel",
  "italy",
  "japan",
  "kazakhstan",
  "kenya",
  "libya",
  "mexico",
  "morocco",
  "netherlands",
  "new zealand",
  "nigeria",
  "north korea",
  "norway",
  "pakistan",
  "peru",
  "poland",
  "portugal",
  "romania",
  "russia",
  "scotland",
  "serbia",
  "south africa",
  "south korea",
  "spain",
  "sweden",
  "switzerland",
  "syria",
  "thailand",
  "turkey",
  "tajikistan",
  "ukraine",
  "united kingdom",
  "united states",
  "united states of america",
  "vietnam",
  "wales",
  "james bay",
  "kingdom of england",
  "ross ice shelf",
  "king william island",
  "begwena",
  "lower lorraine",
  "english channel",
  "khentii mountains",
  "xingqing",
  "pannonia (?)",
  "alföld (great hungarian plain) (?)",
  "(northwestern) roman britain (?)",
  "tyrrhenian sea",
  "near rome",
  "dilmun (?)",
  "off the coast of calicut (kozhikode)",
  "trans-siberian train near lake baikal",
  "mohegan territory, connecticut colony",
}
COUNTRY_APPROX_RADIUS_METERS = 250_000
REGION_APPROX_RADIUS_METERS = 900_000
MAX_CITY_LEVEL_ZOOM = 9
REGION_LEVEL_NAMES = {
    "africa",
    "asia",
    "central asia",
    "east asia",
    "southeast asia",
    "south asia",
    "west asia",
    "europe",
    "central europe",
    "eastern europe",
    "western europe",
    "north america",
    "south america",
    "middle east",
    "levant",
    "mesopotamia",
    "caucasus",
    "balkans",
    "iberia",
    "mediterranean sea",
    "mediterranean sea, off the coast of marseilles",
    "pacific ocean",
    "atlantic ocean",
    "greenland",
    "mali empire",
    "north atlantic",
    "barents sea",
    "mongol empire",
    "along the syr darya river basin",
}
REGION_DIRECTIONAL_PATTERN = re.compile(
    r"\b(?:central|northern|southern|eastern|western|north|south|east|west)\b\s+"
    r"(?:asia|africa|europe|america|americas)\b"
)

CUSTOM_RADIUS_METES: dict[str, int] = {
  "pacific ocean": 3_500_000,
  "mediterranean sea, off the coast of marseilles": 150_000,
  "north atlantic": 1_700_000,
  "ross ice shelf": 300_000,
  "king william island": 100_000,
  "begwena": 200_000,
  "english channel": 160_000,
  "pannonia (?)" : 120_000,
  "alföld (great hungarian plain) (?)": 70_000,
  "(northwestern) roman britain (?)": 150_000,
  "tyrrhenian sea": 170_000,
  "near rome": 100_000,
  "dilmun (?)": 100_000,
  "off the coast of calicut (kozhikode)": 500_000,
  "trans-siberian train near lake baikal": 500_000,
  "mohegan territory, connecticut colony": 35_000,
  "barents sea": 100_000,
  "along the syr darya river basin": 300_000,
}


def _is_country_level_location(location_name: str | None) -> bool:
    if not location_name:
        return False
    normalized = location_name.strip().lower()
    return normalized in COUNTRY_LEVEL_NAMES


def _is_region_level_location(location_name: str | None) -> bool:
    if not location_name:
        return False
    normalized = " ".join(location_name.strip().lower().split())
    return normalized in REGION_LEVEL_NAMES or bool(REGION_DIRECTIONAL_PATTERN.search(normalized))


def _is_approximate_pin_location(location_name: str | None) -> bool:
    return _is_country_level_location(location_name) or _is_region_level_location(location_name)


def _approximate_radius_for_location(location_name: str | None) -> int:
    if location_name and (location_name.lower() in CUSTOM_RADIUS_METES):
      return CUSTOM_RADIUS_METES[location_name.lower()]
    if _is_region_level_location(location_name):
        return REGION_APPROX_RADIUS_METERS
    return COUNTRY_APPROX_RADIUS_METERS


def _build_popup(event_kind: str, location_name: str | None) -> str:
    place = location_name or "Unknown"
    if _is_country_level_location(location_name):
        return (
            f"<b>{event_kind}</b><br>"
            f"Place: {place}<br>"
            "<i>(exact location unknown)</i>"
        )
    if _is_region_level_location(location_name):
        return (
            f"<b>{event_kind}</b><br>"
            f"Place: {place}<br>"
            "<i>(exact location unknown)</i>"
        )
    return f"<b>{event_kind}</b><br>Place: {place}"


def _add_country_precision_circle(
    life_map: folium.Map,
    latitude: float,
    longitude: float,
    popup_html: str,
    *,
    radius_meters: int,
    color: str,
    fill_color: str,
) -> None:
    folium.Circle(
        location=[latitude, longitude],
        radius=radius_meters,
        popup=popup_html,
        color=color,
        weight=1,
        fill=True,
        fill_color=fill_color,
        fill_opacity=0.16,
        opacity=0.7,
    ).add_to(life_map)


def _build_country_date_label_html(date_str: str | None, *, color: str) -> str:
    prefix = "👶" if color == "#1b5e20" else "💀"
    label = f"{prefix} {_format_display_date(date_str)}"
    return (
        "<div class=\"country-date-label\" "
        "style=\""
        "display:inline-block;"
        "padding:2px 12px;"
        "border-radius:8px;"
        "background:rgba(255,255,255,0.9);"
        "border:1px solid rgba(0,0,0,0.2);"
        "font-family:Helvetica Neue, Arial, sans-serif;"
        "font-size:22px;"
        "line-height:1.15;"
        "font-weight:700;"
        f"color:{color};"
        "white-space:nowrap;"
        f"\">{label}</div>"
    )


def generate_life_map(
    birth_event: CartographicDate,
    death_event: CartographicDate,
    person_name: str,
    output_filename: str,
    repeats_each_side: int = DEFAULT_REPEATS_EACH_SIDE,
) -> None:
    """Generates the synchronized Mercator map with custom icons, permanent dates.

    and bounded repetitions matching horizontal scroll thresholds.
    """
    if birth_event.latitude is None or death_event.latitude is None:
        print("\nError: Cannot generate map. One or both coordinates failed to resolve.")
        return

    min_longitude = -180 - (repeats_each_side * 360)
    max_longitude = 180 + (repeats_each_side * 360)

    center_lat = (birth_event.latitude + death_event.latitude) / 2
    center_lon = (birth_event.longitude + death_event.longitude) / 2

    life_map = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=3,
        tiles="CartoDB Voyager",
        max_zoom=MAX_CITY_LEVEL_ZOOM,
        max_bounds=True,
        min_lat=-85,
        max_lat=85,
        min_lon=min_longitude,
        max_lon=max_longitude,
    )

    birth_html = build_birth_marker_svg(birth_event.date_str)
    death_html = build_death_marker_svg(death_event.date_str)

    for world_offset in range(-repeats_each_side, repeats_each_side + 1):
        lon_shift = world_offset * 360

        current_birth_lon = birth_event.longitude + lon_shift
        current_death_lon = death_event.longitude + lon_shift

        birth_popup = _build_popup("Birth", birth_event.location_name)
        death_popup = _build_popup("Death", death_event.location_name)

        if _is_approximate_pin_location(birth_event.location_name):
            birth_radius = _approximate_radius_for_location(birth_event.location_name)
            _add_country_precision_circle(
                life_map,
                birth_event.latitude,
                current_birth_lon,
                birth_popup,
                radius_meters=birth_radius,
                color="#1b5e20",
                fill_color="#66bb6a",
            )
            folium.Marker(
                location=[birth_event.latitude, current_birth_lon],
                icon=folium.DivIcon(
                    html=_build_country_date_label_html(birth_event.date_str, color="#1b5e20"),
                    icon_size=(320, 34),
                    icon_anchor=(160, 0),
                    class_name="empty",
                ),
            ).add_to(life_map)
        else:
            folium.Marker(
                location=[birth_event.latitude, current_birth_lon],
                popup=birth_popup,
                icon=folium.DivIcon(
                    html=birth_html,
                    icon_size=ICON_SIZE,
                    icon_anchor=BIRTH_ICON_ANCHOR,
                ),
            ).add_to(life_map)

        if _is_approximate_pin_location(death_event.location_name):
            death_radius = _approximate_radius_for_location(death_event.location_name)
            _add_country_precision_circle(
                life_map,
                death_event.latitude,
                current_death_lon,
                death_popup,
                radius_meters=death_radius,
                color="#b71c1c",
                fill_color="#ef5350",
            )
            folium.Marker(
                location=[death_event.latitude, current_death_lon],
                icon=folium.DivIcon(
                    html=_build_country_date_label_html(death_event.date_str, color="#b71c1c"),
                    icon_size=(320, 34),
                    icon_anchor=(160, 40),
                    class_name="empty",
                ),
            ).add_to(life_map)
        else:
            folium.Marker(
                location=[death_event.latitude, current_death_lon],
                popup=death_popup,
                icon=folium.DivIcon(
                    html=death_html,
                    icon_size=ICON_SIZE,
                    icon_anchor=DEATH_ICON_ANCHOR,
                ),
            ).add_to(life_map)

    quiz_html = fr"""\
    <style>
      @keyframes streak-flash {{
        0% {{ background-color: rgba(220, 53, 69, 0.3); }}
        100% {{ background-color: transparent; }}
      }}

      .streak-flash {{
        animation: streak-flash 600ms ease-out;
      }}
    </style>
    <div id="quiz-panel" style="position: fixed; top: 16px; left: 16px; z-index: 9999; background: rgba(255,255,255,0.92); border-radius: 10px; padding: 12px 14px; box-shadow: 0 6px 18px rgba(0,0,0,0.2); max-width: 320px; font-family: Helvetica Neue, Arial, sans-serif;">
      <div style="font-weight: 700; margin-bottom: 6px;">Guess The Person</div>
      <div style="font-size: 13px; margin-bottom: 8px;">Use the birth/death markers and map clues to guess who this is.</div>
      <input id="quiz-input" type="text" placeholder="Type a name" style="width: 100%; box-sizing: border-box; padding: 7px 8px; border: 1px solid #bdbdbd; border-radius: 6px; margin-bottom: 8px;" />
      <button id="quiz-submit" style="width: 100%; padding: 7px 8px; border: 0; border-radius: 6px; background: #1565c0; color: white; font-weight: 700; cursor: pointer;">Check Answer</button>
      <div id="quiz-result" style="margin-top: 8px; font-size: 13px;"></div>
      <div id="quiz-stats" style="margin-top: 6px; font-size: 12px; color: #666; font-weight: 600;">Correct: <span id="correct-count">0</span> | Streak: <span id="streak-count">0</span></div>
      <button id="quiz-reset" style="width: 100%; padding: 6px 8px; border: 0; border-radius: 6px; background: #e0e0e0; color: #555; font-weight: 500; font-size: 12px; cursor: pointer; margin-top: 6px;">Reset Score</button>
    </div>
    <script>
      (function() {{
        const expected = {person_name!r};
        const storageKeys = {{
          correct: "correctCount",
          streak: "streak",
        }};

        const normalize = (value) => (value || "")
          .toLowerCase()
          .normalize("NFD")
          .replace(/[\u0300-\u036f]/g, "")
          .replace(/['’`-]/g, "")
          .replace(/[^a-z0-9\s]/g, " ")
          .replace(/\s+/g, " ")
          .trim();

        const canonicalizeName = (value) => (value || "")
          .replace(/\bsaint\b/g, "st")
          .replace(/\s+/g, " ")
          .trim();

        const buildAcceptedAnswers = (expectedValue) => {{
          const variants = new Set();
          const normalizedExpected = normalize(expectedValue);
          if (normalizedExpected) {{
            variants.add(normalizedExpected);
            variants.add(canonicalizeName(normalizedExpected));
          }}

          const commaIndex = expectedValue.indexOf(",");
          if (commaIndex !== -1) {{
            const shortName = normalize(expectedValue.slice(0, commaIndex));
            if (shortName) {{
              variants.add(shortName);
              variants.add(canonicalizeName(shortName));
            }}
          }}

          return variants;
        }};

        const levenshteinDistance = (left, right) => {{
          if (left === right) {{
            return 0;
          }}

          const leftLength = left.length;
          const rightLength = right.length;
          if (leftLength === 0) {{
            return rightLength;
          }}
          if (rightLength === 0) {{
            return leftLength;
          }}

          const matrix = Array.from({{ length: leftLength + 1 }}, () => new Array(rightLength + 1).fill(0));
          for (let i = 0; i <= leftLength; i += 1) {{
            matrix[i][0] = i;
          }}
          for (let j = 0; j <= rightLength; j += 1) {{
            matrix[0][j] = j;
          }}

          for (let i = 1; i <= leftLength; i += 1) {{
            for (let j = 1; j <= rightLength; j += 1) {{
              const cost = left[i - 1] === right[j - 1] ? 0 : 1;
              matrix[i][j] = Math.min(
                matrix[i - 1][j] + 1,
                matrix[i][j - 1] + 1,
                matrix[i - 1][j - 1] + cost,
              );
            }}
          }}

          return matrix[leftLength][rightLength];
        }};

        const isTooGenericGuess = (guess, expectedValue) => {{
          const expectedTokens = expectedValue.split(" ").filter(Boolean);
          const guessTokens = guess.split(" ").filter(Boolean);
          if (expectedTokens.length < 2 || guessTokens.length !== 1) {{
            return false;
          }}
          return expectedTokens.includes(guessTokens[0]);
        }};

        const isCloseMatch = (guess, expectedValue) => {{
          if (!guess || !expectedValue) {{
            return false;
          }}
          if (Math.abs(guess.length - expectedValue.length) > 2) {{
            return false;
          }}
          const distance = levenshteinDistance(guess, expectedValue);
          const threshold = expectedValue.length <= 5 ? 1 : 2;
          return distance <= threshold;
        }};

        const input = document.getElementById("quiz-input");
        const submit = document.getElementById("quiz-submit");
        const result = document.getElementById("quiz-result");
        const correctCountElement = document.getElementById("correct-count");
        const streakCountElement = document.getElementById("streak-count");
        const reset = document.getElementById("quiz-reset");

        let correctCount = 0;
        let streak = 0;

        const updateScoreDisplay = () => {{
          if (correctCountElement) {{
            correctCountElement.textContent = String(correctCount);
          }}
          if (streakCountElement) {{
            streakCountElement.textContent = String(streak);
          }}
        }};

        const initializeScore = () => {{
          const storedCorrectCount = window.sessionStorage.getItem(storageKeys.correct);
          const storedStreak = window.sessionStorage.getItem(storageKeys.streak);

          const parsedCorrectCount = Number.parseInt(storedCorrectCount || "0", 10);
          const parsedStreak = Number.parseInt(storedStreak || "0", 10);

          correctCount = Number.isNaN(parsedCorrectCount) ? 0 : parsedCorrectCount;
          streak = Number.isNaN(parsedStreak) ? 0 : parsedStreak;
          updateScoreDisplay();
        }};

        const flashStreakReset = () => {{
          if (!streakCountElement) {{
            return;
          }}

          streakCountElement.classList.remove("streak-flash");
          void streakCountElement.offsetWidth;
          streakCountElement.classList.add("streak-flash");
          window.setTimeout(() => {{
            streakCountElement.classList.remove("streak-flash");
          }}, 600);
        }};

        const check = () => {{
          if (!input || !result) {{
            return;
          }}

          if (awaitingAdvance) {{
            return;
          }}

          const guess = canonicalizeName(normalize(input.value));
          const acceptedAnswers = buildAcceptedAnswers(expected);
          const normalizedExpected = canonicalizeName(normalize(expected));

          if (isTooGenericGuess(guess, normalizedExpected)) {{
            result.style.color = "#7f6000";
            result.textContent = "Please enter the full name, not just a surname.";
            input.focus();
            return;
          }}

          const matchedExactly = acceptedAnswers.has(guess);
          const matchedClosely = Array.from(acceptedAnswers).some((candidate) => isCloseMatch(guess, candidate));

          if (matchedExactly || matchedClosely) {{
            correctCount += 1;
            streak += 1;
            window.sessionStorage.setItem(storageKeys.correct, String(correctCount));
            window.sessionStorage.setItem(storageKeys.streak, String(streak));
            updateScoreDisplay();

            result.style.color = "#1b5e20";
            result.textContent = "Correct!";
            input.value = "";
            input.focus();
            return;
          }}

          streak = 0;
          window.sessionStorage.setItem(storageKeys.streak, String(streak));
          updateScoreDisplay();
          result.style.color = "#b71c1c";
          result.textContent = "Not quite. Try again.";
          flashStreakReset();
        }};

        const resetScore = () => {{
          if (window.sessionStorage) {{
            window.sessionStorage.removeItem(storageKeys.correct);
            window.sessionStorage.removeItem(storageKeys.streak);
          }}

          correctCount = 0;
          streak = 0;
          updateScoreDisplay();

          if (result) {{
            result.textContent = "";
          }}
          if (input) {{
            input.value = "";
            input.focus();
          }}
        }};

        if (submit) {{
          submit.addEventListener("click", check);
        }}
        if (input) {{
          input.addEventListener("keydown", (event) => {{
            if (event.key === "Enter") {{
              event.preventDefault();
              event.stopPropagation();
              if (awaitingAdvance) {{
                nextRound();
              }} else {{
                check();
              }}
            }}
          }});
        }}
        if (reset) {{
          reset.addEventListener("click", resetScore);
        }}

        initializeScore();
      }})();
    </script>
    """

    life_map.get_root().html.add_child(Element(quiz_html))

    life_map.save(output_filename)
    print(f"\n🎉 Success! Interactive biographical map saved to '{output_filename}'")


def generate_multi_life_map(
    rounds: Sequence[tuple[CartographicDate, CartographicDate, str]],
    output_filename: str,
    repeats_each_side: int = DEFAULT_REPEATS_EACH_SIDE,
) -> None:
    """Generate a multi-round map quiz cycling through multiple people."""
    valid_rounds = [
        round_data
        for round_data in rounds
        if (
            round_data[0].latitude is not None
            and round_data[0].longitude is not None
            and round_data[1].latitude is not None
            and round_data[1].longitude is not None
        )
    ]
    if not valid_rounds:
        print("\nError: Cannot generate map. No rounds with valid coordinates were provided.")
        return

    min_longitude = -180 - (repeats_each_side * 360)
    max_longitude = 180 + (repeats_each_side * 360)

    avg_birth_lat = sum(round_data[0].latitude for round_data in valid_rounds) / len(valid_rounds)
    avg_death_lat = sum(round_data[1].latitude for round_data in valid_rounds) / len(valid_rounds)
    avg_birth_lon = sum(round_data[0].longitude for round_data in valid_rounds) / len(valid_rounds)
    avg_death_lon = sum(round_data[1].longitude for round_data in valid_rounds) / len(valid_rounds)

    center_lat = (avg_birth_lat + avg_death_lat) / 2
    center_lon = (avg_birth_lon + avg_death_lon) / 2

    life_map = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=2,
        tiles="CartoDB Voyager",
        max_zoom=MAX_CITY_LEVEL_ZOOM,
        max_bounds=True,
        min_lat=-85,
        max_lat=85,
        min_lon=min_longitude,
        max_lon=max_longitude,
    )

    rendered_rounds: list[dict[str, object]] = []
    for birth_event, death_event, person_name in valid_rounds:
        rendered_rounds.append(
            {
                "person": person_name,
                "birth": {
                    "lat": birth_event.latitude,
                    "lon": birth_event.longitude,
                    "date": birth_event.date_str,
                    "place": birth_event.location_name,
                    "popup": _build_popup("Birth", birth_event.location_name),
                    "country_level": _is_approximate_pin_location(birth_event.location_name),
                    "icon": (
                        None
                        if _is_approximate_pin_location(birth_event.location_name)
                        else build_birth_marker_svg(birth_event.date_str)
                    ),
                    "country_label_html": (
                        _build_country_date_label_html(birth_event.date_str, color="#1b5e20")
                        if _is_approximate_pin_location(birth_event.location_name)
                        else None
                    ),
                    "circle_radius": _approximate_radius_for_location(birth_event.location_name),
                },
                "death": {
                    "lat": death_event.latitude,
                    "lon": death_event.longitude,
                    "date": death_event.date_str,
                    "place": death_event.location_name,
                    "popup": _build_popup("Death", death_event.location_name),
                    "country_level": _is_approximate_pin_location(death_event.location_name),
                    "icon": (
                        None
                        if _is_approximate_pin_location(death_event.location_name)
                        else build_death_marker_svg(death_event.date_str)
                    ),
                    "country_label_html": (
                        _build_country_date_label_html(death_event.date_str, color="#b71c1c")
                        if _is_approximate_pin_location(death_event.location_name)
                        else None
                    ),
                    "circle_radius": _approximate_radius_for_location(death_event.location_name),
                },
            }
        )

    map_name = life_map.get_name()
    rounds_json = json.dumps(rendered_rounds)

    quiz_html = fr"""\
    <div id="quiz-panel" style="position: fixed; top: 16px; left: 16px; z-index: 9999; background: rgba(255,255,255,0.94); border-radius: 10px; padding: 12px 14px; box-shadow: 0 6px 18px rgba(0,0,0,0.2); max-width: 340px; font-family: Helvetica Neue, Arial, sans-serif;">
      <div style="font-weight: 700; margin-bottom: 6px;">Guess The Person</div>
      <div id="quiz-progress" style="font-size: 12px; color: #555; margin-bottom: 6px;">Round 1/{len(valid_rounds)}</div>
      <div id="quiz-instructions" style="font-size: 13px; margin-bottom: 8px;">One guess per round. Wrong answers move to the next person.</div>
      <input id="quiz-input" type="text" placeholder="Type a name" style="width: 100%; box-sizing: border-box; padding: 7px 8px; border: 1px solid #bdbdbd; border-radius: 6px; margin-bottom: 8px;" />
      <button id="quiz-submit" style="width: 100%; padding: 7px 8px; border: 0; border-radius: 6px; background: #1565c0; color: white; font-weight: 700; cursor: pointer;">Submit Guess</button>
      <div id="quiz-emoji-grid" style="display: none; margin-top: 8px; font-size: 24px; line-height: 1.25; letter-spacing: 1px;"></div>
      <button id="quiz-copy-summary" style="display: none; width: 100%; padding: 6px 8px; border: 0; border-radius: 6px; background: #455a64; color: white; font-weight: 600; cursor: pointer; margin-top: 8px;">Copy Emoji Summary</button>
      <div id="quiz-copy-status" style="margin-top: 6px; font-size: 12px; color: #546e7a; min-height: 16px;"></div>
      <div id="quiz-result" style="margin-top: 8px; font-size: 13px;"></div>
      <div id="quiz-controls" style="display: none; margin-top: 8px;">
        <button id="quiz-continue" style="width: 100%; padding: 7px 8px; border: 0; border-radius: 6px; background: #2e7d32; color: white; font-weight: 700; cursor: pointer; margin-bottom: 6px;">Continue</button>
        <div style="display: flex; gap: 6px;">
          <button id="quiz-force-correct" style="flex: 1; padding: 6px 8px; border: 0; border-radius: 6px; background: #43a047; color: white; font-weight: 600; cursor: pointer;">Force Correct</button>
          <button id="quiz-force-wrong" style="flex: 1; padding: 6px 8px; border: 0; border-radius: 6px; background: #e53935; color: white; font-weight: 600; cursor: pointer;">Force Wrong</button>
        </div>
      </div>
      <div id="quiz-stats" style="margin-top: 6px; font-size: 12px; color: #666; font-weight: 600;">Correct: <span id="correct-count">0</span> | Wrong: <span id="wrong-count">0</span></div>
    </div>
    <script>
      (function() {{
        const rounds = {rounds_json};
        const mapName = "{map_name}";

        const normalize = (value) => (value || "")
          .toLowerCase()
          .normalize("NFD")
          .replace(/[\u0300-\u036f]/g, "")
          .replace(/['’`-]/g, "")
          .replace(/[^a-z0-9\s]/g, " ")
          .replace(/\s+/g, " ")
          .trim();

        const canonicalizeName = (value) => (value || "")
          .replace(/\bsaint\b/g, "st")
          .replace(/\s+/g, " ")
          .trim();

        const buildAcceptedAnswers = (expectedValue) => {{
          const variants = new Set();
          const normalizedExpected = normalize(expectedValue);
          if (normalizedExpected) {{
            variants.add(normalizedExpected);
            variants.add(canonicalizeName(normalizedExpected));
          }}

          const commaIndex = expectedValue.indexOf(",");
          if (commaIndex !== -1) {{
            const shortName = normalize(expectedValue.slice(0, commaIndex));
            if (shortName) {{
              variants.add(shortName);
              variants.add(canonicalizeName(shortName));
            }}
          }}

          return variants;
        }};

        const levenshteinDistance = (left, right) => {{
          if (left === right) {{
            return 0;
          }}

          const leftLength = left.length;
          const rightLength = right.length;
          if (leftLength === 0) {{
            return rightLength;
          }}
          if (rightLength === 0) {{
            return leftLength;
          }}

          const matrix = Array.from({{ length: leftLength + 1 }}, () => new Array(rightLength + 1).fill(0));
          for (let i = 0; i <= leftLength; i += 1) {{
            matrix[i][0] = i;
          }}
          for (let j = 0; j <= rightLength; j += 1) {{
            matrix[0][j] = j;
          }}

          for (let i = 1; i <= leftLength; i += 1) {{
            for (let j = 1; j <= rightLength; j += 1) {{
              const cost = left[i - 1] === right[j - 1] ? 0 : 1;
              matrix[i][j] = Math.min(
                matrix[i - 1][j] + 1,
                matrix[i][j - 1] + 1,
                matrix[i - 1][j - 1] + cost,
              );
            }}
          }}

          return matrix[leftLength][rightLength];
        }};

        const isTooGenericGuess = (guess, expectedValue) => {{
          const expectedTokens = expectedValue.split(" ").filter(Boolean);
          const guessTokens = guess.split(" ").filter(Boolean);
          if (expectedTokens.length < 2 || guessTokens.length !== 1) {{
            return false;
          }}
          return expectedTokens.includes(guessTokens[0]);
        }};

        const isCloseMatch = (guess, expectedValue) => {{
          if (!guess || !expectedValue) {{
            return false;
          }}
          if (Math.abs(guess.length - expectedValue.length) > 2) {{
            return false;
          }}
          const distance = levenshteinDistance(guess, expectedValue);
          const threshold = expectedValue.length <= 5 ? 1 : 2;
          return distance <= threshold;
        }};

        const input = document.getElementById("quiz-input");
        const submit = document.getElementById("quiz-submit");
        const result = document.getElementById("quiz-result");
        const instructions = document.getElementById("quiz-instructions");
        const emojiGrid = document.getElementById("quiz-emoji-grid");
        const progress = document.getElementById("quiz-progress");
        const correctCountElement = document.getElementById("correct-count");
        const wrongCountElement = document.getElementById("wrong-count");
        const controls = document.getElementById("quiz-controls");
        const continueButton = document.getElementById("quiz-continue");
        const forceCorrectButton = document.getElementById("quiz-force-correct");
        const forceWrongButton = document.getElementById("quiz-force-wrong");
        const copySummaryButton = document.getElementById("quiz-copy-summary");
        const copyStatus = document.getElementById("quiz-copy-status");

        let currentIndex = 0;
        let correctCount = 0;
        let wrongCount = 0;
        const roundResults = [];
        let mapRef = null;
        let roundLayer = null;
        let awaitingAdvance = false;
        let pendingResultIndex = -1;
        let latestEmojiSummary = "";

        const setCopyStatus = (message, color = "#546e7a") => {{
          if (!copyStatus) {{
            return;
          }}
          copyStatus.style.color = color;
          copyStatus.textContent = message;
        }};

        const buildEmojiSummary = () => {{
          const total = roundResults.length;
          if (!total) {{
            return "";
          }}

          const columns = total >= 10 ? 5 : Math.min(5, total);
          const symbols = roundResults.map((entry) => (entry.isCorrect ? "✅" : "❌"));
          const lines = [];

          for (let i = 0; i < symbols.length; i += columns) {{
            lines.push(symbols.slice(i, i + columns).join(""));
          }}

          return `Cartographic Quiz: ${{correctCount}}/${{total}} correct\n${{lines.join("\n")}}`;
        }};

        const buildEmojiGridHtml = () => {{
          const total = roundResults.length;
          if (!total) {{
            return "";
          }}

          const columns = total >= 10 ? 5 : Math.min(5, total);
          const symbols = roundResults.map((entry) => (entry.isCorrect ? "✅" : "❌"));
          const lines = [];

          for (let i = 0; i < symbols.length; i += columns) {{
            lines.push(symbols.slice(i, i + columns).join(""));
          }}

          return lines.join("<br>");
        }};

        const copyTextToClipboard = async (text) => {{
          if (navigator.clipboard && navigator.clipboard.writeText) {{
            await navigator.clipboard.writeText(text);
            return;
          }}

          const textArea = document.createElement("textarea");
          textArea.value = text;
          textArea.style.position = "fixed";
          textArea.style.opacity = "0";
          document.body.appendChild(textArea);
          textArea.focus();
          textArea.select();
          document.execCommand("copy");
          document.body.removeChild(textArea);
        }};

        const buildWikipediaUrl = (personName) => {{
          const normalized = (personName || "").trim().replace(/\s+/g, "_");
          return `https://en.wikipedia.org/wiki/${{encodeURIComponent(normalized)}}`;
        }};

        const setGuessingLocked = (locked) => {{
          if (input) {{
            input.disabled = locked;
          }}
          if (submit) {{
            submit.disabled = locked;
            submit.style.opacity = locked ? "0.65" : "1";
          }}
        }};

        const setControlsVisible = (visible) => {{
          if (!controls) {{
            return;
          }}
          controls.style.display = visible ? "block" : "none";
        }};

        const updateStats = () => {{
          if (correctCountElement) {{
            correctCountElement.textContent = String(correctCount);
          }}
          if (wrongCountElement) {{
            wrongCountElement.textContent = String(wrongCount);
          }}
          if (progress) {{
            const shownRound = Math.min(currentIndex + 1, rounds.length);
            progress.textContent = `Round ${{shownRound}}/${{rounds.length}}`;
          }}
        }};

        const drawRound = (roundIndex) => {{
          if (!mapRef || !roundLayer) {{
            return;
          }}

          const round = rounds[roundIndex];
          if (!round) {{
            return;
          }}

          roundLayer.clearLayers();

          if (round.birth.country_level) {{
            L.circle([round.birth.lat, round.birth.lon], {{
              radius: round.birth.circle_radius,
              color: "#1b5e20",
              weight: 1,
              fillColor: "#66bb6a",
              fillOpacity: 0.16,
            }}).bindPopup(round.birth.popup).addTo(roundLayer);
            if (round.birth.country_label_html) {{
              const birthLabelIcon = L.divIcon({{
                html: round.birth.country_label_html,
                iconSize: [320, 34],
                iconAnchor: [160, 0],
                className: "empty",
              }});
              L.marker([round.birth.lat, round.birth.lon], {{ icon: birthLabelIcon, interactive: false }})
                .addTo(roundLayer);
            }}
          }} else {{
            const birthIcon = L.divIcon({{
              html: round.birth.icon,
              iconSize: [320, 90],
              iconAnchor: [160, 0],
              className: "empty",
            }});
            L.marker([round.birth.lat, round.birth.lon], {{ icon: birthIcon }})
              .bindPopup(round.birth.popup)
              .addTo(roundLayer);
          }}

          if (round.death.country_level) {{
            L.circle([round.death.lat, round.death.lon], {{
              radius: round.death.circle_radius,
              color: "#b71c1c",
              weight: 1,
              fillColor: "#ef5350",
              fillOpacity: 0.16,
            }}).bindPopup(round.death.popup).addTo(roundLayer);
            if (round.death.country_label_html) {{
              const deathLabelIcon = L.divIcon({{
                html: round.death.country_label_html,
                iconSize: [320, 34],
                iconAnchor: [160, 34],
                className: "empty",
              }});
              L.marker([round.death.lat, round.death.lon], {{ icon: deathLabelIcon, interactive: false }})
                .addTo(roundLayer);
            }}
          }} else {{
            const deathIcon = L.divIcon({{
              html: round.death.icon,
              iconSize: [320, 90],
              iconAnchor: [160, 90],
              className: "empty",
            }});
            L.marker([round.death.lat, round.death.lon], {{ icon: deathIcon }})
              .bindPopup(round.death.popup)
              .addTo(roundLayer);
          }}

          const bounds = L.latLngBounds([
            [round.birth.lat, round.birth.lon],
            [round.death.lat, round.death.lon],
          ]);
          mapRef.fitBounds(bounds.pad(0.5), {{ maxZoom: {MAX_CITY_LEVEL_ZOOM} }});
        }};

        const renderRound = () => {{
          drawRound(currentIndex);
          updateStats();
        }};

        const finishQuiz = () => {{
          if (!input || !submit || !result || !progress) {{
            return;
          }}

          setControlsVisible(false);
          setGuessingLocked(true);

          const total = rounds.length;
          const accuracy = total ? Math.round((correctCount / total) * 100) : 0;
          progress.textContent = `Complete (${{total}}/${{total}})`;
          result.style.color = "#263238";

          result.innerHTML = `
            <div style="margin-bottom: 8px;">
              Finished! Correct: <b>${{correctCount}}</b> | Wrong: <b>${{wrongCount}}</b> | Accuracy: <b>${{accuracy}}%</b>
            </div>
          `;

          const detailItems = roundResults.map((entry, index) => `
            <button type="button" class="quiz-round-item" data-round-index="${{index}}" style="display: block; width: 100%; text-align: left; border: 1px solid #d0d0d0; border-radius: 6px; padding: 6px; margin-top: 6px; background: #fafafa; cursor: pointer;">
              <div style="font-weight: 600; margin-bottom: 4px;">Round ${{index + 1}}</div>
              <div>Birth: ${{entry.birthDate}} - ${{entry.birthPlace}}</div>
              <div>Death: ${{entry.deathDate}} - ${{entry.deathPlace}}</div>
              <div>Your guess: <b>${{entry.guess}}</b></div>
              <div>Answer: <a href="${{buildWikipediaUrl(entry.answer)}}" target="_blank" rel="noopener noreferrer"><b>${{entry.answer}}</b></a></div>
              <div>Result: <b>${{entry.isCorrect ? "Correct" : "Wrong"}}</b>${{entry.overridden ? " (manual override)" : ""}}</div>
            </button>
          `).join("");

          result.style.maxHeight = "260px";
          result.style.overflowY = "auto";
          result.innerHTML += detailItems;

          if (instructions) {{
            instructions.style.display = "none";
          }}
          input.style.display = "none";
          submit.style.display = "none";

          if (emojiGrid) {{
            emojiGrid.innerHTML = buildEmojiGridHtml();
            emojiGrid.style.display = "block";
          }}

          latestEmojiSummary = buildEmojiSummary();
          if (copySummaryButton) {{
            copySummaryButton.style.display = "block";
          }}
          setCopyStatus("Copy your emoji scorecard to share.");

          result.addEventListener("click", (event) => {{
            const target = event.target;
            if (!(target instanceof Element)) {{
              return;
            }}

            const item = target.closest(".quiz-round-item");
            if (!item) {{
              return;
            }}

            const roundIndexRaw = item.getAttribute("data-round-index");
            const roundIndex = Number.parseInt(roundIndexRaw || "", 10);
            if (Number.isNaN(roundIndex)) {{
              return;
            }}

            drawRound(roundIndex);
          }});
        }};

        const nextRound = () => {{
          awaitingAdvance = false;
          pendingResultIndex = -1;
          setControlsVisible(false);
          setGuessingLocked(false);

          currentIndex += 1;
          if (currentIndex >= rounds.length) {{
            finishQuiz();
            return;
          }}

          if (input) {{
            input.value = "";
            input.focus();
          }}
          renderRound();
        }};

        const check = () => {{
          if (!input || !result) {{
            return;
          }}

          const guess = canonicalizeName(normalize(input.value));
          const acceptedAnswers = buildAcceptedAnswers(rounds[currentIndex].person);
          const normalizedExpected = canonicalizeName(normalize(rounds[currentIndex].person));

          if (isTooGenericGuess(guess, normalizedExpected)) {{
            result.style.color = "#7f6000";
            result.textContent = "Please enter the full name, not just a surname.";
            input.focus();
            return;
          }}

          const rawGuess = (input.value || "").trim();
          const revealed = rounds[currentIndex].person;
          const revealedLink = `<a href="${{buildWikipediaUrl(revealed)}}" target="_blank" rel="noopener noreferrer">${{revealed}}</a>`;
          let isCorrect = false;
          const matchedExactly = acceptedAnswers.has(guess);
          const matchedClosely = Array.from(acceptedAnswers).some((candidate) => isCloseMatch(guess, candidate));

          if (matchedExactly || matchedClosely) {{
            correctCount += 1;
            isCorrect = true;
            result.style.color = "#1b5e20";
            result.innerHTML = `Correct! It was ${{revealedLink}}.`;
          }} else {{
            wrongCount += 1;
            result.style.color = "#b71c1c";
            result.innerHTML = `Not quite. It was ${{revealedLink}}.`;
          }}

          roundResults.push({{
            birthDate: rounds[currentIndex].birth.date,
            birthPlace: rounds[currentIndex].birth.place,
            deathDate: rounds[currentIndex].death.date,
            deathPlace: rounds[currentIndex].death.place,
            guess: rawGuess || "(blank)",
            answer: revealed,
            isCorrect,
            overridden: false,
          }});
          pendingResultIndex = roundResults.length - 1;

          updateStats();
          awaitingAdvance = true;
          setGuessingLocked(true);
          setControlsVisible(true);
        }};

        const applyManualOverride = (forceCorrect) => {{
          if (!result || pendingResultIndex < 0) {{
            return;
          }}

          const entry = roundResults[pendingResultIndex];
          if (!entry) {{
            return;
          }}

          if (entry.isCorrect !== forceCorrect) {{
            if (forceCorrect) {{
              wrongCount = Math.max(0, wrongCount - 1);
              correctCount += 1;
            }} else {{
              correctCount = Math.max(0, correctCount - 1);
              wrongCount += 1;
            }}
            entry.isCorrect = forceCorrect;
          }}

          entry.overridden = true;
          updateStats();
          result.style.color = forceCorrect ? "#1b5e20" : "#b71c1c";
          const answerLink = `<a href="${{buildWikipediaUrl(entry.answer)}}" target="_blank" rel="noopener noreferrer">${{entry.answer}}</a>`;
          result.innerHTML = forceCorrect
            ? `Manually set to correct. It was ${{answerLink}}.`
            : `Manually set to wrong. It was ${{answerLink}}.`;
        }};

        if (submit) {{
          submit.addEventListener("click", check);
        }}
        if (continueButton) {{
          continueButton.addEventListener("click", nextRound);
        }}
        if (forceCorrectButton) {{
          forceCorrectButton.addEventListener("click", () => applyManualOverride(true));
        }}
        if (forceWrongButton) {{
          forceWrongButton.addEventListener("click", () => applyManualOverride(false));
        }}
        if (input) {{
          input.addEventListener("keydown", (event) => {{
            if (event.key === "Enter") {{
              event.preventDefault();
              event.stopPropagation();
              if (awaitingAdvance) {{
                nextRound();
              }} else {{
                check();
              }}
            }}
          }});
        }}
        document.addEventListener("keydown", (event) => {{
          if (event.key !== "Enter" || !awaitingAdvance) {{
            return;
          }}
          event.preventDefault();
          nextRound();
        }});
        if (copySummaryButton) {{
          copySummaryButton.addEventListener("click", async () => {{
            if (!latestEmojiSummary) {{
              setCopyStatus("No summary available yet.", "#b71c1c");
              return;
            }}

            try {{
              await copyTextToClipboard(latestEmojiSummary);
              setCopyStatus("Copied emoji scorecard to clipboard.", "#1b5e20");
            }} catch (_error) {{
              setCopyStatus("Could not copy automatically. Select and copy manually.", "#b71c1c");
            }}
          }});
        }}

        const initializeQuiz = () => {{
          if (typeof L === "undefined") {{
            window.setTimeout(initializeQuiz, 50);
            return;
          }}

          const mapFromWindow = window[mapName];
          if (!mapFromWindow) {{
            window.setTimeout(initializeQuiz, 50);
            return;
          }}

          mapRef = mapFromWindow;
          roundLayer = L.layerGroup().addTo(mapRef);
          if (input) {{
            input.focus();
          }}
          renderRound();
        }};

        initializeQuiz();
      }})();
    </script>
    """

    life_map.get_root().html.add_child(Element(quiz_html))
    life_map.save(output_filename)
    print(f"\n🎉 Success! Multi-round quiz map saved to '{output_filename}'")

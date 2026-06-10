import json
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
from cartographic_quiz.svg_markers import build_birth_marker_svg, build_death_marker_svg


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

        folium.Marker(
            location=[birth_event.latitude, current_birth_lon],
            popup=f"<b>Birth</b><br>Place: {birth_event.location_name}",
            icon=folium.DivIcon(
                html=birth_html,
                icon_size=ICON_SIZE,
                icon_anchor=BIRTH_ICON_ANCHOR,
            ),
        ).add_to(life_map)

        folium.Marker(
            location=[death_event.latitude, current_death_lon],
            popup=f"<b>Death</b><br>Place: {death_event.location_name}",
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

          const guess = normalize(input.value);
          const normalizedExpected = normalize(expected);
          if (!guess) {{
            result.style.color = "#7f6000";
            result.textContent = "Enter a guess first.";
            input.focus();
            return;
          }}

          if (isTooGenericGuess(guess, normalizedExpected)) {{
            result.style.color = "#7f6000";
            result.textContent = "Please enter the full name, not just a surname.";
            input.focus();
            return;
          }}

          if (guess === normalizedExpected || isCloseMatch(guess, normalizedExpected)) {{
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
              check();
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
                    "popup": f"<b>Birth</b><br>Place: {birth_event.location_name}",
                    "icon": build_birth_marker_svg(birth_event.date_str),
                },
                "death": {
                    "lat": death_event.latitude,
                    "lon": death_event.longitude,
                    "date": death_event.date_str,
                    "place": death_event.location_name,
                    "popup": f"<b>Death</b><br>Place: {death_event.location_name}",
                    "icon": build_death_marker_svg(death_event.date_str),
                },
            }
        )

    map_name = life_map.get_name()
    rounds_json = json.dumps(rendered_rounds)

    quiz_html = fr"""\
    <div id="quiz-panel" style="position: fixed; top: 16px; left: 16px; z-index: 9999; background: rgba(255,255,255,0.94); border-radius: 10px; padding: 12px 14px; box-shadow: 0 6px 18px rgba(0,0,0,0.2); max-width: 340px; font-family: Helvetica Neue, Arial, sans-serif;">
      <div style="font-weight: 700; margin-bottom: 6px;">Guess The Person</div>
      <div id="quiz-progress" style="font-size: 12px; color: #555; margin-bottom: 6px;">Round 1/{len(valid_rounds)}</div>
      <div style="font-size: 13px; margin-bottom: 8px;">One guess per round. Wrong answers move to the next person.</div>
      <input id="quiz-input" type="text" placeholder="Type a name" style="width: 100%; box-sizing: border-box; padding: 7px 8px; border: 1px solid #bdbdbd; border-radius: 6px; margin-bottom: 8px;" />
      <button id="quiz-submit" style="width: 100%; padding: 7px 8px; border: 0; border-radius: 6px; background: #1565c0; color: white; font-weight: 700; cursor: pointer;">Submit Guess</button>
      <div id="quiz-result" style="margin-top: 8px; font-size: 13px;"></div>
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
        const progress = document.getElementById("quiz-progress");
        const correctCountElement = document.getElementById("correct-count");
        const wrongCountElement = document.getElementById("wrong-count");

        let currentIndex = 0;
        let correctCount = 0;
        let wrongCount = 0;
        const roundResults = [];
        let mapRef = null;
        let roundLayer = null;

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

          const birthIcon = L.divIcon({{
            html: round.birth.icon,
            iconSize: [320, 90],
            iconAnchor: [160, 0],
            className: "empty",
          }});
          L.marker([round.birth.lat, round.birth.lon], {{ icon: birthIcon }})
            .bindPopup(round.birth.popup)
            .addTo(roundLayer);

          const deathIcon = L.divIcon({{
            html: round.death.icon,
            iconSize: [320, 90],
            iconAnchor: [160, 90],
            className: "empty",
          }});
          L.marker([round.death.lat, round.death.lon], {{ icon: deathIcon }})
            .bindPopup(round.death.popup)
            .addTo(roundLayer);

          const bounds = L.latLngBounds([
            [round.birth.lat, round.birth.lon],
            [round.death.lat, round.death.lon],
          ]);
          mapRef.fitBounds(bounds.pad(0.5));
        }};

        const renderRound = () => {{
          drawRound(currentIndex);
          updateStats();
        }};

        const finishQuiz = () => {{
          if (!input || !submit || !result || !progress) {{
            return;
          }}

          input.disabled = true;
          submit.disabled = true;
          submit.style.opacity = "0.65";

          const total = rounds.length;
          const accuracy = total ? Math.round((correctCount / total) * 100) : 0;
          progress.textContent = `Complete (${{total}}/${{total}})`;
          result.style.color = "#263238";

          const summaryHeader = `
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
              <div>Answer: <b>${{entry.answer}}</b></div>
            </button>
          `).join("");

          result.style.maxHeight = "260px";
          result.style.overflowY = "auto";
          result.innerHTML = summaryHeader + detailItems;

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

          const guess = normalize(input.value);
          const normalizedExpected = normalize(rounds[currentIndex].person);
          if (!guess) {{
            result.style.color = "#7f6000";
            result.textContent = "Enter a guess first.";
            input.focus();
            return;
          }}

          if (isTooGenericGuess(guess, normalizedExpected)) {{
            result.style.color = "#7f6000";
            result.textContent = "Please enter the full name, not just a surname.";
            input.focus();
            return;
          }}

          const rawGuess = (input.value || "").trim();
          const revealed = rounds[currentIndex].person;
          if (guess === normalizedExpected || isCloseMatch(guess, normalizedExpected)) {{
            correctCount += 1;
            result.style.color = "#1b5e20";
            result.textContent = `Correct! It was ${{revealed}}.`;
          }} else {{
            wrongCount += 1;
            result.style.color = "#b71c1c";
            result.textContent = `Not quite. It was ${{revealed}}.`;
          }}

          roundResults.push({{
            birthDate: rounds[currentIndex].birth.date,
            birthPlace: rounds[currentIndex].birth.place,
            deathDate: rounds[currentIndex].death.date,
            deathPlace: rounds[currentIndex].death.place,
            guess: rawGuess || "(blank)",
            answer: revealed,
          }});

          updateStats();
          window.setTimeout(nextRound, 500);
        }};

        if (submit) {{
          submit.addEventListener("click", check);
        }}
        if (input) {{
          input.addEventListener("keydown", (event) => {{
            if (event.key === "Enter") {{
              check();
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

import re
import unicodedata

from cartographic_quiz.map_renderer import generate_life_map
from cartographic_quiz.models import CartographicDate


def _render_map_html(tmp_path, person_name: str = "Napoleon Bonaparte") -> str:
    output_file = tmp_path / "quiz_map.html"
    birth_event = CartographicDate(
        date_str="15 August 1769",
        location_name="Ajaccio",
        latitude=41.9192,
        longitude=8.7386,
    )
    death_event = CartographicDate(
        date_str="5 May 1821",
        location_name="Longwood",
        latitude=-15.9487,
        longitude=-5.7206,
    )

    generate_life_map(
        birth_event=birth_event,
        death_event=death_event,
        person_name=person_name,
        output_filename=str(output_file),
    )
    return output_file.read_text(encoding="utf-8")


def _normalize_for_test(value: str) -> str:
    decomposed = unicodedata.normalize("NFD", value.lower())
    no_accents = "".join(ch for ch in decomposed if not unicodedata.combining(ch))
    no_apostrophes_or_hyphens = re.sub(r"['\u2019`-]", "", no_accents)
    alnum_with_spaces = re.sub(r"[^a-z0-9\s]", " ", no_apostrophes_or_hyphens)
    return re.sub(r"\s+", " ", alnum_with_spaces).strip()


def test_answer_normalization_handles_expected_cases():
    assert _normalize_for_test("napoleon") == _normalize_for_test("Napoleon")
    assert _normalize_for_test("mary queen of scots") == _normalize_for_test("Mary Queen of Scots")
    assert _normalize_for_test("josé martí") == _normalize_for_test("jose marti")
    assert _normalize_for_test("jean-paul sartre") == _normalize_for_test("jeanpaul sartre")
    assert _normalize_for_test("d'artagnan") == _normalize_for_test("dartagnan")
    assert _normalize_for_test("  mary    queen   of   scots  ") == "mary queen of scots"
    assert _normalize_for_test("François! @de? #la* Rochefoucauld") == "francois de la rochefoucauld"
    assert _normalize_for_test("") == ""
    assert _normalize_for_test("1234") == "1234"
    assert _normalize_for_test("#$%^&*") == ""


def test_quiz_panel_html_contains_interactive_game_elements(tmp_path):
    html = _render_map_html(tmp_path)

    assert 'id="quiz-panel"' in html
    assert 'id="quiz-input"' in html
    assert 'id="quiz-submit"' in html
    assert 'id="quiz-result"' in html
    assert 'id="quiz-reset"' in html
    assert 'id="quiz-stats"' in html
    assert 'id="correct-count">0</span>' in html
    assert 'id="streak-count">0</span>' in html
    assert "Reset Score" in html


def test_quiz_script_includes_session_storage_animation_and_events(tmp_path):
    html = _render_map_html(tmp_path)

    assert "@keyframes streak-flash" in html
    assert "streak-flash 600ms ease-out" in html

    assert 'correct: "correctCount"' in html
    assert 'streak: "streak"' in html
    assert "const initializeScore = () =>" in html
    assert "window.sessionStorage.getItem(storageKeys.correct)" in html
    assert "window.sessionStorage.setItem(storageKeys.correct" in html
    assert "window.sessionStorage.setItem(storageKeys.streak" in html
    assert "window.sessionStorage.removeItem(storageKeys.correct)" in html
    assert "window.sessionStorage.removeItem(storageKeys.streak)" in html

    assert "submit.addEventListener(\"click\", check)" in html
    assert "input.addEventListener(\"keydown\"" in html
    assert "if (event.key === \"Enter\")" in html
    assert "reset.addEventListener(\"click\", resetScore)" in html
    assert "initializeScore();" in html

    assert "result.textContent = \"Correct!\";" in html
    assert "result.textContent = \"Not quite. Try again.\";" in html
    assert "window.setTimeout(() =>" in html
    assert "}, 600);" in html
    assert "submit.disabled = true" not in html
    assert "levenshteinDistance" in html
    assert "isCloseMatch" in html
    assert "Please enter the full name, not just a surname." in html
    assert "Enter a guess first." not in html


def test_map_caps_zoom_to_city_level(tmp_path):
    html = _render_map_html(tmp_path)
    assert '"maxZoom": 8' in html


def test_country_level_location_adds_precision_note_and_circle(tmp_path):
    output_file = tmp_path / "country_map.html"
    birth_event = CartographicDate(
        date_str="1572",
        location_name="England",
        latitude=52.3555,
        longitude=-1.1743,
    )
    death_event = CartographicDate(
        date_str="1637",
        location_name="London",
        latitude=51.5074,
        longitude=-0.1278,
    )

    generate_life_map(
        birth_event=birth_event,
        death_event=death_event,
        person_name="Ben Jonson",
        output_filename=str(output_file),
    )
    html = output_file.read_text(encoding="utf-8")

    assert "Country-level location only (approximate pin)" in html
    assert "250000" in html
    assert "#1b5e20" in html
    assert "#66bb6a" in html
    assert "1572" in html
    assert "\\ud83d\\udc76 1572" in html
    assert "country-date-label" in html
    assert "font-size:22px" in html
    assert '"maxZoom": 8' in html


def test_region_level_location_adds_precision_note_and_circle(tmp_path):
    output_file = tmp_path / "region_map.html"
    birth_event = CartographicDate(
        date_str="600 BC",
        location_name="Central Asia",
        latitude=45.0,
        longitude=67.0,
    )
    death_event = CartographicDate(
        date_str="530 BC",
        location_name="Pasargadae",
        latitude=30.2,
        longitude=53.2,
    )

    generate_life_map(
        birth_event=birth_event,
        death_event=death_event,
        person_name="Cyrus the Great",
        output_filename=str(output_file),
    )
    html = output_file.read_text(encoding="utf-8")

    assert "Region-level location only (approximate pin)" in html
    assert "900000" in html
    assert "#1b5e20" in html
    assert "#66bb6a" in html
    assert "600 BC" in html
    assert "\\ud83d\\udc76 600 BC" in html


def test_person_name_embedding_is_safe_for_quotes(tmp_path):
    person_name = "D'Artagnan"
    html = _render_map_html(tmp_path, person_name=person_name)
    assert f"const expected = {person_name!r};" in html

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


def test_person_name_embedding_is_safe_for_quotes(tmp_path):
    person_name = "D'Artagnan"
    html = _render_map_html(tmp_path, person_name=person_name)
    assert f"const expected = {person_name!r};" in html

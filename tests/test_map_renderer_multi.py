from cartographic_quiz.map_renderer import generate_multi_life_map
from cartographic_quiz.models import CartographicDate


def test_generate_multi_life_map_injects_round_data_and_summary_ui(tmp_path):
    output_file = tmp_path / "multi_map.html"
    rounds = [
        (
            CartographicDate("15 August 1769", "Ajaccio", 41.9192, 8.7386),
            CartographicDate("5 May 1821", "Longwood", -15.9487, -5.7206),
            "Napoleon Bonaparte",
        ),
        (
            CartographicDate("7 November 1867", "Warsaw", 52.2297, 21.0122),
            CartographicDate("4 July 1934", "Passy", 48.8578, 2.2750),
            "Marie Curie",
        ),
    ]

    generate_multi_life_map(rounds=rounds, output_filename=str(output_file))
    html = output_file.read_text(encoding="utf-8")

    assert 'id="quiz-progress"' in html
    assert "Round 1/2" in html
    assert 'id="wrong-count"' in html
    assert "One guess per round. Wrong answers move to the next person." in html
    assert "const rounds =" in html
    assert "Napoleon Bonaparte" in html
    assert "Marie Curie" in html
    assert "window.setTimeout(nextRound, 500);" in html
    assert "Finished! Correct:" in html
    assert "Accuracy:" in html
    assert "Birth:" in html
    assert "Death:" in html
    assert "Your guess:" in html
    assert "Answer:" in html
    assert "const roundResults = [];" in html
    assert "class=\"quiz-round-item\"" in html
    assert "data-round-index" in html
    assert "drawRound(roundIndex);" in html
    assert "levenshteinDistance" in html
    assert "isCloseMatch" in html
    assert "Please enter the full name, not just a surname." in html

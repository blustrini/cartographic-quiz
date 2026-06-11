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
    assert 'id="quiz-instructions"' in html
    assert 'id="quiz-emoji-grid"' in html
    assert html.index('id="quiz-emoji-grid"') < html.index('id="quiz-copy-summary"')
    assert html.index('id="quiz-copy-summary"') < html.index('id="quiz-result"')
    assert "const rounds =" in html
    assert "Napoleon Bonaparte" in html
    assert "Marie Curie" in html
    assert "continueButton.addEventListener(\"click\", nextRound);" in html
    assert "fitBounds(bounds.pad(0.5), { maxZoom: 8 });" in html
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
    assert "country_level" in html
    assert 'id="quiz-controls"' in html
    assert 'id="quiz-continue"' in html
    assert 'id="quiz-force-correct"' in html
    assert 'id="quiz-force-wrong"' in html
    assert "awaitingAdvance" in html
    assert "applyManualOverride" in html
    assert 'id="quiz-copy-summary"' in html
    assert 'id="quiz-copy-status"' in html
    assert "let latestEmojiSummary = \"\";" in html
    assert "const buildEmojiSummary = () =>" in html
    assert "const buildEmojiGridHtml = () =>" in html
    assert "const columns = total >= 10 ? 5 : Math.min(5, total);" in html
    assert "entry.isCorrect ? \"✅\" : \"❌\"" in html
    assert "Cartographic Quiz: ${correctCount}/${total} correct" in html
    assert "copySummaryButton.addEventListener(\"click\", async () =>" in html
    assert "copyTextToClipboard" in html
    assert "const buildWikipediaUrl = (personName) =>" in html
    assert "https://en.wikipedia.org/wiki/${encodeURIComponent(normalized)}" in html
    assert "Answer: <a href=\"${buildWikipediaUrl(entry.answer)}\"" in html
    assert "result.innerHTML = `Correct! It was ${revealedLink}.`;" in html
    assert "result.innerHTML = `Not quite. It was ${revealedLink}.`;" in html
    assert "instructions.style.display = \"none\";" in html
    assert "input.style.display = \"none\";" in html
    assert "submit.style.display = \"none\";" in html
    assert "emojiGrid.innerHTML = buildEmojiGridHtml();" in html
    assert "emojiGrid.style.display = \"block\";" in html
    assert "if (awaitingAdvance)" in html
    assert "nextRound();" in html
    assert "event.stopPropagation();" in html
    assert "document.addEventListener(\"keydown\", (event) =>" in html
    assert "if (event.key !== \"Enter\" || !awaitingAdvance)" in html


def test_generate_multi_life_map_marks_country_level_locations(tmp_path):
    output_file = tmp_path / "multi_country_map.html"
    rounds = [
        (
            CartographicDate("1572", "England", 52.3555, -1.1743),
            CartographicDate("1637", "London", 51.5074, -0.1278),
            "Ben Jonson",
        )
    ]

    generate_multi_life_map(rounds=rounds, output_filename=str(output_file))
    html = output_file.read_text(encoding="utf-8")

    assert "Country-level location only (approximate pin)" in html
    assert "radius: 250000" in html
    assert "color: \"#1b5e20\"" in html
    assert "fillColor: \"#66bb6a\"" in html
    assert '"country_level": true' in html
    assert '"icon": null' in html
    assert '"country_label_html"' in html
    assert "1572" in html
    assert "iconSize: [320, 34]" in html

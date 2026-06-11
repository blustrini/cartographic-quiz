from cartographic_quiz.svg_markers import _format_display_date, build_birth_marker_svg


def test_format_display_date_converts_iso_date_to_day_month_year():
    assert _format_display_date("1536-07-12") == "12 July 1536"
    assert _format_display_date("121-04-26") == "26 April 121"


def test_format_display_date_keeps_non_iso_formats_unchanged():
    assert _format_display_date("12 July 1536") == "12 July 1536"
    assert _format_display_date("c. 1536") == "c. 1536"


def test_build_birth_marker_svg_uses_human_readable_date_label():
    svg = build_birth_marker_svg("1536-07-12")
    assert "👶 12 July 1536" in svg
    assert "1536-07-12" not in svg

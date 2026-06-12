from html import escape
import re
from typing import Optional


SVG_WIDTH = 320
SVG_HEIGHT = 90
CENTER_X = SVG_WIDTH // 2
TRI_HALF_WIDTH = 12
BIRTH_TIP_Y = 0
BIRTH_BASE_Y = 22
DEATH_BASE_Y = SVG_HEIGHT - 22
DEATH_TIP_Y = SVG_HEIGHT
MIN_LABEL_BOX_WIDTH = 110
MAX_LABEL_BOX_WIDTH = 288
LABEL_BOX_HEIGHT = 30
LABEL_GAP_FROM_TRIANGLE = 10
MONTH_NAMES = (
    "January",
    "February",
    "March",
    "April",
    "May",
    "June",
    "July",
    "August",
    "September",
    "October",
    "November",
    "December",
)
BIRTH_DATE_PREFIX = "👶"
DEATH_DATE_PREFIX = "💀"


def _compute_label_box_width(label: str) -> int:
    estimated = 18 + (len(label) * 12)
    return max(MIN_LABEL_BOX_WIDTH, min(estimated, MAX_LABEL_BOX_WIDTH))


def _build_label_box(label: str, y: int, color: str) -> str:
    label_box_width = _compute_label_box_width(label)
    label_box_x = (SVG_WIDTH - label_box_width) // 2
    text_y = y + 21
    return (
        f'<rect x="{label_box_x}" y="{y}" width="{label_box_width}" height="{LABEL_BOX_HEIGHT}" '
        f'rx="8" ry="8" fill="white" fill-opacity="0.84" />'
        f'<text x="{CENTER_X}" y="{text_y}" text-anchor="middle" font-size="22" font-weight="bold" '
        f'font-family="Helvetica Neue, Arial, sans-serif" fill="{color}">{escape(label)}</text>'
    )


def _format_display_date(date_str: Optional[str]) -> str:
    if not date_str:
        return "Unknown"

    cleaned = date_str.strip()
    iso_match = re.fullmatch(r"(\d{1,4})-(\d{2})-(\d{2})", cleaned)
    if not iso_match:
        return cleaned

    year = int(iso_match.group(1))
    month = int(iso_match.group(2))
    day = int(iso_match.group(3))
    if month < 1 or month > 12:
        return cleaned
    
    if day:
        return f"{day} {MONTH_NAMES[month - 1]} {year}"
    else:
        return f"{MONTH_NAMES[month - 1]} {year}"


def build_birth_marker_svg(date_str: Optional[str]) -> str:
    label = f"{BIRTH_DATE_PREFIX} {_format_display_date(date_str)}"
    label_y = BIRTH_BASE_Y + LABEL_GAP_FROM_TRIANGLE
    label_group = _build_label_box(label, label_y, "#1b5e20")
    return f"""
    <svg xmlns="http://www.w3.org/2000/svg" width="{SVG_WIDTH}" height="{SVG_HEIGHT}" viewBox="0 0 {SVG_WIDTH} {SVG_HEIGHT}">
        <polygon points="{CENTER_X},{BIRTH_TIP_Y} {CENTER_X - TRI_HALF_WIDTH},{BIRTH_BASE_Y} {CENTER_X + TRI_HALF_WIDTH},{BIRTH_BASE_Y}" fill="#1b5e20" />
        {label_group}
    </svg>
    """


def build_death_marker_svg(date_str: Optional[str]) -> str:
    label = f"{DEATH_DATE_PREFIX} {_format_display_date(date_str)}"
    label_y = DEATH_BASE_Y - LABEL_GAP_FROM_TRIANGLE - LABEL_BOX_HEIGHT
    label_group = _build_label_box(label, label_y, "#b71c1c")
    return f"""
    <svg xmlns="http://www.w3.org/2000/svg" width="{SVG_WIDTH}" height="{SVG_HEIGHT}" viewBox="0 0 {SVG_WIDTH} {SVG_HEIGHT}">
        <polygon points="{CENTER_X - TRI_HALF_WIDTH},{DEATH_BASE_Y} {CENTER_X + TRI_HALF_WIDTH},{DEATH_BASE_Y} {CENTER_X},{DEATH_TIP_Y}" fill="#b71c1c" />
        {label_group}
    </svg>
    """

from unittest.mock import patch

from bs4 import BeautifulSoup

from cartographic_quiz import biography


def test_extract_date_from_cell_keeps_approximate_raw_value():
    cell = BeautifulSoup("<td>c. 1033/4<br/>Aosta</td>", "html.parser").find("td")
    assert biography._extract_date_from_cell(cell) == "c. 1033/4"


def test_extract_location_link_skips_non_place_links():
    html = (
        "<td>"
        "<a href='/wiki/Murder_of_John_Lennon'>Gunshot wounds</a>"
        "<a href='/wiki/New_York_City'>New York City</a>"
        "</td>"
    )
    td = BeautifulSoup(html, "html.parser").find("td")
    assert biography._extract_location_link(td) == "/wiki/New_York_City"


def test_extract_place_from_cell_skips_name_chunks_before_date():
    cell = BeautifulSoup(
        "<td><a href='/wiki/Gaius_Octavius'>Gaius</a> <a href='/wiki/Octavia_gens'>Octavius</a> "
        "23 September 63 <span>BC</span><br><a href='/wiki/Rome'>Rome</a></td>",
        "html.parser",
    ).find("td")

    assert biography._extract_date_from_cell(cell) == "23 September 63 BC"
    assert biography._extract_place_from_cell(cell, "23 September 63 BC") == "Rome"


def test_extract_location_link_prefers_place_after_date():
    cell = BeautifulSoup(
        "<td><a href='/wiki/Gaius_Octavius'>Gaius</a> <a href='/wiki/Octavia_gens'>Octavius</a> "
        "23 September 63 <span>BC</span><br><a href='/wiki/Rome'>Rome</a></td>",
        "html.parser",
    ).find("td")

    assert (
        biography._extract_location_link(cell, date_str="23 September 63 BC", place_text="Rome")
        == "/wiki/Rome"
    )


def test_extract_date_candidate_preserves_bc_suffix():
    assert biography._extract_date_candidate("412 BC") == "412 BC"
    assert biography._extract_date_candidate("c. 412 b.c.") == "c. 412 BC"
    assert biography._extract_date_candidate("c. 412 BCE") == "c. 412 BCE"


def test_extract_date_candidate_supports_split_era_formats():
    assert biography._extract_date_candidate("23 September 63 BC") == "23 September 63 BC"
    assert biography._extract_date_candidate("19 August AD 14 (aged 75)") == "19 August AD 14"
    assert biography._extract_date_candidate("AD 30") == "AD 30"
    assert biography._extract_date_candidate("c. AD 30") == "c. AD 30"


@patch("cartographic_quiz.biography.fetch_json")
def test_scrape_robust_biography_can_be_silent(mock_fetch_json, capsys):
    mock_fetch_json.return_value = None

    assert biography.scrape_robust_biography("No Match", verbose=False) is None
    captured = capsys.readouterr()
    assert captured.out == ""


@patch("cartographic_quiz.biography.geocode_fallback")
@patch("cartographic_quiz.biography.get_coordinates_from_wikipedia_url")
@patch("cartographic_quiz.biography.fetch_html")
@patch("cartographic_quiz.biography.fetch_json")
def test_scrape_robust_biography_vermeer_uses_baptized_when_born_missing(
    mock_fetch_json,
    mock_fetch_html,
    mock_get_coordinates,
    mock_geocode_fallback,
):
    mock_fetch_json.return_value = {"query": {"search": [{"title": "Johannes Vermeer"}]}}

    mock_fetch_html.return_value = """
    <html><body>
      <table class="infobox biography vcard">
        <tr><th>Born</th><td><a href="/wiki/Delft">Delft</a>, Dutch Republic</td></tr>
        <tr><th>Baptized</th><td>31 October 1632</td></tr>
        <tr><th>Died</th><td>15 December 1675<br><a href="/wiki/Delft">Delft</a>, Dutch Republic</td></tr>
      </table>
    </body></html>
    """

    mock_get_coordinates.return_value = (52.01167, 4.35917)
    mock_geocode_fallback.return_value = (None, None)

    data = biography.scrape_robust_biography("Vermeer")

    assert data is not None
    assert data.birth_date == "31 October 1632"
    assert data.death_date == "15 December 1675"
    assert data.birth_place == "Delft"


def test_extract_date_from_cell_handles_era_token_in_separate_chunk():
    cell = BeautifulSoup("<td>23 September 63<br/>BC<br/>Rome</td>", "html.parser").find("td")
    assert biography._extract_date_from_cell(cell) == "23 September 63 BC"


@patch("cartographic_quiz.biography.geocode_fallback")
@patch("cartographic_quiz.biography.get_coordinates_from_wikipedia_url")
@patch("cartographic_quiz.biography.fetch_html")
@patch("cartographic_quiz.biography.fetch_json")
def test_scrape_robust_biography_augustus_birth_place_uses_rome(
    mock_fetch_json,
    mock_fetch_html,
    mock_get_coordinates,
    mock_geocode_fallback,
):
    mock_fetch_json.return_value = {"query": {"search": [{"title": "Augustus"}]}}
    mock_fetch_html.return_value = """
    <html><body>
      <table class="infobox biography vcard">
        <tr>
          <th>Born</th>
          <td>
            <a href="/wiki/Gaius_Octavius">Gaius</a>
            <a href="/wiki/Octavia_gens">Octavius</a>
            23 September 63 <span>BC</span><br>
            <a href="/wiki/Rome">Rome</a>
          </td>
        </tr>
        <tr>
          <th>Died</th>
          <td>19 August AD 14<br><a href="/wiki/Nola">Nola</a></td>
        </tr>
      </table>
    </body></html>
    """

    def fake_coords(url, _headers):
        if url.endswith("/wiki/Rome"):
            return 41.9, 12.5
        if url.endswith("/wiki/Nola"):
            return 40.92611, 14.5275
        return None, None

    mock_get_coordinates.side_effect = fake_coords
    mock_geocode_fallback.return_value = (None, None)

    data = biography.scrape_robust_biography("Augustus")

    assert data is not None
    assert data.birth_date == "23 September 63 BC"
    assert data.birth_place == "Rome"
    assert data.birth_lat == 41.9


def test_is_valid_place_name_rejects_event_terms():
    assert not biography._is_valid_place_name("Gunshot wounds")
    assert not biography._is_valid_place_name("Murder of John Lennon")
    assert not biography._is_valid_place_name("[")
    assert not biography._is_valid_place_name("]")
    assert not biography._is_valid_place_name("a")
    assert not biography._is_valid_place_name("c.")
    assert not biography._is_valid_place_name("1213 BC")
    assert not biography._is_valid_place_name("iii")
    assert biography._is_valid_place_name("New York City")


@patch("cartographic_quiz.biography.geocode_fallback")
@patch("cartographic_quiz.biography.get_coordinates_from_wikipedia_url")
@patch("cartographic_quiz.biography.fetch_html")
@patch("cartographic_quiz.biography.fetch_json")
def test_scrape_robust_biography_rejects_noise_place_tokens(
    mock_fetch_json,
    mock_fetch_html,
    mock_get_coordinates,
    mock_geocode_fallback,
):
    mock_fetch_json.return_value = {"query": {"search": [{"title": "Harold Wilson"}]}}
    mock_fetch_html.return_value = """
    <html><body>
      <table class="infobox biography vcard">
        <tr>
          <th>Born</th>
          <td>11 March 1916<br><a href="/wiki/Cowlersley">Cowlersley</a></td>
        </tr>
        <tr>
          <th>Died</th>
          <td>24 May 1995<br>a</td>
        </tr>
      </table>
    </body></html>
    """

    def fake_coords(url, _headers):
        if url.endswith("/wiki/Cowlersley"):
            return 53.6347, -1.8366
        return None, None

    mock_get_coordinates.side_effect = fake_coords
    mock_geocode_fallback.return_value = (None, None)

    data = biography.scrape_robust_biography("Harold Wilson", verbose=False)
    assert data is None


@patch("cartographic_quiz.biography.geocode_fallback")
@patch("cartographic_quiz.biography.get_coordinates_from_wikipedia_url")
@patch("cartographic_quiz.biography.fetch_html")
@patch("cartographic_quiz.biography.fetch_json")
def test_scrape_robust_biography_reuses_previous_place_link_when_missing_later_link(
    mock_fetch_json,
    mock_fetch_html,
    mock_get_coordinates,
    mock_geocode_fallback,
):
    mock_fetch_json.return_value = {"query": {"search": [{"title": "Antiochus III"}]}}
    mock_fetch_html.return_value = """
    <html><body>
      <table class="infobox biography vcard">
        <tr>
          <th>Born</th>
          <td>c. 241 BC<br><a href="/wiki/Susa">Susa</a></td>
        </tr>
        <tr>
          <th>Died</th>
          <td>3 July 187 BC<br>Susa, Seleucid Empire</td>
        </tr>
      </table>
    </body></html>
    """

    def fake_coords(url, _headers):
        if url.endswith("/wiki/Susa"):
            return 32.19056, 48.25778
        return None, None

    mock_get_coordinates.side_effect = fake_coords
    mock_geocode_fallback.return_value = (None, None)

    data = biography.scrape_robust_biography("Antiochus III")

    assert data is not None
    assert data.birth_place == "Susa"
    assert data.birth_lat == 32.19056
    assert data.death_place == "Susa, Seleucid Empire"
    assert data.death_lat == 32.19056
    assert data.death_lon == 48.25778


@patch("cartographic_quiz.biography.geocode_fallback")
@patch("cartographic_quiz.biography.get_coordinates_from_wikipedia_url")
@patch("cartographic_quiz.biography.fetch_html")
@patch("cartographic_quiz.biography.fetch_json")
def test_scrape_robust_biography_prefers_previous_link_for_composite_repeated_place(
    mock_fetch_json,
    mock_fetch_html,
    mock_get_coordinates,
    mock_geocode_fallback,
):
    mock_fetch_json.return_value = {"query": {"search": [{"title": "Antiochus III"}]}}
    mock_fetch_html.return_value = """
    <html><body>
      <table class="infobox biography vcard">
        <tr>
          <th>Born</th>
          <td>c. 241 BC<br><a href="/wiki/Susa">Susa</a></td>
        </tr>
        <tr>
          <th>Died</th>
          <td>3 July 187 BC<br><a href="/wiki/Susa,_Italy">Susa, Seleucid Empire</a></td>
        </tr>
      </table>
    </body></html>
    """

    def fake_coords(url, _headers):
        if url.endswith("/wiki/Susa"):
            return 32.19056, 48.25778
        if url.endswith("/wiki/Susa,_Italy"):
            return 45.1372115, 7.0539789
        return None, None

    mock_get_coordinates.side_effect = fake_coords
    mock_geocode_fallback.return_value = (None, None)

    data = biography.scrape_robust_biography("Antiochus III")

    assert data is not None
    assert data.death_place == "Susa, Seleucid Empire"
    assert data.death_lat == 32.19056
    assert data.death_lon == 48.25778


@patch("cartographic_quiz.biography.geocode_fallback")
@patch("cartographic_quiz.biography.get_coordinates_from_wikipedia_url")
@patch("cartographic_quiz.biography.fetch_html")
@patch("cartographic_quiz.biography.fetch_json")
def test_scrape_robust_biography_prefers_present_day_place_over_historical_prefecture(
    mock_fetch_json,
    mock_fetch_html,
    mock_get_coordinates,
    mock_geocode_fallback,
):
    mock_fetch_json.return_value = {"query": {"search": [{"title": "Hongwu Emperor"}]}}
    mock_fetch_html.return_value = """
    <html><body>
      <table class="infobox biography vcard">
        <tr>
          <th>Born</th>
          <td>
            21 October 1328<br>
            <a href="/wiki/Hao_Prefecture">Hao Prefecture</a>, Henan Jiangbei
            (present-day <a href="/wiki/Fengyang_County">Fengyang County</a>, Anhui)
          </td>
        </tr>
        <tr>
          <th>Died</th>
          <td>24 June 1398<br><a href="/wiki/Ming_Palace">Ming Palace</a></td>
        </tr>
      </table>
    </body></html>
    """

    def fake_coords(url, _headers):
        if url.endswith("/wiki/Fengyang_County"):
            return 32.88, 117.56
        if url.endswith("/wiki/Hao_Prefecture"):
            return 33.58, 130.38
        if url.endswith("/wiki/Ming_Palace"):
            return 32.03806, 118.8175
        return None, None

    mock_get_coordinates.side_effect = fake_coords
    mock_geocode_fallback.return_value = (None, None)

    data = biography.scrape_robust_biography("Hongwu Emperor")

    assert data is not None
    assert data.birth_place == "Fengyang County"
    assert data.birth_lat == 32.88
    assert data.birth_lon == 117.56


@patch("cartographic_quiz.biography.geocode_fallback")
@patch("cartographic_quiz.biography.get_coordinates_from_wikipedia_url")
@patch("cartographic_quiz.biography.fetch_html")
@patch("cartographic_quiz.biography.fetch_json")
def test_scrape_robust_biography_john_the_baptist_handles_ad_prefix_date(
    mock_fetch_json,
    mock_fetch_html,
    mock_get_coordinates,
    mock_geocode_fallback,
):
    mock_fetch_json.return_value = {"query": {"search": [{"title": "John the Baptist"}]}}

    mock_fetch_html.return_value = """
    <html><body>
      <table class="infobox biography vcard">
        <tr>
          <th>Born</th>
          <td>c. 6 BC<br><a href="/wiki/Herodian_Kingdom_of_Judea">Herodian Kingdom of Judea</a></td>
        </tr>
        <tr>
          <th>Died</th>
          <td>c. AD 30<br><a href="/wiki/Machaerus">Machaerus</a></td>
        </tr>
      </table>
    </body></html>
    """

    def fake_coords(url, _headers):
        if url.endswith("/wiki/Herodian_Kingdom_of_Judea"):
            return 31.77611, 35.22806
        if url.endswith("/wiki/Machaerus"):
            return 31.56722, 35.62417
        return None, None

    mock_get_coordinates.side_effect = fake_coords
    mock_geocode_fallback.return_value = (None, None)

    data = biography.scrape_robust_biography("John the Baptist")

    assert data is not None
    assert data.birth_date == "c. 6 BC"
    assert data.death_date == "c. AD 30"


@patch("cartographic_quiz.biography.geocode_fallback")
@patch("cartographic_quiz.biography.get_coordinates_from_wikipedia_url")
@patch("cartographic_quiz.biography.fetch_html")
@patch("cartographic_quiz.biography.fetch_json")
def test_scrape_robust_biography_does_not_use_death_cause_as_date(
    mock_fetch_json,
    mock_fetch_html,
    mock_get_coordinates,
    mock_geocode_fallback,
):
    mock_fetch_json.return_value = {"query": {"search": [{"title": "John Lennon"}]}}

    mock_fetch_html.return_value = """
    <html><body>
      <table class="infobox biography vcard">
        <tr>
          <th>Born</th>
          <td><span class="bday">1940-10-09</span><br><a href="/wiki/Liverpool">Liverpool</a>, England</td>
        </tr>
        <tr>
          <th>Died</th>
          <td>
            <span class="deathdate">8 December 1980</span><br>
            <a href="/wiki/New_York_City">New York City</a>, U.S.<br>
            Cause of death <a href="/wiki/Murder_of_John_Lennon">Gunshot wounds</a>
          </td>
        </tr>
      </table>
    </body></html>
    """

    def fake_coords(url, _headers):
        if url.endswith("/wiki/Liverpool"):
            return 53.4, -2.99
        if url.endswith("/wiki/New_York_City"):
            return 40.7, -74.0
        return None, None

    mock_get_coordinates.side_effect = fake_coords
    mock_geocode_fallback.return_value = (None, None)

    data = biography.scrape_robust_biography("John Lennon")

    assert data is not None
    assert data.birth_date == "1940-10-09"
    assert data.death_date == "8 December 1980"
    assert data.death_date != "Gunshot wounds"
    assert data.death_place == "New York City"

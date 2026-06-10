from unittest.mock import patch

from cartographic_quiz import biography


def _infobox_html(born_html: str, died_html: str | None) -> str:
    born_row = f"<tr><th>Born</th><td>{born_html}</td></tr>"
    died_row = f"<tr><th>Died</th><td>{died_html}</td></tr>" if died_html is not None else ""
    return (
        "<html><body><table class='infobox biography vcard'>"
        f"{born_row}{died_row}"
        "</table></body></html>"
    )


@patch("cartographic_quiz.biography.geocode_fallback")
@patch("cartographic_quiz.biography.get_coordinates_from_wikipedia_url")
@patch("cartographic_quiz.biography.fetch_html")
@patch("cartographic_quiz.biography.fetch_json")
def test_problematic_people_cases(
    mock_fetch_json,
    mock_fetch_html,
    mock_get_coordinates,
    mock_geocode_fallback,
):
    cases = [
        {
            "name": "Augustus",
            "title": "Augustus",
            "born": "<a href='/wiki/Gaius_Octavius'>Gaius</a> <a href='/wiki/Octavia_gens'>Octavius</a> 23 September 63 <span>BC</span><br><a href='/wiki/Rome'>Rome</a>",
            "died": "19 August AD 14 (aged 75)<br><a href='/wiki/Nola'>Nola</a>",
            "birth_date": "23 September 63 BC",
            "death_date": "19 August AD 14",
            "birth_place": "Rome",
            "death_place": "Nola",
        },
        {
            "name": "Diogenes",
            "title": "Diogenes",
            "born": "c. 412 <span>BC</span><br><a href='/wiki/Sinope'>Sinope</a>",
            "died": "323 BC<br><a href='/wiki/Corinth'>Corinth</a>",
            "birth_date": "c. 412 BC",
            "death_date": "323 BC",
            "birth_place": "Sinope",
            "death_place": "Corinth",
        },
        {
            "name": "Socrates",
            "title": "Socrates",
            "born": "c. 470 BC<br><a href='/wiki/Athens'>Athens</a>",
            "died": "399 BC<br><a href='/wiki/Athens'>Athens</a>",
            "birth_date": "c. 470 BC",
            "death_date": "399 BC",
            "birth_place": "Athens",
            "death_place": "Athens",
        },
        {
            "name": "Aristotle",
            "title": "Aristotle",
            "born": "384 BC<br><a href='/wiki/Stagira_(ancient_city)'>Stagira</a>",
            "died": "322 BC<br><a href='/wiki/Chalcis'>Chalcis</a>",
            "birth_date": "384 BC",
            "death_date": "322 BC",
            "birth_place": "Stagira",
            "death_place": "Chalcis",
        },
        {
            "name": "Cleopatra",
            "title": "Cleopatra VII Philopator",
            "born": "69 BC<br><a href='/wiki/Alexandria'>Alexandria</a>",
            "died": "10 August 30 BC<br><a href='/wiki/Alexandria'>Alexandria</a>",
            "birth_date": "69 BC",
            "death_date": "10 August 30 BC",
            "birth_place": "Alexandria",
            "death_place": "Alexandria",
        },
        {
            "name": "Tutankhamun",
            "title": "Tutankhamun",
            "born": "c. 1341 BC<br><a href='/wiki/Amarna'>Amarna</a>",
            "died": "c. 1323 BC<br><a href='/wiki/Ancient_Egypt'>Ancient Egypt</a>",
            "birth_date": "c. 1341 BC",
            "death_date": "c. 1323 BC",
            "birth_place": "Amarna",
            "death_place": "Ancient Egypt",
        },
        {
            "name": "Jesus",
            "title": "Jesus",
            "born": "c. 4 BC<br><a href='/wiki/Bethlehem'>Bethlehem</a>",
            "died": "30 AD<br><a href='/wiki/Jerusalem'>Jerusalem</a>",
            "birth_date": "c. 4 BC",
            "death_date": "30 AD",
            "birth_place": "Bethlehem",
            "death_place": "Jerusalem",
        },
        {
            "name": "Saint Anselm",
            "title": "Anselm of Canterbury",
            "born": "c. 1033/4<br><a href='/wiki/Aosta'>Aosta</a>",
            "died": "21 April 1109<br><a href='/wiki/Canterbury'>Canterbury</a>",
            "birth_date": "c. 1033/4",
            "death_date": "21 April 1109",
            "birth_place": "Aosta",
            "death_place": "Canterbury",
        },
        {
            "name": "Thomas Aquinas",
            "title": "Thomas Aquinas",
            "born": "c. 1225<br><a href='/wiki/Roccasecca'>Roccasecca</a>",
            "died": "7 March 1274<br><a href='/wiki/Fossanova_Abbey'>Fossanova Abbey</a>",
            "birth_date": "c. 1225",
            "death_date": "7 March 1274",
            "birth_place": "Roccasecca",
            "death_place": "Fossanova Abbey",
        },
        {
            "name": "Charlemagne",
            "title": "Charlemagne",
            "born": "2 April 742<br><a href='/wiki/Liège'>Liege</a>",
            "died": "28 January 814<br><a href='/wiki/Aachen'>Aachen</a>",
            "birth_date": "2 April 742",
            "death_date": "28 January 814",
            "birth_place": "Liege",
            "death_place": "Aachen",
        },
        {
            "name": "Joan of Arc",
            "title": "Joan of Arc",
            "born": "c. 1412<br><a href='/wiki/Domrémy-la-Pucelle'>Domremy-la-Pucelle</a>",
            "died": "30 May 1431<br><a href='/wiki/Rouen'>Rouen</a>",
            "birth_date": "c. 1412",
            "death_date": "30 May 1431",
            "birth_place": "Domremy-la-Pucelle",
            "death_place": "Rouen",
        },
        {
            "name": "William the Conqueror",
            "title": "William the Conqueror",
            "born": "c. 1028<br><a href='/wiki/Falaise'>Falaise</a>",
            "died": "9 September 1087<br><a href='/wiki/Rouen'>Rouen</a>",
            "birth_date": "c. 1028",
            "death_date": "9 September 1087",
            "birth_place": "Falaise",
            "death_place": "Rouen",
        },
        {
            "name": "Pope John Paul II",
            "title": "Pope John Paul II",
            "born": "18 May 1920<br><a href='/wiki/Wadowice'>Wadowice</a>",
            "died": "2 April 2005<br><a href='/wiki/Vatican_City'>Vatican City</a>",
            "birth_date": "18 May 1920",
            "death_date": "2 April 2005",
            "birth_place": "Wadowice",
            "death_place": "Vatican City",
        },
        {
            "name": "Louis XIV",
            "title": "Louis XIV",
            "born": "5 September 1638<br><a href='/wiki/Saint-Germain-en-Laye'>Saint-Germain-en-Laye</a>",
            "died": "1 September 1715<br><a href='/wiki/Palace_of_Versailles'>Versailles</a>",
            "birth_date": "5 September 1638",
            "death_date": "1 September 1715",
            "birth_place": "Saint-Germain-en-Laye",
            "death_place": "Versailles",
        },
        {
            "name": "George VI",
            "title": "George VI",
            "born": "14 December 1895<br><a href='/wiki/Sandringham_House'>Sandringham House</a>",
            "died": "6 February 1952<br><a href='/wiki/Sandringham_House'>Sandringham House</a>",
            "birth_date": "14 December 1895",
            "death_date": "6 February 1952",
            "birth_place": "Sandringham House",
            "death_place": "Sandringham House",
        },
        {
            "name": "Leonardo da Vinci",
            "title": "Leonardo da Vinci",
            "born": "15 April 1452<br><a href='/wiki/Vinci,_Tuscany'>Vinci</a>",
            "died": "2 May 1519<br><a href='/wiki/Amboise'>Amboise</a>",
            "birth_date": "15 April 1452",
            "death_date": "2 May 1519",
            "birth_place": "Vinci",
            "death_place": "Amboise",
        },
        {
            "name": "Maimonides",
            "title": "Maimonides",
            "born": "1138<br><a href='/wiki/Córdoba,_Spain'>Cordoba</a>",
            "died": "1204<br><a href='/wiki/Fustat'>Fustat</a>",
            "birth_date": "1138",
            "death_date": "1204",
            "birth_place": "Cordoba",
            "death_place": "Fustat",
        },
        {
            "name": "Nostradamus",
            "title": "Nostradamus",
            "born": "14 December 1503<br><a href='/wiki/Saint-Rémy-de-Provence'>Saint-Remy-de-Provence</a>",
            "died": "2 July 1566<br><a href='/wiki/Salon-de-Provence'>Salon-de-Provence</a>",
            "birth_date": "14 December 1503",
            "death_date": "2 July 1566",
            "birth_place": "Saint-Remy-de-Provence",
            "death_place": "Salon-de-Provence",
        },
        {
            "name": "Ludwig van Beethoven",
            "title": "Ludwig van Beethoven",
            "born": "17 December 1770<br><a href='/wiki/Bonn'>Bonn</a>",
            "died": "26 March 1827<br><a href='/wiki/Vienna'>Vienna</a>",
            "birth_date": "17 December 1770",
            "death_date": "26 March 1827",
            "birth_place": "Bonn",
            "death_place": "Vienna",
        },
        {
            "name": "Saoirse Ronan",
            "title": "Saoirse Ronan",
            "born": "12 April 1994<br><a href='/wiki/New_York_City'>New York City</a>",
            "died": None,
            "expect_none": True,
        },
        {
            "name": "Taylor Swift",
            "title": "Taylor Swift",
            "born": "13 December 1989<br><a href='/wiki/Reading,_Pennsylvania'>Reading</a>",
            "died": None,
            "expect_none": True,
        },
        {
            "name": "Pele",
            "title": "Pele",
            "born": "23 October 1940<br><a href='/wiki/Três_Corações'>Tres Coracoes</a>",
            "died": "29 December 2022<br><a href='/wiki/São_Paulo'>Sao Paulo</a>",
            "birth_date": "23 October 1940",
            "death_date": "29 December 2022",
            "birth_place": "Tres Coracoes",
            "death_place": "Sao Paulo",
        },
        {
            "name": "Bjork",
            "title": "Bjork",
            "born": "21 November 1965<br><a href='/wiki/Reykjavík'>Reykjavik</a>",
            "died": None,
            "expect_none": True,
        },
        {
            "name": "Rene Descartes",
            "title": "Rene Descartes",
            "born": "31 March 1596<br><a href='/wiki/Descartes,_Indre-et-Loire'>Descartes</a>",
            "died": "11 February 1650<br><a href='/wiki/Stockholm'>Stockholm</a>",
            "birth_date": "31 March 1596",
            "death_date": "11 February 1650",
            "birth_place": "Descartes",
            "death_place": "Stockholm",
        },
        {
            "name": "Muammar Gaddafi",
            "title": "Muammar Gaddafi",
            "born": "7 June 1942<br><a href='/wiki/Qasr_Abu_Hadi'>Qasr Abu Hadi</a>",
            "died": "20 October 2011<br><a href='/wiki/Sirte'>Sirte</a>",
            "birth_date": "7 June 1942",
            "death_date": "20 October 2011",
            "birth_place": "Qasr Abu Hadi",
            "death_place": "Sirte",
        },
    ]

    html_by_slug = {
        case["title"].replace(" ", "_"): _infobox_html(case["born"], case.get("died"))
        for case in cases
    }
    title_by_name = {case["name"]: case["title"] for case in cases}

    def fake_fetch_json(_url, params, headers):
        _ = headers
        title = title_by_name.get(params["srsearch"])
        if not title:
            return {"query": {"search": []}}
        return {"query": {"search": [{"title": title}]}}

    def fake_fetch_html(url, headers):
        _ = headers
        slug = url.rsplit("/", 1)[-1]
        return html_by_slug[slug]

    mock_fetch_json.side_effect = fake_fetch_json
    mock_fetch_html.side_effect = fake_fetch_html
    mock_get_coordinates.return_value = (10.0, 20.0)
    mock_geocode_fallback.return_value = (11.0, 21.0)

    for case in cases:
        data = biography.scrape_robust_biography(case["name"])
        if case.get("expect_none"):
            assert data is None
            continue

        assert data is not None
        assert data.birth_date == case["birth_date"]
        assert data.death_date == case["death_date"]
        assert data.birth_place == case["birth_place"]
        assert data.death_place == case["death_place"]

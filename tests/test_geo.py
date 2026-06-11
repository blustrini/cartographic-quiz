from cartographic_quiz import geo


def test_geocode_candidates_prioritizes_base_for_historical_polity_suffix():
    candidates = geo._geocode_candidates("Susa, Seleucid Empire")
    assert candidates == ["Susa", "Susa, Seleucid Empire"]


def test_geocode_candidates_keeps_full_text_first_without_historical_suffix():
    candidates = geo._geocode_candidates("Paris, France")
    assert candidates == ["Paris, France", "Paris"]


def test_geocode_fallback_uses_candidate_order(monkeypatch):
    class FakeLocation:
        latitude = 32.19
        longitude = 48.25

    class FakeNominatim:
        def __init__(self, user_agent):
            self.user_agent = user_agent

        def geocode(self, query):
            if query == "Susa":
                return FakeLocation()
            return None

    monkeypatch.setattr("cartographic_quiz.geo.Nominatim", FakeNominatim)

    lat, lon = geo.geocode_fallback("Susa, Seleucid Empire")
    assert (lat, lon) == (32.19, 48.25)


def test_geocode_fallback_uses_region_centroid_for_central_asia(monkeypatch):
    class FakeNominatim:
        def __init__(self, user_agent):
            self.user_agent = user_agent

        def geocode(self, query):
            class FakeLocation:
                latitude = 3.1624869
                longitude = 101.7125461

            return FakeLocation()

    monkeypatch.setattr("cartographic_quiz.geo.Nominatim", FakeNominatim)

    lat, lon = geo.geocode_fallback("Central Asia")
    assert (lat, lon) == (43.0, 66.0)

from cartographic_quiz.__main__ import _is_complete_biography


def test_is_complete_biography_rejects_garbage_places():
    bad_place_data = {
        "status": "ok",
        "birth_date": "1900-01-01",
        "birth_place": "c.",
        "birth_lat": 10.0,
        "birth_lon": 20.0,
        "death_date": "1950-01-01",
        "death_place": "a",
        "death_lat": 30.0,
        "death_lon": 40.0,
    }
    assert not _is_complete_biography(bad_place_data)


def test_is_complete_biography_accepts_normal_places():
    good_data = {
        "status": "ok",
        "birth_date": "1900-01-01",
        "birth_place": "Paris",
        "birth_lat": 48.8,
        "birth_lon": 2.3,
        "death_date": "1950-01-01",
        "death_place": "London",
        "death_lat": 51.5,
        "death_lon": -0.1,
    }
    assert _is_complete_biography(good_data)

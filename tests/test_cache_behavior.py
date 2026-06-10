import json

from cartographic_quiz.__main__ import _build_round_profiles, _rescan_bad_names
from cartographic_quiz.biography import BiographyData


def test_build_round_profiles_marks_bad_and_uses_cache(monkeypatch, tmp_path):
    data_dir = tmp_path / "data"
    data_dir.mkdir(parents=True, exist_ok=True)

    monkeypatch.setattr("cartographic_quiz.__main__._data_dir", lambda: data_dir)

    called = {"count": 0}

    def fake_scrape(name, verbose=True):
        called["count"] += 1
        if name == "Unknown Person":
            return None
        if name == "Valid Person":
            return BiographyData(
                birth_date="1900-01-01",
                birth_place="Paris",
                birth_lat=1.0,
                birth_lon=2.0,
                death_date="1950-01-01",
                death_place="London",
                death_lat=3.0,
                death_lon=4.0,
            )
        raise AssertionError(f"unexpected lookup: {name}")

    monkeypatch.setattr("cartographic_quiz.__main__.scrape_robust_biography", fake_scrape)

    rounds = _build_round_profiles(["Unknown Person", "Valid Person"])
    assert len(rounds) == 1
    assert rounds[0][2] == "Valid Person"
    assert called["count"] == 2

    bad_file = data_dir / "people_bad.txt"
    assert bad_file.exists()
    assert "Unknown Person" in bad_file.read_text(encoding="utf-8")

    good_file = data_dir / "people_good.txt"
    assert good_file.exists()
    assert "Valid Person" in good_file.read_text(encoding="utf-8")

    cache_file = data_dir / "people_cache.json"
    cache = json.loads(cache_file.read_text(encoding="utf-8"))
    assert cache["Unknown Person"]["status"] == "bad"
    assert cache["Valid Person"]["status"] == "ok"

    called["count"] = 0

    def should_not_scrape(name, verbose=True):
        raise AssertionError(f"unexpected scrape call for {name}")

    monkeypatch.setattr("cartographic_quiz.__main__.scrape_robust_biography", should_not_scrape)

    rounds_second = _build_round_profiles(["Unknown Person", "Valid Person"])
    assert len(rounds_second) == 1
    assert rounds_second[0][2] == "Valid Person"


def test_build_round_profiles_normalizes_existing_bad_ok_records(monkeypatch, tmp_path):
    data_dir = tmp_path / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr("cartographic_quiz.__main__._data_dir", lambda: data_dir)

    (data_dir / "people_cache.json").write_text(
        json.dumps(
            {
                "Zhuge Liang": {
                    "status": "ok",
                    "birth_date": "181",
                    "birth_place": "Yangdu",
                    "birth_lat": 30.1,
                    "birth_lon": 107.9,
                    "death_date": "October 234",
                    "death_place": "a",
                    "death_lat": -25.2,
                    "death_lon": -64.5,
                }
            }
        ),
        encoding="utf-8",
    )

    monkeypatch.setattr(
        "cartographic_quiz.__main__.scrape_robust_biography",
        lambda name, verbose=True: (_ for _ in ()).throw(AssertionError("should not rescrape normalized bad cache entry")),
    )

    rounds = _build_round_profiles(["Zhuge Liang"])
    assert rounds == []

    cache = json.loads((data_dir / "people_cache.json").read_text(encoding="utf-8"))
    assert cache["Zhuge Liang"]["status"] == "bad"
    assert "Zhuge Liang" in (data_dir / "people_bad.txt").read_text(encoding="utf-8")


def test_rescan_bad_names_updates_cache_and_lists(monkeypatch, tmp_path):
    data_dir = tmp_path / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr("cartographic_quiz.__main__._data_dir", lambda: data_dir)

    (data_dir / "people_bad.txt").write_text("Recoverable Person\nStill Bad\n", encoding="utf-8")
    (data_dir / "people_good.txt").write_text("", encoding="utf-8")
    (data_dir / "people_cache.json").write_text(
        json.dumps({"Recoverable Person": {"status": "bad"}, "Still Bad": {"status": "bad"}}),
        encoding="utf-8",
    )

    def fake_scrape(name, verbose=True):
        if name == "Recoverable Person":
            return BiographyData(
                birth_date="1900-01-01",
                birth_place="Paris",
                birth_lat=1.0,
                birth_lon=2.0,
                death_date="1950-01-01",
                death_place="London",
                death_lat=3.0,
                death_lon=4.0,
            )
        if name == "Still Bad":
            return None
        raise AssertionError(f"unexpected lookup: {name}")

    monkeypatch.setattr("cartographic_quiz.__main__.scrape_robust_biography", fake_scrape)

    total, rescued, still_bad = _rescan_bad_names()
    assert (total, rescued, still_bad) == (2, 1, 1)

    cache = json.loads((data_dir / "people_cache.json").read_text(encoding="utf-8"))
    assert cache["Recoverable Person"]["status"] == "ok"
    assert cache["Still Bad"]["status"] == "bad"

    bad_lines = (data_dir / "people_bad.txt").read_text(encoding="utf-8")
    assert "Still Bad" in bad_lines
    assert "Recoverable Person" not in bad_lines

    good_lines = (data_dir / "people_good.txt").read_text(encoding="utf-8")
    assert "Recoverable Person" in good_lines

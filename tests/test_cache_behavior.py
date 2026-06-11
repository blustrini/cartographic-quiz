import json
import random

from cartographic_quiz.__main__ import (
    _build_random_round_profiles,
    _build_round_profiles,
    _compute_difficulty_targets,
    _rescan_bad_names,
)
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


def test_build_round_profiles_rescrapes_invalid_cached_ok_records(monkeypatch, tmp_path):
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

    def fake_scrape(name, verbose=True):
        assert name == "Zhuge Liang"
        return BiographyData(
            birth_date="181",
            birth_place="Yangdu",
            birth_lat=35.062,
            birth_lon=118.342,
            death_date="October 234",
            death_place="Wuzhang Plains",
            death_lat=34.3,
            death_lon=107.7,
        )

    monkeypatch.setattr("cartographic_quiz.__main__.scrape_robust_biography", fake_scrape)

    rounds = _build_round_profiles(["Zhuge Liang"])
    assert len(rounds) == 1
    assert rounds[0][2] == "Zhuge Liang"

    cache = json.loads((data_dir / "people_cache.json").read_text(encoding="utf-8"))
    assert cache["Zhuge Liang"]["status"] == "ok"
    assert cache["Zhuge Liang"]["death_place"] == "Wuzhang Plains"


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


def test_build_round_profiles_force_rescrape_bad_name(monkeypatch, tmp_path):
    data_dir = tmp_path / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr("cartographic_quiz.__main__._data_dir", lambda: data_dir)

    (data_dir / "people_bad.txt").write_text("Hongwu Emperor\n", encoding="utf-8")
    (data_dir / "people_good.txt").write_text("", encoding="utf-8")
    (data_dir / "people_cache.json").write_text(
        json.dumps({"Hongwu Emperor": {"status": "bad"}}),
        encoding="utf-8",
    )

    def fake_scrape(name, verbose=True):
        assert name == "Hongwu Emperor"
        return BiographyData(
            birth_date="21 October 1328",
            birth_place="Haozhou",
            birth_lat=32.9,
            birth_lon=117.3,
            death_date="24 June 1398",
            death_place="Ming Palace",
            death_lat=32.03806,
            death_lon=118.8175,
        )

    monkeypatch.setattr("cartographic_quiz.__main__.scrape_robust_biography", fake_scrape)

    rounds = _build_round_profiles(["Hongwu Emperor"], force_rescrape_bad=True)
    assert len(rounds) == 1
    assert rounds[0][2] == "Hongwu Emperor"

    cache = json.loads((data_dir / "people_cache.json").read_text(encoding="utf-8"))
    assert cache["Hongwu Emperor"]["status"] == "ok"
    assert cache["Hongwu Emperor"]["birth_place"] == "Haozhou"

    bad_lines = (data_dir / "people_bad.txt").read_text(encoding="utf-8")
    assert "Hongwu Emperor" not in bad_lines


def test_build_round_profiles_force_rescrape_all_ignores_cached_ok(monkeypatch, tmp_path):
    data_dir = tmp_path / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr("cartographic_quiz.__main__._data_dir", lambda: data_dir)

    (data_dir / "people_bad.txt").write_text("", encoding="utf-8")
    (data_dir / "people_good.txt").write_text("Antiochus III\n", encoding="utf-8")
    (data_dir / "people_cache.json").write_text(
        json.dumps(
            {
                "Antiochus III": {
                    "status": "ok",
                    "birth_date": "c. 241 BC",
                    "birth_place": "Susa",
                    "birth_lat": 32.19,
                    "birth_lon": 48.25,
                    "death_date": "3 July 187 BC",
                    "death_place": "Susa, Seleucid Empire",
                    "death_lat": 45.13,
                    "death_lon": 7.05,
                }
            }
        ),
        encoding="utf-8",
    )

    def fake_scrape(name, verbose=True):
        assert name == "Antiochus III"
        return BiographyData(
            birth_date="c. 241 BC",
            birth_place="Susa",
            birth_lat=32.19056,
            birth_lon=48.25778,
            death_date="3 July 187 BC",
            death_place="Susa, Seleucid Empire",
            death_lat=32.19056,
            death_lon=48.25778,
        )

    monkeypatch.setattr("cartographic_quiz.__main__.scrape_robust_biography", fake_scrape)

    rounds = _build_round_profiles(["Antiochus III"], force_rescrape_all=True)
    assert len(rounds) == 1
    assert rounds[0][2] == "Antiochus III"

    cache = json.loads((data_dir / "people_cache.json").read_text(encoding="utf-8"))
    assert cache["Antiochus III"]["status"] == "ok"
    assert cache["Antiochus III"]["death_lat"] == 32.19056
    assert cache["Antiochus III"]["death_lon"] == 48.25778


def test_build_random_round_profiles_refills_until_target_reached(monkeypatch):
    pool = ["Bad 1", "Good 1", "Bad 2", "Good 2", "Good 3"]
    choices_iter = iter(
        [
            ["Bad 1", "Good 1", "Bad 2"],
            ["Good 2", "Good 3"],
        ]
    )

    def fake_sample(population, k):
        chosen = next(choices_iter)
        assert len(chosen) == k
        assert set(chosen).issubset(set(population))
        return chosen

    def fake_build_round_profiles(names, *, force_rescrape_bad=False, force_rescrape_all=False):
        _ = force_rescrape_bad, force_rescrape_all
        rounds = []
        for name in names:
            if name.startswith("Good"):
                rounds.append((None, None, name))
        return rounds

    monkeypatch.setattr(random, "sample", fake_sample)
    monkeypatch.setattr("cartographic_quiz.__main__._build_round_profiles", fake_build_round_profiles)

    rounds, target = _build_random_round_profiles(pool, requested_count=3)

    assert target == 3
    assert [round_data[2] for round_data in rounds] == ["Good 1", "Good 2", "Good 3"]


def test_compute_difficulty_targets_uses_40_40_20_split():
    assert _compute_difficulty_targets(10) == {"easy": 4, "medium": 4, "hard": 2}
    assert _compute_difficulty_targets(7) == {"easy": 3, "medium": 3, "hard": 1}


def test_build_random_round_profiles_with_difficulty_pools(monkeypatch):
    pools = {
        "easy": ["Easy A", "Easy B", "Easy C", "Easy D"],
        "medium": ["Medium A", "Medium B", "Medium C", "Medium D"],
        "hard": ["Hard A", "Hard B", "Hard C"],
    }

    def fake_sample(population, k):
        return list(population)[:k]

    def fake_shuffle(values):
        _ = values

    def fake_build_round_profiles(names, *, force_rescrape_bad=False, force_rescrape_all=False):
        _ = force_rescrape_bad, force_rescrape_all
        return [(None, None, name) for name in names]

    monkeypatch.setattr(random, "sample", fake_sample)
    monkeypatch.setattr(random, "shuffle", fake_shuffle)
    monkeypatch.setattr("cartographic_quiz.__main__._build_round_profiles", fake_build_round_profiles)

    rounds, target = _build_random_round_profiles(pools, requested_count=10)

    assert target == 10
    selected = [round_data[2] for round_data in rounds]
    assert sum(1 for name in selected if name.startswith("Easy")) == 4
    assert sum(1 for name in selected if name.startswith("Medium")) == 4
    assert sum(1 for name in selected if name.startswith("Hard")) == 2

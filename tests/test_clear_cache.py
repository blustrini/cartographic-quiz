from cartographic_quiz.__main__ import _clear_cache_files, clear_cache_main


def test_clear_cache_files_removes_existing_targets(monkeypatch, tmp_path):
    data_dir = tmp_path / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr("cartographic_quiz.__main__._data_dir", lambda: data_dir)

    (data_dir / "people_cache.json").write_text("{}", encoding="utf-8")
    (data_dir / "people_good.txt").write_text("Alice\n", encoding="utf-8")
    (data_dir / "people_bad.txt").write_text("Bob\n", encoding="utf-8")

    removed, missing = _clear_cache_files()
    assert removed == 3
    assert missing == 0

    assert not (data_dir / "people_cache.json").exists()
    assert not (data_dir / "people_good.txt").exists()
    assert not (data_dir / "people_bad.txt").exists()


def test_clear_cache_files_handles_missing_targets(monkeypatch, tmp_path):
    data_dir = tmp_path / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr("cartographic_quiz.__main__._data_dir", lambda: data_dir)

    removed, missing = _clear_cache_files()
    assert removed == 0
    assert missing == 3


def test_clear_cache_main_prints_summary(monkeypatch, capsys):
    monkeypatch.setattr("cartographic_quiz.__main__._clear_cache_files", lambda: (2, 1))

    clear_cache_main()

    captured = capsys.readouterr()
    assert "Removed: 2" in captured.out
    assert "Already missing: 1" in captured.out

import argparse
import json
import random
from pathlib import Path
from typing import Sequence

from cartographic_quiz.biography import _is_valid_place_name, scrape_robust_biography
from cartographic_quiz.constants import DEFAULT_REPEATS_EACH_SIDE
from cartographic_quiz.map_renderer import generate_life_map, generate_multi_life_map
from cartographic_quiz.models import CartographicDate


def _data_dir() -> Path:
    return Path(__file__).resolve().parents[2] / "data"


def _cache_path() -> Path:
    return _data_dir() / "people_cache.json"


def _bad_list_path() -> Path:
    return _data_dir() / "people_bad.txt"


def _good_list_path() -> Path:
    return _data_dir() / "people_good.txt"


def _load_cache() -> dict[str, dict[str, object]]:
    path = _cache_path()
    if not path.exists():
        return {}

    try:
        parsed = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}

    if not isinstance(parsed, dict):
        return {}

    return {str(key): value for key, value in parsed.items() if isinstance(value, dict)}


def _save_cache(cache: dict[str, dict[str, object]]) -> None:
    data_dir = _data_dir()
    data_dir.mkdir(parents=True, exist_ok=True)
    _cache_path().write_text(json.dumps(cache, indent=2, sort_keys=True), encoding="utf-8")


def _load_bad_names() -> set[str]:
    path = _bad_list_path()
    if not path.exists():
        return set()
    return {line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip()}


def _save_bad_names(names: set[str]) -> None:
    data_dir = _data_dir()
    data_dir.mkdir(parents=True, exist_ok=True)
    content = "\n".join(sorted(names))
    if content:
        content = f"{content}\n"
    _bad_list_path().write_text(content, encoding="utf-8")


def _load_good_names() -> set[str]:
    path = _good_list_path()
    if not path.exists():
        return set()
    return {line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip()}


def _save_good_names(names: set[str]) -> None:
    data_dir = _data_dir()
    data_dir.mkdir(parents=True, exist_ok=True)
    content = "\n".join(sorted(names))
    if content:
        content = f"{content}\n"
    _good_list_path().write_text(content, encoding="utf-8")


def _is_complete_biography(data: dict[str, object]) -> bool:
    required_text = ("birth_date", "death_date")
    required_coords = ("birth_lat", "birth_lon", "death_lat", "death_lon")

    for key in required_text:
        value = data.get(key)
        if not isinstance(value, str) or not value.strip():
            return False

    birth_place = data.get("birth_place")
    death_place = data.get("death_place")
    if not isinstance(birth_place, str) or not _is_valid_place_name(birth_place):
        return False
    if not isinstance(death_place, str) or not _is_valid_place_name(death_place):
        return False

    for key in required_coords:
        value = data.get(key)
        if not isinstance(value, (int, float)):
            return False

    return True


def _cache_record_to_round(name: str, record: dict[str, object]) -> tuple[CartographicDate, CartographicDate, str] | None:
    if record.get("status") != "ok":
        return None

    if not _is_complete_biography(record):
        return None

    birth_profile = CartographicDate(
        date_str=str(record["birth_date"]),
        location_name=str(record["birth_place"]),
        latitude=float(record["birth_lat"]),
        longitude=float(record["birth_lon"]),
    )
    death_profile = CartographicDate(
        date_str=str(record["death_date"]),
        location_name=str(record["death_place"]),
        latitude=float(record["death_lat"]),
        longitude=float(record["death_lon"]),
    )
    return birth_profile, death_profile, name


def _normalize_cached_records(
    cache: dict[str, dict[str, object]],
    bad_names: set[str],
    good_names: set[str],
) -> tuple[bool, bool, bool]:
    cache_changed = False
    bad_changed = False
    good_changed = False

    for name, record in list(cache.items()):
        status = record.get("status")
        if status == "ok" and not _is_complete_biography(record):
            cache[name] = {"status": "bad"}
            cache_changed = True
            if name not in bad_names:
                bad_names.add(name)
                bad_changed = True
            if name in good_names:
                good_names.discard(name)
                good_changed = True

        if cache.get(name, {}).get("status") == "bad" and name not in bad_names:
            bad_names.add(name)
            bad_changed = True

    return cache_changed, bad_changed, good_changed


def _read_person_pool() -> list[str]:
    data_dir = _data_dir()
    pool_files = ("people_easy.txt", "people_medium.txt", "people_hard.txt", "people_good.txt")
    names: list[str] = []
    bad_names = _load_bad_names()

    for filename in pool_files:
        path = data_dir / filename
        if not path.exists():
            continue
        for line in path.read_text(encoding="utf-8").splitlines():
            cleaned = line.strip()
            if cleaned and cleaned not in bad_names:
                names.append(cleaned)

    # Keep order while deduplicating.
    return list(dict.fromkeys(names))


def _build_round_profiles(names: Sequence[str]) -> list[tuple[CartographicDate, CartographicDate, str]]:
    rounds: list[tuple[CartographicDate, CartographicDate, str]] = []
    cache = _load_cache()
    bad_names = _load_bad_names()
    good_names = _load_good_names()
    cache_changed = False
    bad_changed = False
    good_changed = False

    normalized_cache_changed, normalized_bad_changed, normalized_good_changed = _normalize_cached_records(
        cache=cache,
        bad_names=bad_names,
        good_names=good_names,
    )
    cache_changed = cache_changed or normalized_cache_changed
    bad_changed = bad_changed or normalized_bad_changed
    good_changed = good_changed or normalized_good_changed

    for name in names:
        if name in bad_names:
            continue

        cached_record = cache.get(name, {})
        if cached_record.get("status") == "bad":
            bad_names.add(name)
            bad_changed = True
            continue

        cached_round = _cache_record_to_round(name, cached_record)
        if cached_round is not None:
            good_names.add(name)
            good_changed = True
            rounds.append(cached_round)
            continue

        biography_data = scrape_robust_biography(name, verbose=False)
        if not biography_data:
            cache[name] = {"status": "bad"}
            bad_names.add(name)
            cache_changed = True
            bad_changed = True
            if name in good_names:
                good_names.discard(name)
                good_changed = True
            continue

        record = {
            "status": "ok",
            "birth_date": biography_data.birth_date,
            "birth_place": biography_data.birth_place,
            "birth_lat": biography_data.birth_lat,
            "birth_lon": biography_data.birth_lon,
            "death_date": biography_data.death_date,
            "death_place": biography_data.death_place,
            "death_lat": biography_data.death_lat,
            "death_lon": biography_data.death_lon,
        }
        if not _is_complete_biography(record):
            cache[name] = {"status": "bad"}
            bad_names.add(name)
            cache_changed = True
            bad_changed = True
            if name in good_names:
                good_names.discard(name)
                good_changed = True
            continue

        cache[name] = record
        cache_changed = True
        good_names.add(name)
        good_changed = True

        birth_profile = CartographicDate(
            date_str=biography_data.birth_date,
            location_name=biography_data.birth_place,
            latitude=biography_data.birth_lat,
            longitude=biography_data.birth_lon,
        )
        death_profile = CartographicDate(
            date_str=biography_data.death_date,
            location_name=biography_data.death_place,
            latitude=biography_data.death_lat,
            longitude=biography_data.death_lon,
        )
        rounds.append((birth_profile, death_profile, name))

    if cache_changed:
        _save_cache(cache)
    if bad_changed:
        _save_bad_names(bad_names)
    if good_changed:
        _save_good_names(good_names)

    return rounds


def _rescan_bad_names() -> tuple[int, int, int]:
    cache = _load_cache()
    bad_names = _load_bad_names()
    good_names = _load_good_names()

    if not bad_names:
        return 0, 0, 0

    rescued = 0
    still_bad = 0

    for name in sorted(bad_names):
        biography_data = scrape_robust_biography(name, verbose=False)
        if not biography_data:
            cache[name] = {"status": "bad"}
            still_bad += 1
            continue

        record = {
            "status": "ok",
            "birth_date": biography_data.birth_date,
            "birth_place": biography_data.birth_place,
            "birth_lat": biography_data.birth_lat,
            "birth_lon": biography_data.birth_lon,
            "death_date": biography_data.death_date,
            "death_place": biography_data.death_place,
            "death_lat": biography_data.death_lat,
            "death_lon": biography_data.death_lon,
        }
        if not _is_complete_biography(record):
            cache[name] = {"status": "bad"}
            still_bad += 1
            continue

        cache[name] = record
        good_names.add(name)
        rescued += 1

    updated_bad_names = {name for name in bad_names if cache.get(name, {}).get("status") == "bad"}
    for name in bad_names - updated_bad_names:
        good_names.add(name)

    _save_cache(cache)
    _save_bad_names(updated_bad_names)
    _save_good_names(good_names)

    return len(bad_names), rescued, still_bad


def parse_cli_args(argv: Sequence[str] | None = None) -> tuple[str | None, str, int | None, bool]:
    parser = argparse.ArgumentParser(description="Generate a life map from a Wikipedia biography.")
    parser.add_argument("name", nargs="*", help="Name of the person to map")
    parser.add_argument(
        "-o",
        "--output",
        default="output.html",
        help="Output HTML filename (default: output.html)",
    )
    parser.add_argument(
        "-n",
        "--num-random",
        type=int,
        default=None,
        help="Generate a multi-round quiz with N random names from the bundled pool",
    )
    parser.add_argument(
        "--rescan-bad",
        action="store_true",
        help="Re-scrape names in people_bad.txt and refresh cache/bad-good lists",
    )
    args = parser.parse_args(argv)

    person_name = " ".join(args.name).strip() if args.name else None
    output_name = args.output
    if not Path(output_name).suffix:
        output_name = f"{output_name}.html"

    if args.num_random is None and not person_name and not args.rescan_bad:
        parser.error("either a person name, --num-random N, or --rescan-bad is required")

    if args.num_random is not None and args.num_random <= 0:
        parser.error("--num-random must be a positive integer")

    return person_name, output_name, args.num_random, args.rescan_bad


def main() -> None:
    subject_name, output_filename, num_random, rescan_bad = parse_cli_args()

    if rescan_bad:
        total, rescued, still_bad = _rescan_bad_names()
        print(f"Rescanned bad names: {total} | rescued: {rescued} | still bad: {still_bad}")
        return

    if num_random is not None:
        person_pool = _read_person_pool()
        if not person_pool:
            print("Error: No people pool files found under data/.")
            return

        sample_size = min(num_random, len(person_pool))
        if sample_size < num_random:
            print(f"Warning: Requested {num_random} names but only {len(person_pool)} are available. Using {sample_size}.")

        selected_names = random.sample(person_pool, sample_size)
        rounds = _build_round_profiles(selected_names)
        if not rounds:
            print("Error: No valid biographies could be scraped for the random selection.")
            return

        if len(rounds) < sample_size:
            print(f"Warning: Only {len(rounds)} of {sample_size} random names produced valid quiz rounds.")

        generate_multi_life_map(
            rounds=rounds,
            output_filename=output_filename,
            repeats_each_side=DEFAULT_REPEATS_EACH_SIDE,
        )
        return

    if not subject_name:
        print("Error: Missing person name.")
        return

    rounds = _build_round_profiles([subject_name])
    if not rounds:
        return

    birth_profile, death_profile, person_name = rounds[0]
    generate_life_map(
        birth_event=birth_profile,
        death_event=death_profile,
        person_name=person_name,
        output_filename=output_filename,
        repeats_each_side=DEFAULT_REPEATS_EACH_SIDE,
    )


if __name__ == "__main__":
    main()

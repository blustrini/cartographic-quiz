from cartographic_quiz.__main__ import parse_cli_args


def test_parse_cli_args_joins_multi_word_name_and_adds_html_extension():
    name, output, num_random, rescan_bad, clear_cache = parse_cli_args(["John", "the", "Baptist", "-o", "test1"])
    assert name == "John the Baptist"
    assert output == "test1.html"
    assert num_random is None
    assert not rescan_bad
    assert not clear_cache


def test_parse_cli_args_preserves_output_extension_when_provided():
    name, output, num_random, rescan_bad, clear_cache = parse_cli_args(["Albert", "Einstein", "--output", "einstein_map.html"])
    assert name == "Albert Einstein"
    assert output == "einstein_map.html"
    assert num_random is None
    assert not rescan_bad
    assert not clear_cache


def test_parse_cli_args_default_output_filename():
    name, output, num_random, rescan_bad, clear_cache = parse_cli_args(["Marie", "Curie"])
    assert name == "Marie Curie"
    assert output == "quizzes/output.html"
    assert num_random is None
    assert not rescan_bad
    assert not clear_cache


def test_parse_cli_args_num_random_mode_without_name():
    name, output, num_random, rescan_bad, clear_cache = parse_cli_args(["--num-random", "8", "-o", "rounds"])
    assert name is None
    assert output == "rounds.html"
    assert num_random == 8
    assert not rescan_bad
    assert not clear_cache


def test_parse_cli_args_rescan_bad_mode_without_name():
    name, output, num_random, rescan_bad, clear_cache = parse_cli_args(["--rescan-bad"])
    assert name is None
    assert output == "quizzes/output.html"
    assert num_random is None
    assert rescan_bad
    assert not clear_cache


def test_parse_cli_args_clear_cache_mode_without_name():
    name, output, num_random, rescan_bad, clear_cache = parse_cli_args(["--clear-cache"])
    assert name is None
    assert output == "quizzes/output.html"
    assert num_random is None
    assert not rescan_bad
    assert clear_cache

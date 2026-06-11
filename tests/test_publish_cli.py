import subprocess

from cartographic_quiz.__main__ import (
    _github_pages_url_from_remote,
    _publish_html_file,
    parse_publish_args,
)


def test_parse_publish_args_accepts_no_push_flag():
    html_path, no_push = parse_publish_args(["output.html", "--no-push"])
    assert html_path == "output.html"
    assert no_push


def test_github_pages_url_from_remote_supports_common_github_formats():
    assert _github_pages_url_from_remote("git@github.com:octo/cartographic-quiz.git") == "https://octo.github.io/cartographic-quiz/"
    assert _github_pages_url_from_remote("https://github.com/octo/cartographic-quiz.git") == "https://octo.github.io/cartographic-quiz/"
    assert _github_pages_url_from_remote("ssh://git@github.com/octo/cartographic-quiz.git") == "https://octo.github.io/cartographic-quiz/"


def test_publish_html_file_copies_to_docs_and_reports_url(monkeypatch, tmp_path, capsys):
    repo_root = tmp_path / "repo"
    repo_root.mkdir(parents=True, exist_ok=True)
    source_html = tmp_path / "quiz.html"
    source_html.write_text("<html><body>quiz</body></html>", encoding="utf-8")

    monkeypatch.setattr("cartographic_quiz.__main__._repo_root", lambda: repo_root)

    def fake_git(args, cwd):
        assert cwd == repo_root
        if args == ["status", "--porcelain", "--", "docs/index.html", "docs/.nojekyll"]:
            return subprocess.CompletedProcess(args=["git", *args], returncode=0, stdout=" M docs/index.html\n", stderr="")
        if args == ["add", "docs/index.html", "docs/.nojekyll"]:
            return subprocess.CompletedProcess(args=["git", *args], returncode=0, stdout="", stderr="")
        if args == ["commit", "-m", "Publish quiz map to GitHub Pages"]:
            return subprocess.CompletedProcess(
                args=["git", *args],
                returncode=0,
                stdout="[main abc123] Publish quiz map to GitHub Pages\n",
                stderr="",
            )
        if args == ["remote", "get-url", "origin"]:
            return subprocess.CompletedProcess(
                args=["git", *args],
                returncode=0,
                stdout="git@github.com:octo/cartographic-quiz.git\n",
                stderr="",
            )
        raise AssertionError(f"unexpected git command: {args}")

    monkeypatch.setattr("cartographic_quiz.__main__._run_git_command", fake_git)

    result_code = _publish_html_file(str(source_html), push=False)
    assert result_code == 0

    destination_html = repo_root / "docs" / "index.html"
    assert destination_html.exists()
    assert destination_html.read_text(encoding="utf-8") == "<html><body>quiz</body></html>"
    assert (repo_root / "docs" / ".nojekyll").exists()

    captured = capsys.readouterr()
    assert "https://octo.github.io/cartographic-quiz/" in captured.out


def test_publish_html_file_rejects_non_html_input(tmp_path):
    source_txt = tmp_path / "quiz.txt"
    source_txt.write_text("not html", encoding="utf-8")

    result_code = _publish_html_file(str(source_txt), push=False)
    assert result_code == 1

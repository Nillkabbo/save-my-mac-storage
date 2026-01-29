import json

from click.testing import CliRunner

from mac_cleaner.cli import main


def test_cli_clean_unknown_category_json():
    runner = CliRunner()
    result = runner.invoke(main, ["clean", "--category", "unknown", "--json"])
    assert result.exit_code == 2
    payload = json.loads(result.output)
    assert payload["error"] == "Unknown category"


def test_cli_clean_dry_run_json():
    runner = CliRunner()
    result = runner.invoke(
        main, ["clean", "--dry-run", "--category", "cache", "--json"]
    )
    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["category"] == "cache"
    assert "total_files" in payload
    assert "total_space" in payload

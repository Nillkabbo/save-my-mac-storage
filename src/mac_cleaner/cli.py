#!/usr/bin/env python3
"""
CLI interface for macOS Cleaner.
"""

import json
import sys
import subprocess
import click
from mac_cleaner.__version__ import __version__
from mac_cleaner.mac_cleaner import MacCleaner
from mac_cleaner.space_analyzer import SpaceAnalyzer
from mac_cleaner.categories import CATEGORY_MAP, CATEGORY_CHOICES


@click.group()
@click.version_option(__version__)
def main():
    """macOS Cleaner - safe system cleaning tool."""


@main.command()
@click.option("--dry-run/--no-dry-run", default=True, help="Preview without deleting")
@click.option(
    "--category",
    default="all",
    show_default=True,
    help=f"Category to clean ({', '.join(CATEGORY_CHOICES)})",
)
@click.option("--json", "output_json", is_flag=True, help="Output results as JSON")
def clean(dry_run, category, output_json):
    """Clean system files."""
    cleaner = MacCleaner()

    if not output_json:
        click.echo("🍎 macOS Cleaner")
        click.echo(f"Mode: {'DRY RUN' if dry_run else 'LIVE CLEANING'}")

    if category not in CATEGORY_CHOICES:
        if output_json:
            click.echo(json.dumps({"error": "Unknown category", "category": category}))
        else:
            click.echo(f"Unknown category: {category}")
        sys.exit(2)

    if category == "all":
        results = cleaner.clean_all(dry_run=dry_run)
        if output_json:
            click.echo(json.dumps(results, indent=2))
        else:
            click.echo(f"Files processed: {results['total_files']}")
            click.echo(f"Space freed: {results['total_space_human']}")
        sys.exit(0)

    mapped = CATEGORY_MAP.get(category, [])

    total_files = 0
    total_space = 0
    category_results = []
    for mapped_category in mapped:
        result = cleaner.clean_category(mapped_category, dry_run=dry_run)
        total_files += result.get("files_deleted", 0)
        total_space += result.get("space_freed", 0)
        category_results.append(result)

    if output_json:
        payload = {
            "category": category,
            "results": category_results,
            "total_files": total_files,
            "total_space": total_space,
            "total_space_human": cleaner.format_bytes(total_space),
        }
        click.echo(json.dumps(payload, indent=2))
    else:
        click.echo(f"Files processed: {total_files}")
        click.echo(f"Space freed: {cleaner.format_bytes(total_space)}")
    sys.exit(0)


@main.command()
@click.option("--json", "output_json", is_flag=True, help="Output report as JSON")
def analyze(output_json):
    """Analyze disk usage."""
    analyzer = SpaceAnalyzer()
    report = analyzer.generate_report()

    if output_json:
        click.echo(json.dumps(report, indent=2, default=str))
        sys.exit(0)

    analyzer.print_report(report)
    sys.exit(0)


@main.command()
def gui():
    """Launch Tkinter GUI."""
    subprocess.run([sys.executable, "-m", "mac_cleaner.gui"], check=True)


@main.command(name="detailed-gui")
def detailed_gui():
    """Launch detailed analysis GUI."""
    subprocess.run([sys.executable, "-m", "mac_cleaner.detailed_gui"], check=True)


@main.command()
def web():
    """Launch web interface."""
    subprocess.run([sys.executable, "-m", "mac_cleaner.web_gui"], check=True)


if __name__ == "__main__":
    main()

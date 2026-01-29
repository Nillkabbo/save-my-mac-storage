#!/usr/bin/env python3
"""
CLI interface for macOS Cleaner.

Copyright (c) 2026 macOS Cleaner contributors
Licensed under the MIT License
"""

import json
import sys
import subprocess
import click
from pathlib import Path
from mac_cleaner.__version__ import __version__
from mac_cleaner.mac_cleaner import MacCleaner
from mac_cleaner.space_analyzer import SpaceAnalyzer
from mac_cleaner.categories import CATEGORY_MAP, CATEGORY_CHOICES
from mac_cleaner.security import sanitize_shell_input


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
    type=click.Choice(CATEGORY_CHOICES, case_sensitive=False),
)
@click.option("--json", "output_json", is_flag=True, help="Output results as JSON")
@click.option("--force", is_flag=True, help="Skip confirmation prompts")
@click.option("--verbose", "-v", is_flag=True, help="Verbose output")
def clean(dry_run, category, output_json, force, verbose):
    """Clean system files."""
    cleaner = MacCleaner()

    if not output_json:
        click.echo("🍎 macOS Cleaner")
        click.echo(f"Mode: {'DRY RUN' if dry_run else 'LIVE CLEANING'}")

    # Add confirmation for live cleaning
    if not dry_run and not force:
        if not click.confirm(f"⚠️  This will permanently delete files in category '{category}'. Continue?"):
            click.echo("Operation cancelled.")
            sys.exit(0)

    if category == "all":
        if output_json:
            results = cleaner.clean_all(dry_run=dry_run)
            click.echo(json.dumps(results, indent=2))
        else:
            with click.progressbar(length=100, label="Cleaning") as bar:
                results = cleaner.clean_all(dry_run=dry_run, progress=bar.update)
            click.echo(f"Files processed: {results['total_files']}")
            click.echo(f"Space freed: {results['total_space_human']}")
        sys.exit(0)

    mapped = CATEGORY_MAP.get(category, [])

    total_files = 0
    total_space = 0
    category_results = []
    
    if output_json:
        # JSON mode - no progress bars
        for mapped_category in mapped:
            result = cleaner.clean_category(mapped_category, dry_run=dry_run)
            total_files += result.get("files_deleted", 0)
            total_space += result.get("space_freed", 0)
            category_results.append(result)
    else:
        # Interactive mode - show progress bars
        with click.progressbar(length=len(mapped), label="Cleaning categories") as bar:
            for i, mapped_category in enumerate(mapped):
                if verbose:
                    click.echo(f"\nProcessing: {mapped_category}")
                result = cleaner.clean_category(mapped_category, dry_run=dry_run)
                total_files += result.get("files_deleted", 0)
                total_space += result.get("space_freed", 0)
                category_results.append(result)
                bar.update(1)

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
    try:
        # Validate the subprocess call
        cmd = [sys.executable, "-m", "mac_cleaner.gui"]
        sanitized_cmd = [sanitize_shell_input(str(arg)) for arg in cmd]
        subprocess.run(sanitized_cmd, check=True)
    except subprocess.CalledProcessError as e:
        click.echo(f"Error launching GUI: {e}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"Unexpected error: {e}", err=True)
        sys.exit(1)


@main.command(name="detailed-gui")
def detailed_gui():
    """Launch detailed analysis GUI."""
    try:
        # Validate the subprocess call
        cmd = [sys.executable, "-m", "mac_cleaner.detailed_gui"]
        sanitized_cmd = [sanitize_shell_input(str(arg)) for arg in cmd]
        subprocess.run(sanitized_cmd, check=True)
    except subprocess.CalledProcessError as e:
        click.echo(f"Error launching detailed GUI: {e}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"Unexpected error: {e}", err=True)
        sys.exit(1)


@main.command()
def web():
    """Launch web interface."""
    try:
        # Validate the subprocess call
        cmd = [sys.executable, "-m", "mac_cleaner.web_gui"]
        sanitized_cmd = [sanitize_shell_input(str(arg)) for arg in cmd]
        subprocess.run(sanitized_cmd, check=True)
    except subprocess.CalledProcessError as e:
        click.echo(f"Error launching web interface: {e}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"Unexpected error: {e}", err=True)
        sys.exit(1)


if __name__ == "__main__":
    main()

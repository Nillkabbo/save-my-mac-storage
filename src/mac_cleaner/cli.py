#!/usr/bin/env python3
"""
CLI interface for macOS Cleaner.

Copyright (c) 2026 macOS Cleaner contributors
Licensed under the MIT License
"""

import json
import sys
import subprocess
import os
import click
from pathlib import Path
from typing import Optional

from mac_cleaner.__version__ import __version__
from mac_cleaner.core.enhanced_cleaner import EnhancedCleaner
from mac_cleaner.core.config_manager import ConfigurationManager
from mac_cleaner.space_analyzer import SpaceAnalyzer
from mac_cleaner.safety_manager import SafetyManager
from mac_cleaner.categories import CATEGORY_MAP, CATEGORY_CHOICES
from mac_cleaner.security import sanitize_shell_input, SecurityValidator
from mac_cleaner.interfaces import PluginManager, OperationMode, SafetyLevel
from mac_cleaner.plugins import register_builtin_plugins


def format_bytes(bytes_size) -> str:
    """Format bytes into human readable format."""
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if bytes_size < 1024.0:
            return f"{bytes_size:.2f} {unit}"
        bytes_size /= 1024.0
    return f"{bytes_size:.2f} PB"


@click.group()
@click.version_option(__version__)
@click.option("--config", type=click.Path(exists=True), help="Configuration file path")
@click.pass_context
def main(ctx, config):
    """macOS Cleaner - Safe disk usage analysis tool (read-only)."""
    ctx.ensure_object(dict)
    
    # Initialize configuration
    if config:
        ctx.obj["config_manager"] = ConfigurationManager(config)
    else:
        ctx.obj["config_manager"] = ConfigurationManager()
    
    ctx.obj["config"] = config


@main.command()
@click.option("--dry-run/--no-dry-run", default=True, help="Preview without deleting")
@click.option(
    "--category",
    default="all",
    show_default=True,
    help=f'Category to clean ({", ".join(CATEGORY_CHOICES)})',
    type=click.Choice(CATEGORY_CHOICES, case_sensitive=False),
)
@click.option("--json", "output_json", is_flag=True, help="Output results as JSON")
@click.option("--force", is_flag=True, help="Skip confirmation prompts")
@click.option("--verbose", "-v", is_flag=True, help="Verbose output")
@click.option("--plugin", help="Use specific plugin instead of category")
@click.pass_context
def clean(ctx, dry_run, category, output_json, force, verbose, plugin):
    """Analyze system files and directories (read-only mode)."""
    config_manager = ctx.obj["config_manager"]
    cleaner = EnhancedCleaner(config_manager)

    if not output_json:
        click.echo("🔍 macOS Cleaner - Enhanced Analysis Mode")
        click.echo("ℹ️  This tool performs disk usage analysis and identifies data that is safe to remove.")
        click.echo("ℹ️  No files are modified or deleted in this mode.")
        click.echo(
            f'Mode: {"ANALYSIS" if dry_run else "ANALYSIS (Read-Only)"}'
        )

    # No confirmation needed for read-only analysis
    if not dry_run and not force:
        click.echo("ℹ️  Live cleaning is disabled - running in analysis mode only")
        dry_run = True

    if plugin:
        # Use specific plugin
        plugin_info = cleaner.get_plugin_info()
        if plugin not in plugin_info:
            click.echo(f'Plugin "{plugin}" not found.', err=True)
            available_plugins = list(plugin_info.keys())
            click.echo(f'Available plugins: {", ".join(available_plugins)}')
            sys.exit(1)
        
        # Get plugin and analyze
        plugin_manager = cleaner.plugin_manager
        selected_plugin = plugin_manager.get_plugin(plugin)
        
        if output_json:
            results = selected_plugin.analyze_paths()
            click.echo(json.dumps(results, indent=2))
        else:
            if verbose:
                click.echo(f"Using plugin: {selected_plugin.name}")
                click.echo(f"Description: {selected_plugin.description}")
                click.echo(f"Category: {selected_plugin.category}")
                click.echo(f"Priority: {selected_plugin.priority}")

            results = selected_plugin.analyze_paths()

            click.echo(f'Paths analyzed: {len(results["paths"])}')
            click.echo(f'Space analyzed: {results["total_size_human"]}')
            click.echo(f'Files found: {results["file_count"]}')
            click.echo(f'Safe to clean: {results["safe_to_clean"]}')

            if verbose and results["paths"]:
                click.echo("\nDetailed results:")
                for path_info in results["paths"]:
                    status = "✅" if path_info["safe"] else "⚠️"
                    click.echo(f'  {status} {path_info["path"]} ({path_info["size_human"]})')

        sys.exit(0)
    
    # Use category-based analysis
    if category != "all":
        # Analyze specific category
        if output_json:
            results = cleaner.analyze_category(category)
            click.echo(json.dumps(results, indent=2))
        else:
            if verbose:
                click.echo(f"Analyzing category: {category}")
            
            results = cleaner.analyze_category(category)
            
            if 'error' in results:
                click.echo(f'Error: {results["error"]}', err=True)
                sys.exit(1)
            
            click.echo(f'Category: {category}')
            click.echo(f'Space analyzed: {results["total_size_human"]}')
            click.echo(f'Files found: {results["total_files"]}')
            
            if verbose and 'categories' in results:
                for cat_name, cat_info in results['categories'].items():
                    click.echo(f'  {cat_name}: {cat_info["size"] / (1024**3):.2f} GB')
    else:
        # Analyze all categories
        if output_json:
            results = cleaner.analyze()
            click.echo(json.dumps(results, indent=2))
        else:
            if verbose:
                click.echo("Analyzing all categories...")
            
            results = cleaner.analyze()
            
            if 'error' in results:
                click.echo(f'Error: {results["error"]}', err=True)
                sys.exit(1)
            
            click.echo(f'Total space analyzed: {results["total_size_human"]}')
            click.echo(f'Total files found: {results["total_files"]}')
            click.echo(f'Plugins used: {results["plugins_analyzed"]}')
            
            # Show category breakdown
            if 'categories' in results:
                click.echo("\nCategory breakdown:")
                for cat_name, cat_info in results['categories'].items():
                    size_gb = cat_info["size"] / (1024**3)
                    click.echo(f'  {cat_name}: {size_gb:.2f} GB ({cat_info["files"]:,} files)')
            
            # Show recommendations
            if 'summary' in results and 'recommendations' in results['summary']:
                click.echo("\nRecommendations:")
                for rec in results['summary']['recommendations']:
                    click.echo(f'  💡 {rec}')
            
            # Show safety breakdown
            if 'summary' in results and 'safety_breakdown' in results['summary']:
                click.echo("\nSafety breakdown:")
                for level, count in results['summary']['safety_breakdown'].items():
                    if count > 0:
                        click.echo(f'  {level}: {count:,} items')

    if category == "all":
        if output_json:
            results = cleaner.clean_all(dry_run=dry_run)
            click.echo(json.dumps(results, indent=2))
        else:
            with click.progressbar(length=100, label="Analyzing") as bar:
                results = cleaner.clean_all(dry_run=dry_run, progress=bar.update)
            click.echo(f'Files identified: {results["total_files"]}')
            click.echo(f'Potential savings: {results["total_space_human"]}')
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
            "total_space_human": format_bytes(total_space),
        }
        click.echo(json.dumps(payload, indent=2))
    else:
        click.echo(f"Files identified: {total_files}")
        click.echo(f"Potential savings: {format_bytes(total_space)}")
    sys.exit(0)


@main.command()
@click.option("--json", "output_json", is_flag=True, help="Output report as JSON")
@click.option("--plugin", help="Analyze specific plugin")
def analyze(output_json, plugin):
    """Analyze disk usage."""

    if plugin:
        # Plugin-based analysis
        plugin_manager = register_builtin_plugins(PluginManager())
        selected_plugin = plugin_manager.get_plugin(plugin)

        if not selected_plugin:
            click.echo(f'Plugin "{plugin}" not found.', err=True)
            available_plugins = [p.name for p in plugin_manager.get_all_plugins()]
            click.echo(f'Available plugins: {", ".join(available_plugins)}')
            sys.exit(1)

        results = selected_plugin.analyze_paths()

        if output_json:
            click.echo(json.dumps(results, indent=2))
        else:
            click.echo(f"Plugin Analysis: {selected_plugin.name}")
            click.echo(f"Description: {selected_plugin.description}")
            click.echo(f"Category: {selected_plugin.category}")
            click.echo(f'Total paths: {len(results["paths"])}')
            click.echo(f'Total files: {results.get("file_count", 0)}')
            click.echo(f'Total size: {results.get("total_size_human", "0 B")}')
            click.echo(
                f'Safe to clean: {"Yes" if results.get("safe_to_clean", True) else "No"}'
            )

            for path_info in results["paths"]:
                safety_icon = "✅" if path_info["safe"] else "⚠️"
                click.echo(f'  {safety_icon} {path_info["path"]}')
                click.echo(
                    f'     Size: {path_info["size_human"]}, Files: {path_info["file_count"]}'
                )

        sys.exit(0)

    # Standard analysis
    analyzer = SpaceAnalyzer()
    report = analyzer.generate_report()

    if output_json:
        click.echo(json.dumps(report, indent=2, default=str))
        sys.exit(0)

    analyzer.print_report(report)
    sys.exit(0)


@main.command()
@click.option("--json", "output_json", is_flag=True, help="Output list as JSON")
def plugins(output_json):
    """List available plugins."""
    plugin_manager = register_builtin_plugins(PluginManager())

    if output_json:
        plugin_info = []
        for plugin in plugin_manager.get_all_plugins():
            plugin_info.append(
                {
                    "name": plugin.name,
                    "category": plugin.category,
                    "description": plugin.description,
                }
            )
        click.echo(json.dumps(plugin_info, indent=2))
    else:
        click.echo("Available Plugins:")
        click.echo()

        for category in plugin_manager.get_categories():
            click.echo(f"{category.upper()}:")
            for plugin in plugin_manager.get_plugins_by_category(category):
                click.echo(f"  • {plugin.name}")
                click.echo(f"    {plugin.description}")
            click.echo()

    sys.exit(0)


@main.command()
@click.option("--path", required=True, help="Path to backup")
@click.option("--json", "output_json", is_flag=True, help="Output result as JSON")
def backup(path, output_json):
    """Create backup of specified path."""
    # Validate input path
    if not path or not isinstance(path, str):
        click.echo("❌ Invalid path: must be a non-empty string", err=True)
        sys.exit(1)

    # Validate path using SecurityValidator
    is_valid, error_msg = SecurityValidator.validate_filename(path)
    if not is_valid:
        click.echo(f"❌ Invalid path: {error_msg}", err=True)
        sys.exit(1)

    safety_manager = SafetyManager()

    try:
        success = safety_manager.create_backup(path)

        if output_json:
            click.echo(
                json.dumps(
                    {
                        "success": success,
                        "path": path,
                        "backup_path": safety_manager.backup_dir / Path(path).name,
                    },
                    indent=2,
                )
            )
        else:
            if success:
                click.echo(f"✅ Backup created successfully")
                click.echo(f"Path: {path}")
                click.echo(
                    f"Backup location: {safety_manager.backup_dir / Path(path).name}"
                )
            else:
                click.echo(f"❌ Backup failed for path: {path}", err=True)
                sys.exit(1)

    except Exception as e:
        if output_json:
            click.echo(
                json.dumps({"success": False, "path": path, "error": str(e)}, indent=2)
            )
        else:
            click.echo(f"❌ Error creating backup: {e}", err=True)
            sys.exit(1)

    sys.exit(0)


@main.command()
@click.option(
    "--list-backups", "list_backups", is_flag=True, help="List available backups"
)
@click.option("--restore", help="Restore specific backup")
@click.option("--json", "output_json", is_flag=True, help="Output result as JSON")
def restore(list_backups, restore, output_json):
    """Manage and restore backups."""
    safety_manager = SafetyManager()

    if list_backups:
        backups = safety_manager.list_backups()

        if output_json:
            click.echo(json.dumps(backups, indent=2, default=str))
        else:
            if not backups:
                click.echo("No backups found.")
                sys.exit(0)

            click.echo("Available Backups:")
            for backup in backups:
                size_str = (
                    safety_manager.format_bytes(backup["total_size"])
                    if hasattr(safety_manager, "format_bytes")
                    else f"{backup['total_size']} bytes"
                )
                click.echo(f'  • Session {backup["session_id"]}')
                click.echo(f'    Created: {backup["timestamp"]}')
                click.echo(f"    Size: {size_str}")
                click.echo(f'    Files: {len(backup["files"])}')
                for file_info in backup["files"]:
                    click.echo(f'      - {file_info["original_path"]}')
                click.echo()

        sys.exit(0)

    if restore:
        try:
            success = safety_manager.restore_backup(restore)

            if output_json:
                click.echo(
                    json.dumps({"success": success, "backup": restore}, indent=2)
                )
            else:
                if success:
                    click.echo(f"✅ Backup restored successfully: {restore}")
                else:
                    click.echo(f"❌ Failed to restore backup: {restore}", err=True)
                    sys.exit(1)

        except Exception as e:
            if output_json:
                click.echo(
                    json.dumps(
                        {"success": False, "backup": restore, "error": str(e)}, indent=2
                    )
                )
            else:
                click.echo(f"❌ Error restoring backup: {e}", err=True)
                sys.exit(1)

        sys.exit(0)

    # No options specified, show help
    click.echo(
        "Use --list-backups to see available backups or --restore <backup_name> to restore."
    )
    sys.exit(0)



@main.command()
@click.option("--host", default="127.0.0.1", help="Web server host")
@click.option("--port", default=5000, help="Web server port")
def web(host, port):
    """Launch web interface (recommended)."""
    # Validate inputs
    if not isinstance(host, str) or not host.strip():
        click.echo("❌ Invalid host: must be a non-empty string", err=True)
        sys.exit(1)

    if not isinstance(port, int) or port < 1 or port > 65535:
        click.echo("❌ Invalid port: must be an integer between 1 and 65535", err=True)
        sys.exit(1)

    try:
        click.echo("🌐 Launching web interface...")
        click.echo(f"📋 Open your browser to: http://{host}:{port}")
        
        # Import and run web GUI directly
        from mac_cleaner.web.web_gui import app
        app.run(host=host, port=port, debug=False)
        
    except KeyboardInterrupt:
        click.echo("\n✅ Web interface stopped")
    except ImportError as e:
        click.echo(f"❌ Import error: {e}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"Error launching web interface: {e}", err=True)
        sys.exit(1)


@main.command()
@click.option("--json", "output_json", is_flag=True, help="Output info as JSON")
def info(output_json):
    """Show system information."""
    from mac_cleaner.mac_cleaner import MacCleaner
    cleaner = MacCleaner()

    try:
        system_info = cleaner.get_system_info()

        if output_json:
            click.echo(json.dumps(system_info, indent=2, default=str))
        else:
            click.echo("System Information:")
            click.echo(
                f'  macOS Version: {system_info.get("macos_version", "Unknown")}'
            )
            click.echo(
                f'  Python Version: {system_info.get("python_version", "Unknown")}'
            )
            click.echo(
                f'  Total Disk Space: {system_info.get("total_space_human", "Unknown")}'
            )
            click.echo(
                f'  Used Disk Space: {system_info.get("used_space_human", "Unknown")}'
            )
            click.echo(
                f'  Free Disk Space: {system_info.get("free_space_human", "Unknown")}'
            )
            click.echo(
                f'  Disk Usage: {system_info.get("disk_usage_percent", "Unknown")}%'
            )

    except Exception as e:
        if output_json:
            click.echo(json.dumps({"error": str(e)}, indent=2))
        else:
            click.echo(f"Error getting system info: {e}", err=True)
            sys.exit(1)

    sys.exit(0)


if __name__ == "__main__":
    main()

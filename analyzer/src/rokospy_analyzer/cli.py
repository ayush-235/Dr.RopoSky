"""Command-line interface (CLI) for Rokospy Static & Security Analyzer."""

import json
import sys
from pathlib import Path
import click
from rokospy_analyzer.pipeline import AnalyzerPipeline
from rokospy_analyzer.reporting.formatter import TerminalFormatter


@click.group()
@click.version_option(version="0.1.0", prog_name="rokospy-analyzer")
def main():
    """Dr.RopoSky — Standalone Core Static & Cybersecurity Analyzer."""
    pass


@main.command(name="analyze")
@click.argument("target", type=str, required=True)
@click.option(
    "--output",
    "-o",
    type=click.Path(dir_okay=False, writable=True),
    default=None,
    help="Path to write the JSON audit report to.",
)
@click.option(
    "--json-only",
    is_flag=True,
    default=False,
    help="Print raw JSON to stdout instead of formatted terminal summary.",
)
def analyze(target: str, output: str, json_only: bool):
    """
    Analyzes a GitHub repository URL, local project directory, or ZIP archive.

    Examples:

      rokospy analyze https://github.com/owner/repo

      rokospy analyze ./project.zip --output report.json

      rokospy analyze ./my-app
    """
    try:
        report = AnalyzerPipeline.analyze(target)
    except Exception as e:
        click.echo(f"Error during analysis: {str(e)}", err=True)
        sys.exit(1)

    # Format JSON
    report_json = report.model_dump_json(indent=2)

    # Save to file if requested
    if output:
        out_path = Path(output).resolve()
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(report_json, encoding="utf-8")
        if not json_only:
            click.echo(f"\n[✓] Audit report saved to {out_path}")

    # Output results
    if json_only:
        click.echo(report_json)
    else:
        formatted_terminal = TerminalFormatter.format_report(report)
        click.echo(formatted_terminal)


if __name__ == "__main__":
    main()

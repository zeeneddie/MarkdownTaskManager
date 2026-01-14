#!/usr/bin/env python3
"""
SIG Top 10 + OWASP Security Analysis Runner

Standalone script to run all quality metrics on a codebase.
Designed for Classic ASP, .NET, and mixed codebases.

Usage:
    python run_sig_analysis.py /path/to/codebase [--output report.json]
"""

import asyncio
import json
import sys
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List

# Add backend to path
SCRIPT_DIR = Path(__file__).parent
BACKEND_DIR = SCRIPT_DIR.parent
sys.path.insert(0, str(BACKEND_DIR))

from app.scanners.base import ScanResult
from app.scanners.dotnet.dotnet_scanner import DotNetVolumeScanner, DotNetDuplicationScanner
from app.scanners.metrics.complexity_analyzer import ComplexityAnalyzer
from app.scanners.metrics.interfacing_analyzer import InterfacingAnalyzer
from app.scanners.metrics.coupling_analyzer import CouplingAnalyzer
from app.scanners.metrics.balance_analyzer import BalanceAnalyzer
from app.scanners.metrics.duplication_analyzer import DuplicationAnalyzer
from app.scanners.metrics.comments_analyzer import CommentsAnalyzer


class SIGAnalysisRunner:
    """Run all SIG Top 10 metrics analysis."""

    def __init__(self, project_path: str):
        self.project_path = Path(project_path)
        if not self.project_path.exists():
            raise ValueError(f"Project path does not exist: {project_path}")

        # Initialize all analyzers
        self.analyzers = {
            # SIG #1: Volume
            'volume': DotNetVolumeScanner(str(self.project_path)),
            # SIG #2: Duplication (two analyzers for comparison)
            'duplication_dotnet': DotNetDuplicationScanner(str(self.project_path)),
            'duplication_hci': DuplicationAnalyzer(str(self.project_path)),
            # SIG #3: Unit Complexity
            'complexity': ComplexityAnalyzer(str(self.project_path)),
            # SIG #4: Unit Interfacing
            'interfacing': InterfacingAnalyzer(str(self.project_path)),
            # SIG #5 & #8: Module Coupling & Component Independence
            'coupling': CouplingAnalyzer(str(self.project_path)),
            # SIG #6: Component Balance
            'balance': BalanceAnalyzer(str(self.project_path)),
            # SIG #9: Code Comments
            'comments': CommentsAnalyzer(str(self.project_path)),
        }

    async def run_all(self) -> Dict[str, Any]:
        """Run all SIG metrics and aggregate results."""
        results = {
            'project_path': str(self.project_path),
            'project_name': self.project_path.name,
            'analysis_timestamp': datetime.now().isoformat(),
            'sig_ratings': {},
            'scanner_results': {},
            'summary': {},
            'findings': [],
        }

        print(f"\n{'='*70}")
        print(f"SIG Top 10 Analysis: {self.project_path.name}")
        print(f"Path: {self.project_path}")
        print(f"{'='*70}\n")

        for name, analyzer in self.analyzers.items():
            print(f"Running {name}...", end=" ", flush=True)
            try:
                result = await analyzer.scan()
                results['scanner_results'][name] = self._serialize_result(result)

                if result.success:
                    # Extract rating if available
                    if result.metrics and result.metrics.metadata:
                        rating = result.metrics.metadata.get('rating')
                        if rating:
                            results['sig_ratings'][name] = {
                                'rating': rating,
                                'stars': '★' * rating + '☆' * (5 - rating)
                            }

                    # Collect findings
                    if result.findings:
                        for finding in result.findings:
                            results['findings'].append({
                                'scanner': name,
                                'rule_id': finding.rule_id,
                                'severity': finding.severity.value,
                                'message': finding.message,
                                'file': finding.file_path,
                                'line': finding.line_number,
                            })

                    findings_count = len(result.findings) if result.findings else 0
                    print(f"✓ ({findings_count} findings)")
                else:
                    print(f"✗ Error: {result.error_message}")

            except Exception as e:
                print(f"✗ Exception: {e}")
                results['scanner_results'][name] = {
                    'success': False,
                    'error': str(e)
                }

        # Generate summary
        results['summary'] = self._generate_summary(results)

        return results

    def _serialize_result(self, result: ScanResult) -> Dict[str, Any]:
        """Serialize ScanResult to dict."""
        data = {
            'scanner_name': result.scanner_name,
            'scanner_version': result.scanner_version,
            'success': result.success,
            'error_message': result.error_message,
        }

        if result.metrics:
            data['metrics'] = {
                'files_scanned': result.metrics.files_scanned,
                'lines_of_code': result.metrics.lines_of_code,
                'code_lines': result.metrics.code_lines,
                'complexity_average': result.metrics.complexity_average,
                'duplication_percentage': result.metrics.duplication_percentage,
            }
            if result.metrics.metadata:
                data['metrics']['metadata'] = result.metrics.metadata

        if result.findings:
            data['findings_count'] = len(result.findings)
            data['findings_by_severity'] = {}
            for finding in result.findings:
                sev = finding.severity.value
                data['findings_by_severity'][sev] = data['findings_by_severity'].get(sev, 0) + 1

        return data

    def _generate_summary(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate overall quality summary."""
        summary = {
            'overall_rating': 0,
            'total_findings': len(results['findings']),
            'critical_findings': 0,
            'high_findings': 0,
            'medium_findings': 0,
            'low_findings': 0,
            'ratings_breakdown': {},
        }

        # Count findings by severity
        for finding in results['findings']:
            sev = finding['severity']
            if sev == 'critical':
                summary['critical_findings'] += 1
            elif sev == 'high':
                summary['high_findings'] += 1
            elif sev == 'medium':
                summary['medium_findings'] += 1
            elif sev == 'low':
                summary['low_findings'] += 1

        # Calculate overall rating (average of all ratings)
        ratings = [r['rating'] for r in results['sig_ratings'].values()]
        if ratings:
            summary['overall_rating'] = round(sum(ratings) / len(ratings), 1)
            summary['overall_stars'] = '★' * int(summary['overall_rating']) + '☆' * (5 - int(summary['overall_rating']))

        # Breakdown by scanner
        for name, rating_data in results['sig_ratings'].items():
            summary['ratings_breakdown'][name] = rating_data['stars']

        return summary


def print_report(results: Dict[str, Any]):
    """Print formatted report to console."""
    print(f"\n{'='*70}")
    print("SIG TOP 10 QUALITY REPORT")
    print(f"{'='*70}\n")

    # Summary
    summary = results.get('summary', {})
    print(f"Overall Rating: {summary.get('overall_stars', 'N/A')} ({summary.get('overall_rating', 0)}/5)")
    print(f"Total Findings: {summary.get('total_findings', 0)}")
    print(f"  - Critical: {summary.get('critical_findings', 0)}")
    print(f"  - High:     {summary.get('high_findings', 0)}")
    print(f"  - Medium:   {summary.get('medium_findings', 0)}")
    print(f"  - Low:      {summary.get('low_findings', 0)}")

    # Ratings breakdown
    print(f"\n{'─'*40}")
    print("SIG Metric Ratings:")
    print(f"{'─'*40}")

    sig_mapping = {
        'volume': 'SIG #1: Volume',
        'duplication_dotnet': 'SIG #2: Duplication (.NET)',
        'duplication_hci': 'SIG #2: Duplication (HCI)',
        'complexity': 'SIG #3: Unit Complexity',
        'interfacing': 'SIG #4: Unit Interfacing',
        'coupling': 'SIG #5/#8: Coupling/Independence',
        'balance': 'SIG #6: Component Balance',
        'comments': 'SIG #9: Code Comments',
    }

    for name, display_name in sig_mapping.items():
        rating_data = results.get('sig_ratings', {}).get(name, {})
        stars = rating_data.get('stars', 'N/A')
        print(f"  {display_name:35} {stars}")

    # Volume stats
    volume_result = results.get('scanner_results', {}).get('volume', {})
    if volume_result.get('success'):
        metrics = volume_result.get('metrics', {})
        metadata = metrics.get('metadata', {})

        print(f"\n{'─'*40}")
        print("Volume Statistics:")
        print(f"{'─'*40}")
        print(f"  Files Scanned:    {metrics.get('files_scanned', 0):,}")
        print(f"  Total Lines:      {metrics.get('lines_of_code', 0):,}")
        print(f"  Code Lines:       {metrics.get('code_lines', 0):,}")

        if metadata.get('by_extension'):
            print(f"\n  By Extension:")
            for ext, data in sorted(metadata['by_extension'].items(),
                                   key=lambda x: x[1].get('code_lines', 0),
                                   reverse=True)[:10]:
                print(f"    {ext:12} {data.get('count', 0):5} files, {data.get('code_lines', 0):,} code lines")

    # Top findings
    if results.get('findings'):
        print(f"\n{'─'*40}")
        print(f"Top {min(10, len(results['findings']))} Findings:")
        print(f"{'─'*40}")

        # Sort by severity
        severity_order = {'critical': 0, 'high': 1, 'medium': 2, 'low': 3, 'info': 4}
        sorted_findings = sorted(
            results['findings'],
            key=lambda x: severity_order.get(x['severity'], 5)
        )[:10]

        for i, finding in enumerate(sorted_findings, 1):
            sev = finding['severity'].upper()[:4]
            msg = finding['message'][:60]
            file = Path(finding['file']).name if finding['file'] else ''
            print(f"  {i:2}. [{sev:4}] {msg}")
            if file:
                print(f"      └─ {file}:{finding.get('line', '?')}")

    print(f"\n{'='*70}")


async def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage: python run_sig_analysis.py <project_path> [--output <file.json>]")
        sys.exit(1)

    project_path = sys.argv[1]
    output_file = None

    if '--output' in sys.argv:
        idx = sys.argv.index('--output')
        if idx + 1 < len(sys.argv):
            output_file = sys.argv[idx + 1]

    try:
        runner = SIGAnalysisRunner(project_path)
        results = await runner.run_all()

        # Print console report
        print_report(results)

        # Save to file if requested
        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, default=str)
            print(f"\nFull results saved to: {output_file}")

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    asyncio.run(main())

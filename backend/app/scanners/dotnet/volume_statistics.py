#!/usr/bin/env python3
"""
Volume Statistics Generator

Generates statistical distributions and visualizations from code analysis CSV data.
This provides deeper insights into:
- Code distribution across languages/file types
- File size distributions (Pareto analysis)
- Code density metrics (comments/blank lines ratio)
- Complexity indicators

Usage:
    python volume_statistics.py [--csv path/to/code_analysis.csv]

Output:
    - Statistical summary in Markdown
    - Distribution charts (optional - requires matplotlib)
"""

import csv
import sys
from pathlib import Path
from collections import defaultdict
from datetime import datetime
import argparse

# Add parent directory for config import
sys.path.insert(0, str(Path(__file__).parent.parent))
from config import get_report_path

class VolumeStatistics:
    """Generates statistical analysis of code volume data"""

    def __init__(self, csv_path):
        self.csv_path = Path(csv_path)
        self.data = []
        self.stats_by_type = defaultdict(lambda: {
            'files': 0,
            'total_loc': 0,
            'code_loc': 0,
            'comment_loc': 0,
            'blank_loc': 0,
            'avg_file_size': 0,
            'max_file_size': 0,
            'min_file_size': float('inf'),
            'file_sizes': []
        })

    def load_data(self):
        """Load CSV data"""
        print(f"[*] Loading data from: {self.csv_path}")

        with open(self.csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                self.data.append({
                    'path': row['path'],
                    'filename': row['filename'],
                    'type': row['type'],
                    'extension': row['extension'],
                    'total_lines': int(row['total_lines']),
                    'code_lines': int(row['code_lines']),
                    'comment_lines': int(row['comment_lines']),
                    'blank_lines': int(row['blank_lines'])
                })

        print(f"[+] Loaded {len(self.data)} files")
        return self

    def calculate_statistics(self):
        """Calculate statistical distributions"""
        print("[*] Calculating statistics...")

        # Aggregate by type
        for file_data in self.data:
            file_type = file_data['type']
            stats = self.stats_by_type[file_type]

            stats['files'] += 1
            stats['total_loc'] += file_data['total_lines']
            stats['code_loc'] += file_data['code_lines']
            stats['comment_loc'] += file_data['comment_lines']
            stats['blank_loc'] += file_data['blank_lines']
            stats['file_sizes'].append(file_data['code_lines'])

            if file_data['code_lines'] > stats['max_file_size']:
                stats['max_file_size'] = file_data['code_lines']
            if file_data['code_lines'] < stats['min_file_size']:
                stats['min_file_size'] = file_data['code_lines']

        # Calculate averages
        for file_type, stats in self.stats_by_type.items():
            if stats['files'] > 0:
                stats['avg_file_size'] = stats['code_loc'] / stats['files']

        print("[+] Statistics calculated")
        return self

    def pareto_analysis(self):
        """
        Pareto analysis: Find which file types contribute to 80% of code volume

        This identifies the dominant languages/file types in the codebase.
        Typically, 20% of file types contribute to 80% of the code (Pareto principle).
        """
        print("[*] Performing Pareto analysis...")

        # Sort by code volume
        sorted_types = sorted(
            self.stats_by_type.items(),
            key=lambda x: x[1]['code_loc'],
            reverse=True
        )

        total_code = sum(stats['code_loc'] for _, stats in sorted_types)
        cumulative = 0
        pareto_80 = []
        pareto_95 = []

        for file_type, stats in sorted_types:
            percentage = (stats['code_loc'] / total_code * 100) if total_code > 0 else 0
            cumulative += percentage

            if cumulative <= 80:
                pareto_80.append((file_type, stats['code_loc'], percentage, cumulative))
            if cumulative <= 95:
                pareto_95.append((file_type, stats['code_loc'], percentage, cumulative))

        print(f"[+] Pareto 80%: {len(pareto_80)} file types")
        print(f"[+] Pareto 95%: {len(pareto_95)} file types")

        return {
            'pareto_80': pareto_80,
            'pareto_95': pareto_95,
            'total_types': len(sorted_types),
            'sorted_types': sorted_types
        }

    def file_size_distribution(self):
        """
        Analyze file size distribution to identify:
        - Large files that may need refactoring
        - Average file sizes per language
        - Outliers (files significantly larger than average)
        """
        print("[*] Analyzing file size distribution...")

        all_files = sorted(self.data, key=lambda x: x['code_lines'], reverse=True)

        # Overall statistics
        total_files = len(all_files)
        total_code = sum(f['code_lines'] for f in all_files)
        avg_file_size = total_code / total_files if total_files > 0 else 0

        # Find large files (> 2 standard deviations from mean)
        import math
        variance = sum((f['code_lines'] - avg_file_size) ** 2 for f in all_files) / total_files
        std_dev = math.sqrt(variance)
        threshold = avg_file_size + (2 * std_dev)

        large_files = [f for f in all_files if f['code_lines'] > threshold]

        # Top 10 largest files
        top_10 = all_files[:10]

        # Files contributing to 50% of code
        cumulative = 0
        files_50_percent = []
        for file_data in all_files:
            cumulative += file_data['code_lines']
            files_50_percent.append(file_data)
            if cumulative >= total_code * 0.5:
                break

        print(f"[+] Average file size: {avg_file_size:.1f} LOC")
        print(f"[+] Large files (>{threshold:.0f} LOC): {len(large_files)}")
        print(f"[+] Top {len(files_50_percent)} files = 50% of code")

        return {
            'avg_file_size': avg_file_size,
            'std_dev': std_dev,
            'threshold': threshold,
            'large_files': large_files,
            'top_10': top_10,
            'files_50_percent': files_50_percent
        }

    def code_density_analysis(self):
        """
        Analyze code density metrics:
        - Comment ratio (comments / total lines)
        - Code ratio (code / total lines)
        - Blank line ratio

        Higher comment ratios indicate better documentation.
        Balance between code/comments/blanks indicates readability.
        """
        print("[*] Analyzing code density...")

        density_by_type = {}

        for file_type, stats in self.stats_by_type.items():
            total = stats['total_loc']
            if total > 0:
                density_by_type[file_type] = {
                    'code_ratio': (stats['code_loc'] / total) * 100,
                    'comment_ratio': (stats['comment_loc'] / total) * 100,
                    'blank_ratio': (stats['blank_loc'] / total) * 100,
                    'comments_per_100_loc': (stats['comment_loc'] / stats['code_loc'] * 100) if stats['code_loc'] > 0 else 0
                }

        # Overall density
        total_all = sum(stats['total_loc'] for stats in self.stats_by_type.values())
        code_all = sum(stats['code_loc'] for stats in self.stats_by_type.values())
        comment_all = sum(stats['comment_loc'] for stats in self.stats_by_type.values())
        blank_all = sum(stats['blank_loc'] for stats in self.stats_by_type.values())

        overall_density = {
            'code_ratio': (code_all / total_all * 100) if total_all > 0 else 0,
            'comment_ratio': (comment_all / total_all * 100) if total_all > 0 else 0,
            'blank_ratio': (blank_all / total_all * 100) if total_all > 0 else 0,
            'comments_per_100_loc': (comment_all / code_all * 100) if code_all > 0 else 0
        }

        print(f"[+] Overall comment ratio: {overall_density['comment_ratio']:.1f}%")
        print(f"[+] Comments per 100 LOC: {overall_density['comments_per_100_loc']:.1f}")

        return {
            'by_type': density_by_type,
            'overall': overall_density
        }

    def generate_report(self, pareto, distribution, density):
        """Generate statistical analysis report in Markdown"""

        output_file = get_report_path('volume', 'volume_statistics.md')

        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("# Code Volume Statistical Analysis\n\n")
            f.write(f"**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write(f"**Source**: `{self.csv_path.name}`\n\n")

            # Executive Summary
            f.write("## Executive Summary\n\n")
            f.write("Deze statistische analyse identificeert de belangrijkste kenmerken van de codebase volume:\n\n")
            f.write("**Wat zeggen deze statistieken over de codebase?**\n\n")

            # Interpretation paragraph 1
            f.write("De **Pareto analyse** (80/20 regel) toont welke programmeertalen of bestandstypes het meest ")
            f.write("dominant zijn in de codebase. Als bijvoorbeeld slechts 2-3 talen 80% van de code vertegenwoordigen, ")
            f.write("dan is de technologie stack gefocust en homogeen. Dit vereenvoudigt migratie, omdat je slechts expertise ")
            f.write("nodig hebt in deze dominante talen. Omgekeerd, als 8-10 talen nodig zijn voor 80%, wijst dit op een ")
            f.write("gefragmenteerde codebase met hogere complexiteit en migratie-inspanning.\n\n")

            # Interpretation paragraph 2
            f.write("De **bestandsgrootte distributie** identificeert 'god files' - extreem grote bestanden die vaak ")
            f.write("meerdere verantwoordelijkheden bevatten en refactoring nodig hebben. Bestanden groter dan 2x het ")
            f.write("gemiddelde zijn technische schuld hotspots. De **code density** (comment ratio) geeft aan hoe goed ")
            f.write("de code gedocumenteerd is: <10% comments duidt op slechte documentatie, 10-30% is acceptabel, ")
            f.write(">30% kan duiden op over-documentatie of gegenereerde code. Ideaal is 15-25% met betekenisvolle comments.\n\n")

            # Pareto Analysis
            f.write("## Pareto Analysis (80/20 Rule)\n\n")
            f.write("### Dominant File Types (80% of Code)\n\n")

            f.write("| File Type | LOC | % of Total | Cumulative % |\n")
            f.write("|-----------|----:|----------:|-------------:|\n")
            for file_type, loc, pct, cum in pareto['pareto_80']:
                f.write(f"| {file_type} | {loc:,} | {pct:.2f}% | {cum:.2f}% |\n")

            f.write(f"\n**Key Insight**: {len(pareto['pareto_80'])} out of {pareto['total_types']} file types ")
            f.write(f"({len(pareto['pareto_80'])/pareto['total_types']*100:.1f}%) contain 80% of the code.\n\n")

            if len(pareto['pareto_80']) <= 3:
                f.write("✅ **Focused Stack**: Very concentrated technology stack - easier to migrate.\n\n")
            elif len(pareto['pareto_80']) <= 5:
                f.write("⚠️ **Moderate Diversity**: Reasonably focused but some technology fragmentation.\n\n")
            else:
                f.write("❌ **Fragmented Stack**: Highly diverse technologies - complex migration path.\n\n")

            # File Size Distribution
            f.write("## File Size Distribution\n\n")

            f.write(f"- **Average File Size**: {distribution['avg_file_size']:.1f} LOC\n")
            f.write(f"- **Standard Deviation**: {distribution['std_dev']:.1f} LOC\n")
            f.write(f"- **Large File Threshold**: >{distribution['threshold']:.0f} LOC (avg + 2σ)\n")
            f.write(f"- **Large Files Found**: {len(distribution['large_files'])} files\n")
            f.write(f"- **50% of Code in**: {len(distribution['files_50_percent'])} files ({len(distribution['files_50_percent'])/len(self.data)*100:.1f}% of total)\n\n")

            # Top 10 Largest Files
            f.write("### Top 10 Largest Files (Refactoring Candidates)\n\n")
            f.write("| File | Type | LOC | Path |\n")
            f.write("|------|------|----:|------|\n")
            for file_data in distribution['top_10']:
                f.write(f"| {file_data['filename']} | {file_data['type']} | ")
                f.write(f"{file_data['code_lines']:,} | `{file_data['path']}` |\n")

            f.write("\n")

            # Code Density
            f.write("## Code Density Analysis\n\n")

            overall = density['overall']
            f.write("### Overall Metrics\n\n")
            f.write(f"- **Code Ratio**: {overall['code_ratio']:.1f}%\n")
            f.write(f"- **Comment Ratio**: {overall['comment_ratio']:.1f}%\n")
            f.write(f"- **Blank Line Ratio**: {overall['blank_ratio']:.1f}%\n")
            f.write(f"- **Comments per 100 LOC**: {overall['comments_per_100_loc']:.1f}\n\n")

            # Documentation quality assessment
            if overall['comment_ratio'] < 10:
                f.write("❌ **Poor Documentation**: <10% comments - technical debt risk.\n\n")
            elif overall['comment_ratio'] < 15:
                f.write("⚠️ **Minimal Documentation**: 10-15% comments - below industry standard.\n\n")
            elif overall['comment_ratio'] < 25:
                f.write("✅ **Good Documentation**: 15-25% comments - healthy balance.\n\n")
            elif overall['comment_ratio'] < 30:
                f.write("✅ **Well Documented**: 25-30% comments - above average.\n\n")
            else:
                f.write("⚠️ **Over-Documented**: >30% comments - possibly auto-generated or redundant.\n\n")

            # Density by file type
            f.write("### Documentation by File Type\n\n")
            f.write("| File Type | Code % | Comment % | Blank % | Comments/100 LOC |\n")
            f.write("|-----------|-------:|----------:|--------:|-----------------:|\n")

            sorted_density = sorted(
                density['by_type'].items(),
                key=lambda x: self.stats_by_type[x[0]]['code_loc'],
                reverse=True
            )

            for file_type, dens in sorted_density[:10]:  # Top 10 by volume
                f.write(f"| {file_type} | {dens['code_ratio']:.1f}% | ")
                f.write(f"{dens['comment_ratio']:.1f}% | {dens['blank_ratio']:.1f}% | ")
                f.write(f"{dens['comments_per_100_loc']:.1f} |\n")

            f.write("\n")

            # Recommendations
            f.write("## Recommendations\n\n")

            f.write("### Priority Actions\n\n")

            # Large files
            if len(distribution['large_files']) > 0:
                f.write(f"1. **Refactor Large Files**: {len(distribution['large_files'])} files exceed ")
                f.write(f"{distribution['threshold']:.0f} LOC. Consider splitting into smaller, ")
                f.write(f"more focused modules.\n\n")

            # Documentation
            if overall['comment_ratio'] < 15:
                f.write(f"2. **Improve Documentation**: Current {overall['comment_ratio']:.1f}% comment ratio ")
                f.write(f"is below recommended 15-25%. Add meaningful comments to complex logic.\n\n")

            # Technology fragmentation
            if len(pareto['pareto_80']) > 5:
                f.write(f"3. **Consolidate Technology Stack**: {len(pareto['pareto_80'])} languages in 80% of code ")
                f.write(f"indicates fragmentation. Consider standardizing on fewer technologies.\n\n")

            # 50% concentration
            concentration = len(distribution['files_50_percent']) / len(self.data) * 100
            if concentration < 5:
                f.write(f"4. **High Code Concentration Risk**: Just {len(distribution['files_50_percent'])} files ")
                f.write(f"({concentration:.1f}%) contain 50% of code. These are critical for business continuity.\n\n")

        print(f"\n[+] Statistical report generated: {output_file}")
        return output_file


def main():
    parser = argparse.ArgumentParser(
        description='Generate statistical analysis of code volume data'
    )
    parser.add_argument(
        '--csv',
        default=None,
        help='Path to code_analysis.csv (default: reports/01-volume/code_analysis.csv)'
    )

    args = parser.parse_args()

    # Determine CSV path
    if args.csv:
        csv_path = Path(args.csv)
    else:
        csv_path = get_report_path('volume', 'code_analysis.csv')

    if not csv_path.exists():
        print(f"[!] Error: CSV file not found: {csv_path}")
        print(f"[!] Run analyze_codebase.py first to generate the CSV data.")
        return 1

    # Run analysis
    analyzer = VolumeStatistics(csv_path)
    analyzer.load_data()
    analyzer.calculate_statistics()

    pareto = analyzer.pareto_analysis()
    distribution = analyzer.file_size_distribution()
    density = analyzer.code_density_analysis()

    analyzer.generate_report(pareto, distribution, density)

    print(f"\n[+] Statistical analysis complete!")
    return 0


if __name__ == '__main__':
    sys.exit(main())

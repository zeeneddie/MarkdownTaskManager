#!/usr/bin/env python3
"""
Code Analyzer - ASP.NET Legacy Codebase Analysis Tool
Analyzes file types, line counts, and generates comprehensive statistics
"""

import os
import csv
import json
import sys
import io
from pathlib import Path
from collections import defaultdict
from datetime import datetime
import argparse

# Import central configuration
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from config import get_report_path, VOLUME_REPORTS, should_exclude_path, EXCLUDED_DIRS
from logging_utils import ProgressLogger  # This handles UTF-8 encoding

class CodeAnalyzer:
    # File extensions mapping
    EXTENSIONS = {
        '.asp': 'ASP Classic',
        '.aspx': 'ASP.NET WebForms',
        '.ascx': 'ASP.NET User Control',
        '.master': 'ASP.NET Master Page',
        '.cs': 'C#',
        '.vb': 'VB.NET',
        '.sql': 'SQL',
        '.js': 'JavaScript',
        '.ts': 'TypeScript',
        '.css': 'CSS',
        '.html': 'HTML',
        '.xml': 'XML',
        '.config': 'Config',
        '.json': 'JSON'
    }

    def __init__(self, root_path, extensions=None, debug=False):
        self.root_path = Path(root_path)
        self.extensions = extensions or list(self.EXTENSIONS.keys())
        self.results = []
        self.stats = defaultdict(lambda: {
            'count': 0,
            'total_lines': 0,
            'code_lines': 0,
            'blank_lines': 0,
            'comment_lines': 0
        })
        self.debug = debug
        self.logger = ProgressLogger("Volume Analyzer", debug=debug)

    def count_lines(self, file_path):
        """Count different types of lines in a file"""
        total = 0
        blank = 0
        comment = 0
        code = 0

        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                in_block_comment = False

                for line in f:
                    total += 1
                    stripped = line.strip()

                    # Blank line
                    if not stripped:
                        blank += 1
                        continue

                    # Block comment detection (/* */ for C#/JS, <!-- --> for ASP/HTML)
                    if '/*' in stripped or '<!--' in stripped:
                        in_block_comment = True

                    if in_block_comment:
                        comment += 1
                        if '*/' in stripped or '-->' in stripped:
                            in_block_comment = False
                        continue

                    # Single line comments
                    if (stripped.startswith('//') or
                        stripped.startswith('\'') or  # VB comment
                        stripped.startswith('--') or  # SQL comment
                        stripped.startswith('#')):    # Some configs
                        comment += 1
                        continue

                    # Otherwise it's code
                    code += 1

        except Exception as e:
            print(f"Warning: Could not read {file_path}: {e}")
            return total, blank, comment, code

        return total, blank, comment, code

    def analyze(self):
        """Analyze the directory structure"""
        self.logger.log_info(f"Analyzing codebase: {self.root_path}")
        self.logger.log_info(f"Looking for extensions: {', '.join(self.extensions)}")

        # Phase 1: Inventory - Count total files first
        self.logger.start_inventory("Scanning directory structure")
        file_list = []
        excluded_count = 0

        for root, dirs, files in os.walk(self.root_path):
            # Skip excluded directories using central config
            dirs[:] = [d for d in dirs if not should_exclude_path(Path(root) / d)]

            for file in files:
                ext = Path(file).suffix.lower()
                if ext in self.extensions:
                    file_path = Path(root) / file

                    # Use central exclusion logic
                    if should_exclude_path(file_path):
                        excluded_count += 1
                        continue

                    file_list.append(file_path)
                    self.logger.update_inventory(len(file_list), self.EXTENSIONS.get(ext, ext))

        self.logger.complete_inventory(len(file_list), excluded_count)

        # Phase 2: Processing - Analyze each file
        self.logger.start_processing("Analyzing files")

        for idx, file_path in enumerate(file_list, 1):
            ext = file_path.suffix.lower()
            relative_path = file_path.relative_to(self.root_path)

            self.logger.log_detail(f"Processing: {relative_path}")

            total, blank, comment, code = self.count_lines(file_path)

            file_type = self.EXTENSIONS.get(ext, ext)

            self.results.append({
                'path': str(relative_path),
                'filename': file_path.name,
                'type': file_type,
                'extension': ext,
                'total_lines': total,
                'code_lines': code,
                'comment_lines': comment,
                'blank_lines': blank
            })

            self.stats[file_type]['count'] += 1
            self.stats[file_type]['total_lines'] += total
            self.stats[file_type]['code_lines'] += code
            self.stats[file_type]['comment_lines'] += comment
            self.stats[file_type]['blank_lines'] += blank

            self.logger.update(idx)

        self.logger.complete()
        return self

    def print_summary(self):
        """Print summary statistics"""
        print("\n" + "="*80)
        print("CODE STATISTICS SUMMARY")
        print("="*80)
        print(f"{'Language':<25} {'Files':>8} {'Total':>12} {'Code':>12} {'Comments':>12} {'Blank':>12}")
        print("-"*80)

        total_files = 0
        total_total = 0
        total_code = 0
        total_comment = 0
        total_blank = 0

        for file_type in sorted(self.stats.keys()):
            data = self.stats[file_type]
            print(f"{file_type:<25} {data['count']:>8} {data['total_lines']:>12,} "
                  f"{data['code_lines']:>12,} {data['comment_lines']:>12,} {data['blank_lines']:>12,}")

            total_files += data['count']
            total_total += data['total_lines']
            total_code += data['code_lines']
            total_comment += data['comment_lines']
            total_blank += data['blank_lines']

        print("-"*80)
        print(f"{'TOTAL':<25} {total_files:>8} {total_total:>12,} "
              f"{total_code:>12,} {total_comment:>12,} {total_blank:>12,}")
        print("="*80)

        # Calculate percentages
        if total_total > 0:
            print(f"\nCode Metrics:")
            print(f"   Code:     {total_code/total_total*100:>6.2f}%")
            print(f"   Comments: {total_comment/total_total*100:>6.2f}%")
            print(f"   Blank:    {total_blank/total_total*100:>6.2f}%")

        # Calculate and display Volume Quality Rating
        metrics = self.calculate_volume_rating()
        print(f"\nVolume Quality Rating:")
        print(f"   Total LOC:        {metrics['total_loc']:>12,}")
        print(f"   Volume Category:  {metrics['category']}")
        print(f"   Quality Rating:   {metrics['rating_stars']} ({metrics['quality_rating']}/5)")
        print(f"   Rebuild Value:    ~{metrics['rebuild_months']:.1f} man-months")

    def calculate_volume_rating(self):
        """
        Calculate Volume Quality Rating based on total LOC

        INVERTED RATING: Smaller codebase = Better maintainability = Higher rating

        Volume Quality Thresholds:
        - 5 stars: < 66K LOC (very small - excellent maintainability)
        - 4 stars: 66K - 246K LOC (small - good maintainability)
        - 3 stars: 246K - 665K LOC (medium - moderate maintainability)
        - 2 stars: 665K - 1,310K LOC (large - poor maintainability)
        - 1 star:  > 1,310K LOC (very large - very poor maintainability)

        Returns:
            dict with total_loc, quality_rating, rating_stars, category, rebuild_months
        """
        total_loc = sum(data['code_lines'] for data in self.stats.values())

        # Determine quality rating (INVERTED: smaller = better)
        if total_loc < 66000:
            quality_rating = 5
            rating_stars = '⭐⭐⭐⭐⭐'
            category = 'Very Small'
        elif total_loc < 246000:
            quality_rating = 4
            rating_stars = '⭐⭐⭐⭐'
            category = 'Small'
        elif total_loc < 665000:
            quality_rating = 3
            rating_stars = '⭐⭐⭐'
            category = 'Medium'
        elif total_loc < 1310000:
            quality_rating = 2
            rating_stars = '⭐⭐'
            category = 'Large'
        else:
            quality_rating = 1
            rating_stars = '⭐'
            category = 'Very Large'

        # Estimate rebuild value (man-months)
        # Industry average: ~150-200 LOC per man-day, ~20 working days/month
        # Conservative estimate: 3000 LOC per man-month
        rebuild_months = total_loc / 3000

        return {
            'total_loc': total_loc,
            'quality_rating': quality_rating,
            'rating_stars': rating_stars,
            'category': category,
            'rebuild_months': rebuild_months
        }

    def export_volume_report(self, output_file=None):
        """Generate Volume Quality Report in Markdown"""
        if output_file is None:
            output_file = get_report_path('volume', 'volume_report.md')
        metrics = self.calculate_volume_rating()

        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("# Codebase Volume Analysis Report\n\n")
            f.write(f"**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write(f"**Codebase**: `{self.root_path}`\n\n")

            # Summary
            f.write("## Summary\n\n")
            f.write(f"- **Total Code Lines (LOC)**: {metrics['total_loc']:,}\n")
            f.write(f"- **Volume Category**: {metrics['category']}\n")
            f.write(f"- **Quality Rating**: {metrics['rating_stars']} ({metrics['quality_rating']}/5)\n")
            f.write(f"- **Estimated Rebuild Value**: ~{metrics['rebuild_months']:.1f} man-months (~{metrics['rebuild_months']/12:.1f} man-years)\n\n")

            # Quality Thresholds
            f.write("## Volume Quality Rating Thresholds\n\n")
            f.write("**INVERTED RATING**: Smaller codebase = Better maintainability = Higher rating\n\n")
            f.write("| Rating | Stars | LOC Range | Category | Maintainability |\n")
            f.write("|--------|-------|-----------|----------|----------------|\n")
            f.write("| 5 | ⭐⭐⭐⭐⭐ | < 66K | Very Small | Excellent |\n")
            f.write("| 4 | ⭐⭐⭐⭐ | 66K - 246K | Small | Good |\n")
            f.write("| 3 | ⭐⭐⭐ | 246K - 665K | Medium | Moderate |\n")
            f.write("| 2 | ⭐⭐ | 665K - 1,310K | Large | Poor |\n")
            f.write("| 1 | ⭐ | > 1,310K | Very Large | Very Poor |\n\n")

            # Volume Distribution
            f.write("## Code Volume Distribution\n\n")
            f.write("| Language | LOC | % of Total |\n")
            f.write("|----------|----:|----------:|\n")

            total_loc = metrics['total_loc']
            for file_type in sorted(self.stats.keys(), key=lambda x: self.stats[x]['code_lines'], reverse=True):
                data = self.stats[file_type]
                loc = data['code_lines']
                percentage = (loc / total_loc * 100) if total_loc > 0 else 0
                f.write(f"| {file_type} | {loc:,} | {percentage:.2f}% |\n")

            f.write(f"| **TOTAL** | **{total_loc:,}** | **100.00%** |\n\n")

            # Insights
            f.write("## Insights & Recommendations\n\n")

            if metrics['quality_rating'] >= 4:
                f.write("### Small Codebase - Excellent Maintainability\n\n")
                f.write(f"This is a **{metrics['category'].lower()}** codebase ({metrics['total_loc']:,} LOC). ")
                f.write("Considerations:\n\n")
                f.write("- [+] Migration should be relatively straightforward\n")
                f.write("- [+] Lower maintenance burden\n")
                f.write("- [+] Easier to understand and modify\n")
                f.write("- Estimated effort: ~{:.1f} man-months\n\n".format(metrics['rebuild_months']))
            elif metrics['quality_rating'] == 3:
                f.write("### Medium Codebase - Moderate Maintainability\n\n")
                f.write(f"This is a **medium-sized** codebase ({metrics['total_loc']:,} LOC). ")
                f.write("Manageable migration with proper planning.\n\n")
                f.write("- Budget for ~{:.1f} man-months of development effort\n\n".format(metrics['rebuild_months']))
            else:
                f.write("### Large Codebase - Poor Maintainability\n\n")
                f.write(f"This is a **{metrics['category'].lower()}** codebase ({metrics['total_loc']:,} LOC). ")
                f.write("Considerations:\n\n")
                f.write("- [!] Migration will require significant planning and resources\n")
                f.write("- [!] Consider phased migration approach (incremental modernization)\n")
                f.write("- [!] Establish strong testing and quality gates\n")
                f.write("- Budget for ~{:.1f} man-months of development effort\n\n".format(metrics['rebuild_months']))

        print(f"\n[+] Volume Quality Report saved to: {output_file}")

    def export_csv(self, output_file=None):
        """Export detailed results to CSV"""
        if output_file is None:
            output_file = get_report_path('volume', 'code_analysis.csv')
        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=[
                'path', 'filename', 'type', 'extension',
                'total_lines', 'code_lines', 'comment_lines', 'blank_lines'
            ])
            writer.writeheader()
            writer.writerows(self.results)
        print(f"\n[+] Detailed results exported to: {output_file}")
        return output_file

    def export_json(self, output_file=None):
        """Export results to JSON"""
        if output_file is None:
            output_file = get_report_path('volume', 'code_analysis.json')
        export_data = {
            'analyzed_at': datetime.now().isoformat(),
            'root_path': str(self.root_path),
            'summary': dict(self.stats),
            'files': self.results
        }

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2)
        print(f"[+] JSON export saved to: {output_file}")

    def export_markdown(self, output_file=None):
        """Export summary to Markdown"""
        if output_file is None:
            output_file = get_report_path('volume', 'code_analysis.md')
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(f"# Code Analysis Report\n\n")
            f.write(f"**Analyzed**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write(f"**Root Path**: `{self.root_path}`\n\n")
            f.write(f"**Note**: Third-party libraries (jQuery, Bootstrap, TinyMCE, Telerik, etc.), binary files (.dll), and vendor directories (Bin Extern Web) are excluded from this analysis.\n\n")
            f.write(f"## Summary Statistics\n\n")
            f.write(f"| Language | Files | Total Lines | Code | Comments | Blank |\n")
            f.write(f"|----------|------:|------------:|-----:|---------:|------:|\n")

            for file_type in sorted(self.stats.keys()):
                data = self.stats[file_type]
                f.write(f"| {file_type} | {data['count']:,} | {data['total_lines']:,} | "
                       f"{data['code_lines']:,} | {data['comment_lines']:,} | {data['blank_lines']:,} |\n")

            f.write(f"\n## Top 10 Largest Files\n\n")
            sorted_files = sorted(self.results, key=lambda x: x['total_lines'], reverse=True)[:10]
            f.write(f"| File | Type | Lines |\n")
            f.write(f"|------|------|------:|\n")
            for file in sorted_files:
                f.write(f"| `{file['path']}` | {file['type']} | {file['total_lines']:,} |\n")

        print(f"[+] Markdown report saved to: {output_file}")


def main():
    parser = argparse.ArgumentParser(
        description='Analyze codebase and generate statistics'
    )
    parser.add_argument(
        'path',
        nargs='?',
        default='.',
        help='Path to analyze (default: current directory)'
    )
    parser.add_argument(
        '--csv',
        default=None,
        help='CSV output filename'
    )
    parser.add_argument(
        '--json',
        action='store_true',
        help='Export to JSON'
    )
    parser.add_argument(
        '--md',
        action='store_true',
        help='Export to Markdown'
    )
    parser.add_argument(
        '--extensions',
        nargs='+',
        help='Specific extensions to analyze (e.g., .cs .aspx)'
    )
    parser.add_argument(
        '--quality-report',
        default=None,
        help='Volume Quality Report output filename (default: volume_report.md)'
    )
    parser.add_argument(
        '--stats',
        action='store_true',
        help='Generate statistical analysis (Pareto, distributions, density)'
    )
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Enable debug mode (detailed logging with 15-25%% performance impact)'
    )

    args = parser.parse_args()

    # Run analysis
    analyzer = CodeAnalyzer(args.path, args.extensions, debug=args.debug)
    analyzer.analyze()
    analyzer.print_summary()

    # Export results
    csv_path = analyzer.export_csv(args.csv)

    if args.json:
        analyzer.export_json()

    if args.md:
        analyzer.export_markdown()

    # Always generate Volume Quality Report
    analyzer.export_volume_report(args.quality_report)

    # Optional: Generate statistical analysis
    if args.stats:
        print("\n[*] Generating statistical analysis...")
        import subprocess
        stats_script = Path(__file__).parent / 'volume_statistics.py'
        result = subprocess.run(
            [sys.executable, str(stats_script)],
            capture_output=True,
            text=True,
            encoding='utf-8'
        )
        if result.returncode == 0:
            print(result.stdout)
        else:
            print(f"[!] Statistics generation failed:")
            print(result.stderr)

    print(f"\n[+] Analysis complete!\n")


if __name__ == '__main__':
    main()

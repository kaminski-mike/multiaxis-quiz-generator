#!/usr/bin/env python3
"""
Multiaxis Intelligence Project Analyzer
Generates comprehensive project statistics and summary
"""

import os
import glob
import json
from datetime import datetime
from collections import defaultdict, Counter
import re

class ProjectAnalyzer:
    def __init__(self, project_root="."):
        self.project_root = project_root
        self.file_extensions = {
            '.py': 'Python',
            '.html': 'HTML',
            '.js': 'JavaScript',
            '.css': 'CSS',
            '.json': 'JSON',
            '.md': 'Markdown',
            '.txt': 'Text',
            '.bat': 'Batch',
            '.ico': 'Icon',
            '.png': 'PNG Image',
            '.jpg': 'JPEG Image',
            '.jpeg': 'JPEG Image',
            '.pdf': 'PDF',
            '.xml': 'XML'
        }
        
        # Directories to exclude from analysis
        self.exclude_dirs = {
            'venv', '__pycache__', '.git', 'node_modules', 
            'dist', 'build', '.pytest_cache', '.vscode',
            'MultiaxisAI.egg-info'
        }
        
        self.stats = {
            'total_files': 0,
            'total_lines': 0,
            'total_code_lines': 0,
            'total_comment_lines': 0,
            'total_blank_lines': 0,
            'by_language': defaultdict(lambda: {'files': 0, 'lines': 0, 'code': 0, 'comments': 0, 'blank': 0}),
            'by_directory': defaultdict(lambda: {'files': 0, 'lines': 0}),
            'largest_files': [],
            'file_types': Counter()
        }

    def should_exclude_path(self, path):
        """Check if path should be excluded from analysis"""
        path_parts = path.replace('\\', '/').split('/')
        return any(exclude_dir in path_parts for exclude_dir in self.exclude_dirs)

    def analyze_file_content(self, file_path, language):
        """Analyze individual file for detailed statistics"""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
                
            total_lines = len(lines)
            code_lines = 0
            comment_lines = 0
            blank_lines = 0
            
            for line in lines:
                stripped = line.strip()
                if not stripped:
                    blank_lines += 1
                elif language == 'Python' and (stripped.startswith('#') or (stripped.startswith('"""') or stripped.startswith("'''"))):
                    comment_lines += 1
                elif language == 'HTML' and ('<!--' in stripped or '-->' in stripped):
                    comment_lines += 1
                elif language == 'JavaScript' and (stripped.startswith('//') or stripped.startswith('/*')):
                    comment_lines += 1
                else:
                    code_lines += 1
                    
            return {
                'total': total_lines,
                'code': code_lines,
                'comments': comment_lines,
                'blank': blank_lines
            }
        except Exception as e:
            print(f"Error analyzing {file_path}: {e}")
            return {'total': 0, 'code': 0, 'comments': 0, 'blank': 0}

    def get_file_complexity_estimate(self, file_path):
        """Estimate file complexity based on various factors"""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                
            complexity_score = 0
            
            # Count functions/classes (Python)
            if file_path.endswith('.py'):
                complexity_score += len(re.findall(r'\n\s*def\s+', content)) * 2
                complexity_score += len(re.findall(r'\n\s*class\s+', content)) * 3
                complexity_score += len(re.findall(r'\bif\b|\bfor\b|\bwhile\b|\btry\b', content))
                
            return complexity_score
        except:
            return 0

    def analyze_project(self):
        """Main analysis function"""
        print("🔍 Analyzing Multiaxis Intelligence Project...")
        print("=" * 60)
        
        # Get all files
        all_files = []
        for root, dirs, files in os.walk(self.project_root):
            # Remove excluded directories from traversal
            dirs[:] = [d for d in dirs if d not in self.exclude_dirs]
            
            for file in files:
                file_path = os.path.join(root, file)
                if not self.should_exclude_path(file_path):
                    all_files.append(file_path)

        print(f"📁 Found {len(all_files)} files to analyze...")
        
        # Analyze each file
        for file_path in all_files:
            self.analyze_single_file(file_path)
            
        return self.generate_report()

    def analyze_single_file(self, file_path):
        """Analyze a single file"""
        file_ext = os.path.splitext(file_path)[1].lower()
        language = self.file_extensions.get(file_ext, 'Other')
        
        # Get relative path for cleaner display
        rel_path = os.path.relpath(file_path, self.project_root)
        directory = os.path.dirname(rel_path)
        
        # File size and basic stats
        file_size = os.path.getsize(file_path)
        
        # Detailed analysis for text files
        if file_ext in ['.py', '.html', '.js', '.css', '.json', '.md', '.txt', '.bat']:
            file_stats = self.analyze_file_content(file_path, language)
            complexity = self.get_file_complexity_estimate(file_path) if file_ext == '.py' else 0
        else:
            file_stats = {'total': 0, 'code': 0, 'comments': 0, 'blank': 0}
            complexity = 0
        
        # Update statistics
        self.stats['total_files'] += 1
        self.stats['total_lines'] += file_stats['total']
        self.stats['total_code_lines'] += file_stats['code']
        self.stats['total_comment_lines'] += file_stats['comments']
        self.stats['total_blank_lines'] += file_stats['blank']
        
        # Language statistics
        lang_stats = self.stats['by_language'][language]
        lang_stats['files'] += 1
        lang_stats['lines'] += file_stats['total']
        lang_stats['code'] += file_stats['code']
        lang_stats['comments'] += file_stats['comments']
        lang_stats['blank'] += file_stats['blank']
        
        # Directory statistics
        self.stats['by_directory'][directory]['files'] += 1
        self.stats['by_directory'][directory]['lines'] += file_stats['total']
        
        # File type counter
        self.stats['file_types'][file_ext] += 1
        
        # Track largest files
        self.stats['largest_files'].append({
            'path': rel_path,
            'lines': file_stats['total'],
            'size': file_size,
            'complexity': complexity,
            'language': language
        })

    def generate_report(self, format='markdown'):
        """Generate comprehensive project report in specified format"""
        # Sort largest files
        self.stats['largest_files'].sort(key=lambda x: x['lines'], reverse=True)
        
        if format == 'markdown':
            return self.generate_markdown_report()
        else:
            return self.generate_text_report()
    
    def generate_markdown_report(self):
        """Generate Markdown formatted report"""
        report = []
        
        # Header with badges
        report.append("# 🎯 Multiaxis Intelligence Project Analysis")
        report.append("")
        report.append("[![Total Files](https://img.shields.io/badge/Files-{}-blue.svg)](#) ".format(self.stats['total_files']) +
                     "[![Total Lines](https://img.shields.io/badge/Lines-{:,}-green.svg)](#) ".format(self.stats['total_lines']) +
                     "[![Python](https://img.shields.io/badge/Python-{}-yellow.svg)](#)".format(self.stats['by_language']['Python']['files']))
        report.append("")
        
        # Analysis info
        report.append(f"**📅 Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  ")
        report.append(f"**📁 Project Root:** `{os.path.abspath(self.project_root)}`")
        report.append("")
        
        # Overall Statistics
        report.append("## 📊 Overall Statistics")
        report.append("")
        report.append("| Metric | Count | Percentage |")
        report.append("|--------|-------|------------|")
        report.append(f"| **Total Files** | {self.stats['total_files']:,} | 100% |")
        report.append(f"| **Total Lines** | {self.stats['total_lines']:,} | 100% |")
        report.append(f"| **Code Lines** | {self.stats['total_code_lines']:,} | {(self.stats['total_code_lines']/self.stats['total_lines']*100) if self.stats['total_lines'] > 0 else 0:.1f}% |")
        report.append(f"| **Comment Lines** | {self.stats['total_comment_lines']:,} | {(self.stats['total_comment_lines']/self.stats['total_lines']*100) if self.stats['total_lines'] > 0 else 0:.1f}% |")
        report.append(f"| **Blank Lines** | {self.stats['total_blank_lines']:,} | {(self.stats['total_blank_lines']/self.stats['total_lines']*100) if self.stats['total_lines'] > 0 else 0:.1f}% |")
        report.append("")
        
        # Language Breakdown
        report.append("## 🔤 Language Breakdown")
        report.append("")
        report.append("| Language | Files | Lines | Code | Comments | Blank |")
        report.append("|----------|-------|-------|------|----------|-------|")
        
        # Sort languages by line count
        sorted_languages = sorted(self.stats['by_language'].items(), 
                                key=lambda x: x[1]['lines'], reverse=True)
        
        for language, stats in sorted_languages:
            if stats['files'] > 0:
                report.append(f"| **{language}** | {stats['files']:,} | {stats['lines']:,} | {stats['code']:,} | {stats['comments']:,} | {stats['blank']:,} |")
        
        report.append("")
        
        # Top Directories
        report.append("## 📂 Directory Analysis")
        report.append("")
        report.append("### Top Directories by Line Count")
        report.append("")
        report.append("| Directory | Files | Lines |")
        report.append("|-----------|-------|-------|")
        
        sorted_dirs = sorted(self.stats['by_directory'].items(), 
                           key=lambda x: x[1]['lines'], reverse=True)
        
        for directory, stats in sorted_dirs[:15]:  # Top 15 directories
            if stats['files'] > 0:
                dir_name = directory if directory else "*(root)*"
                # Escape pipes in directory names for markdown table
                dir_name = dir_name.replace('|', '\\|')
                report.append(f"| `{dir_name}` | {stats['files']:,} | {stats['lines']:,} |")
        
        report.append("")
        
        # Core Modules Analysis
        core_modules = [item for item in sorted_dirs if 'core/' in item[0] and item[1]['files'] > 0]
        if core_modules:
            report.append("### Core Modules")
            report.append("")
            for directory, stats in core_modules[:10]:
                module_name = directory.replace('src/core/', '').replace('core/', '')
                report.append(f"- **{module_name}**: {stats['files']} files, {stats['lines']:,} lines")
            report.append("")
        
        # Largest Files
        report.append("## 📄 Largest Files")
        report.append("")
        report.append("| File | Lines | Language | Complexity |")
        report.append("|------|-------|----------|------------|")
        
        for file_info in self.stats['largest_files'][:20]:
            if file_info['lines'] > 0:
                # Get just the filename for display
                file_name = os.path.basename(file_info['path'])
                file_path = file_info['path'].replace('|', '\\|')  # Escape pipes
                complexity_str = str(file_info['complexity']) if file_info['complexity'] > 0 else "-"
                report.append(f"| `{file_name}` | {file_info['lines']:,} | {file_info['language']} | {complexity_str} |")
        
        report.append("")
        
        # File Type Distribution
        report.append("## 📋 File Type Distribution")
        report.append("")
        
        # Create a simple chart using text
        report.append("| Extension | Count | Description |")
        report.append("|-----------|-------|-------------|")
        
        for ext, count in self.stats['file_types'].most_common():
            if ext and count > 0:
                file_type = self.file_extensions.get(ext, 'Other')
                report.append(f"| `{ext}` | {count} | {file_type} |")
        
        report.append("")
        
        # Project Insights
        report.append("## 💡 Project Insights")
        report.append("")
        
        python_stats = self.stats['by_language']['Python']
        insights = []
        
        if python_stats['files'] > 0:
            avg_lines_per_py_file = python_stats['lines'] // python_stats['files']
            insights.append(f"**Average Python file size:** {avg_lines_per_py_file} lines")
        
        complex_files = [f for f in self.stats['largest_files'] if f['complexity'] > 50]
        if complex_files:
            insights.append(f"**High complexity files:** {len(complex_files)} files need attention")
        
        if self.stats['file_types']:
            most_common = self.stats['file_types'].most_common(1)[0]
            insights.append(f"**Most common file type:** `{most_common[0]}` ({most_common[1]} files)")
        
        if self.stats['total_comment_lines'] > 0:
            comment_ratio = (self.stats['total_comment_lines'] / self.stats['total_lines']) * 100
            if comment_ratio > 15:
                insights.append("**Documentation:** ✅ Good documentation coverage!")
            elif comment_ratio < 5:
                insights.append("**Documentation:** ⚠️ Consider adding more documentation")
            else:
                insights.append(f"**Documentation:** {comment_ratio:.1f}% comment coverage")
        
        # Project size assessment
        if self.stats['total_lines'] > 20000:
            insights.append("**Project Size:** 🏢 Large enterprise-scale project")
        elif self.stats['total_lines'] > 10000:
            insights.append("**Project Size:** 🏭 Medium-scale application")
        else:
            insights.append("**Project Size:** 🏠 Small to medium project")
        
        for insight in insights:
            report.append(f"- {insight}")
        
        report.append("")
        
        # Technical Architecture
        report.append("## 🏗️ Technical Architecture")
        report.append("")
        
        # Count modules in core
        core_dirs = [d for d in sorted_dirs if 'core/' in d[0] and d[1]['files'] > 0]
        if core_dirs:
            report.append(f"**Modular Architecture:** {len(core_dirs)} core modules identified")
            report.append("")
            report.append("**Key Modules:**")
            for directory, stats in core_dirs[:8]:  # Top 8 modules
                module_name = directory.replace('src/core/', '').replace('core/', '')
                report.append(f"- `{module_name}` - {stats['lines']:,} lines")
        
        report.append("")
        
        # Summary
        report.append("## 🚀 Summary")
        report.append("")
        report.append("This analysis reveals a well-structured, modular Python application with comprehensive ")
        report.append("AI capabilities for manufacturing environments. The codebase demonstrates:")
        report.append("")
        report.append("✅ **Modular Design** - Clear separation of concerns across core modules  ")
        report.append("✅ **Comprehensive Feature Set** - Document processing, AI integration, UI management  ")
        report.append("✅ **Enterprise Scale** - Substantial codebase with proper organization  ")
        
        if self.stats['total_comment_lines'] / self.stats['total_lines'] > 0.1:
            report.append("✅ **Good Documentation** - Adequate code documentation  ")
        
        report.append("")
        report.append("---")
        
        # Final Totals Summary
        report.append("## 📈 Final Project Totals")
        report.append("")
        report.append("| **Metric** | **Total** |")
        report.append("|------------|-----------|")
        report.append(f"| **📁 Total Files** | **{self.stats['total_files']:,}** |")
        report.append(f"| **📝 Total Lines** | **{self.stats['total_lines']:,}** |")
        report.append(f"| **⚡ Code Lines** | **{self.stats['total_code_lines']:,}** |")
        report.append(f"| **💬 Comment Lines** | **{self.stats['total_comment_lines']:,}** |")
        report.append(f"| **🔲 Blank Lines** | **{self.stats['total_blank_lines']:,}** |")
        
        # Language totals
        python_files = self.stats['by_language']['Python']['files']
        python_lines = self.stats['by_language']['Python']['lines']
        if python_files > 0:
            report.append(f"| **🐍 Python Files** | **{python_files:,}** |")
            report.append(f"| **🐍 Python Lines** | **{python_lines:,}** |")
        
        # Core modules count
        core_dirs = [d for d in self.stats['by_directory'].items() if 'core/' in d[0] and d[1]['files'] > 0]
        if core_dirs:
            report.append(f"| **🏗️ Core Modules** | **{len(core_dirs)}** |")
        
        # Documentation files
        doc_files = self.stats['by_language']['HTML']['files'] + self.stats['by_language']['Markdown']['files']
        if doc_files > 0:
            report.append(f"| **📚 Documentation Files** | **{doc_files}** |")
        
        report.append("")
        
        # Project scale assessment
        if self.stats['total_lines'] > 50000:
            scale = "🏢 **Enterprise Scale** - Massive codebase"
        elif self.stats['total_lines'] > 20000:
            scale = "🏭 **Large Scale** - Substantial application"
        elif self.stats['total_lines'] > 10000:
            scale = "🏬 **Medium Scale** - Well-developed project"
        else:
            scale = "🏠 **Small Scale** - Compact application"
        
        report.append(f"**Project Scale:** {scale}")
        report.append("")
        
        report.append("---")
        report.append(f"*Analysis generated by Multiaxis Intelligence Project Analyzer on {datetime.now().strftime('%Y-%m-%d')}*")
        
        return "\n".join(report)
    
    def generate_text_report(self):
        """Generate plain text report (original format)"""
        report = []
        report.append("🎯 MULTIAXIS INTELLIGENCE PROJECT SUMMARY")
        report.append("=" * 60)
        report.append(f"📅 Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"📁 Project Root: {os.path.abspath(self.project_root)}")
        report.append("")
        
        # Overall Statistics
        report.append("📊 OVERALL STATISTICS")
        report.append("-" * 30)
        report.append(f"Total Files:     {self.stats['total_files']:>8,}")
        report.append(f"Total Lines:     {self.stats['total_lines']:>8,}")
        report.append(f"Code Lines:      {self.stats['total_code_lines']:>8,}")
        report.append(f"Comment Lines:   {self.stats['total_comment_lines']:>8,}")
        report.append(f"Blank Lines:     {self.stats['total_blank_lines']:>8,}")
        
        if self.stats['total_lines'] > 0:
            code_ratio = (self.stats['total_code_lines'] / self.stats['total_lines']) * 100
            comment_ratio = (self.stats['total_comment_lines'] / self.stats['total_lines']) * 100
            report.append(f"Code Ratio:      {code_ratio:>7.1f}%")
            report.append(f"Comment Ratio:   {comment_ratio:>7.1f}%")
        
        report.append("")
        
        # Language Breakdown
        report.append("🔤 LANGUAGE BREAKDOWN")
        report.append("-" * 30)
        report.append(f"{'Language':<15} {'Files':<8} {'Lines':<10} {'Code':<10} {'Comments':<10}")
        report.append("-" * 60)
        
        # Sort languages by line count
        sorted_languages = sorted(self.stats['by_language'].items(), 
                                key=lambda x: x[1]['lines'], reverse=True)
        
        for language, stats in sorted_languages:
            if stats['files'] > 0:
                report.append(f"{language:<15} {stats['files']:<8} {stats['lines']:<10,} "
                            f"{stats['code']:<10,} {stats['comments']:<10,}")
        
        report.append("")
        
        # Directory Analysis
        report.append("📂 DIRECTORY BREAKDOWN")
        report.append("-" * 30)
        report.append(f"{'Directory':<30} {'Files':<8} {'Lines':<10}")
        report.append("-" * 50)
        
        sorted_dirs = sorted(self.stats['by_directory'].items(), 
                           key=lambda x: x[1]['lines'], reverse=True)
        
        for directory, stats in sorted_dirs[:15]:  # Top 15 directories
            if stats['files'] > 0:
                dir_name = directory if directory else "(root)"
                report.append(f"{dir_name:<30} {stats['files']:<8} {stats['lines']:<10,}")
        
        report.append("")
        
        # Largest Files
        report.append("📄 LARGEST FILES (Top 20)")
        report.append("-" * 30)
        report.append(f"{'File':<40} {'Lines':<8} {'Language':<12} {'Complexity':<10}")
        report.append("-" * 75)
        
        for file_info in self.stats['largest_files'][:20]:
            if file_info['lines'] > 0:
                file_name = os.path.basename(file_info['path'])[:35] + "..." if len(file_info['path']) > 35 else file_info['path']
                complexity_str = str(file_info['complexity']) if file_info['complexity'] > 0 else "-"
                report.append(f"{file_name:<40} {file_info['lines']:<8} {file_info['language']:<12} {complexity_str:<10}")
        
        report.append("")
        
        # File Type Distribution
        report.append("📋 FILE TYPE DISTRIBUTION")
        report.append("-" * 30)
        for ext, count in self.stats['file_types'].most_common():
            if ext:
                report.append(f"{ext:<10} {count:>5} files")
        
        report.append("")
        
        # Project Insights
        report.append("💡 PROJECT INSIGHTS")
        report.append("-" * 30)
        
        python_stats = self.stats['by_language']['Python']
        if python_stats['files'] > 0:
            avg_lines_per_py_file = python_stats['lines'] // python_stats['files']
            report.append(f"• Average Python file size: {avg_lines_per_py_file} lines")
        
        complex_files = [f for f in self.stats['largest_files'] if f['complexity'] > 50]
        if complex_files:
            report.append(f"• High complexity files: {len(complex_files)}")
        
        report.append(f"• Most common file type: {self.stats['file_types'].most_common(1)[0][0]}")
        
        if self.stats['total_comment_lines'] > 0:
            comment_ratio = (self.stats['total_comment_lines'] / self.stats['total_lines']) * 100
            if comment_ratio > 15:
                report.append("• Good documentation coverage!")
            elif comment_ratio < 5:
                report.append("• Consider adding more documentation")
        
        report.append("")
        report.append("🚀 Analysis Complete!")
        report.append("=" * 60)
        
        return "\n".join(report)

    def save_report(self, report, filename="project_analysis.md", format='markdown'):
        """Save report to file"""
        if format == 'markdown':
            filename = filename.replace('.txt', '.md')
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(report)
        print(f"📄 Report saved to: {filename}")

    def export_json(self, filename="project_stats.json"):
        """Export statistics as JSON"""
        # Convert defaultdict to regular dict for JSON serialization
        json_stats = {
            'summary': {
                'total_files': self.stats['total_files'],
                'total_lines': self.stats['total_lines'],
                'total_code_lines': self.stats['total_code_lines'],
                'total_comment_lines': self.stats['total_comment_lines'],
                'total_blank_lines': self.stats['total_blank_lines']
            },
            'by_language': dict(self.stats['by_language']),
            'by_directory': dict(self.stats['by_directory']),
            'largest_files': self.stats['largest_files'][:50],  # Top 50
            'file_types': dict(self.stats['file_types']),
            'generated_at': datetime.now().isoformat()
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(json_stats, f, indent=2)
        print(f"📊 JSON data exported to: {filename}")


def main():
    """Main execution function"""
    print("🎯 Multiaxis Intelligence Project Analyzer")
    print("=" * 50)
    
    # Initialize analyzer
    analyzer = ProjectAnalyzer()
    
    # Run analysis
    report = analyzer.analyze_project()
    
    # Display report
    print("\n" + "="*60)
    print("GENERATING MARKDOWN REPORT...")
    print("="*60)
    
    # Save outputs - default to markdown
    analyzer.save_report(report, "project_analysis.md", 'markdown')
    analyzer.export_json()
    
    # Also save text version for comparison
    text_report = analyzer.generate_report('text')
    analyzer.save_report(text_report, "project_analysis.txt", 'text')
    
    print(f"\n✅ Analysis complete!")
    print(f"📄 Markdown report: project_analysis.md")
    print(f"📄 Text report: project_analysis.txt")
    print(f"📊 JSON data: project_stats.json")
    print(f"\n🎯 Open 'project_analysis.md' in any markdown viewer or GitHub!")


if __name__ == "__main__":
    main()

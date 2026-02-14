import click
from pathlib import Path
from datetime import datetime

@click.command()
@click.option('--limit', '-n', default=10, help='Number of reports to show')
@click.option('--format', '-f', 'fmt', type=click.Choice(['md', 'html', 'pdf', 'all']), default='all')
def history(limit, fmt):
    """📚 List historical reports"""
    project_root = Path(__file__).parent.parent.parent
    reports_dir = project_root / 'reports'
    
    if not reports_dir.exists():
        click.echo("No reports directory found.")
        return
    
    click.echo("📚 Report History")
    click.echo("-" * 60)
    
    patterns = {
        'md': '*.md',
        'html': '*.html', 
        'pdf': '*.pdf',
        'all': '*.*'
    }
    
    pattern = patterns.get(fmt, '*.*')
    # Search recursively in subdirectories
    files = sorted(reports_dir.rglob(pattern), key=lambda f: f.stat().st_mtime, reverse=True)
    
    # 排除 latest 软链 and directories
    files = [f for f in files if f.is_file() and not f.is_symlink() and not f.name.startswith('latest')]
    
    if not files:
        click.echo("No reports found.")
        return
    
    for f in files[:limit]:
        stat = f.stat()
        size_kb = stat.st_size / 1024
        mtime = datetime.fromtimestamp(stat.st_mtime).strftime('%m-%d %H:%M')
        suffix = f.suffix.upper().replace('.', '')
        click.echo(f"  {mtime}  [{suffix:4s}]  {f.name}  ({size_kb:.0f}KB)")
    
    total = len(files)
    if total > limit:
        click.echo(f"\n  ... and {total - limit} more")
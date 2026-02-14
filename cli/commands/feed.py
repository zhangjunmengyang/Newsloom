import click
from pathlib import Path

@click.command()
@click.option('--output', '-o', default='reports/feed.xml', help='Output path')
def feed(output):
    """📡 Generate RSS feed"""
    import sys
    import importlib.util
    project_root = Path(__file__).parent.parent.parent
    
    # 直接导入 rss_generator 模块，避免 __init__.py 依赖问题
    spec = importlib.util.spec_from_file_location(
        "rss_generator", 
        project_root / "src" / "processors" / "rss_generator.py"
    )
    rss_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(rss_module)
    RSSGenerator = rss_module.RSSGenerator
    
    gen = RSSGenerator()
    
    click.echo("📡 Generating RSS feed from reports...")
    xml = gen.generate_from_reports(reports_dir=str(project_root / "reports"))
    gen.save_feed(xml, output)
    click.echo(f"✅ RSS feed saved: {output}")
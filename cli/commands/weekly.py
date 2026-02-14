import click
from pathlib import Path

@click.command()
@click.option('--date', '-d', default=None, help='End date (YYYY-MM-DD), default today')
def weekly(date):
    """📅 Generate weekly report"""
    import sys
    import importlib.util
    project_root = Path(__file__).parent.parent.parent
    
    # 直接导入 aggregator 模块，避免 __init__.py 依赖问题
    spec = importlib.util.spec_from_file_location(
        "aggregator", 
        project_root / "src" / "processors" / "aggregator.py"
    )
    aggregator_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(aggregator_module)
    ReportAggregator = aggregator_module.ReportAggregator
    
    agg = ReportAggregator(
        data_dir=str(project_root / "data"),
        reports_dir=str(project_root / "reports")
    )
    
    click.echo("📅 Generating weekly report...")
    content = agg.generate_weekly(end_date=date)
    
    from datetime import datetime
    d = date or datetime.now().strftime("%Y-%m-%d")
    filename = f"weekly_{d}.md"
    agg.save_report(content, filename)
    click.echo(f"✅ Weekly report saved: reports/{filename}")
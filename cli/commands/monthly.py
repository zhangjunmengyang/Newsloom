import click
from pathlib import Path

@click.command()
@click.option('--year', '-y', type=int, default=None, help='Year (default: current year)')
@click.option('--month', '-m', type=int, default=None, help='Month 1-12 (default: current month)')
def monthly(year, month):
    """📊 Generate monthly report"""
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
    
    click.echo(f"📊 Generating monthly report for {year or 'current year'}/{month or 'current month'}...")
    content = agg.generate_monthly(year=year, month=month)
    
    from datetime import datetime
    now = datetime.now()
    y = year or now.year
    m = month or now.month
    filename = f"monthly_{y}_{m:02d}.md"
    agg.save_report(content, filename)
    click.echo(f"✅ Monthly report saved: reports/{filename}")
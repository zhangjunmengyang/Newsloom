import click
import json
from pathlib import Path
from datetime import datetime

@click.command()
def status():
    """📊 Show system status"""
    project_root = Path(__file__).parent.parent.parent
    
    click.echo("🗞️ Newsloom Status")
    click.echo("=" * 40)
    
    # 检查最新报告
    reports_dir = project_root / 'reports'
    if reports_dir.exists():
        md_files = sorted(reports_dir.glob('*.md'), reverse=True)
        if md_files:
            latest = md_files[0]
            stat = latest.stat()
            size_kb = stat.st_size / 1024
            mtime = datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M')
            click.echo(f"\n📄 Latest report: {latest.name}")
            click.echo(f"   Generated: {mtime}")
            click.echo(f"   Size: {size_kb:.1f} KB")
        else:
            click.echo("\n📄 No reports found")
    
    # 检查数据源配置
    sources_file = project_root / 'config' / 'sources.yaml'
    config_file = project_root / 'config' / 'config.yaml'
    
    sources = []
    if sources_file.exists():
        import yaml
        with open(sources_file, 'r') as f:
            sources_config = yaml.safe_load(f)
        sources_dict = sources_config.get('sources', {})
        sources = list(sources_dict.values())
    elif config_file.exists():
        import yaml
        with open(config_file, 'r') as f:
            config = yaml.safe_load(f)
        sources = config.get('sources', [])
    
    if sources:
        enabled = [s for s in sources if s.get('enabled', True)]
        click.echo(f"\n📡 Data sources: {len(enabled)}/{len(sources)} enabled")
    
    # 检查趋势历史
    trend_dir = project_root / 'data' / 'trend_history'
    if trend_dir.exists():
        history_files = list(trend_dir.glob('*.json'))
        click.echo(f"\n📊 Trend history: {len(history_files)} days tracked")
    
    # 检查 server
    click.echo(f"\n🖥️  Server: check with `news serve`")
    
    click.echo("\n" + "=" * 40)
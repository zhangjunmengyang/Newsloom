import click
from pathlib import Path

@click.command()
@click.option('--verbose', '-v', is_flag=True, help='Show detailed info')
def sources(verbose):
    """📡 List data sources"""
    project_root = Path(__file__).parent.parent.parent
    
    # Check for sources.yaml first, then config.yaml
    sources_file = project_root / 'config' / 'sources.yaml'
    config_file = project_root / 'config' / 'config.yaml'
    
    sources_list = []
    
    # Try sources.yaml first (dedicated sources file)
    if sources_file.exists():
        import yaml
        with open(sources_file, 'r') as f:
            sources_config = yaml.safe_load(f)
        sources_dict = sources_config.get('sources', {})
        # Convert dict to list format
        for key, source in sources_dict.items():
            source['name'] = source.get('name', key)
            source['id'] = key
            sources_list.append(source)
    # Fallback to config.yaml
    elif config_file.exists():
        import yaml
        with open(config_file, 'r') as f:
            config = yaml.safe_load(f)
        sources_list = config.get('sources', [])
    else:
        click.echo("❌ No config files found: config/sources.yaml or config/config.yaml")
        return
    
    click.echo("📡 Data Sources")
    click.echo("-" * 50)
    
    for s in sources_list:
        enabled = s.get('enabled', True)
        status_icon = "✅" if enabled else "❌"
        name = s.get('name', 'unnamed')
        source_type = s.get('type', 'unknown')
        
        click.echo(f"  {status_icon} {name} ({source_type})")
        
        if verbose:
            if 'url' in s:
                click.echo(f"      URL: {s['url']}")
            if 'feeds' in s:
                click.echo(f"      Feeds: {len(s['feeds'])}")
            click.echo()
    
    enabled_count = sum(1 for s in sources_list if s.get('enabled', True))
    click.echo(f"\nTotal: {enabled_count}/{len(sources_list)} enabled")
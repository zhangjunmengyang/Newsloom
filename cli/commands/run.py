import click
import subprocess
import sys
from pathlib import Path

@click.command()
@click.option('--config', '-c', default='config/config.yaml', help='Config file path')
@click.option('--dry-run', is_flag=True, help='Dry run without AI analysis')
@click.option('--skip-fetch', is_flag=True, help='Skip fetching, use cached data')
def run(config, dry_run, skip_fetch):
    """🚀 Run the news pipeline"""
    project_root = Path(__file__).parent.parent.parent
    script = project_root / 'run_v2.py'
    
    if not script.exists():
        # fallback to run.py
        script = project_root / 'run.py'
    
    cmd = [sys.executable, str(script)]
    if dry_run:
        cmd.append('--dry-run')
    
    click.echo("🗞️ Starting Newsloom pipeline...")
    click.echo(f"   Config: {config}")
    
    try:
        result = subprocess.run(cmd, cwd=str(project_root))
        if result.returncode == 0:
            click.echo("\n✅ Pipeline completed successfully!")
        else:
            click.echo(f"\n❌ Pipeline failed with exit code {result.returncode}")
    except KeyboardInterrupt:
        click.echo("\n⚠️ Pipeline interrupted")
import click
import subprocess
import sys
from pathlib import Path

@click.command()
@click.option('--port', '-p', default=8000, help='API server port')
@click.option('--frontend', '-f', is_flag=True, help='Also start frontend dev server')
def serve(port, frontend):
    """🖥️ Start the Dashboard server"""
    project_root = Path(__file__).parent.parent.parent
    
    click.echo(f"🗞️ Starting Newsloom server on port {port}...")
    
    server_main = project_root / 'server' / 'main.py'
    if not server_main.exists():
        click.echo("❌ Server not found. Run from project root.")
        return
    
    try:
        if frontend:
            click.echo("   Starting frontend dev server too...")
            # Start frontend in background
            web_dir = project_root / 'web'
            if web_dir.exists():
                subprocess.Popen(
                    ['npm', 'run', 'dev'],
                    cwd=str(web_dir),
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
                click.echo("   Frontend: http://localhost:3000")
        
        click.echo(f"   API: http://localhost:{port}")
        click.echo(f"   Docs: http://localhost:{port}/docs")
        
        subprocess.run(
            [sys.executable, '-m', 'uvicorn', 'server.main:app',
             '--host', '0.0.0.0', '--port', str(port), '--reload'],
            cwd=str(project_root)
        )
    except KeyboardInterrupt:
        click.echo("\n👋 Server stopped")
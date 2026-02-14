"""Newsloom CLI — news 命令行工具"""
import click

@click.group()
@click.version_option(version="0.2.0", prog_name="newsloom")
def cli():
    """🗞️ Newsloom — AI-Powered Daily Intelligence"""
    pass

# 注册子命令
from cli.commands.run import run
from cli.commands.status import status
from cli.commands.serve import serve
from cli.commands.history import history
from cli.commands.sources import sources

cli.add_command(run)
cli.add_command(status)
cli.add_command(serve)
cli.add_command(history)
cli.add_command(sources)

if __name__ == '__main__':
    cli()
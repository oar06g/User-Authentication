import click
from src import run

@click.group()
def cli():
    pass

@cli.command()
def migrate():
    import scripts.migrate
    scripts.migrate.migrate()

@cli.command()
def runserver():
    run()

@cli.command()
def wrapping():
    ...

# Entry point
if __name__ == "__main__":
    cli()
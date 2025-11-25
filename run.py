import click
from src import run

@click.group()
def cli():
    pass

@cli.command()
def runserver(): run()

@cli.command()
@click.option(
    "--fullsetup",
    is_flag=True,
    default=False,
    help="If full setup use true or update database."
)
def setup(fullsetup): 
    import scripts.migrate
    if fullsetup:
        scripts.migrate.setup(True)
    else:
        scripts.migrate.setup()


if __name__ == "__main__":
    cli()
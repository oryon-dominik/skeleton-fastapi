#!/usr/bin/env python3
# coding: utf-8

"""Typer cli interface to manage the dev-environment"""

import subprocess
import webbrowser
from pathlib import Path
import json

from sqlmodel import Session
import typer
import uvicorn

from rich import inspect
from rich.console import Console
from rich.markdown import Markdown

from pydantic.error_wrappers import ValidationError

from application.config import settings as app_settings
from application.apps.authentication import crud
from application.apps.authentication.models import UserCreate
from application.database.dependencies import get_session
from application.database.sqlmodel import manually_create_all_tables
from application.apps.authentication.exceptions import bypass_email_validation_error


#----------CONFIG--------------------------------------------------------------
cli = typer.Typer()
DEBUG = True
CWD = '.'


# ---------HELPERS-------------------------------------------------------------
def echo(
    message: str,
    fg_color: str = typer.colors.WHITE,
    bg_color: str = typer.colors.BLACK,
    bold: bool = False
    ):
    """colors:
        "bright_" + black, red, green, yellow, blue, magenta, cyan, white
    """
    typer.echo(
        typer.style(
            message,
            fg=fg_color,
            bg=bg_color,
            bold=bold,
        )
    )

def delete_folder(path: Path):
    for element in path.iterdir():
        if element.is_dir():
            delete_folder(element)
        else:
            element.unlink()
    path.rmdir()

def clean_build():
    echo(f"Unlinking build-files: build/; dist/ *.egg-info; __pycache__;", fg_color=typer.colors.RED)
    cwd = Path(CWD)
    [delete_folder(p) for p in cwd.rglob('build')]
    [delete_folder(p) for p in cwd.rglob('*.egg-info')]
    [delete_folder(p) for p in cwd.rglob('__pycache__')]
    try:
        [delete_folder(p) for p in cwd.rglob('dist')]
    except OSError as err:
        echo(f"Error deleting dist-folder: {err}", fg_color=typer.colors.RED)

def clean_pyc():
    echo(f"Unlinking caches: *.pyc; *pyo; *~;", fg_color=typer.colors.RED)
    [p.unlink() for p in Path(CWD).rglob('*.py[co]')]
    [p.unlink() for p in Path(CWD).rglob('*~')]

def run_command(command, debug=False, cwd=CWD, env=None, shell=False):
    if debug:
        echo(f">>> Running command: {command}")
    try:
        subprocess.run(command.split(), cwd=cwd, env=env, shell=shell)
    except FileNotFoundError:
        echo(f'The command {command} threw a FileNotFoundError', fg_color=typer.colors.RED)


#----------GENERAL COMMANDS----------------------------------------------------
@cli.command()
def clean():
    """Cleaning pycache, buildfiles"""
    clean_build()
    clean_pyc()

@cli.command()
def black(path: str = typer.Argument(None)):
    """black <path>"""
    command = "black"
    if path is not None:
        command = f"{command} {path}"
    run_command(command, debug=DEBUG)

@cli.command()
def pytest(test_path: str = typer.Argument(None)):
    """pytest <path>"""
    command = "pytest"
    if test_path is not None:
        command = f"{command} {test_path}"
    run_command(command, debug=DEBUG)

@cli.command()
def run_coverage(skip: bool = False):
    """test coverage"""
    commands = [
        "coverage run --source=./application --module pytest",
        "coverage report -mi",
        "coverage html"
    ]
    # TODO: fixme, this is broken commands[0] += " --skip-empty" if skip else ""
    for command in commands:
        run_command(command, debug=DEBUG)
    coverage_index_file_url = f'file://{Path("./htmlcov/index.html").resolve()}'
    webbrowser.open_new_tab(coverage_index_file_url)

@cli.command()
def coverage(skip: bool = False):
    """= run-coverage"""
    run_coverage(skip=skip)

@cli.command()
def test(test_path: str = typer.Argument(None), coverage: bool = False, skip: bool = False):
    """test --coverage"""
    if coverage:
        run_coverage(skip=skip)
    else:
        pytest(test_path)

@cli.command()
def rebuild():
    """= clean + initialize"""
    clean()
    initialize()

@cli.command()
def initialize():
    """Initialize the skeleton-application FAST-API server..."""
    echo(f'{initialize.__doc__}...', fg_color=typer.colors.GREEN)

    # ... TODO: reset database, makemigrations, migrate

    echo(f'Successfully initialized the project...', fg_color=typer.colors.GREEN)


# ---------- ABBREVIATIONS ----------------------------------------------------
@cli.command()
def rb():
    "= rebuild"
    rebuild()

@cli.command()
def init():
    "= initialize"
    initialize()

@cli.command()
def mm(message: str):
    """= makemigrations"""
    makemigrations(message)

@cli.command()
def mig(revision: str = "head"):
    """= migrate"""
    migrate(revision)

@cli.command()
def mmm(message: str = "", revision: str = "head"):
    """= makemigrations + migrate"""
    makemigrations(message)
    migrate(revision)

@cli.command()
def up(port: int = 8000, host: str = "127.0.0.1", log_level: str = "info", reload: bool = True, docs: bool = False):
    """= run (start the devserver)"""
    run (port=port, host=host, log_level=log_level, reload=reload, docs=docs)

@cli.command()
def serve(port: int = 8000, host: str = "127.0.0.1", log_level: str = "info", reload: bool = True, docs: bool = False):
    """= run (start the devserver)"""
    run (port=port, host=host, log_level=log_level, reload=reload, docs=docs)


# ---------- INTROSPECTION ----------------------------------------------------
@cli.command()
def readme():
    """README"""
    console = Console()
    with open("README.md") as readme:
        markdown = Markdown(readme.read())
    console.print(markdown)

@cli.command()
def settings():
    """debugging output"""
    inspect(app_settings)


# ---------- DOCUMENTATION mkdocs ---------------------------------------------
@cli.command()
def docs(
    serve: bool = True,
    build: bool = False,
    clean: bool = False,
    openapi: bool = False,
    doc_path: Path = Path(CWD) / 'docs',
    site_path: Path = Path(CWD) / 'site',
):
    """
    default: mkdocs serve
    --build: clean, openapi and `mkdocs build`
    --clean: delete the site-folder
    --openapi: generate a fresh openapi.json
    """
    if openapi:
        docs_openapi(doc_path=doc_path)
    elif build:
        docs_build(site_path=site_path)
    elif clean:
        docs_clean(site_path=site_path)
    elif serve:
        docs_serve()

@cli.command()
def docs_build(site_path: Path = Path(CWD) / 'site'):
    """
    build mkdocs

    cleans old docs in doc_path
    gets a new openapi-spec
    builds new docs to ./site
    """
    docs_clean(site_path=site_path)
    docs_openapi()
    run_command("mkdocs build", debug=DEBUG)

@cli.command()
def docs_openapi(doc_path: Path = Path(CWD) / 'docs'):
    """load new openapi.json into mkdocs"""
    from application.main import app
    open_api_schema = app.openapi()
    with open(doc_path / "openapi.json", "w") as file:
        json.dump(open_api_schema, file, indent=4)
    echo(f"Updated {doc_path / 'openapi.json'}.")

@cli.command()
def docs_serve():
    """serve mkdocs"""
    run_command("mkdocs serve", debug=DEBUG)

@cli.command()
def docs_clean(site_path: Path = Path(CWD) / 'site'):
    """Delete the site_path directory recursively."""
    def rm_tree(path: Path):
        """Recursively delete the directory tree."""
        for child in path.iterdir():
            if child.is_file():
                child.unlink(missing_ok=True)
            elif child.is_dir():
                rm_tree(child)
        path.rmdir()
    if site_path.exists():
        rm_tree(site_path)
    echo(f"Deletes .site/")


# ---------- MANAGE THE DATABASE ----------------------------------------------
@cli.command()
def makemigrations(message: str = ""):
    """
    Makemigrations via alembic

    """
    command = "alembic revision"
    if message:
        m = message.replace(" ", "")
        command += f" --message '{m}'"
    command += " --autogenerate"
    run_command(command, debug=DEBUG)

@cli.command()
def migrate(revision: str = "head"):
    """
    Migrate via alembic.

    Calls upgrade() in every revision (migrations/versions). Order by down_revision (1st=None to the latest 'head'.)

    You can manually run any revision with:
        alembic upgrade <revision> (abbreviations work as well)

    You can manually jump up and down revisions with:
        alembic upgrade +2
        alembic downgrade -1
        alembic upgrade 345s+2
    """
    command = f"alembic upgrade {revision}"
    run_command(command, debug=DEBUG)

@cli.command()
def db_version(history: bool = False, verbose: bool = False):
    """
    Prints the current database migration or history.
    Optional: verbose.
    """
    command = "alembic current"
    if history:
        command = "alembic history"
    if verbose:
        command += " --verbose"
    run_command(command, debug=DEBUG)

@cli.command()
def db_reset():
    """
    Resets the database to the initial state.
    Back to base and forth to head again.
    """
    command = "alembic downgrade base"
    run_command(command, debug=DEBUG)
    command = "alembic upgrade head"
    run_command(command, debug=DEBUG)

@cli.command()
def remove_database():
    """remove the database"""
    run_command('rm ./application/database/production.db', debug=DEBUG)


# ---------- MANAGE THE USERS -------------------------------------------------
@cli.command()
def create_user(
    email: str = "",
    password: str = "",
    name: str = "",
    superuser: bool = False,
    disabled: bool = False,
    scopes: str = "unauthorized"
):
    """
    Example:
    cc create-user --email=foo@bar.baz --password=bar --name="Foo Bar Baz" --superuser --scopes="users/whoami"
    """
    if not email or not password or not name:
        echo("Please provide atleast --email --password and --name.", fg_color=typer.colors.RED)
        echo(f"{create_user.__doc__}", fg_color=typer.colors.WHITE)
        return

    session: Session = next(get_session())
    new_user = UserCreate(
        email=email,
        password=password,
        superuser=superuser,
        name=name,
        disabled=disabled,
        scopes=scopes,
    )
    try:
        db_user = crud.create_user(session=session, user=new_user)
    except ValidationError as e:
        bypass_email_validation_error(e)
        echo(f"The email {email} already exists.", fg_color=typer.colors.RED)
        return
    inspect(db_user)
    echo(f"Created user: {db_user.email}")
    return db_user

# ---------- MANAGE THE SERVER -------------------------------------------------
@cli.command()
def run(
    port: int = 8000,
    host: str = "127.0.0.1",
    log_level: str = "info",
    reload: bool = True,
    docs: bool = False,
):  # pragma: no cover
    """
    Run the API server.
    if --docs: run the mkdocs server instead.

    on docker run uvicorn over gunicorn (on windows fcntl is not available, -> ModuleNotFoundError: No module named 'fcntl')
    https://www.uvicorn.org/#running-with-gunicorn
    gunicorn application.main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker
    """
    if docs:
        docs_serve()
        return

    uvicorn.run(
        "application.main:app",
        host=host,
        port=port,
        log_level=log_level,
        reload=reload,
    )


if __name__ == "__main__":
    cli()

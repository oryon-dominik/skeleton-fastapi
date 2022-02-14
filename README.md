# Fast-API skeleton

> Use this skeleton as a base for quick fast-api server application development.

A little skeleton for a quick Fast-API setup including authentication (JWT via [python-jose](https://python-jose.readthedocs.io/en/latest/)), docs (with [mkdocs](https://www.mkdocs.org/)) and a database including a migrations system (using [alembic](https://alembic.sqlalchemy.org/en/latest/)).  

This project is heavily inspired by Sebastian Ramirez ([tiangolo](https://github.com/tiangolo)).  
Using [Fast-API](https://fastapi.tiangolo.com/) (including [pydantic](https://pydantic-docs.helpmanual.io/)) and [SQLModel](https://sqlmodel.tiangolo.com/). As well as a [typer](https://typer.tiangolo.com/) CLI for the project managment commands.  

## Dependencies

Dependencies are managed via [poetry](https://python-poetry.org/) and a `pyproject.toml`.  


## Management Commands

I'm aliasing `python commands.py` -> `cc` to *call* management *commands* in all my projects.  
It's a CLI interface using the python library `typer`. All available commands are defined in `commands.py`  
(Trivia: I'm never aliasing `gcc` or any other c-compilers to `cc`, so: no conflicts here).  

`cc up`: Start the application.  
`cc readme`: Show this readme in your terminal.  
`cc docs`: Serve, build, or delete your mkdocs.  

There are also some abbreviations available.
`cc mmm`: _makemigrations_ & _migrate_.

Look up all other control-commands for the project via `cc --help` or glimpse into the `commands.py` yourself.  

Example implementation of the `cc <command>` alias in a `powershell` script:  

```powershell
function cc () {
    $commands = ".\commands.py"
    $cwd = (Get-Location)
    $parent = Split-Path -Path $cwd
    if (Test-Path $commands -PathType leaf) {
        python commands.py $args
    }
    elseif (Test-Path (Join-Path -Path $parent -ChildPath $commands) -PathType leaf) {
        Set-Location $parent
        python commands.py $args
        Set-Location $cwd
    }
    else {
        Write-Host "commands.py not found" 
    }
}
```


## Setup

Install dependencies.

    poetry install

Activate your newly created env. (however, you know how to do this on your python)  
Create a fresh db (you have to redo this for dev-mode too!).

    alembic upgrade head

Migrate the database.

    cc mmm

Run the server.

    cc up

Lookup [Database migrations with alembic](#database-migrations-with-alembic) for more details.

To enter develop-mode set an environment-variable.

    # powershell
    $Env:DEBUG_FASTAPI_SKELETON = $true


## Models from swagger

Pydantic imports generated models from any `swagger.json`: Use the [datamodel-code-generator](https://koxudaxi.github.io/datamodel-code-generator/).

    poetry add datamodel-code-generator
    datamodel-codegen --input swagger.json --input-file-type openapi --output model.py --target-python-version 3.10


## Documentation

This project uses [mkdocs.org](https://www.mkdocs.org) with [material theme](https://squidfunk.github.io/mkdocs-material/) for documentation.

* `poetry add mkdocs mkdocs-material mkdocs-render-swagger-plugin` - Add mkdocs to an existing `pyproject`.
* `mkdocs new .` - Create a new project.
* `mkdocs serve` - Start the live-reloading docs server.
* `mkdocs build` - Build the documentation site.

To add an updated `openapi.json` to the docs run `cc docs --openapi`.  

Layout:

    mkdocs.yml        # The configuration file.
    docs/
        index.md      # The documentation homepage.
        openapi.json  # Downloaded from the FastAPI devserver. Use the plugin with `!!swagger openapi.json!!`
        ...           # Other markdown pages, images and other files.


## Database migrations with alembic

To easily auto-register a model that should have its changes tracked by alembics revision system (`YourModel(SQLModel, table=True)`), 
all models inside any app in `apps` are automatically imported into `application.database.revisions`.  

Setup following the [tutorial](https://alembic.sqlalchemy.org/en/latest/tutorial.html):  

`env.py` - This is a Python script that is run whenever the alembic migration
tool is invoked. At the very least, it contains instructions to configure and
generate a SQLAlchemy engine, procure a connection from that engine along with
a transaction, and then invoke the migration engine, using the connection as a
source of database connectivity.  

So, to start our revision system:  

Create the `migrations` folder and the `alembic.ini`.

    alembic init migrations

Remove this line from `alembic.ini`, we'll monkey path the database_url in `env.py`.

    sqlalchemy.url = driver://user:pass@localhost/dbname

In `migrations/script.py.mako` we need to add the import of sqlmodel to be available in all revisions.

    # ...
    from alembic import op
    import sqlalchemy as sa
    import sqlmodel
    # ...

Edit `migrations/env.py` to patch the `DATABASE_URL` and use the `METADATA`.

    from application.config import settings
    config.set_main_option('sqlalchemy.url', str(settings.DATABASE_URL))

    # this metadata has to include all your table information to be able to autogenerate revisions.
    from application.database.alchemy import METADATA
    target_metadata = METADATA

And add the "no empty migrations" part (also to `migrations/env.py`).

    # ...
    def run_migrations_online():
    # ...

    def process_revision_directives(context, revision, directives):
        if config.cmd_opts.autogenerate:
            script = directives[0]
            if script.upgrade_ops.is_empty():
                from rich.console import Console
                console = Console()
                console.print("Skipped creating a new revision. No changes found.", style="red")
                directives[:] = []

    # ...

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            process_revision_directives=process_revision_directives
        )

    # ...

Make a custom migration.

    alembic revision -m "create user table"
    # or:
    cc mm "message"

Edit the migration for your needs.  
Customize and populate the upgrade and downgrade functions with some database actions.

    revision = '11234ea83b712'
    down_revision = None  # if None, this is the first migration inline otherwise points to the exact previous revision hash.

    # ...

    def upgrade():
        # create or modify a sqlmodel table here

    def downgrade():
        # destroy the table here, to assure correct teardown in both directions

Migrate (also see the migrate docstring in `commands.py`)

    alembic upgrade <revision_no>
    # directly upgrade to the latest revision:
    alembic upgrade head

Watch the history of all migrations or the current revision state.

    alembic current
    alembic history --verbose

    # alternatives with our typer interface:
    cc db-version
    cc db-version --history

See: https://www.encode.io/databases/tests_and_migrations/  
or: https://alembic.sqlalchemy.org/en/latest/tutorial.html  
and: https://alembic.sqlalchemy.org/en/latest/cookbook.html#don-t-generate-empty-migrations-with-autogenerate  


## other skeletons

[django minimal sqlite](https://github.com/oryon-dominik/skeleton-django-sqlite-minimal)  
[django with postgres & docker](https://github.com/oryon-dominik/skeleton-django-postgres-docker)  
[fastAPI](https://github.com/oryon-dominik/skeleton-fastapi) (this repo)  

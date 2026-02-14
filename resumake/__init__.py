"""resumake — Build styled CV documents from a single YAML source."""

import typer

app = typer.Typer(
    name="resumake",
    help="Build styled CV documents from a single YAML source.",
    invoke_without_command=True,
    no_args_is_help=False,
)


@app.callback(invoke_without_command=True)
def default(ctx: typer.Context):
    """Default: run the build command if no subcommand is given."""
    if ctx.invoked_subcommand is None:
        from .build import build
        build()


# Register commands
from .build import build
app.command()(build)

from .tailor import tailor
app.command()(tailor)

from .bio import bio
app.command()(bio)

from .validate_cmd import validate
app.command()(validate)

from .init_cmd import init
app.command()(init)

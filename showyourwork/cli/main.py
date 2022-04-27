from . import commands
from .. import git, exceptions, __version__
import os
import shutil
import click


BANNER = r"""
         _                                                             _    _ 
     ___| |__   _____      ___   _  ___  _   _ _ ____      _____  _ __| | _| |
    / __| '_ \ / _ \ \ /\ / / | | |/ _ \| | | | '__\ \ /\ / / _ \| '__| |/ / |
    \__ \ | | | (_) \ V  V /| |_| | (_) | |_| | |   \ V  V / (_) | |  |   <|_|
    |___/_| |_|\___/ \_/\_/  \__, |\___/ \__,_|_|    \_/\_/ \___/|_|  |_|\_(_)
                             |___/                                            
"""


def show_banner():
    try:
        terminal_size = shutil.get_terminal_size().columns
    except:
        terminal_size = 0
    if terminal_size > 77:
        click.echo(
            click.style(
                BANNER,
                fg="red",
                bold=True,
            )
        )


def ensure_top_level():
    # Ensure we're running the command in the top level of a git repo
    root = os.path.realpath(git.get_repo_root())
    here = os.path.realpath(".")
    if 0:  # not root == here:
        raise exceptions.ShowyourworkException(
            "The `showyourwork` command must be called "
            "from the top level of a git repo."
        )


@click.group(invoke_without_command=True)
@click.option(
    "--version", is_flag=True, help="Show the program version and exit."
)
@click.pass_context
def entry_point(context, version):
    """Easily build open-source, reproducible scientific articles."""
    # Parse
    if version:
        print(__version__)
    elif context.invoked_subcommand is None:
        # Default command is `build`
        context.invoke(build)


@entry_point.command(
    context_settings=dict(
        ignore_unknown_options=True,
    )
)
@click.argument("snakemake_args", nargs=-1, type=click.UNPROCESSED)
def build(snakemake_args):
    """Build an article in the current working directory."""
    ensure_top_level()
    commands.preprocess(snakemake_args)
    commands.build(snakemake_args)


def validate_slug(context, param, slug):
    def pause():
        if context.params.get("yes"):
            pass
        else:
            click.echo(
                "Press any key to continue, or Ctrl+C to abort...", nl=False
            )
            click.getchar()
            click.echo()

    if "/" in slug and len(slug.split("/")) == 2:

        # Introductory message
        user, repo = slug.split("/")
        click.echo(
            "Let's get you set up with a new repository. "
            "I'm going to create a folder called\n\n"
            + click.style(f"    {repo} ", fg="blue")
            + "\n\nin the current working directory. "
            "If you haven't done this yet, please visit\n\n"
            + click.style("    https://github.com/new ", fg="blue")
            + "\n\nat this time and create an empty repository called\n\n"
            + click.style(f"    {slug}\n", fg="blue")
        )
        pause()

        # Check Zenodo credentials
        if os.getenv("ZENODO_TOKEN"):
            click.echo(
                "\nI found a "
                + click.style("ZENODO_TOKEN", fg="blue")
                + " environment variable, so I'm going to create a Zenodo\n"
                + "deposit draft where intermediate results will be cached. "
                + "In order for this to\n"
                + "work on GitHub Actions, please go to\n\n"
                + click.style(
                    f"    https://github.com/{slug}/settings/secrets/actions/new\n\n",
                    fg="blue",
                )
                + "at this time and create a "
                + click.style("ZENODO_TOKEN", fg="blue")
                + " secret with your Zenodo access token.\n"
            )
        else:
            click.echo(
                "\nI didn't find a "
                + click.style("ZENODO_TOKEN", fg="blue")
                + " environment variable, so I'm not going to set up\n"
                + "a Zenodo deposit for caching intermediate results. If you "
                + "would like to enable\nthis, please go to\n\n"
                + click.style(
                    f"    https://zenodo.org/account/settings/applications/tokens/new\n\n",
                    fg="blue",
                )
                + "to create a new personal access token with "
                + click.style("deposit:actions", fg="blue")
                + " and "
                + click.style("deposit:write\n", fg="blue")
                + "scopes, store it in a local "
                + click.style("ZENODO_TOKEN", fg="blue")
                + " environment "
                + "variable, and re-run this\nsetup script.\n"
            )
        pause()

        # Check Overleaf credentials
        if not context.params.get("overleaf"):
            click.echo(
                "\nYou didn't provide an Overleaf project id "
                + "(via the "
                + click.style("--overleaf", fg="blue")
                + " command-line\noption), "
                + "so I'm not going to set up "
                + "Overleaf integration for this repository.\n"
            )
        else:
            if os.getenv("OVERLEAF_EMAIL") and os.getenv("OVERLEAF_PASSWORD"):
                click.echo(
                    "\nYou provided an Overleaf project id, and "
                    "I found both "
                    + click.style("OVERLEAF_EMAIL", fg="blue")
                    + " and\n"
                    + click.style("OVERLEAF_PASSWORD", fg="blue")
                    + " environment variables, so I'm going to set up "
                    + "Overleaf\nintegration for this repository. "
                    + "In order for this to\n"
                    + "work on GitHub Actions, please go to\n\n"
                    + click.style(
                        f"    https://github.com/{slug}/settings/secrets/actions/new\n\n",
                        fg="blue",
                    )
                    + "at this time and create "
                    + click.style("OVERLEAF_EMAIL", fg="blue")
                    + " and "
                    + click.style("OVERLEAF_PASSWORD", fg="blue")
                    + " secrets with\nyour Overleaf credentials.\n"
                )
            else:
                click.echo(
                    "\nIt looks like you provided an Overleaf project id, but "
                    "I didn't find an\n"
                    + click.style("OVERLEAF_EMAIL", fg="blue")
                    + " and/or an "
                    + click.style("OVERLEAF_PASSWORD", fg="blue")
                    + " environment "
                    + "variable, so I'm not\ngoing to set up "
                    + "Overleaf integration for this repository.\n"
                )
        pause()

        return slug

    else:

        raise click.BadParameter("Must have the form `user/repo`.")


@entry_point.command()
@click.argument("slug", callback=validate_slug)
@click.option(
    "--yes",
    is_flag=True,
    default=False,
    help="Accept all `Press any key to continue` prompts automatically.",
)
@click.option(
    "--overleaf",
    help="Overleaf project id to sync with (optional). Requires Overleaf "
    "credentials, provided as the environment variables and GitHub repository "
    "secrets OVERLEAF_EMAIL and OVERLEAF_PASSWORD.",
    default=None,
)
@click.option(
    "--ssh",
    is_flag=True,
    help="Use ssh to authenticate with GitHub? Default is to use https.",
)
@click.option(
    "--showyourwork-version",
    help="Version of showyourwork to use. Default is the current version.",
    default=None,
)
def setup(slug, yes, overleaf, ssh, showyourwork_version):
    """
    Set up a new article repository in the current working directory.

    This command expects a single positional argument, `SLUG`, of the form
    `user/repo`, where `user` is the user's GitHub handle and `repo` is the
    name of the repository (and local directory) to create.
    """
    commands.setup(slug, overleaf, ssh, showyourwork_version)


@entry_point.command()
def clean():
    """Clean the article build in the current working directory."""
    ensure_top_level()
    commands.clean()


@entry_point.command()
def tarball():
    """Generate a tarball of the build in the current working directory."""
    ensure_top_level()
    commands.preprocess()
    commands.tarball()


@entry_point.command(hidden=True)
@click.option("--restore", is_flag=True)
@click.option("--update", is_flag=True)
def cache(restore, update):
    """Update or restore the cache on GitHub Actions."""
    ensure_top_level()
    if not restore != update:
        raise exceptions.ShowyourworkException(
            "Must provide either `--restore` or `--update`."
        )
    if restore:
        commands.cache_restore()
    else:
        commands.cache_update()
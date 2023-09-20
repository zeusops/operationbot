# Operationbot

A Discord bot for listing events on a channel. Originally made for handling
Arma 3 operations in the [Zeusops](https://www.zeusops.com) community.

**Note:** Requires Python 3.11 or newer.

## Setting up

1. Create a new Discord bot at <https://discord.com/developers/applications>

   See [here](https://discordpy.readthedocs.io/en/latest/discord.html) for more
   detailed instructions. Note that the bot does not have to be marked as
   public.

2. Copy `secret.py.example` to `src/operationbot/secret.py` and add your bot
   token. Other values can be customised as well but they are not critical for
   a basic setup.

3. Change the channel IDs in `src/operationbot/config.py` if the bot is not
   running on the Zeusops discord.

4. Install the package locally (via `poetry`, get it via `pip install poetry`).

   ```shell
   make install
   # or
   poetry install
   ```

   On Windows (or some other platforms which don't include the
   [time zone data](https://docs.python.org/3/library/zoneinfo.html)
   by default), you might need to install the `tzdata` package.

   ```shell
   poetry run pip install tzdata
   ```

5. Then inside the virtual environment, launch the command:

   ```shell
   # Run single command inside virtualenv
   poetry run operationbot
   # or
   # Load the virtualenv first
   poetry shell
   # Then launch the command, staying in virtualenv
   operationbot
   ```

## Development

### Python setup

This repository uses Python3.11, using
[Poetry](https://python-poetry.org) as package manager to define a
Python package inside `src/operationbot/`.

`poetry` will create virtual environments if needed, fetch
dependencies, and install them for development.

For ease of development, a `Makefile` is provided, use it like this:

```shell
make  # equivalent to "make all" = install lint docs test build
# run only specific tasks:
make install
make lint
make test
# Combine tasks:
make install test
```

Once installed, the module's code can now be reached through running
Python in Poetry:

```shell
$ poetry run python
>>> from operationbot import main
>>> main("blabla")
```

This codebase uses [pre-commit](https://pre-commit.com) to run linting
tools like `flake8`. Use `pre-commit install` to install git
pre-commit hooks to force running these checks before any code can be
committed, use `make lint` to run these manually. Testing is provided
by `pytest` separately in `make test`.

### Documentation

Documentation is generated via [Sphinx](https://www.sphinx-doc.org/en/master/),
using the cool [myst_parser](https://myst-parser.readthedocs.io/en/latest/)
plugin to support Markdown files like this one.

Other Sphinx plugins provide extra documentation features, like the recent
[sphinx-autodoc2](https://sphinx-autodoc2.readthedocs.io/en/latest/index.html)
to generate API reference without headaches, and with myst-markdown support in
docstrings too!

To build the documentation, run

```shell
# Requires the project dependencies provided by "make install"
make docs
# Generates docs/build/html/
```

To browse the web version of the documentation you just built, run:

```shell
make docs-serve
```

And remember that `make` supports multiple targets, so you can generate the
documentation and serve it:

```shell
make docs docs-serve
```

### Templated repository

This repository was created by the copier template available at
gh:OverkillGuy/python-template, using version v1.3.1-2-g705747a.

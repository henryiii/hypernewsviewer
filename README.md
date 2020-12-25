### Instructions

This is a Poetry project. Poetry is like a combination of setuptools, pip,
venv, and twine.  It's like bundle for Ruby, or yarn for NodeJS.

To install poetry, use `pip install poetry`, `pipx install poetry`, or `brew
install poetry`, whatever you like using. There's also a bootstrap script, just
like pip has.

Now, to install a virtual env for this project, do:

```bash
poetry install
```

Now, you are ready to use anything, just prefix any command with `poetry run`
to run inside the environment.

If this bugs you for some reason, you can use `poetry shell` to spawn a shell
inside the environment.

### Dev: styles

Please use pre-commit if editing any files. Install pre-commit your favorite
way (`pip`, `pipx`, or `brew`). Then turn on pre-commit:

```bash
pre-commit install
```

If you want to run it manually (perhaps instead of the above install step), run:

```bash
pre-commit run -a
```

### Running the code

Currently, the only application is a simple parser for the `utc` files. Run like this:

```bash
poetry run hn-model --help  # help
poetry run hn-model ../hnfiles/hnTest.html,urc --kind main  # The main file
poetry run hn-model ../hnfiles/hnTest/1.html,urc --kind msg # Message files
```


### Quickstart

This project has a nox file for quick runs. If you have nox:

```console
nox -e serve
```

If you don't have nox but do have pipx, then `pipx run nox` replaces `nox` above. And if you have docker, you can use `docker run --rm -it -v $PWD:/src thekevjames/nox:latest nox -f /src/noxfile.py` instead.

### Instructions

This project recommends PDM for development. PDM is like a combination of
setuptools, pip, venv, and twine.  It's like bundle for Ruby, or yarn for
NodeJS.

To install PDM, use `pip install pdm`, `pipx install pdm`, or `brew
install pdm`, whatever you like using.

Now, to install a virtual env for this project, do:

```bash
pdm install
```

Now, you are ready to use anything, just prefix any command with `pdm run`
to run inside the environment.

If this bugs you for some reason, you can use `pdm --pep582 >> ~./bash_profile`
(or rc) to teach Python about the PDM package folder.

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

### Running the webapp

This will start up a server:

```bash
pdm run flask run
```

### Running the code

There is a command-line interface to the `utc` files. Run like this:

```bash
pdm run hyper-model --help  # help
```

The package will assume `--root ../hnfiles`; but you set set this to wherever the data is stored.

#### Showing a message

```bash
pdm run hyper-model hnTest show  # The main file
pdm run hyper-model hnTest/1 show  # A message
```

#### Listing messages

```bash
poetry run hyper-model hnTest list
poetry run hyper-model hnTest/1 list
```


#### Tree view of messages

```bash
poetry run hyper-model hnTest tree
poetry run hyper-model hnTest/1 tree
```

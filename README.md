### Quickstart

Python 3.8+ required, 3.9 used in production.

This project has a nox file for quick runs. If you have nox:

```console
nox -s serve
```

If you don't have nox but do have pipx, then `pipx run nox` replaces `nox`
above. And if you have docker, you can use
`docker run --rm -it -v $PWD:/src thekevjames/nox:latest nox -f /src/noxfile.py`
instead.

### Instructions

This project recommends PDM for development. PDM is like a combination of
setuptools, pip, venv, and twine. It's like bundle for Ruby, or yarn for NodeJS.

To install PDM, use `pip install pdm`, `pipx install pdm`, or
`brew install pdm`, whatever you like using.

Now, to install a virtual env for this project, do:

```bash
pdm install
```

Now, you are ready to use anything, just prefix any command with `pdm run` to
run inside the environment.

### Locking dependencies

PDM is used to manage the dependencies. You get a locked set of dependencies
when you install. If you want to update your dependencies, run:

```bash
pdm update
```

You'll also want to update the requirements.txt file - pre-commit (below) will
do this for you, or you can run `pdm export -o requirements.txt` yourself.

### Dev: styles

Please use pre-commit if editing any files. Install pre-commit your favorite way
(`pip`, `pipx`, or `brew`). Then turn on pre-commit:

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

The package will assume `--root ../hnfiles`; but you set set this to wherever
the data is stored.

#### Showing a message

```bash
pdm run hyper-model hnTest show  # The main file
pdm run hyper-model hnTest/1 show  # A message
```

#### Listing messages

```bash
pdm run hyper-model hnTest list
pdm run hyper-model hnTest/1 list
```

#### Tree view of messages

```bash
pdm run hyper-model hnTest tree
pdm run hyper-model hnTest/1 tree
```

#### Listing of forum

```bash
pdm run hyper-model any forum
```

#### Producing a database

You need to pre-process the file root to make two database files; one for
metadata, and one for full text search. For example:

```bash
HNFILES=$PWD/cms-hndocs HNDATABASE=hnvdb.sql3 pdm run hyper-model populate
HNFTSDATABASE=hnvfullfts.sql3 HNDATABASE=hnvdb.sql3 HNFILES=$PWD/cms-hndocs pdm run populate-search
```

### Selecting a file to use

If you produce a database (and optionally a search database), then those can be
specified by environment variables:

- `HNFTSDATABASE`: The full-text-search database
- `HNDATABASE`: The database with all the metadata
- `HNFILES`: tTe file directory root


## Setup for development

### Connecting to CERN

Following the [guide](https://security.web.cern.ch/recommendations/en/ssh_tunneling.shtml), run this in a terminal:

```console
sshuttle --dns -vr hschrein@lxplus.cern.ch 137.138.0.0/16 128.141.0.0/16 128.142.0.0/16 188.184.0.0/15
```

### Platform as a Service

Log on to <https://paas.cern.ch>. Site at <https://test-hypernewsviewer.app.cern.ch>.

See `/eos/project/c/cms-hn-archive/www/hnDocs`.

Followed <https://paas.docs.cern.ch/3._Storage/eos/> for EOS access.

Followed <https://paas.docs.cern.ch/4._CERN_Authentication/2-deploy-sso-proxy/> for SSO proxy.

I set up the group access with <https://paas.docs.cern.ch/4._CERN_Authentication/3-configuring-authorized-users/> .


### Local

Local:

I used a recent Rπ. I used:

```bash
sudo apt install sshfs
sudo mkdir /eos
sshfs -o allow_other hschrein@lxplus.cern.ch:/eos /eos/
```

Now you can use `HNFILES=/eos/project/c/cms-hn-archive/www/hnDocs` instead of `/eos/user/h/hschrein/hnfiles` in the BC (Build Config).

<https://cern.service-now.com/service-portal?id=kb_article&sys_id=68deb363db3f0c58006fd9f9f49619aa>

Database transfer:

```bash
oc get pods
oc rsync . hypernewsviewer-c55f84966-9c2lh:/hnvstorage
```

```bash
HNDATABASE=/hnvstorage/hnvdb-2022-03-21.sql3
HNFILES=/eos/project/c/cms-hn-archive/www/hnDocs
```

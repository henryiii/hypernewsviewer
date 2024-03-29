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
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[cli]"
cd ../allfiles
scp 'lxplus:/eos/project/c/cms-hn-archive/www/tarballs/2023-05-17/*' .
cat cms-hndocs.tgz.aa cms-hndocs.tgz.ab cms-hndocs.tgz.ac cms-hndocs.tgz.ad cms-hndocs.tgz.ae > cms-hndocs.tgz
rm rm cms-hndocs.tgz.a?
mkdir cms-hndocs
tar xzf cms-hndocs.tgz -C cms-hndocs  # Takes about 40 mins
HNFILES=$PWD/cms-hndocs HNDATABASE=hnvdb.sql3 hyper-model populate  # Takes about 40 mins
HNFTSDATABASE=hnvfullfts.sql3 HNDATABASE=hnvdb.sql3 HNFILES=$PWD/cms-hndocs hyper-model populate-search  # Takes about 30 mins
```

### Selecting a file to use

If you produce a database (and optionally a search database), then those can be
specified by environment variables:

- `HNFTSDATABASE`: The full-text-search database
- `HNDATABASE`: The database with all the metadata
- `HNFILES`: The file directory root

## Setup for development

### Connecting to CERN

Following the
[guide](https://security.web.cern.ch/recommendations/en/ssh_tunneling.shtml),
run this in a terminal:

```console
sshuttle --dns -vr <username>@lxplus.cern.ch 137.138.0.0/16 128.141.0.0/16 128.142.0.0/16 188.184.0.0/15 128.141.0.0/16 128.142.0.0/16 137.138.0.0/16 185.249.56.0/22 188.184.0.0/15 192.65.196.0/23 192.91.242.0/24 194.12.128.0/18 2001:1458::/32 2001:1459::/32
```

(If you want to use `oc`, you'll need the above to shuttle IPv6 too; it's a
little simpler if you just needed IPv4).

### Platform as a Service

Log on to <https://paas.cern.ch>. Site at <https://hypernewsviewer.app.cern.ch>.

See `/eos/project/c/cms-hn-archive/www/hnDocs`.

Followed [pass eos docs](https://paas.docs.cern.ch/3._Storage/eos/) for EOS
access.

Followed
[paas sso docs](https://paas.docs.cern.ch/4._CERN_Authentication/2-deploy-sso-proxy/)
for SSO proxy.

I set up the group access with
[paas auth docs](https://paas.docs.cern.ch/4._CERN_Authentication/3-configuring-authorized-users/).

### Local

Local:

I used a recent Rπ. I used:

````bash sudo apt install sshfs sudo mkdir /eos sshfs -o allow_other
<username>@lxplus.cern.ch:/eos /eos/ ```

Now you can use `HNFILES=/eos/project/c/cms-hn-archive/www/hnDocs` instead of
`/eos/user/h/<username>/hnfiles` in the BC (Build Config).

[Service now
page](https://cern.service-now.com/service-portal?id=kb_article&sys_id=68deb363db3f0c58006fd9f9f49619aa).

Database transfer (you can get `openshift-cli` from brew, and your login
command from [here](https://oauth-openshift.paas.cern.ch/oauth/token/display):

```bash oc get pods oc rsync . hypernewsviewer-c55f84966-9c2lh:/hnvstorage ```

I find that transferring is far too slow. A much faster way is to rsync the
files to lxplus, then use `oc` on lxplus (you can download a binary for it
[here](https://readthedocs.web.cern.ch/pages/viewpage.action?pageId=170033571))
can then do the rsync much faster. Th two step procedure takes about 20
minutes, while a direct transfer takes ~4 days.

You can log into the container with `oc rsh <podname>`.

```bash
HNDATABASE=/hnvstorage/hnvdb-2023-07-05.sql3
HNFILES=/eos/project/c/cms-hn-archive/www/hnDocs
````

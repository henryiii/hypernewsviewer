import nox

nox.options.sessions = ["tests"]


@nox.session
def tests(session):
    """
    Run the package tests (minimal at the moment).
    """
    session.install(".[test]")
    session.run("pytest")


@nox.session
def serve(session):
    """
    Serve a session (Ctrl-C to quit).
    """
    session.install(".")
    session.run("flask", "run")

@nox.session
def production(session):
    """
    Serve with a production level server (Ctrl-C to quit).
    """

    session.install(".")
    session.install("gunicorn")
    session.run("gunicorn", "hypernewsviewer.app:app")

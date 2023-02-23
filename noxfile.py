from __future__ import annotations

import os

import nox

nox.options.sessions = ["lint", "tests"]


@nox.session
def lint(session: nox.Session) -> None:
    """
    Run pre-commit linting.
    """
    session.install("pre-commit")
    session.run(
        "pre-commit", "run", "--show-diff-on-failure", "--all-files", *session.posargs
    )


@nox.session
def tests(session: nox.Session) -> None:
    """
    Run the package tests (minimal at the moment).
    """
    session.install("-e", ".[test]")
    session.run("pytest", *session.posargs)


@nox.session
def serve(session: nox.Session) -> None:
    """
    Serve a session (Ctrl-C to quit).
    """
    env = os.environ.copy()
    env["FLASK_ENV"] = "development"
    session.install(".")
    session.run("flask", "run", *session.posargs, env=env)


@nox.session
def production(session: nox.Session) -> None:
    """
    Serve with a production level server (Ctrl-C to quit).
    """

    session.install(".")
    session.install("gunicorn")
    session.run("gunicorn", "hypernewsviewer.app:app")

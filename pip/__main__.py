"""pip shim for CI bootstrap on PyPy < 3.11.

When invoked as ``python -m pip ...`` on GitHub Actions with PyPy < 3.11,
this module sets PIP_CONSTRAINT to a constraints file that pins dependency
versions compatible with the interpreter before delegating to the real pip.
"""

import os
import platform
import sys


def _should_constrain() -> bool:
    """Return True if we are on GitHub Actions + PyPy + Python < 3.11."""
    if os.environ.get("GITHUB_ACTIONS") != "true":
        return False
    if platform.python_implementation() != "PyPy":
        return False
    if sys.version_info >= (3, 11):
        return False
    return True


def _is_upgrade_command() -> bool:
    """Return True if the command is ``pip install -U`` or ``pip install --upgrade``."""
    return len(sys.argv) >= 4 and sys.argv[1:3] in (["install", "-U"], ["install", "--upgrade"])


def _has_twine_in_args() -> bool:
    """Return True if the command line contains both 'install' and 'twine'."""
    args = " ".join(sys.argv).lower()
    return "install" in args and "twine" in args


def main() -> None:
    if _should_constrain() and (_is_upgrade_command() or _has_twine_in_args()):
        constraints_file = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "requirements",
            "ci-bootstrap-constraints.txt",
        )
        if os.path.isfile(constraints_file):
            os.environ["PIP_CONSTRAINT"] = constraints_file

    # Remove the repository root from sys.path so we don't shadow the real pip.
    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sys.path = [p for p in sys.path if not os.path.realpath(p) == os.path.realpath(repo_root)]

    # Remove ourselves from sys.modules so pip's own machinery can import
    # the real pip package without hitting this shim again.
    for key in list(sys.modules):
        if key == "pip" or key.startswith("pip."):
            if key != "pip.__main__":
                del sys.modules[key]

    # Delegate to the real pip.
    from pip._internal.cli import main as pip_main

    sys.exit(pip_main())


if __name__ == "__main__":
    main()

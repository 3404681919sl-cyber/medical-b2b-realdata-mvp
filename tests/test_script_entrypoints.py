import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_extract_and_audit_script_starts_from_project_root():
    """Catches the script directory shadowing the project root on sys.path."""
    result = subprocess.run(
        [sys.executable, "scripts/extract_and_audit.py", "--help"],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert "--dump" in result.stdout


def test_build_deploy_bundle_script_starts_from_project_root():
    result = subprocess.run(
        [sys.executable, "scripts/build_deploy_bundle.py", "--help"],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert "--project-root" in result.stdout


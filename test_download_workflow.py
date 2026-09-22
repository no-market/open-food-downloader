"""Contract tests for the manual food-record download workflow."""

import os
import subprocess
from pathlib import Path


WORKFLOW_PATH = Path(".github/workflows/download-food-records.yml")
DOWNLOAD_STEP_NAME = "    - name: Download and display food records"


def _download_step() -> str:
    workflow = WORKFLOW_PATH.read_text(encoding="utf-8")
    step_start = workflow.index(DOWNLOAD_STEP_NAME)
    next_step = workflow.find("\n    - name:", step_start + len(DOWNLOAD_STEP_NAME))
    return workflow[step_start:next_step]


def _download_script(step: str) -> str:
    run_marker = "      run: |\n"
    script_start = step.index(run_marker) + len(run_marker)
    lines = step[script_start:].splitlines()
    return "\n".join(line[8:] if line.startswith("        ") else line for line in lines)


def test_download_step_requires_hf_token_before_invoking_downloader(tmp_path):
    """A missing token stops the workflow before its downloader is invoked."""
    step = _download_step()
    script = _download_script(step)
    make_marker = tmp_path / "make-was-called"
    fake_make = tmp_path / "make"
    fake_make.write_text(f"#!/bin/sh\ntouch '{make_marker}'\n", encoding="utf-8")
    fake_make.chmod(0o755)

    environment = os.environ.copy()
    environment.pop("HF_TOKEN", None)
    environment["PATH"] = f"{tmp_path}:{environment['PATH']}"

    result = subprocess.run(
        ["bash", "-c", script],
        capture_output=True,
        check=False,
        env=environment,
        text=True,
    )

    assert result.returncode != 0
    assert "Missing required repository secret: HF_TOKEN" in result.stdout
    assert not make_marker.exists()


def test_download_step_wires_hf_secret_and_does_not_print_it(tmp_path):
    """The workflow exposes the repository secret through the standard variable."""
    step = _download_step()
    assert "        HF_TOKEN: ${{ secrets.HF_TOKEN }}" in step

    script = _download_script(step)
    make_marker = tmp_path / "make-was-called"
    fake_make = tmp_path / "make"
    fake_make.write_text(f"#!/bin/sh\ntouch '{make_marker}'\n", encoding="utf-8")
    fake_make.chmod(0o755)

    token = "test-token-must-not-be-printed"
    environment = os.environ.copy()
    environment["HF_TOKEN"] = token
    environment["PATH"] = f"{tmp_path}:{environment['PATH']}"

    result = subprocess.run(
        ["bash", "-c", script],
        capture_output=True,
        check=False,
        env=environment,
        text=True,
    )

    assert result.returncode == 0
    assert make_marker.exists()
    assert token not in result.stdout
    assert token not in result.stderr

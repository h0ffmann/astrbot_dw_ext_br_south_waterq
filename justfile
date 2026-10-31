# Commands for this repository. Run "just" to see the list.

set shell := ["bash", "-euo", "pipefail", "-c"]

# The extension system is not yet in the main branch of the host. Change this when it is.
host_repo := "https://github.com/h0ffmann/astrbot_plugin_disaster_warning.git"
host_ref := "2d2f2612dece0100170151e63ec3d9c04327055d"
host_dir := justfile_directory() / ".host/astrbot_plugin_disaster_warning"

export DW_HOST_DIR := env("DW_HOST_DIR", host_dir)

python := justfile_directory() / ".venv/bin/python"
ruff := env("RUFF", python + " -m ruff")
id := "br_south_waterq"

# Show the list of commands
default:
    @just --list --unsorted

# Make .venv and get the host (do this one time)
setup: host
    uv venv --allow-existing .venv
    uv pip install --python {{python}} -r {{host_dir}}/requirements.txt -r requirements-dev.txt

# Get the pinned host in .host/
host:
    #!/usr/bin/env bash
    set -euo pipefail
    mkdir -p "{{host_dir}}"
    cd "{{host_dir}}"
    if [ -d .git ] && [ "$(git rev-parse HEAD)" = "{{host_ref}}" ]; then
        exit 0
    fi
    git init -q
    git fetch -q --depth 1 "{{host_repo}}" "{{host_ref}}"
    git checkout -q FETCH_HEAD

# Run the offline tests (example: just test -k enso)
test *args:
    {{python}} -m pytest {{args}}

# Run the offline tests with the coverage limit
cov:
    {{python}} -m pytest --cov --cov-report=term-missing

# Run the live tests with the real FEPAM, IMA and IAT services
live *args:
    DW_LIVE_TESTS=1 {{python}} -m pytest tests/live {{args}}

# Change the format of the code
fmt:
    {{ruff}} format .

# Check the format and the strict rules
lint:
    {{ruff}} format --check .
    {{ruff}} check .

# Check the types
types:
    {{python}} -m mypy

# Fail on a function with complexity rank C or worse
complexity:
    {{python}} -m radon cc -s -a . -e '.venv/*,.host/*,tests/*,scripts/*,.claude/*,dist/*'
    ! {{python}} -m radon cc -n C . -e '.venv/*,.host/*,tests/*,scripts/*,.claude/*,dist/*' | grep -q .

# Run all checks. The CI runs this command.
check: lint types complexity cov

# Make the release zip in dist/ from the last commit
package:
    mkdir -p dist
    git archive --format=zip --prefix={{id}}/ -o dist/{{id}}.zip HEAD
    unzip -l dist/{{id}}.zip

# Make dist/mock.html: a page with the real messages from the release zip in a mock chat
mock *args: package
    rm -rf dist/installed
    unzip -q dist/{{id}}.zip -d dist/installed
    {{python}} scripts/make_mock.py dist/installed dist/mock.html {{args}}

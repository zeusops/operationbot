DOCKER_IMAGE_NAME=operationbot
DOCKER_REGISTRY=
APP_VERSION=$(shell poetry version --short)

.PHONY: all
all: install lint test build install-hooks

.PHONY: install
install:
	poetry install

# Enforce the pre-commit hooks
.PHONY: install-hooks
install-hooks:
	pre-commit install

.PHONY: lint
lint:  # Use all linters on all files (not just staged for commit)
	pre-commit run --all --all-files

.PHONY: test
test:
	poetry run pytest ${TESTARGS}

.PHONY: docs
docs:
	cd docs && make html
	poetry run doc2dash \
		--force \
		--name operationbot \
		docs/build/html \
		--destination docs/build/docset

.PHONY: docs-serve
docs-serve:
	cd docs/build/html && python3 -m http.server

.PHONY: build
build:
	poetry build

.PHONY: docker-build-release
docker-build-release: export-requirements
	docker build \
		-t "${DOCKER_REGISTRY}${DOCKER_IMAGE_NAME}:${APP_VERSION}" \
		-f release.Dockerfile \
		.

.PHONY: docker-build-dev
docker-build-dev:
	docker build -t ${DOCKER_IMAGE_NAME}-dev .

# Make a release commit + tag, creating Changelog entry
# Set BUMP variable to any of poetry-supported (major, minor, patch)
# or number (1.2.3 etc), see 'poetry version' docs for details
.PHONY: release
# Default the bump to a patch (v1.2.3 -> v1.2.4)
release: BUMP=patch
release:
# Set the new version Makefile variable after the version bump
	$(eval NEW_VERSION := $(shell poetry version --short ${BUMP}))
	$(eval TMP_CHANGELOG := $(shell mktemp))
	sed \
		"s/\(## \[Unreleased\]\)/\1\n\n## v${NEW_VERSION} - $(shell date +%Y-%m-%d)/" \
		CHANGELOG.md > ${TMP_CHANGELOG}
	mv --force ${TMP_CHANGELOG} CHANGELOG.md
	git add CHANGELOG.md pyproject.toml
	git commit -m "Bump to version v${NEW_VERSION}"
	git tag --annotate "v${NEW_VERSION}" \
		--message "Release v${NEW_VERSION}"

# Less commonly used commands

# Generate/update the poetry.lock file
.PHONY: lock
lock:
	poetry lock --no-update

# Update dependencies (within pyproject.toml specs)
# Update the lock-file at the same time
.PHONY: update
update:
	poetry update --lock

# Generate a pip-compatible requirements.txt
# From the poetry.lock. Mostly for CI use.
.PHONY: export-requirements
export-requirements: lock
	sha256sum poetry.lock > requirements.txt \
		&& sed -i '1s/^/# /' requirements.txt \
		&& poetry export --format=requirements.txt >>requirements.txt


# Confirm the requirements.txt's source (poetry.lock) is identical to current
# poetry.lock file
check-requirements:
	head -n1 requirements.txt | sed 's/^# //' | sha256sum -c

# Install poetry from pip
# IMPORTANT: Make sure "pip" resolves to a virtualenv
# Or that you are happy with poetry installed system-wide
.PHONY: install-poetry
install-poetry:
	pip install poetry

# Ensure Poetry will generate virtualenv inside the git repo /.venv/
# rather than in a centralized location. This makes it possible to
# manipulate venv more simply
.PHONY: poetry-venv-local
poetry-venv-local:
	poetry config virtualenvs.in-project true

# Delete the virtualenv to clean dependencies
# Useful when switching to a branch with less dependencies
# Requires the virtualenv to be local (see "poetry-venv-local")
.PHONY: poetry-venv-nuke
poetry-venv-nuke:
	find .venv -delete

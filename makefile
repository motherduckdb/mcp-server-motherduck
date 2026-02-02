.ONESHELL:

.PHONY: install lint lint-fix test test-unit test-e2e publish

# Install dependencies
install:
	uv sync --all-extras

# Run linter (check only)
lint:
	uv run ruff check src/ tests/
	uv run ruff format --check src/ tests/

# Run linter and fix issues
lint-fix:
	uv run ruff check --fix src/ tests/
	uv run ruff format src/ tests/

# Run all tests
test:
	uv run pytest tests/ -v

# Run unit tests only
test-unit:
	uv run pytest tests/unit/ -v

# Run e2e tests only
test-e2e:
	uv run pytest tests/e2e/ -v

# Publish to PyPI
publish:
	uv publish --token $(PYPI_KEY)

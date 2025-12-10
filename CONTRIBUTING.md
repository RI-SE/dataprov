# Contributing to dataprov

Thank you for your interest in contributing to dataprov!

## Development Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/RI-SE/dataprov.git
   cd dataprov
   ```

2. Create a virtual environment and install dependencies:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   pip install -e ".[dev]"
   ```

3. Install pre-commit hooks:
   ```bash
   pre-commit install
   ```

## Code Style

This project uses [Ruff](https://docs.astral.sh/ruff/) for linting and formatting.

- **Format code:** `ruff format .`
- **Lint code:** `ruff check .`
- **Auto-fix issues:** `ruff check --fix .`

Pre-commit hooks will automatically check formatting and linting before each commit.

## Running Tests

```bash
pytest
```

With coverage:
```bash
pytest --cov=dataprov
```

## Submitting Changes

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/my-feature`)
3. Make your changes
4. Ensure tests pass and code is formatted
5. Commit your changes with a descriptive message
6. Push to your fork and submit a pull request

## Reporting Issues

Please use GitHub Issues to report bugs or request features. Include:

- A clear description of the problem or feature
- Steps to reproduce (for bugs)
- Expected vs actual behavior
- Python version and OS

## Questions

Feel free to open an issue for questions about the codebase or usage.

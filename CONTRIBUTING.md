# Contributing to cftc-cot

Contributions are welcome! Whether it's reporting a bug, suggesting a feature, or improving documentation, your help makes this project better.

## How to Contribute

### Reporting Bugs
Please use the [Bug Report issue template](.github/ISSUE_TEMPLATE/bug_report.md) when reporting bugs. Include:
- A clear description of the issue.
- Steps to reproduce.
- Expected vs actual behavior.
- Environment details (OS, Python version, package versions).

### Suggesting Features
Please use the [Feature Request issue template](.github/ISSUE_TEMPLATE/feature_request.md). Include:
- A clear description of the feature.
- Use cases and why this would be helpful.

### Development Process

1. **Fork** the repository.
2. **Clone** your fork.
3. **Create a branch** for your feature or fix.
4. **Install development dependencies**:
   ```bash
   pip install -e ".[dev]"
   ```
5. **Make your changes**.
6. **Add/Update tests** to cover your changes.
7. **Run tests**:
   ```bash
   pytest
   ```
8. **Commit** using [Conventional Commits](https://www.conventionalcommits.org/).
9. **Push** to your branch and submit a **Pull Request**.

### Code Style
- Follow PEP 8.
- Use type hints (`typing` module / standard types).
- Google-style docstrings for all public functions/classes.
- Ensure all tests pass.

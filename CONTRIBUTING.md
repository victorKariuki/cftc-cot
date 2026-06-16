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

This project uses the **Git-Flow** workflow.

1. **Fork** the repository and **Clone** your fork.
2. **Install development dependencies**:
   ```bash
   pip install -e ".[dev]"
   ```
3. **Initialize Git-Flow** (if not already done):
   ```bash
   git flow init -d
   ```
4. **Create a branch** for your task:
   ```bash
   # For new features
   git flow feature start <name>
   
   # For bug fixes
   git flow bugfix start <name>
   ```
5. **Make your changes** and add/update tests.
6. **Run tests**:
   ```bash
   pytest
   ```
7. **Finish your branch**:
   ```bash
   # For features
   git flow feature finish <name>
   
   # For bug fixes
   git flow bugfix finish <name>
   ```
8. **Push** your changes to `develop` and submit a Pull Request to merge `develop` into `master` for releases.

### Code Style
- Follow PEP 8.
- Use type hints (`typing` module / standard types).
- Google-style docstrings for all public functions/classes.
- Ensure all tests pass.

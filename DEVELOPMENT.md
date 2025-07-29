# PyObjict Development Guide

This guide covers the development workflow for the PyObjict package.

## 🚀 Quick Start

```bash
# Set up development environment
make dev-setup

# Run tests and linting
make check

# Show current version
make version

# Release a patch version (most common)
make release-patch
```

## 📦 Development Environment

### Prerequisites

- Python 3.8+
- Poetry
- Git

### Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/311labs/objict.git
   cd objict
   ```

2. **Set up development environment:**
   ```bash
   make dev-setup
   ```

   This will:
   - Install Poetry dependencies
   - Set up the virtual environment
   - Install dev dependencies (pytest, coverage tools, etc.)

## 🧪 Testing

### Running Tests

```bash
# Run all tests
make test

# Run tests with coverage report
make test-cov

# Run tests quietly (for scripts/CI)
make test-quiet

# Run linting
make lint

# Run both linting and tests
make check
```

### Test Structure

Tests are located in `tests/test_objict.py` and use pytest. The test suite includes:

- Unit tests for all objict functionality
- Edge case testing
- Python 2/3 compatibility tests
- Coverage reporting

## 📈 Version Management

### Semantic Versioning

PyObjict follows [semantic versioning](https://semver.org/):

- **MAJOR**: Breaking changes (e.g., 1.0.0 → 2.0.0)
- **MINOR**: New features, backward compatible (e.g., 1.0.0 → 1.1.0)  
- **PATCH**: Bug fixes, backward compatible (e.g., 1.0.0 → 1.0.1)

### Bumping Versions

The project uses a custom Python script (`bump_version.py`) that automatically updates:

- `pyproject.toml` version
- `objict/__init__.py` version variables
- Creates Git commits and tags

```bash
# Show current version
make version

# Bump patch version (2.0.6 → 2.0.7)
make bump-patch

# Bump minor version (2.0.6 → 2.1.0)
make bump-minor

# Bump major version (2.0.6 → 3.0.0)
make bump-major
```

Each bump command will:

1. ✅ Run pre-release checks (tests, linting, git status)
2. 📝 Update version numbers in all files
3. 📦 Create a git commit
4. 🏷️ Create a git tag
5. ⬆️ Ask if you want to push to remote

## 🚀 Release Process

### Full Release Workflow

The release commands run the complete workflow: **test** → **bump** → **build** → **publish**

```bash
# Most common: patch release
make release-patch

# For new features
make release-minor

# For breaking changes  
make release-major
```

### Step-by-Step Release

If you prefer more control, you can run each step manually:

```bash
# 1. Ensure everything is clean and tested
make check

# 2. Bump the version
make bump-patch

# 3. Build the package
make build

# 4. Publish to PyPI
make publish
```

### Testing Releases

Before publishing to PyPI, you can test with TestPyPI:

```bash
# Test release workflows (publish to TestPyPI)
make release-patch-test
make release-minor-test
make release-major-test
```

### Pre-Release Checks

The system automatically runs these checks before any release:

- ✅ **Git status**: Working directory must be clean
- ✅ **Tests**: All tests must pass
- ✅ **Linting**: Code must pass linting checks
- ⚠️ **Branch check**: Warns if not on main/master branch

## 🛠️ Available Commands

### Core Development

| Command | Description |
|---------|-------------|
| `make help` | Show all available commands |
| `make install` | Install dependencies |
| `make test` | Run tests |
| `make test-cov` | Run tests with coverage |
| `make lint` | Run code linting |
| `make check` | Run linting + tests |
| `make build` | Build the package |
| `make clean` | Clean build artifacts |

### Version Management

| Command | Description |
|---------|-------------|
| `make version` | Show current version |
| `make bump-patch` | Bump patch version |
| `make bump-minor` | Bump minor version |
| `make bump-major` | Bump major version |

### Publishing

| Command | Description |
|---------|-------------|
| `make publish` | Publish to PyPI |
| `make publish-test` | Publish to TestPyPI |
| `make release-patch` | Full patch release workflow |
| `make release-minor` | Full minor release workflow |
| `make release-major` | Full major release workflow |

### Shortcuts

| Command | Description |
|---------|-------------|
| `make patch` | Alias for `release-patch` |
| `make minor` | Alias for `release-minor` |
| `make major` | Alias for `release-major` |
| `make ci` | Run all CI checks |

## 🔧 Development Workflow

### Typical Development Cycle

1. **Start development:**
   ```bash
   git checkout -b feature/my-new-feature
   # Make your changes
   ```

2. **Test your changes:**
   ```bash
   make check
   ```

3. **Commit and push:**
   ```bash
   git add .
   git commit -m "Add my new feature"
   git push origin feature/my-new-feature
   ```

4. **Create pull request** and get it merged to main

5. **Release (from main branch):**
   ```bash
   git checkout main
   git pull origin main
   make release-patch  # or minor/major as appropriate
   ```

### Hot Fix Workflow

For urgent bug fixes:

```bash
git checkout main
git pull origin main
git checkout -b hotfix/urgent-bug-fix

# Make the fix
# Test the fix
make check

# Commit the fix
git add .
git commit -m "Fix urgent bug"
git push origin hotfix/urgent-bug-fix

# After merging to main:
git checkout main
git pull origin main
make release-patch
```

## 📝 Code Style

- Follow PEP 8 Python style guidelines
- Use meaningful variable and function names
- Add docstrings for public methods
- Keep backward compatibility when possible
- Write tests for new features

## 🚨 Troubleshooting

### Common Issues

**Version bump fails with git errors:**
- Ensure your working directory is clean (`git status`)
- Make sure you're on the main/master branch
- Check that you have push permissions to the repository

**Tests fail:**
- Run `make test-cov` to see detailed coverage report
- Check if new code needs additional tests
- Ensure all dependencies are installed: `make install`

**Build fails:**
- Clean build artifacts: `make clean`
- Check `pyproject.toml` for syntax errors
- Ensure Poetry is up to date: `poetry --version`

**Publish fails:**
- Check PyPI credentials are configured: `poetry config --list`
- Ensure you have permissions to publish the package
- Try publishing to TestPyPI first: `make publish-test`

### Getting Help

- Check existing tests in `tests/test_objict.py` for examples
- Run `make help` to see all available commands
- Look at the `bump_version.py` script for version management details
- Check Poetry documentation for publishing issues

## 📚 Additional Resources

- [Poetry Documentation](https://python-poetry.org/docs/)
- [Semantic Versioning](https://semver.org/)
- [Python Packaging Guide](https://packaging.python.org/)
- [pytest Documentation](https://docs.pytest.org/)
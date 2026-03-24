# Contributing to Lockr

Thank you for your interest in contributing to Lockr! We welcome contributions from the community.

## Getting Started

1. **Fork the repository** on GitHub
2. **Clone your fork** locally:
   ```bash
   git clone https://github.com/balakumaran1507/Lockr.git
   cd Lockr
   ```
3. **Set up development environment**:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -e ".[dev]"
   ```

## Development Workflow

### 1. Create a Branch

```bash
git checkout -b feature/your-feature-name
# or
git checkout -b fix/issue-description
```

### 2. Make Your Changes

- Write clean, readable code
- Follow existing code style
- Add tests for new features
- Update documentation as needed

### 3. Run Tests

```bash
# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_store.py -v

# Check code style
black cli/ server/ intent/
ruff check .
```

### 4. Commit Your Changes

```bash
git add .
git commit -m "feat: add awesome new feature"
```

**Commit message format:**
- `feat:` - New feature
- `fix:` - Bug fix
- `docs:` - Documentation changes
- `test:` - Adding tests
- `refactor:` - Code refactoring
- `chore:` - Maintenance tasks

### 5. Push and Create Pull Request

```bash
git push origin feature/your-feature-name
```

Then create a Pull Request on GitHub.

## Code Style

- **Python**: Follow PEP 8
- **Line length**: 100 characters max
- **Type hints**: Use type hints where appropriate
- **Docstrings**: Add docstrings for all functions and classes

## Testing Guidelines

- Write tests for all new features
- Maintain or improve test coverage
- Tests should be in `tests/` directory
- Use descriptive test names

## Areas We Need Help

- 🐛 **Bug fixes** - Check our [Issues](https://github.com/balakumaran1507/Lockr/issues)
- 📚 **Documentation** - Improve guides, add examples
- ✨ **Features** - See our roadmap in README.md
- 🧪 **Testing** - Increase test coverage
- 🌍 **Integrations** - Kubernetes, Terraform, etc.

## Questions?

- Open an issue for questions
- Join discussions on GitHub Discussions
- Email: hello@lockr.dev

## Code of Conduct

Be respectful, inclusive, and professional. We want this to be a welcoming community for everyone.

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

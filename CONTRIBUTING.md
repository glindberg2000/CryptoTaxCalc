# Contributing to CryptoTaxCalc

Thank you for your interest in contributing to CryptoTaxCalc! This document provides guidelines and information for contributors.

## 🚀 Quick Start

1. **Fork** the repository
2. **Clone** your fork locally
3. **Install** development dependencies: `make install-dev`
4. **Create** a feature branch: `git checkout -b feature/your-feature-name`
5. **Make** your changes
6. **Test** your changes: `make test`
7. **Format** your code: `make format`
8. **Lint** your code: `make lint`
9. **Commit** with a descriptive message
10. **Push** to your fork and create a Pull Request

## 📋 Development Setup

### Prerequisites
- Python 3.12.3 or higher
- Git
- Make (optional, for using Makefile commands)

### Installation
```bash
# Clone the repository
git clone https://github.com/your-username/CryptoTaxCalc.git
cd CryptoTaxCalc

# Install development dependencies
make install-dev

# Verify installation
make shell
```

### Development Commands
```bash
make help          # Show all available commands
make test          # Run tests
make test-cov      # Run tests with coverage
make lint          # Run linting
make format        # Format code
make check         # Run all checks (format, lint, test)
make clean         # Clean build artifacts
```

## 🧪 Testing

### Running Tests
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=cryptotaxcalc --cov-report=html

# Run specific test file
pytest tests/test_parser.py

# Run tests matching pattern
pytest -k "test_fifo"
```

### Writing Tests
- Place tests in the `tests/` directory
- Use descriptive test names
- Test both success and failure cases
- Use fixtures for common test data
- Aim for >80% code coverage

### Test Data
- Use anonymized sample data for tests
- Never commit real user data
- Create fixtures for common test scenarios
- Use small, focused test datasets

## 📝 Code Style

### Python Style Guide
We follow [PEP 8](https://www.python.org/dev/peps/pep-0008/) with some modifications:

- **Line length**: 88 characters (Black default)
- **Import sorting**: Use `isort` with Black profile
- **Type hints**: Required for all public functions
- **Docstrings**: Use Google style docstrings

### Code Formatting
```bash
# Format code automatically
make format

# Check formatting
black --check cryptotaxcalc/ tests/
isort --check-only cryptotaxcalc/ tests/
```

### Linting
```bash
# Run all linters
make lint

# Individual linters
flake8 cryptotaxcalc/ tests/
mypy cryptotaxcalc/
```

## 🔒 Security Guidelines

### Data Privacy
- **Never commit** real user data or API keys
- **Anonymize** any sample data used in tests
- **Use environment variables** for sensitive configuration
- **Validate** all user inputs

### Code Security
- **Sanitize** CSV inputs
- **Validate** transaction data
- **Use parameterized queries** for database operations
- **Follow** OWASP guidelines for web components

## 📊 Pull Request Process

### Before Submitting
1. **Test** your changes thoroughly
2. **Format** your code: `make format`
3. **Lint** your code: `make lint`
4. **Update** documentation if needed
5. **Add** tests for new functionality

### Pull Request Guidelines
- **Title**: Clear, descriptive title
- **Description**: Explain what and why, not how
- **Related Issues**: Link to relevant issues
- **Screenshots**: Include for UI changes
- **Breaking Changes**: Clearly mark and document

### Review Process
1. **Automated Checks**: Must pass CI/CD pipeline
2. **Code Review**: At least one maintainer approval
3. **Testing**: Verify functionality works as expected
4. **Documentation**: Ensure docs are updated

## 🏗️ Architecture Guidelines

### Module Structure
```
cryptotaxcalc/
├── __init__.py          # Package initialization
├── parser.py            # Main transaction parser
├── fifo_manager.py      # FIFO queue management
├── fmv_fetcher.py       # Fair Market Value fetching
├── tax_calculator.py    # Tax computation logic
├── reporter.py          # Report generation
├── database.py          # Database operations
├── utils.py            # Common utilities
└── cli.py              # Command-line interface
```

### Design Principles
- **Single Responsibility**: Each module has one clear purpose
- **Dependency Injection**: Pass dependencies explicitly
- **Error Handling**: Graceful degradation with logging
- **Configuration**: Environment-based configuration
- **Testing**: Testable, modular design

## 📚 Documentation

### Code Documentation
- **Docstrings**: Required for all public functions
- **Type Hints**: Required for function signatures
- **Comments**: Explain complex logic, not obvious code
- **Examples**: Include usage examples in docstrings

### User Documentation
- **README**: Keep updated with installation and usage
- **API Docs**: Document public interfaces
- **Examples**: Provide sample data and use cases
- **Troubleshooting**: Common issues and solutions

## 🐛 Bug Reports

### Before Reporting
1. **Search** existing issues
2. **Test** with latest version
3. **Reproduce** the issue consistently
4. **Check** documentation

### Bug Report Template
```markdown
**Description**
Clear description of the issue

**Steps to Reproduce**
1. Step 1
2. Step 2
3. Step 3

**Expected Behavior**
What should happen

**Actual Behavior**
What actually happens

**Environment**
- OS: [e.g., macOS 14.0]
- Python: [e.g., 3.12.3]
- CryptoTaxCalc: [e.g., 0.1.0]

**Additional Context**
Screenshots, logs, sample data
```

## 💡 Feature Requests

### Before Requesting
1. **Search** existing issues
2. **Check** if it aligns with project goals
3. **Consider** implementation complexity
4. **Think** about user impact

### Feature Request Template
```markdown
**Problem**
Clear description of the problem

**Proposed Solution**
Description of the proposed solution

**Alternatives Considered**
Other approaches considered

**Additional Context**
Screenshots, mockups, use cases
```

## 🤝 Community Guidelines

### Communication
- **Be respectful** and inclusive
- **Use clear language** and avoid jargon
- **Provide context** for questions
- **Help others** when possible

### Code of Conduct
- **Respect** all contributors
- **Be inclusive** and welcoming
- **Focus on** constructive feedback
- **Report** inappropriate behavior

## 📞 Getting Help

### Resources
- **Documentation**: Check `cline_docs/` and `README.md`
- **Issues**: Search existing issues
- **Discussions**: Use GitHub Discussions
- **Wiki**: Check project wiki (if available)

### Contact
- **Issues**: GitHub Issues for bugs and features
- **Discussions**: GitHub Discussions for questions
- **Security**: Private email for security issues

## 🏆 Recognition

### Contributors
- **Code Contributors**: Listed in GitHub contributors
- **Documentation**: Acknowledged in docs
- **Testing**: Recognized for bug reports
- **Community**: Valued for support and feedback

### Contribution Types
- **Code**: Bug fixes, features, improvements
- **Documentation**: Guides, examples, API docs
- **Testing**: Test cases, bug reports
- **Community**: Support, feedback, evangelism

---

Thank you for contributing to CryptoTaxCalc! 🚀 
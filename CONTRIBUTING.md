# Contributing to ETL Dashboard

Thank you for your interest in contributing to the ETL Dashboard project! 

## 🤝 How to Contribute

### Reporting Issues
- Use GitHub Issues to report bugs or request features
- Provide detailed descriptions and steps to reproduce
- Include system information and error messages

### Development Setup
1. Fork the repository
2. Clone your fork: `git clone <your-fork-url>`
3. Create virtual environment: `python -m venv venv`
4. Activate environment: `venv\Scripts\activate` (Windows) or `source venv/bin/activate` (Unix)
5. Install dependencies: `pip install -r requirements.txt`
6. Run tests: `python -m pytest tests/`

### Pull Request Process
1. Create a feature branch: `git checkout -b feature/your-feature-name`
2. Make your changes
3. Write/update tests
4. Ensure all tests pass
5. Update documentation if needed
6. Commit with clear messages: `feat(scope): description`
7. Push and create pull request

### Code Standards
- Follow PEP 8 Python style guide
- Use descriptive variable and function names
- Add docstrings to functions and classes
- Write unit tests for new functionality
- Keep commits focused and atomic

### Commit Message Format
```
type(scope): description

Types: feat, fix, docs, style, refactor, test, chore
Examples:
- feat(backend): add Excel validation
- fix(frontend): resolve upload progress issue
- docs(readme): update installation steps
```

## 🧪 Testing
- Run full test suite: `python -m pytest tests/`
- Test specific module: `python -m pytest tests/test_cleaning.py`
- Generate coverage: `python -m pytest --cov=backend tests/`

## 📝 Documentation
- Update README.md for significant changes
- Add docstrings for new functions/classes
- Update PowerBI documentation in `powerbi/` directory

## ❓ Questions?
- Open a GitHub Discussion
- Check existing Issues and Discussions
- Contact maintainers through GitHub

We appreciate your contributions! 🎉
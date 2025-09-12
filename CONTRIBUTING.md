# Contributing to F1 Undercut Simulator

Thank you for your interest in contributing to the F1 Undercut Simulator! This document provides guidelines and information for contributors.

## 🎯 Project Overview

The F1 Undercut Simulator is a comprehensive tool for analyzing Formula 1 pit stop strategies and undercut probabilities. It combines real F1 data with statistical modeling to provide strategic insights.

## 🌟 Branch Strategy

We follow **Git Flow** with the following branch structure:

### Main Branches
- `main` - Production-ready code, protected branch
- `develop` - Integration branch for features

### Feature Branches  
- `feature/short-description` - New features
- `bugfix/issue-description` - Bug fixes
- `hotfix/critical-fix` - Emergency production fixes

### Branch Naming Convention
```
feature/tire-temperature-modeling
bugfix/api-timeout-handling
hotfix/cors-configuration
docs/api-documentation-update
test/integration-test-improvements
```

## 📝 Commit Message Format

We use **Conventional Commits** for clear, semantic commit messages:

### Format
```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

### Types
- `feat`: New feature
- `fix`: Bug fix  
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring without feature changes
- `perf`: Performance improvements
- `test`: Adding or modifying tests
- `chore`: Build process, dependency updates, etc.
- `ci`: CI/CD pipeline changes

### Examples
```bash
feat(models): add tire temperature modeling to DegModel

fix(api): resolve timeout issues in OpenF1 client

docs: update README with deployment instructions

test(models): add comprehensive edge case tests for PitModel

chore(deps): bump pandas from 2.1.0 to 2.1.4

ci: add integration tests to GitHub Actions workflow
```

### Scope Guidelines
- `models`: Changes to modeling classes (DegModel, PitModel, OutlapModel)
- `api`: FastAPI endpoints and routing
- `services`: API clients (OpenF1Client, JolpicaClient)
- `frontend`: React/Next.js components and logic
- `tests`: Test files and testing utilities
- `docs`: Documentation files
- `ci`: CI/CD and automation

## 🚀 Development Setup

### Prerequisites
- Python 3.9+ 
- Node.js 18+
- Git

### Backend Setup
```bash
# Clone the repository
git clone <repository-url>
cd f1-undercut-sim

# Create and activate virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -e .

# Install development dependencies
pip install pytest pytest-cov black isort flake8

# Run tests
cd backend
python -m pytest tests/ -v
```

### Frontend Setup  
```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Run development server
npm run dev

# Run type checking
npm run build
```

## 🧪 Running Tests

### Backend Tests
```bash
cd backend

# Run all tests with coverage
python -m pytest tests/ -v --cov=models --cov=services --cov=app

# Run specific test file
python -m pytest tests/test_deg_model.py -v

# Run tests matching pattern
python -m pytest tests/ -k "test_fit" -v

# Run tests with parallel execution
python -m pytest tests/ -n auto
```

### Frontend Tests
```bash
cd frontend

# Type check
npm run build

# Linting (if configured)
npm run lint
```

### Integration Tests
```bash
# Start backend server
cd backend && python app.py &

# Wait for startup, then test endpoints
curl http://localhost:8000/health
curl http://localhost:8000/

# Build frontend
cd frontend && npm run build
```

## 🎨 Code Style Guidelines

### Python (Backend)
We use **Black** for code formatting and **isort** for import sorting:

```bash
# Format code
black backend/

# Sort imports  
isort backend/

# Check formatting
black --check backend/
isort --check-only backend/

# Linting
flake8 backend/
```

### Python Style Rules
- Maximum line length: 127 characters
- Use type hints for function signatures
- Docstrings for all public methods (Google style)
- Descriptive variable names
- Single responsibility principle for functions/classes

### TypeScript (Frontend)
```bash
# Type checking
cd frontend && npm run build

# Formatting (if configured)
npm run format
```

### TypeScript Style Rules
- Use TypeScript strict mode
- Descriptive component and variable names
- Extract complex logic into custom hooks
- Use semantic HTML elements

## 📋 Pull Request Process

### Before Submitting
1. **Create Feature Branch**: `git checkout -b feature/your-feature`
2. **Write Tests**: Ensure new functionality has test coverage
3. **Run Tests**: All tests must pass
4. **Format Code**: Run formatters and linters
5. **Update Documentation**: Update relevant docs
6. **Commit Changes**: Use conventional commit format

### PR Checklist
- [ ] Branch follows naming convention
- [ ] Commits follow conventional commit format
- [ ] All tests pass (`pytest backend/tests/`)
- [ ] Code is formatted (`black`, `isort`)
- [ ] Documentation updated (if applicable)
- [ ] No merge conflicts with target branch
- [ ] PR description explains changes and motivation

### PR Template
```markdown
## Description
Brief description of changes made.

## Type of Change
- [ ] Bug fix (non-breaking change)
- [ ] New feature (non-breaking change)  
- [ ] Breaking change (fix/feature causing existing functionality to not work)
- [ ] Documentation update

## Testing
- [ ] Tests pass locally
- [ ] Added tests for new functionality
- [ ] Verified integration with existing features

## Screenshots (if applicable)
Add screenshots for UI changes.

## Additional Notes
Any additional context or notes for reviewers.
```

## 🏗️ Project Architecture

### Backend Structure
```
backend/
├── models/           # Statistical models
│   ├── deg.py       # DegModel - tire degradation
│   ├── pit.py       # PitModel - pit stop simulation
│   └── outlap.py    # OutlapModel - outlap penalty
├── services/         # External API clients
│   ├── openf1.py    # OpenF1 API client
│   └── jolpica.py   # Jolpica API client  
├── tests/           # Unit tests
└── app.py           # FastAPI application
```

### Frontend Structure  
```
frontend/
├── app/             # Next.js App Router pages
├── components/      # React components
├── lib/            # Utilities and API client
├── types/          # TypeScript type definitions
└── styles/         # Global styles
```

## 🔧 Adding New Features

### Adding a New Model
1. Create model class in `backend/models/`
2. Implement required methods: `fit()`, `predict()`/`sample()`
3. Add comprehensive tests in `backend/tests/`
4. Update FastAPI endpoints if needed
5. Add frontend integration if applicable

### Adding a New API Endpoint
1. Add endpoint to `backend/app.py`
2. Define Pydantic models for request/response
3. Add error handling and logging
4. Write tests in `backend/tests/test_app.py`
5. Update OpenAPI documentation
6. Add frontend integration

### Adding Frontend Components
1. Create component in `frontend/components/`
2. Add TypeScript types in `frontend/types/`
3. Integrate with existing pages
4. Test component functionality
5. Update documentation

## 📊 Testing Guidelines

### Test Categories
1. **Unit Tests**: Individual model/component testing
2. **Integration Tests**: API endpoint testing  
3. **End-to-End Tests**: Complete workflow testing

### Writing Good Tests
- **Descriptive Names**: `test_deg_model_handles_insufficient_data`
- **Test Edge Cases**: Empty data, invalid inputs, boundary values
- **Use Fixtures**: Reusable test data
- **Assert Meaningful Values**: Not just "no exceptions"
- **Test Both Success and Failure**: Happy path and error cases

### Test Coverage Goals
- Models: 95%+ coverage
- API endpoints: 90%+ coverage  
- Services: 85%+ coverage
- Overall: 90%+ coverage

## 🚀 Release Process

### Version Numbering
We use **Semantic Versioning** (SemVer):
- `MAJOR.MINOR.PATCH`
- Major: Breaking changes
- Minor: New features (backwards compatible)
- Patch: Bug fixes (backwards compatible)

### Release Steps
1. Update version in `pyproject.toml` and `package.json`
2. Update CHANGELOG.md
3. Create release PR to `main`
4. Tag release: `git tag v1.2.0`
5. Deploy to production

## 🤝 Community Guidelines

### Communication
- Be respectful and constructive
- Use clear, descriptive language
- Provide context and examples
- Ask questions when uncertain

### Code Review
- Review for logic, style, and tests
- Provide specific, actionable feedback
- Explain the "why" behind suggestions
- Approve when ready, request changes when needed

### Issue Reporting
When reporting bugs:
- Provide reproduction steps
- Include error messages and logs
- Specify environment (OS, Python/Node version)
- Suggest potential solutions if possible

### Feature Requests
- Describe the use case and problem
- Explain why existing solutions don't work
- Provide examples or mockups
- Consider implementation complexity

## 📚 Resources

### F1 Data Sources
- [OpenF1 API Documentation](https://openf1.org/)
- [Jolpica F1 API (Ergast)](http://ergast.com/mrd/)
- [FastF1 Documentation](https://docs.fastf1.dev/)

### Development Resources
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Next.js Documentation](https://nextjs.org/docs)
- [pytest Documentation](https://docs.pytest.org/)
- [Conventional Commits](https://www.conventionalcommits.org/)

### Project Tools
- **Backend**: Python, FastAPI, pandas, scipy
- **Frontend**: Next.js, TypeScript, Tailwind CSS
- **Testing**: pytest, React Testing Library
- **CI/CD**: GitHub Actions

## ❓ Getting Help

- **GitHub Issues**: Report bugs and request features
- **Discussions**: Ask questions and share ideas
- **Documentation**: Check existing docs first
- **Code Review**: Request review from maintainers

---

**Happy Contributing! 🏎️💨**

*Made with ❤️ for the F1 community*
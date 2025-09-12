# Contributing to F1 Undercut Simulator

Thank you for your interest in contributing to the F1 Undercut Simulator! This document provides guidelines and information for contributors.

## Code of Conduct

By participating in this project, you agree to abide by our code of conduct:

- Be respectful and inclusive
- Welcome newcomers and help them learn
- Focus on constructive feedback
- Respect different viewpoints and experiences
- Show empathy towards other community members

## Getting Started

### Development Setup

1. **Fork and Clone**
   ```bash
   git clone https://github.com/your-username/f1-undercut-sim.git
   cd f1-undercut-sim
   ```

2. **Backend Setup**
   ```bash
   pip install -e ".[dev]"
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. **Frontend Setup**
   ```bash
   npm install
   ```

4. **Install Pre-commit Hooks**
   ```bash
   pre-commit install
   ```

### Running the Development Environment

1. **Start Backend**
   ```bash
   cd backend
   python app.py
   ```

2. **Start Frontend**
   ```bash
   npm run dev
   ```

## How to Contribute

### Types of Contributions

We welcome various types of contributions:

- 🐛 **Bug fixes**
- ✨ **New features**
- 📚 **Documentation improvements**
- 🧪 **Test coverage enhancements**
- 🎨 **UI/UX improvements**
- ⚡ **Performance optimizations**
- 🔧 **Refactoring and code quality**

### Contribution Workflow

1. **Create an Issue** (optional but recommended)
   - Describe the problem or feature request
   - Get feedback from maintainers before starting work

2. **Create a Branch**
   ```bash
   git checkout -b feature/your-feature-name
   # or
   git checkout -b fix/your-bug-fix
   ```

3. **Make Your Changes**
   - Follow the coding standards
   - Add tests for new functionality
   - Update documentation as needed

4. **Test Your Changes**
   ```bash
   # Backend tests
   pytest backend/tests/ -v
   
   # Frontend type checking
   npm run type-check
   
   # Linting
   ruff check backend/
   npm run lint
   ```

5. **Commit Your Changes**
   ```bash
   git add .
   git commit -m "feat: add new tire degradation algorithm"
   ```

6. **Push and Create PR**
   ```bash
   git push origin feature/your-feature-name
   ```
   Then create a Pull Request on GitHub.

## Coding Standards

### Python (Backend)

- **Style**: Follow PEP 8, enforced by Ruff and Black
- **Type Hints**: Use type hints for all function parameters and return values
- **Docstrings**: Use Google-style docstrings for all public functions and classes
- **Testing**: Write unit tests for all new functionality

Example:
```python
def calculate_degradation(
    compound: str, 
    stint_length: int, 
    temperature: float
) -> Dict[str, float]:
    """
    Calculate tire degradation for given conditions.
    
    Args:
        compound: Tire compound (SOFT, MEDIUM, HARD)
        stint_length: Number of laps in the stint
        temperature: Track temperature in Celsius
        
    Returns:
        Dictionary containing degradation analysis results
    """
    # Implementation here
    pass
```

### TypeScript/React (Frontend)

- **Style**: Use ESLint and Prettier configurations
- **Components**: Use functional components with TypeScript
- **Hooks**: Prefer custom hooks for complex logic
- **Styling**: Use Tailwind CSS classes

Example:
```typescript
interface TireAnalysisProps {
  sessionKey: string
  compound: string
}

export function TireAnalysis({ sessionKey, compound }: TireAnalysisProps) {
  const [data, setData] = useState<TireData | null>(null)
  
  // Component implementation
}
```

### Commit Messages

Use conventional commit format:

- `feat:` new feature
- `fix:` bug fix
- `docs:` documentation changes
- `test:` adding or updating tests
- `refactor:` code refactoring
- `style:` formatting changes
- `perf:` performance improvements

Examples:
```
feat: add undercut opportunity detection algorithm
fix: resolve tire degradation calculation edge case
docs: update API documentation for pit strategy endpoint
test: add unit tests for outlap performance model
```

## Testing Guidelines

### Backend Testing

- Write unit tests for all models and services
- Use pytest fixtures for common test data
- Mock external API calls
- Aim for >80% code coverage

Example test:
```python
def test_tire_degradation_calculation():
    """Test tire degradation calculation with valid input."""
    model = TireDegradationModel()
    result = model.analyze({
        "lap_times": [90.5, 90.7, 90.9],
        "tire_compounds": ["SOFT"],
        "track_temperature": 25.0
    })
    
    assert "analyses" in result
    assert len(result["analyses"]) == 1
    assert result["analyses"][0]["compound"] == "SOFT"
```

### Frontend Testing

- Component testing with React Testing Library
- Integration tests for API interactions
- E2E tests for critical user flows

## Documentation

### Code Documentation

- **Python**: Use Google-style docstrings
- **TypeScript**: Use JSDoc comments for complex functions
- **README**: Keep README.md up to date with new features

### API Documentation

- Update OpenAPI/Swagger documentation for new endpoints
- Include example requests and responses
- Document error cases and status codes

## Performance Guidelines

### Backend Performance

- Use async/await for I/O operations
- Implement caching for expensive calculations
- Profile code for performance bottlenecks
- Use database indexes for query optimization

### Frontend Performance

- Lazy load heavy components
- Optimize bundle size
- Use React.memo for expensive components
- Implement proper loading states

## Review Process

### What Reviewers Look For

- **Functionality**: Does the code work as intended?
- **Tests**: Are there adequate tests?
- **Documentation**: Is the code well-documented?
- **Performance**: Are there any performance concerns?
- **Security**: Are there any security implications?
- **Style**: Does the code follow our standards?

### Responding to Reviews

- Be open to feedback and suggestions
- Ask questions if review comments are unclear
- Make requested changes promptly
- Thank reviewers for their time and insights

## Release Process

### Versioning

We use semantic versioning (SemVer):
- **MAJOR**: Breaking changes
- **MINOR**: New features (backward compatible)
- **PATCH**: Bug fixes (backward compatible)

### Release Notes

- Document all changes in releases
- Include migration guides for breaking changes
- Highlight important new features

## Getting Help

### Questions and Discussions

- **GitHub Issues**: For bugs and feature requests
- **GitHub Discussions**: For questions and general discussion
- **Code Reviews**: For specific implementation feedback

### Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Next.js Documentation](https://nextjs.org/docs)
- [React Documentation](https://react.dev/)
- [TypeScript Documentation](https://www.typescriptlang.org/docs/)

## Recognition

Contributors are recognized in:
- Release notes
- Contributors section in README
- Special recognition for significant contributions

## License

By contributing to this project, you agree that your contributions will be licensed under the MIT License.

---

Thank you for contributing to the F1 Undercut Simulator! Your efforts help make Formula 1 strategy analysis more accessible to everyone. 🏎️
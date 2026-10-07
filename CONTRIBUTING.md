# Contributing to NCERT AI Teacher Assistant

We welcome contributions from **educators, developers, and researchers** to help teachers reduce paperwork and focus on teaching!

## 🚀 Quick Start

1. **Fork the repository** on GitHub
2. **Clone your fork** locally:
   ```bash
   git clone https://github.com/your-username/NCERT-AI-Teacher-Assistant.git
   cd NCERT-AI-Teacher-Assistant
   ```

3. **Set up development environment**:

   **Backend (Python/FastAPI)**:
   ```bash
   cd backend  # when created
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

   **Frontend (Next.js)**:
   ```bash
   # From repo root
   npm install
   npm run dev
   ```

4. **Create a feature branch**:
   ```bash
   git checkout -b feature/your-feature-name
   ```

5. **Make your changes** and test them

6. **Submit a pull request**

## 🔧 Development Setup

### Prerequisites
- Python 3.10+
- Node.js 18+
- npm/pnpm
- Git
- LLM API Key (Google AI Studio / OpenAI / Anthropic)

### Environment Setup
```bash
# Backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install black isort flake8 mypy pytest pytest-asyncio

# Frontend
npm install
```

### Running Tests
```bash
# Backend tests
cd backend
pytest tests/ -v

# Frontend tests
npm test
npm run lint
npm run type-check
```

## 📝 Code Style

### Python (Backend)
- **Black** for code formatting
- **isort** for import sorting
- **flake8** for linting
- **mypy** for type checking
- Line length: 88 characters (Black default)

```bash
# Format
black .
isort .

# Check
flake8 . --max-line-length=88 --extend-ignore=E203,W503
mypy . --ignore-missing-imports
```

### TypeScript/React (Frontend)
- **ESLint** for linting
- **Prettier** for formatting (via ESLint)
- **TypeScript** strict mode

```bash
# Check
npm run lint
npm run type-check

# Format (if configured)
npm run format
```

## 🏗️ Project Structure

```
NCERT-AI-Teacher-Assistant/
├── backend/                 # Python FastAPI backend (to be created)
│   ├── app/
│   │   ├── api/            # API routes
│   │   ├── core/           # Config, security
│   │   ├── models/         # Pydantic models
│   │   ├── services/       # Business logic (LLM, RAG)
│   │   └── utils/          # Helpers
│   ├── tests/
│   └── requirements.txt
├── app/                     # Next.js 15 App Router
│   ├── components/         # React components
│   ├── lib/               # Utilities
│   └── api/               # API routes
├── components/             # Shared components
├── data/                  # Static data (curriculum maps)
├── public/                # Static assets
├── .github/
│   ├── workflows/         # CI/CD
│   └── ISSUE_TEMPLATE/    # Issue templates
└── docs/                  # Documentation
```

## 🧪 Testing Guidelines

### Backend Tests
- Unit tests for each service module
- Integration tests for API endpoints
- Mock LLM responses for deterministic testing

### Frontend Tests
- Component tests with React Testing Library
- E2E tests for critical user flows (when added)

### Writing Tests
- Use descriptive test names
- Include docstrings explaining test purpose
- Test both success and failure cases
- Use fixtures for common test data

## 📋 Pull Request Guidelines

### Before Submitting
- [ ] Code follows style guidelines (`black`, `isort`, `flake8`, `eslint` pass)
- [ ] Type checks pass (`mypy`, `tsc`)
- [ ] Tests pass (`pytest`, `npm test`)
- [ ] New functionality includes tests
- [ ] Documentation is updated if needed
- [ ] CHANGELOG.md is updated for significant changes

### Pull Request Description
Include:
- **Purpose**: What does this PR accomplish?
- **Changes**: What specific changes were made?
- **Testing**: How was this tested?
- **Breaking Changes**: Any backwards incompatible changes?
- **Screenshots**: For UI changes

### Example PR Description
```
## Purpose
Add lesson plan generator for Class 10 Science Chapter 1

## Changes
- Added NCERT curriculum mapping for Class 10 Science
- Implemented 5E model prompt template
- Added PDF export for lesson plans
- Created unit tests for prompt generation

## Testing
- Verified prompt generates valid lesson plan structure
- Tested PDF export with sample data
- All existing tests pass

## Breaking Changes
None - new endpoint added

## Screenshots
![Lesson Plan Output](screenshot.png)
```

## 🐛 Bug Reports

When reporting bugs, please include:

1. **Environment**: OS, Browser, Python/Node versions, LLM provider
2. **Reproduction**: Minimal steps to reproduce
3. **Expected vs Actual**: What you expected vs what happened
4. **Error Messages**: Full error traceback/logs
5. **Screenshots**: If UI-related

## 💡 Feature Requests

For new features:
1. **Check existing issues** to avoid duplicates
2. **Describe the teacher workflow** - how does this help teachers?
3. **Consider curriculum alignment** - which NCERT class/subject/chapter?
4. **Propose implementation** if you have ideas
5. **Consider privacy** - no student PII, offline-first options

## 📚 Documentation

### Code Documentation
- Use clear, descriptive docstrings (Google style for Python)
- Include examples for complex functions
- Document LLM prompts and expected outputs

### Adding Documentation
- Update README.md for user-facing changes
- Update docs/ for technical documentation
- Add inline comments for complex logic
- Update API documentation for endpoint changes

### Prompt Documentation
All LLM prompts should include:
```python
def generate_lesson_plan_prompt(chapter: str, class_level: int) -> str:
    """
    Generate a structured prompt for lesson plan creation.
    
    Args:
        chapter: NCERT chapter name
        class_level: Class number (6-12)
        
    Returns:
        Formatted prompt string for LLM
        
    Example:
        >>> generate_lesson_plan_prompt("Light", 10)
        "Create a lesson plan for Class 10 Science Chapter 'Light'..."
    """
```

## 🏫 Educational Guidelines

### Curriculum Alignment
All generated content must align with:
- **NCERT Textbooks** (primary source)
- **CBSE Syllabus** (examination pattern)
- **NCF 2005** (pedagogical framework)
- **NEP 2020** (competency-based education)
- **Bloom's Taxonomy** (objective classification)

### Quality Standards
- **Accuracy**: Factual correctness verified against NCERT
- **Appropriateness**: Age/grade-appropriate language and complexity
- **Inclusivity**: Gender-neutral, culturally sensitive content
- **Accessibility**: Clear structure, readable formatting

## 🤝 Community Guidelines

- **Be respectful** and inclusive
- **Help teachers** - this is for them
- **Ask questions** if something is unclear
- **Provide constructive feedback**
- **Share classroom experiences** - real feedback is gold

## 📞 Getting Help

- **GitHub Issues**: For bugs and feature requests
- **GitHub Discussions**: For questions and general discussion
- **Documentation**: Check docs/ folder

## 🙏 Special Thanks

This project exists because of teachers who spend countless hours on paperwork. Every contribution helps give them time back for what matters: **teaching**.

Thank you for contributing to NCERT AI Teacher Assistant! 🎉
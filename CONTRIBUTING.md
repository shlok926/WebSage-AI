# Contributing to WebSage AI

Thank you for your interest in contributing to **WebSage AI**! 🎉

We welcome contributions of all kinds: bug fixes, documentation improvements, performance optimizations, and feature enhancements. Please take a moment to review this document before getting started.

---

## 🔒 Important Project Constraints

Before proposing changes, please note our core project rules:

1. **Frozen Requirements Baseline (v1.2):**
   - The specifications in `docs/requirements.md`, `docs/acceptance-criteria.md`, and `docs/security.md` represent our approved baseline.
   - Any modification to core requirements, API contracts, or resource limits requires prior discussion and an explicit versioned specification update.
2. **Zero Mandatory Cost (₹0):**
   - The application must always remain operable under 100% free-tier resources (Groq Free Tier, Render Free Tier, Vercel Hobby Tier).
   - Do not introduce dependencies that require paid subscriptions or credit card verification.
3. **Defense-in-Depth Security:**
   - Security controls (SSRF protection, IP connection pinning, streaming byte caps, redirect limits, and prompt isolation) are non-negotiable and cannot be weakened or bypassed.

---

## 🛠️ Development Setup

### Prerequisites
* Python 3.10+
* Node.js 18+ and npm
* Git

### Backend Setup

```bash
cd backend

# Create and activate a virtual environment
python -m venv venv
# Windows:
venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create local environment file (do NOT commit .env!)
cp .env.example .env

# Run development server
uvicorn app.main:app --reload --port 8000
```

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Run Vite development server
npm run dev
```

---

## 🧪 Testing Guidelines

All contributions must pass existing automated tests before being merged.

### Running Backend Tests

```bash
# From workspace root
python -m pytest backend/tests -v -c backend/pytest.ini
```

Make sure that:
* All 26+ test cases pass without errors or warnings.
* New features or bug fixes include corresponding unit or regression tests in `backend/tests/`.
* Mock networking is used for SSRF/fetcher tests — never make real outbound network requests in tests.

### Running Frontend Checks

```bash
cd frontend

# Run TypeScript compilation and Vite production build
npm run build
```

---

## 📝 Coding Standards

### Backend (Python)
* Follow **PEP 8** style guidelines.
* Use explicit **type hints** for all function signatures and Pydantic models.
* Use asynchronous I/O (`async`/`await`) for I/O-bound operations.
* Sanitize all exceptions before returning them to client responses; never leak stack traces, internal paths, or API keys.

### Frontend (React & TypeScript)
* Use **TypeScript strict mode** (`noImplicitAny`, proper interface definitions).
* Maintain accessible UI practices (proper `aria-*` attributes, semantic tags, keyboard navigation).
* Use **Tailwind CSS** utility classes; avoid inline styles where possible.

---

## 📦 Commit Message Guidelines

We follow the [Conventional Commits](https://www.conventionalcommits.org/) convention:

```text
<type>(<scope>): <short description>
```

### Types:
* `feat`: A new feature
* `fix`: A bug fix
* `docs`: Documentation-only changes
* `test`: Adding or updating automated tests
* `refactor`: Code change that neither fixes a bug nor adds a feature
* `chore`: Maintenance tasks, dependency updates, configuration changes

### Examples:
* `feat(extractor): support article reading-time estimation`
* `fix(fetcher): correct IPv6 unwrap edge case in link-local check`
* `docs: update API contract examples in README`
* `test(security): add test for IPv4-mapped IPv6 loopback address`

---

## 🚀 Submitting a Pull Request (PR)

1. **Fork the repository** on GitHub.
2. **Create a branch** from `main`:
   ```bash
   git checkout -b feature/my-cool-feature
   ```
3. **Make your changes** cleanly with appropriate commit messages.
4. **Run the full test suite and build**:
   ```bash
   python -m pytest backend/tests -v -c backend/pytest.ini
   cd frontend && npm run build
   ```
5. **Push your branch** to your fork:
   ```bash
   git push origin feature/my-cool-feature
   ```
6. **Open a Pull Request** against the `main` branch. Provide a clear summary of changes, motivation, and test coverage in your PR description.

---

## 🛡️ Reporting Security Issues

Please **do not** open public GitHub issues for security vulnerabilities. Instead, refer to our [SECURITY.md](SECURITY.md) for confidential disclosure instructions.

---

## 📜 Code of Conduct

All contributors and participants are expected to adhere to our [Code of Conduct](CODE_OF_CONDUCT.md). Please read it to ensure a welcoming and inclusive environment for everyone.

# WebSage AI — Intelligent Webpage Summarizer

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Python: 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688.svg)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/Frontend-React%2019-61DAFB.svg)](https://react.dev/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.0%2B-3178C6.svg)](https://www.typescriptlang.org/)
[![Vite](https://img.shields.io/badge/Bundler-Vite-646CFF.svg)](https://vitejs.dev/)
[![Tailwind CSS](https://img.shields.io/badge/Styling-Tailwind%20CSS-38B2AC.svg)](https://tailwindcss.com/)
[![AI Provider](https://img.shields.io/badge/AI%20Provider-Groq%20LPU-f55036.svg)](https://groq.com/)
[![Cost: ₹0](https://img.shields.io/badge/Cost-%E2%82%B90%20Free%20Tier-success.svg)](#zero-cost-budget-constraint)

> A lightweight, security-hardened full-stack application that transforms any public article or documentation webpage into an instant, concise 100–200 word summary using high-speed AI inference.

---

## 📖 Table of Contents
- [Overview](#-overview)
- [Key Features](#-key-features)
- [System Architecture](#-system-architecture)
- [Tech Stack](#-tech-stack)
- [Prerequisites](#-prerequisites)
- [Local Installation & Setup](#-local-installation--setup)
- [Running the Application](#-running-the-application)
- [Running Automated Tests](#-running-automated-tests)
- [API Contract & Specifications](#-api-contract--specifications)
- [Security Defenses](#-security-defenses)
- [Zero-Cost Budget Constraint](#-zero-cost-budget-constraint)
- [Deployment Guide](#-deployment-guide)
- [Project Documentation](#-project-documentation)
- [Contributing & Code of Conduct](#-contributing--code-of-conduct)
- [License](#-license)

---

## 🌟 Overview

Users often need key takeaways from dense articles, news reports, and documentation without reading through thousands of words or navigating web clutter. 

**WebSage AI** accepts a publicly accessible URL, fetches the page using defense-in-depth security controls, strips boilerplate HTML (scripts, styles, navigation, ads), extracts readable content, and invokes an AI inference engine to deliver an objective synthesis in seconds.

---

## ✨ Key Features

* **Strict SSRF Mitigation:** Pre-request DNS resolution with blocking of private (RFC 1918), loopback, link-local (cloud metadata `169.254.169.254`), multicast, reserved, and CGNAT (`100.64.0.0/10`) IP ranges.
* **DNS Rebinding Defense:** Outbound IP connection pinning binds the TCP socket exclusively to the pre-validated IP address, eliminating Time-of-Check to Time-of-Use (TOCTOU) DNS manipulation.
* **Redirect Revalidation:** Enforces a maximum of 3 redirect hops, re-validating the resolved IP on every hop before connecting.
* **Streaming Byte Cap:** Streams downloaded HTML and aborts immediately if the body exceeds 2 MiB, mitigating Denial-of-Service (DoS) and decompression bombs.
* **Clean Text Extraction:** Uses BeautifulSoup4 to strip non-content tags (`<script>`, `<style>`, `<nav>`, `<footer>`, `<aside>`) and limits extracted text to 20,000 characters.
* **Zero Mandatory Cost:** Designed to run 100% free using Groq's Free Tier (`openai/gpt-oss-20b`) with a deterministic offline mock provider for automated tests.
* **Modern Responsive UI:** Polished dark-mode interface built with React 19, TypeScript, Tailwind CSS, Lucide icons, keyboard navigation, and one-click clipboard copying.

---

## 🏛️ System Architecture

```text
[ User / Browser ]
        │  (HTTP / HTTPS)
        ▼
[ React 19 + TypeScript SPA (Vite) ]
        │  POST /api/summarize { "url": "https://..." }
        ▼
[ FastAPI Backend API ]
        │
        ├─► [ 1. SSRF Validation & DNS Check ]
        │         Blocks private, loopback, link-local & CGNAT IPs
        │
        ├─► [ 2. Outbound Pinned Fetcher (HTTPX) ]
        │         Connects to validated public IP (DNS rebinding safe)
        │         Enforces 2 MiB streaming limit & 10s timeout
        │
        ├─► [ 3. HTML Content Extractor (BeautifulSoup4) ]
        │         Strips scripts, styles, boilerplate; bounds text to 20k chars
        │
        └─► [ 4. AI Summarizer Service (Groq API) ]
                  Sends untrusted-isolated prompt to Groq (openai/gpt-oss-20b)
                  Falls back to mock provider in development/test
        │
        ▼
[ JSON Summary Response ] ──► Rendered on UI with character count & source host
```

---

## 🛠️ Tech Stack

| Layer | Technology | Purpose |
| :--- | :--- | :--- |
| **Frontend** | React 19, TypeScript, Vite | Fast, responsive single-page application |
| **Styling** | Tailwind CSS v4, Lucide React | Modern dark aesthetic and accessible components |
| **Backend** | Python 3.10+, FastAPI, Pydantic v2 | High-performance asynchronous REST API |
| **HTTP Client** | HTTPX, HTTPCore | Asynchronous streaming fetcher with custom IP pinning |
| **HTML Parser** | BeautifulSoup4 | Structured HTML parsing and boilerplate removal |
| **AI Provider** | Groq Free Plan (`openai/gpt-oss-20b`) | Ultra-fast LPU text summarization |
| **Testing** | Pytest, Pytest-Asyncio | Automated unit, security, and integration tests |

---

## 📋 Prerequisites

Ensure you have the following installed on your machine:
* **Python:** Version `3.10` or higher (verified on Python 3.14)
* **Node.js:** Version `18.0` or higher (verified on Node.js v24)
* **npm:** Version `9.0` or higher (verified on npm 11)
* **Git:** Version `2.x`

---

## 🚀 Local Installation & Setup

### 1. Clone the Repository
```bash
git clone https://github.com/<your-username>/websage-ai.git
cd websage-ai
```

### 2. Backend Setup
```bash
# Navigate to backend directory
cd backend

# Create and activate a virtual environment (optional but recommended)
python -m venv venv
# Windows:
venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create your local environment configuration from template
cp .env.example .env
```

### 3. Frontend Setup
```bash
# In a new terminal, navigate to frontend directory
cd frontend

# Install frontend dependencies
npm install
```

---

## 💻 Running the Application

### Start Backend API Server
```bash
cd backend
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```
* Backend API will be available at: `http://127.0.0.1:8000`
* Interactive API docs (Swagger): `http://127.0.0.1:8000/docs`
* Health check: `http://127.0.0.1:8000/health`

### Start Frontend Development Server
```bash
cd frontend
npm run dev
```
* Frontend application will be available at: `http://localhost:5173`
* Vite automatically proxies `/api` and `/health` requests to `http://127.0.0.1:8000`.

---

## 🧪 Running Automated Tests

### Backend Test Suite (Pytest)
Run all 26 unit, security, and integration tests:
```bash
python -m pytest backend/tests -v -c backend/pytest.ini
```

### Frontend Production Build Verification
Verify TypeScript types and create the production bundle:
```bash
cd frontend
npm run build
```

---

## 📡 API Contract & Specifications

### `POST /api/summarize`
Extracts readable text from a public HTML webpage and returns an AI summary.

#### Request Body
```json
{
  "url": "https://example.com/article"
}
```

#### Success Response (`200 OK`)
```json
{
  "summary": "A concise, objective summary of the webpage content...",
  "source_url": "https://example.com/article",
  "source_host": "example.com",
  "extracted_characters": 3200
}
```

#### Error Response (`4xx / 5xx`)
```json
{
  "error": {
    "code": "SSRF_BLOCKED",
    "message": "Access to private, loopback, or internal network destinations is prohibited."
  }
}
```

#### HTTP Status Code Mapping
| Status Code | Error Code | Description |
| :--- | :--- | :--- |
| **`200 OK`** | — | Webpage summarized successfully. |
| **`400 Bad Request`** | `INVALID_URL` / `INVALID_REQUEST` / `SSRF_BLOCKED` | Malformed URL, missing fields, or internal IP target. |
| **`413 Content Too Large`** | `PAYLOAD_TOO_LARGE` | Downloaded HTML body exceeded the 2 MiB streaming limit. |
| **`415 Unsupported Media Type`** | `UNSUPPORTED_CONTENT` | Response is not HTML (e.g. PDF, image, audio). |
| **`422 Unprocessable Entity`** | `INSUFFICIENT_CONTENT` | Webpage contains fewer than 50 readable characters. |
| **`429 Too Many Requests`** | `RATE_LIMIT_EXCEEDED` | Upstream AI provider quota reached. |
| **`502 Bad Gateway`** | `UPSTREAM_ERROR` / `AI_PROVIDER_ERROR` | Target site returned error or AI provider failed. |
| **`504 Gateway Timeout`** | `UPSTREAM_TIMEOUT` / `AI_TIMEOUT` | Web fetch (>10s) or AI inference (>30s) timed out. |

### `GET /health`
Returns minimal server health status without exposing environment configuration.
```json
{
  "status": "ok"
}
```

---

## 🛡️ Security Defenses

1. **SSRF Isolation:** URLs targeting `localhost`, `127.0.0.0/8`, `10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`, link-local (`169.254.0.0/16`), cloud metadata (`169.254.169.254`), CGNAT (`100.64.0.0/10`), documentation IPs, or IPv4-mapped IPv6 are strictly rejected.
2. **DNS Rebinding Prevention:** The outbound TCP connection is pinned to the verified IP address via `PinningTransport`, avoiding TOCTOU socket re-lookups while preserving full TLS certificate and SNI validation.
3. **Redirect Revalidation:** Redirect targets are re-checked at every hop; redirecting to internal IP spaces is blocked immediately.
4. **Credential Isolation:** The AI key is backend-only. Never bundled in frontend code, client assets, or logs.
5. **Prompt Injection Guardrails:** Webpage text is treated as untrusted data; the system prompt explicitly commands the model to disregard instructions embedded within scraped pages.
6. **No Stack Trace Leakage:** Unhandled exceptions return sanitized error JSON without leaking internal filepaths or stack traces.

---

## 💰 Zero-Cost Budget Constraint

WebSage AI is architected with a strict **₹0 budget constraint**:
* **Groq Free Plan:** Provides generous free inference quotas on active production models (30 RPM, 8,000 TPM, 200,000 TPD). No credit card required.
* **Render Free Web Service:** 750 free instance hours per month with automatic spin-down after 15 minutes of inactivity.
* **Vercel Hobby Tier:** 100 GB/month free bandwidth for the React SPA.
* **Mock Provider:** Used automatically for tests and development without consuming live API tokens.

---

## 🚀 Deployment Guide

### Backend on Render (Free Tier)
1. Create a new **Web Service** on [Render](https://render.com/).
2. Connect your GitHub repository.
3. Set the following settings:
   * **Root Directory:** `backend`
   * **Runtime:** `Python 3`
   * **Build Command:** `pip install -r requirements.txt`
   * **Start Command:** `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
4. In **Environment Variables**, add:
   * `ENVIRONMENT`: `production`
   * `GROQ_API_KEY`: `<your_groq_api_key>`
   * `GROQ_MODEL`: `openai/gpt-oss-20b`
   * `USE_MOCK_AI`: `false`
   * `CORS_ORIGINS`: `https://your-frontend.vercel.app`

### Frontend on Vercel (Hobby Tier)
1. Import the repository on [Vercel](https://vercel.com/).
2. Set the following settings:
   * **Root Directory:** `frontend`
   * **Framework Preset:** `Vite`
   * **Build Command:** `npm run build`
   * **Output Directory:** `dist`
3. In **Environment Variables**, add:
   * `VITE_API_BASE_URL`: `https://your-backend.onrender.com`

---

## 📚 Project Documentation

The approved, frozen Requirements v1.2 specification is preserved in the `docs/` directory:
* [docs/requirements.md](docs/requirements.md) — Scope, functional specifications, and API design.
* [docs/acceptance-criteria.md](docs/acceptance-criteria.md) — Observable criteria and verification matrix.
* [docs/security.md](docs/security.md) — Security baseline, SSRF mitigations, and resource limits.

---

## 🤝 Contributing & Code of Conduct

Contributions, bug reports, and suggestions are welcome! Please read our:
* [CONTRIBUTING.md](CONTRIBUTING.md) — Development workflow, testing standards, and pull request procedures.
* [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) — Community guidelines and standards of behavior.
* [SECURITY.md](SECURITY.md) — Vulnerability reporting and disclosure policy.

---

## 📄 License

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details.

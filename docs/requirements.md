# WebSage AI — Product Requirements

- **Version:** 1.2
- **Status:** Proposed baseline — pending final approval
- **Product:** WebSage AI (working name)

## 1. Problem statement
Users often want the key ideas from a webpage without reading the entire article. WebSage AI accepts a publicly accessible webpage URL, extracts readable text from supported HTML pages, asks an AI provider to summarize that text, and presents the result in a simple web interface.

## 2. Product objective
Deliver a small, polished, deployable full-stack application demonstrating frontend development, backend API design, HTML text extraction, AI integration, validation, error handling, security awareness, testing, and clear documentation.

## 3. Primary user flow
1. User pastes a URL and selects **Summarize**.
2. Frontend performs basic URL syntax validation and shows a loading state.
3. Backend validates the URL and safely fetches a supported HTML page.
4. Backend extracts readable text and sends bounded text to the configured AI provider.
5. Frontend displays a concise summary and source hostname, or a helpful error.

## 4. Scope

### Must-have
- Responsive, keyboard-accessible single-page interface.
- URL input and Summarize button.
- Server-side URL validation; client-side checks are only for UX.
- `POST /api/summarize` with a documented JSON contract.
- Fetch ordinary public HTML pages without bypassing bot protection.
- Remove scripts, styles, and common non-content elements where practical.
- Use one AI provider with a verified free-tier option for this task.
- Keep AI credentials exclusively on the backend.
- Loading, success, validation, unsupported-content, timeout, scraping-failure, and AI-provider error states.
- Environment-configured API base URL for local and deployed frontend builds.
- Automated backend tests for core success and failure paths.
- Public GitHub repository, README, `.env.example`, and deployed application.

### Should-have
- Display source hostname and extracted character count.
- Clear prior result when a new request starts.
- Copy-summary action if it does not delay core requirements.
- Minimal health endpoint.
- Basic request rate limiting if practical on the chosen host.

### Out of scope for v1
- Accounts, authentication, database, saved history, or cloud persistence.
- Browser extension or mobile app.
- PDF, image, or file uploads.
- CAPTCHA or bot-protection bypass.
- Guaranteed support for JavaScript-rendered, authenticated, or paywalled pages.
- Multiple working AI providers, streaming responses, background queues, or analytics.

## 5. Proposed technology baseline

| Layer | Proposed choice |
|---|---|
| Frontend | React + TypeScript + Vite |
| Styling | Tailwind CSS |
| Backend | Python + FastAPI + Pydantic |
| HTTP client | HTTPX |
| HTML parser | BeautifulSoup4 |
| AI | Gemini or Groq, final choice after provider verification |
| Configuration | Environment variables; local backend `.env` |
| Tests | Pytest; mock external HTTP and AI calls |
| Version control | Git + public GitHub repository |
| Deployment | Vercel frontend + Render backend, subject to current plan limits |

## 6. AI provider selection gate
No provider is selected yet. Before implementation:
1. Check official developer documentation for Gemini and Groq.
2. Verify free-tier availability for the intended account and region.
3. Check rate/token limits, model availability, billing requirements, and applicable data-use terms.
4. Confirm the provider supports the required text summarization request.
5. Select one provider and record the decision before coding.

A consumer subscription does not automatically imply API access or free API quota. Never add a real key to source control or frontend configuration.

## 7. API contract

### `POST /api/summarize`

Request:

```json
{
  "url": "https://example.com/article"
}
```

Success response:

```json
{
  "summary": "A concise summary of the webpage.",
  "source_url": "https://example.com/article",
  "source_host": "example.com",
  "extracted_characters": 3200
}
```

Error response:

```json
{
  "error": {
    "code": "UNSUPPORTED_CONTENT",
    "message": "This page does not contain readable HTML content."
  }
}
```

Suggested status mapping:
- `400` — malformed or unsupported URL/input.
- `413` — request or fetched page exceeds a configured limit.
- `415` — unsupported response content type.
- `422` — insufficient readable text.
- `429` — rate limit exceeded, if implemented.
- `502` — upstream webpage or AI provider failure.
- `504` — upstream timeout.

Keep error codes consistent. Never return stack traces, credentials, internal IPs, or raw provider internals.

### `GET /health`
Returns minimal status such as `{"status":"ok"}` without sensitive configuration.

## 8. Summarization behavior
- Summarize extracted webpage text, not raw HTML.
- Aim for approximately 100–200 words; output length may vary.
- Do not add claims unsupported by the extracted page text.
- Treat webpage content as untrusted and instruct the model to ignore embedded instructions and summarize informational content only.
- Enforce the AI input-text limit before calling the provider.
- Return a helpful error when extracted text is empty or too short.
- Do not claim that the summary has been independently fact-checked.

## 9. Proposed security and reliability limits
Initial limits to validate through tests:
- Maximum URL length: **2,048 characters**.
- Maximum redirects: **3**, validating every redirect destination.
- Maximum downloaded HTML body: **2 MiB**, enforced while streaming.
- Maximum extracted text sent to AI: **20,000 characters**.
- Web fetch overall timeout: **10 seconds**, with connection/read timeouts as appropriate.
- AI provider timeout: **30 seconds**.
- Only HTTP/HTTPS; reject URL credentials and non-public destinations, including localhost, private, loopback, link-local, multicast, unspecified, and reserved IP ranges.
- Validate DNS results and resolved IPs; account for redirect and DNS-rebinding risks as far as the chosen client allows. DNS pre-checks alone do not fully eliminate SSRF.
- Keep AI credentials backend-only.
- Restrict CORS to local development and the actual deployed frontend origin.
- Never commit `.env` or real keys.
- Avoid logging full page contents or credentials.
- Add a modest rate limit if practical.

## 10. UX requirements
- Main action is obvious and keyboard accessible.
- Submit action is disabled during processing.
- Loading remains visible until success or failure.
- Render summaries as text, not trusted HTML.
- Keep the layout usable on mobile and desktop.
- Explain failures in plain language and allow retry where appropriate.
- Never show a result as successful before receiving a successful backend response.

## 11. Handover and deployment
- Frontend and backend run independently in local development.
- Production frontend uses a configured deployed API base URL.
- Production backend receives the AI key through host environment/secret configuration.
- README covers prerequisites, exact commands, `.env` location, environment variables, tests, API contract, deployment setup, and known limitations.
- `.env.example` contains placeholders only.
- Verify the deployed app with at least one supported public HTML page before submission.

## 12. Assumptions and change control
This is a demonstration app, not a general-purpose crawler. Target pages are public and accessible without login. Free-tier quotas and hosting plans may change; some sites block automated requests or provide little readable HTML. These cases must fail gracefully.

This is a proposed v1.2 baseline pending approval. Major scope changes, new infrastructure, persistence, authentication, or a changed user flow require explicit review. Small bug fixes and visual refinements do not require a requirements revision.

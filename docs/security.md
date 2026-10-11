# WebSage AI — Security Baseline

- **Version:** 1.2
- **Status:** Proposed baseline — pending final approval

This is a practical security baseline for a small demonstration app, not a formal certification.

## 1. SSRF prevention
The backend fetches user-supplied URLs, so an attacker may try to reach internal services or cloud metadata endpoints.

- Parse and normalize URLs using a well-tested URL parser.
- Permit only HTTP/HTTPS; reject embedded credentials and malformed hostnames.
- Resolve hostnames and reject non-public IPv4/IPv6 destinations, including private, loopback, link-local, multicast, unspecified, and reserved ranges.
- Limit redirects to three and revalidate every destination before connecting.
- Enforce the 2 MiB response-body limit while streaming.
- Apply a 10-second overall webpage-fetch timeout and connection/read timeouts.
- Accept only HTML-compatible content types.
- Do not allow caller-supplied arbitrary headers, proxy settings, or alternate network routes.

**Important:** DNS pre-validation alone does not fully prevent DNS rebinding or time-of-check/time-of-use issues if the HTTP client performs a fresh DNS lookup on connect. Review and test actual client behavior; do not claim perfect SSRF protection based only on a preliminary lookup.

## 2. Secrets
- Local backend secrets belong in `backend/.env`.
- Ignore `.env` in Git.
- Commit `backend/.env.example` with placeholders only.
- Store deployed credentials in hosting-provider environment/secret settings.
- Never expose the AI key through frontend variables or bundles.
- Never log or return credentials.

## 3. Resource limits
Initial proposed values:
- URL length: 2,048 characters.
- Redirects: 3 maximum.
- Downloaded HTML: 2 MiB maximum, enforced during streaming.
- Extracted text sent to AI: 20,000 characters maximum.
- Web fetch overall timeout: 10 seconds.
- AI timeout: 30 seconds.
- Request a concise summary, approximately 100–200 words.

Change limits only with a documented reason and relevant tests.

## 4. HTML and AI safety
- Parse HTML as data; never execute scripts.
- Render summaries as plain text.
- Treat webpage content as untrusted.
- Prompt the model to ignore instructions embedded in the webpage and summarize informational content only.
- Do not claim AI output is independently verified.

## 5. CORS, errors, and logging
- Allow only deployed frontend and necessary local origins.
- Do not combine wildcard CORS with credentials.
- Return structured errors without stack traces, secrets, internal addresses, or raw provider internals.
- Do not log full webpage bodies or API keys.
- Health checks must not reveal sensitive configuration.

## 6. Verification checklist
- [ ] Reject non-HTTP/HTTPS schemes and URLs containing credentials.
- [ ] Reject localhost and non-public IP destinations.
- [ ] Reject redirects to blocked destinations.
- [ ] Enforce redirect, byte, text, and timeout limits.
- [ ] Verify errors do not leak internal details.
- [ ] Verify keys are absent from frontend assets and Git history.
- [ ] Test missing-key, rate-limit, timeout, and malformed AI responses.

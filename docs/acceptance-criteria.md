# WebSage AI — Acceptance Criteria

- **Version:** 1.2
- **Status:** Proposed baseline — pending final approval

A criterion is complete only after it has been tested or otherwise verified.

## A. Core flow
- [ ] User can submit a public HTTP/HTTPS webpage URL.
- [ ] Frontend sends the URL to `POST /api/summarize`.
- [ ] Loading state is visible and submission is disabled while processing.
- [ ] Success displays the summary and source hostname.
- [ ] User can submit another URL without refreshing.
- [ ] Frontend handles documented success/error response shapes.

## B. Validation and scraping
- [ ] Empty, malformed, overlong, and unsupported-scheme URLs are rejected.
- [ ] Localhost and non-public IP destinations are rejected.
- [ ] Redirects are limited to three hops; each target is revalidated.
- [ ] Supported public HTML pages yield readable text.
- [ ] Scripts, styles, and common non-content elements are removed where practical.
- [ ] Non-HTML responses return a controlled error.
- [ ] Empty or insufficient extracted text returns a helpful error.
- [ ] Slow fetches time out.
- [ ] Downloaded bodies over 2 MiB are stopped while streaming.
- [ ] Text sent to AI is capped at 20,000 characters.

## C. AI behavior
- [ ] AI receives extracted text, not raw HTML.
- [ ] Prompt instructs model to summarize and ignore embedded webpage instructions.
- [ ] Successful output follows the documented API contract.
- [ ] Missing credentials, rate limits, provider timeouts, and malformed responses return controlled errors.
- [ ] Normal automated tests mock AI calls and require no real API key.
- [ ] AI key is absent from frontend assets, API responses, logs, and Git history.

## D. Security
- [ ] Only HTTP/HTTPS URLs without embedded credentials are accepted.
- [ ] Private, loopback, link-local, multicast, unspecified, and reserved destinations are blocked.
- [ ] Redirect destinations are validated before following.
- [ ] Fetch, AI, response-size, URL-length, and extracted-text limits are enforced.
- [ ] CORS permits intended origins only.
- [ ] `.env` and actual credentials are ignored by Git.
- [ ] Errors disclose no stack traces, credentials, internal IPs, or raw provider internals.
- [ ] Summaries render as text, not injected HTML.

## E. UI and accessibility
- [ ] Main flow works on common desktop and mobile widths.
- [ ] Input and submit action are keyboard accessible.
- [ ] Loading, success, and failure states are distinguishable.
- [ ] Duplicate submissions are prevented during processing.
- [ ] Summary is readable and selectable/copyable.
- [ ] Error messages are understandable and allow retry where appropriate.

## F. Tests and delivery
- [ ] Backend tests cover validation, success, scrape failure, timeout, AI failure, and SSRF-sensitive cases.
- [ ] Normal tests do not require live websites or real AI credentials.
- [ ] README includes exact frontend/backend setup and run commands.
- [ ] README identifies backend `.env` location and required variables.
- [ ] `.env.example` has placeholders only.
- [ ] Public repository contains no secrets.
- [ ] Deployed frontend and backend communicate.
- [ ] A supported public webpage succeeds in the deployed app.
- [ ] Known limitations are documented.
- [ ] GitHub and live URLs are ready for submission.

## Release gate
Do not submit until the core flow, secret handling, basic SSRF protections, tests, README, public repository, and deployed application are verified. Document incomplete optional features as limitations.

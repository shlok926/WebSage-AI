# Security Policy

The WebSage AI team takes the security of our application, infrastructure, and users seriously. This document outlines how to report vulnerabilities and describes our security baseline.

---

## 🛡️ Supported Versions

Only the latest commit on the `main` branch is actively supported with security updates.

| Version / Branch | Supported          |
| ---------------- | ------------------ |
| `main`           | :white_check_mark: |
| Older releases   | :x:                |

---

## 🚨 Reporting a Vulnerability

If you discover a security vulnerability or potential exposure in WebSage AI, **please do NOT report it publicly via GitHub Issues, Discussions, or social media**.

Instead, please use one of the following confidential channels:

1. **GitHub Private Security Advisory (Preferred):**
   * Navigate to the repository's **Security** tab.
   * Click **Advisories** → **Report a vulnerability**.
   * Fill out the advisory draft with reproducible steps and technical details.

2. **Security Contact:**
   * If private advisories are unavailable, please open an issue requesting a private security contact channel without disclosing the vulnerability details.

### What to Include in Your Report
To help us triage and resolve the issue quickly, please provide:
* A detailed description of the vulnerability.
* Steps to reproduce, proof-of-concept (PoC) code, or an HTTP request trace.
* The affected component (`fetcher.py`, `extractor.py`, `ai/`, etc.).
* Potential impact and attack scenarios.
* Any suggested remediation or patches, if available.

### Response Timeline
* **Acknowledgement:** Within 48 hours of initial receipt.
* **Triage & Assessment:** Within 7 days with an estimated remediation timeline.
* **Coordinated Disclosure:** We kindly request that you allow reasonable time for remediation before publishing details publicly.

---

## 🔒 Security Baseline & Defenses

WebSage AI is engineered with defense-in-depth principles specifically designed to mitigate web-crawling and AI-inference threats:

### 1. Server-Side Request Forgery (SSRF) Protection
* All target URLs must use `http` or `https` schemes.
* Pre-request DNS resolution parses and evaluates all IP addresses against strict public IP criteria (`ipaddress.IPv4Address` / `ipaddress.IPv6Address`).
* The following address ranges are strictly blocked:
  - Private networks (RFC 1918: `10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`)
  - Loopback addresses (`127.0.0.0/8`, `::1`)
  - Link-local and cloud metadata addresses (`169.254.0.0/16`, including `169.254.169.254`, `fe80::/10`)
  - Shared CGNAT address spaces (`100.64.0.0/10`)
  - Multicast, broadcast, documentation (`RFC 5737`, `RFC 3849`), and reserved blocks
  - IPv4-mapped IPv6 representations (`::ffff:x.x.x.x`) are unmapped and validated against IPv4 rules.

### 2. DNS Rebinding & TOCTOU Defense
* Outbound connections use a custom transport (`PinningTransport` + `httpcore.AsyncNetworkBackend`) that explicitly pins the socket to the pre-validated IP address.
* TLS certificate verification and SNI (`server_hostname`) are strictly preserved, preventing MITM while defeating DNS rebinding.

### 3. Redirect Revalidation
* HTTP redirects are not followed automatically by the underlying transport.
* Each redirect target URL is independently inspected, parsed, DNS-resolved, and re-validated before establishing a new pinned connection (maximum 3 hops).

### 4. Denial-of-Service & Resource Limits
* **Body Size Cap:** Response content is read in chunks and aborted immediately if the streamed payload exceeds **2 MiB (2,097,152 bytes)**.
* **Timeout Limits:** All outbound requests enforce a hard **10-second total timeout**.
* **Extraction Boundary:** Extracted clean text is capped at **20,000 characters** before reaching the AI summarizer.

### 5. AI Prompt Injection & Content Isolation
* Untrusted webpage text is strictly quarantined within clearly delineated boundaries in the system prompt.
* System instructions prohibit the AI model from following instructions embedded within the target webpage.

For in-depth security documentation, refer to [docs/security.md](docs/security.md).

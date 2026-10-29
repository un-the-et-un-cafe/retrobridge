---
name: Adapter proposal
about: Describe an authorized interface, security boundary and test plan
---

## Purpose and status
- User need and proposed input/output:
- Design-only or implemented? What explicitly does not work?
- Eligible device profiles and bandwidth/encoding constraints:

## Rights and interface limits
- Official interface/documentation and access requirements:
- Content rights, attribution and redistribution restrictions:
- Provider API/account limits, rate limits and applicable policy review:
- Authorization needed before any live access:
- Third-party dependency/code provenance and license review status:

## Threat model
- Trusted modern gateway versus untrusted legacy/client boundary:
- Authentication/authorization design (no shared assistant account):
- Secrets isolation; private-content access boundaries:
- Allowed hosts/routes, input bounds, sanitation and output escaping:
- Plaintext links and encryption limitations (no unsupported E2EE claim):
- Retention, deletion, consent and unsubscribe needs, if relevant:
- Abuse, malformed input, replay, failure and offline behavior:

## Verification and maintenance
- Synthetic fixtures, positive/negative tests and reproducible steps:
- What has actually been tested, on which revision:
- Human review/release gates and rollback:
- Proposed maintainer and bounded maintenance scope:

## Guardrails
- [ ] No private data, credentials, arbitrary-URL fetch or request execution.
- [ ] No live account connection, spend, listener or sending without authorization.
- [ ] A business API is not represented as personal-account synchronization.
- [ ] A proposal or mockup is not represented as a working integration.

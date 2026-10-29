# Security reporting and pilot boundaries

This pre-release prototype is offline and synthetic-only. It has not received an
independent security audit and is not approved for real user data or public service.
The role functions demonstrate policy; they are not authentication.

## Report privately

Do not file a public issue or disclose exploit details in a community discussion.
A dedicated vulnerability-reporting address and external reporting channel have
**not** been configured. No address is implied by this file.

For people with an existing verified relationship to this project, use your existing
verified private communication with the owner to request a secure reporting route.
Initially send only a short non-sensitive description and affected version. Do not
send secrets, personal data, actual user communications or weaponized payloads.
If no verified private route is available, ask the owner to establish one before
transmitting details. Maintainers must verify the chosen route's privacy; repository visibility does not make attached services or issue channels private.

Before inviting outside contributors or launching publicly, configure and verify
a private reporting channel, triage ownership, response expectations and a
coordinated-disclosure process. This document makes no response-time commitment.

## Maintainer handling

Limit access to authorized reviewers, reproduce with synthetic data, avoid running
untrusted commands, redact evidence, and track the affected revision and fix tests.
Security investigation does not grant access to private user content or new accounts.
Obtain owner authorization for containment steps outside existing task authority.
See README for the gateway/legacy-client boundary and backup trust assumptions.

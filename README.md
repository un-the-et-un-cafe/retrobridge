<picture>
  <source media="(prefers-color-scheme: dark)" srcset="assets/retrobridge-dark.svg">
  <source media="(prefers-color-scheme: light)" srcset="assets/retrobridge-light.svg">
  <img alt="Retrobridge — Useful connections for classic computers." src="assets/retrobridge-light.svg" width="960">
</picture>

# Retrobridge

**Keep classic computers useful—without pretending they are modern browsers.**

Retrobridge explores small, understandable adapters between today's information
and the text-first interfaces older computers can handle. The aim is a growing,
evidence-backed catalog of devices and adapters—not a collection of compatibility
claims nobody has tested.

**Current stage: offline prototype.** The runnable examples use synthetic local
fixtures. No accounts are connected, no network service runs, and nothing is sent
or collected. The first-party software is [MPL-2.0 licensed](#licensing);
branding is separate. Public source availability is not a production release.

[Quick start](#quick-start) · [Adapters](#adapter-catalog) · [Architecture](#architecture)
· [Roadmap](#roadmap) · [Contributing](#contributing) · [Security](#security-and-privacy)

## What you can do today

- Browse three **synthetic device archetypes** and their capability constraints.
- Convert local RSS fixture titles or text lines into an **inert IRC-style transcript**.
- Generate a static **HTML 3-friendly catalog**, without JavaScript or CSS dependencies.
- Choose **Paper & Ink** or **Blue Thread**, two simple original palette choices.
- Inspect consent schemas and an inert, role-based suggestion-review demonstration.
- Run the tests and create a checksum-verified, source-only recovery bundle.

No real device, emulator or vintage browser is certified yet. Live feeds, real IRC,
email, Atom, authentication and messaging integrations are **not implemented**.

## Quick start

### Requirements

- **Python 3.12.14 is verified** for this checkpoint. The code targets Python 3.11+;
  other versions have not been tested here.
- No third-party Python packages are required.
- Git is needed for the backup/restore commands, not for running the demo.
- Examples below use a POSIX shell and assume you are in the repository root.

```sh
python3 -m unittest discover -s tests -v
python3 retrobridge.py catalog
python3 retrobridge.py rss
python3 retrobridge.py text
```

Example RSS output:

```text
[retro-news] Volunteer terminal test day (fictional)
[retro-news] Plain text catalog draft ready
```

Generate a catalog and open the resulting file locally:

```sh
mkdir -p preview
python3 retrobridge.py html > preview/catalog.html
python3 retrobridge.py html --theme blue-thread > preview/catalog-blue.html
```

These commands read fixed fixtures under `fixtures/`; they do not fetch URLs,
connect to IRC, or start a server. Keep the demo offline and use synthetic data.
A future local preview must bind to loopback, not a public interface.

## Adapter catalog

| Adapter | Input → output | Current reality |
| --- | --- | --- |
| RSS transcript | Local RSS titles → ASCII transcript | Implemented offline; no feed fetching or IRC connection |
| Text transcript | Local text lines → ASCII transcript | Implemented offline; no command execution |
| Catalog renderer | Synthetic profiles → basic HTML | Implemented offline; not vintage-browser certified |
| Modern gateway | Authorized modern interfaces → bounded legacy formats | Architecture only |
| Mail / community messaging | Authorized provider data → constrained client views | Concepts only; no accounts, transport or sending |
| WhatsApp Business | Potential official business interface | Not implemented; no personal-account synchronization promised |

The prototype does not include a personal WhatsApp connector. Access to an official
business API would not establish personal-account synchronization or permission to
relay private messages. Every future adapter needs its own rights, policy and
security review before live use.

## Devices and support evidence

The target is computers **at least 30 years old**, determined by the exact model's
introduction date—not a product family's age, a purchase date or a broad year label.
The intended policy rolls forward with an explicitly recorded assessment date.

**This prototype pins its assessment to 2026-10-29:** eligible dates are on or before
**1996-10-29**. A model introduced on 1996-10-30 does not qualify for that snapshot.
The implementation does not advance the cutoff automatically. A later assessment
must deliberately update the date, cutoff and boundary tests; a general rolling-date
calculator remains a roadmap item.

| Evidence label | What it means |
| --- | --- |
| Proposed | Exact model, dated source, capability profile and a test plan |
| Emulator-tested | Reproducible results for a named emulator, configuration and revision |
| Hardware-tested | Reproducible results on the exact physical model and configuration |
| Maintained | An explicit maintainer and regression scope; not a compatibility guarantee |

**Today:** the 1985 text terminal, 1993 dial-up workstation and 1996 early-web client
are invented archetypes. Host unit tests do not establish emulator or hardware
support. See the [support matrix](docs/SUPPORT_MATRIX.md) for evidence requirements,
limitations and stale/retired status handling.

## Client library and ongoing improvement

The planned client is a **Steam-like library for adapters**, not a store or an
automatic converter for arbitrary modern apps. Each adapter has a detail page
showing its purpose, supported capabilities, exact device/OS evidence, version,
setup guide and lifecycle state: proposed, available, active, paused, update
available, unsupported or retired. These are planned UI states, not current claims.

Selecting an adapter may activate only an implemented, reviewed and authorized
integration through a trusted modern gateway. WhatsApp, Telegram and other service
names are examples of possible catalog entries, not claims that working adapters
exist or that personal-account access is permitted. Unsupported entries must remain
clearly unavailable. Selection never authorizes arbitrary code generation, new
account access or execution of unreviewed downloads.

The next functional client release must demonstrate **one useful permitted
adapter**, a runnable client for one declared target, explicit support evidence,
and a reviewed authenticated update/recovery design. Updates require verified
provenance and integrity, staged rollout, failure recovery and rollback—not blind
automatic daily installation. The current offline prototype implements none of
these live-client, gateway or update-service capabilities.

Improvement priorities combine security findings, reproducible usability feedback
and, only with explicit opt-in, minimal aggregate usage signals. No message
contents, credentials, religious attributes or device serial numbers belong in
telemetry. Aggregate measurement still needs a documented consent, minimization,
retention and deletion design; no telemetry collection is running today.
**Security fixes outrank popularity.** UI/UX and adapter demand inform the remaining
queue, with reviewed tests and staged releases before changes reach users.

Continuous improvement is a development goal, not a claim of unattended 24/7
coverage, an operational SLA or guaranteed release cadence. Work and review occur
when resources are actually available; publish evidence of completed changes rather
than implying workers are always running. See the [maintenance and release
specification](docs/GOVERNANCE_AND_ROADMAP.md#maintenance-and-release-specification).

## Architecture

```text
Future authorized modern sources
              |
              v
  Trusted modern gateway             NOT IMPLEMENTED AS A SERVICE
  - credentials and authentication
  - explicit source/interface allowlists
  - policy, consent and rate limits
              |
              v
  Bounded conversion boundary         OFFLINE SUBSET EXISTS
  - untrusted content treated as data
  - sanitation and output escaping
  - minimal plain-text / basic HTML
              |
              v
  Isolated legacy client              NOT HARDWARE-VALIDATED
  - constrained display and transport
  - no secrets or user-request execution
```

The gateway is trusted and can see what it processes. It is **not** a transparent
end-to-end encrypted relay. Plaintext serial, IRC or legacy HTTP legs do not gain
modern encryption merely because an upstream connection uses TLS. Keep legacy
networks isolated and do not pass credentials or private messages to those links.

In the current implementation, fixed local fixtures replace modern sources, and
stdout/static files replace a network transport. There is no daemon, URL fetcher,
public listener, shell-command adapter or deployment configuration.

## Security and privacy

- RSS accepts UTF-8 input up to **64 KiB**, takes at most **20 titles**, and limits
  rendered fields to **240 ASCII characters**. DTDs, entities and NULs are rejected.
- Transcript content is sanitized and prefixed as inert display text. It is not an
  outbound IRC command stream. HTML data is escaped.
- Suggestions remain non-executable even after acceptance. Demonstration role
  functions are **not authentication** and must not be exposed to untrusted callers.
- No shared assistant account, administrative access to private content or execution
  of user requests is provided.
- Feedback/newsletter schemas are design artifacts only. Device/interests fields
  are optional; newsletter consent is explicit and the proposed lifecycle includes
  pending confirmation and unsubscribe. No signup form, database or sender exists.
- Email shape validation is not address verification; real collection requires a
  consent, retention, deletion, abuse-prevention and security design first.

Do not use real user data in this pilot. For vulnerabilities, follow
[SECURITY.md](SECURITY.md). A dedicated external private-reporting channel is not
configured; do not post vulnerability details or secrets in public issues.

## Tests and verification limits

```sh
python3 -m unittest discover -s tests -v
```

The current **12 tests** cover the exact age boundary, catalog filtering, XML
rejection/limits, transcript framing, HTML escaping, both themes, explicit consent,
optional fields, role policy and schema JSON parsing. The source checkpoint also
passes these tests after a clean bundle restore.

They do **not** establish JSON Schema conformance beyond parsing, actual hardware
compatibility, provider compliance, transport encryption, production authorization,
real signup behavior or operational security. No CI status is implied.

## Roadmap

Milestones are acceptance gates, not delivery-date promises. Nothing below is
implemented merely because it appears in this list.

| Milestone | Scope | Done when |
| --- | --- | --- |
| **0 · Reproducible foundation** | Offline examples, clear labels, tests and recovery | Demo commands pass from a clean checkout; source-only backup restores and tests pass. Current baseline, not v1.0. |
| **1 · First real device** | One sourced exact-model profile and explicit rolling-date policy | Date/boundary tests pass; emulator setup and results are reproducible; physical testing is separately labeled. |
| **2 · Adapter contract** | Typed capability descriptions, bounded conversion and failure behavior | One adapter has synthetic positive/negative fixtures, encoding/size budgets, provenance and maintainer-reviewed tests. |
| **3 · Client MVP** | A runnable library client for one deliberately chosen legacy OS | Adapter library/detail views, themes, status, setup guides and feedback access work in a reproducible runnable build; emulator tests pass, with physical-hardware coverage separately reported. No live sending is implied. |
| **4 · Controlled gateway** | One authorized live interface in an isolated test environment | Rights/API review, authentication, secret isolation, allowlists, rate limits and threat-model tests are complete; live access is explicitly approved. |
| **5 · Community readiness** | Contribution terms, evidence review and maintenance | MPL-2.0 contribution provenance is reviewed; private security reporting works; reviewers and support scopes are documented. |
| **6 · v1.0 release candidate** | A deliberately small supported end-to-end path | One useful permitted adapter, exact support evidence, authenticated update/recovery design, security/privacy review, rollback and maintenance ownership are accepted; release is explicitly approved. |

The current Python CLI and static HTML renderer are not the planned native client.
The Client MVP begins after the device and adapter-contract milestones, before
live gateway integration. Provisional target candidates are 68k Macintosh with
System 7.5.x and Windows 95; neither is claimed as supported by this published
prototype. A release must declare its exact tested target and evidence. Feedback
access initially means an offline/local route; any network submission needs a
separate privacy and consent design.

Public repository visibility is not a v1.0 release. New integrations, accounts,
outbound communications and access to user data require their own authorization.

## Contributing

Start with a precise device proposal, a reproducible synthetic test or an adapter
idea whose interface limits are understood. Evidence and small maintainable changes
are more useful than broad unsupported claims.

- [Contribution guide](CONTRIBUTING.md)
- [Device proposal template](.github/ISSUE_TEMPLATE/device-proposal.md)
- [Adapter proposal template](.github/ISSUE_TEMPLATE/adapter-proposal.md)
- [Support evidence matrix](docs/SUPPORT_MATRIX.md)
- [Governance and roadmap](docs/GOVERNANCE_AND_ROADMAP.md)

The contribution guide's permission and licensing requirements apply. First-party
software contributions use MPL-2.0, with provenance and existing notices preserved. Optional themes
never affect permissions or support priority. Do not attach proprietary ROMs,
credentials, serial numbers, network identifiers or personal communications.

## Source backup and recovery

Create a fresh destination for every snapshot; both commands refuse to overwrite
an existing target:

```sh
python3 scripts/backup.py backup /tmp/retrobridge-backup-001
python3 scripts/backup.py restore /tmp/retrobridge-backup-001 /tmp/retrobridge-restored-001
cd /tmp/retrobridge-restored-001
python3 -m unittest discover -s tests -v
```

The explicit allowlist captures reviewed source, docs, synthetic fixtures, schemas,
tests and original SVG branding into a fresh single-commit bundle plus a SHA-256
manifest. It excludes original Git history/config, generated design mockups,
credentials, user data, caches and arbitrary extra files. Review allowlisted content
for secrets: an allowlist cannot detect a secret pasted into a source file.

Restore checks bundle and file hashes, rejects unexpected source trees, and does
not run restored code automatically. Restore only trusted backups: checksums detect
corruption, not replacement of both bundle and manifest. The bundle is not encrypted;
keep it in an authorized durable private location. Local storage and a Git remote
are not substitutes for a tested recovery copy. Scripts do not schedule themselves.

## Repository map

```text
retrobridge.py          Offline adapters, renderer and policy demonstrations
fixtures/              Synthetic catalog, RSS and text inputs
schemas/               Feedback, signup and subscription-state designs
tests/                 Unit tests
scripts/backup.py      Allowlisted snapshot and restore tool
assets/                Original light/dark SVG wordmarks
docs/                  Support evidence and governance
.github/ISSUE_TEMPLATE/ Device and adapter proposal templates
```

## Licensing

The first-party software and accompanying technical documentation are licensed
under **Mozilla Public License 2.0 (MPL-2.0)**. See [LICENSE](LICENSE) for the full
terms and [NOTICE.md](NOTICE.md) for the exact covered paths. Contributions to
Covered Software use the same MPL-2.0 terms; no separate CLA is required here.

MPL-2.0 provides file-level copyleft: distribution of modified Covered Software
requires its covered source to remain available under MPL-2.0. The license also
permits larger works under its conditions; the full text controls.

**Branding is separate:** SVG logos/wordmarks are not included in that software
grant. See [branding terms](assets/BRANDING.md). No trademark registration or
endorsement is implied. Preserve applicable third-party notices and verify rights
before contributing material.

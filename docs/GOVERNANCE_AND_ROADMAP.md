# Governance and staged roadmap

## Decisions and access

The owner approves repository visibility, licensing, collaborators, spending,
account connections, outbound communications and releases. Maintainers review
bounded technical changes and evidence; contributors propose changes. These are
project roles, not a shared assistant login or authority to inspect private content.
No role is weighted by personal identity, theme choice, donations or social ranking. Record decisions, reasons and dissent respectfully.

Accepting a suggestion does not authorize code execution, deployment, contacting
people or accessing their data. New permissions require explicit authorization.
No external collaborators, endorsements or organization affiliations are implied.

## Stage 0 — current offline pilot

- Preserve the offline synthetic prototype and clear concept labels.
- Publish only reviewed neutral source; keep backups private and verified by clean restore.
- Define device/adapter proposals and evidence labels without claiming support.

## Stage 1 — evidence and maintenance

- Choose a small exact-model target using sourced introduction dates.
- Agree legal test environments; execute reproducible emulator tests, then isolated
  physical-hardware tests where equipment and authorization are available.
- Record failure cases, accessibility, encoding and bandwidth constraints.
- Identify willing maintainers; no invented compatibility or response commitments.

## Stage 2 — adapter contract

- Define capability descriptions, bounded conversion and failure behavior.
- Require synthetic positive/negative fixtures, encoding/size budgets, provenance
  and maintainer-reviewed tests for one adapter.

## Stage 3 — Client MVP

- Choose one legacy OS after the first-device and adapter-contract milestones.
- Build an actual runnable library client: adapter library and detail views,
  theme selection, adapter status, setup guides and feedback access.
- Require reproducible build/run instructions and emulator tests. Report physical
  hardware coverage separately; emulator success is not physical certification.
- Start offline with synthetic data; feedback access does not authorize network
  submission. The current Python CLI/static HTML renderer is not this native client.
- Provisional target candidates are 68k Macintosh/System 7.5.x and Windows 95.
  Candidate selection is not a claim of published native source, successful target
  execution or hardware support. Declare exact release scope from actual evidence;
  no delivery date is promised.

## Stage 4 — gated gateway experiments

- Review connector rights/API limits and a concrete threat model before coding.
- Keep credentials on the modern side, legacy outputs minimized/read-only, and
  authentication separate from demonstration role functions.
- Add bounded input/negative tests, private reporting and operational controls.
- Any live accounts, user data, external listener or sending needs separate approval.

## Stage 5 — community readiness

- Review MPL-2.0 contribution provenance and preserve third-party notices.
- Establish private security reporting, reviewers and explicit support scopes.

## Stage 6 — candidate v1.0 release

Release is not achieved merely by adding docs or publishing a repository. Require
explicit owner signoff on scope, licensing/contribution terms, evidence-backed
support labels, security/privacy review, consent/deletion behavior where relevant,
verified backups, maintenance ownership and rollback instructions. Public source visibility is owner-approved; community invitations remain a separate
approval decision.

Any planned organizational invitation may only be considered after the new
platform v1.0 ships and after recipient/content authorization. Do not send
now, activate newsletter addresses, imply endorsement or treat this roadmap as
consent. Newsletter enrollment requires explicit consent and double opt-in.

## Maintenance and release specification

Retrobridge remains a nonprofit project. Its client direction is a Steam-like
adapter library, not arbitrary app conversion or a new parallel product. Each
adapter detail view must disclose capabilities, permissions, supported device/OS
profiles with evidence, version, setup guide and lifecycle status. Planned states
are proposed, available, active, paused, update available, unsupported and retired;
status transitions must be explicit and must not imply unverified compatibility.

Selection activates only an implemented, reviewed, permitted integration via the
modern gateway. A catalog entry for WhatsApp, Telegram or another service is not
permission to access personal accounts, scrape services, generate executable code
or install unreviewed components. Unimplemented or unauthorized entries cannot
activate; explain the missing capability or approval instead.

### Next functional client release gate

- Demonstrate one genuinely useful permitted adapter on one declared client target.
- Document the official/authorized interface and least-privilege gateway boundary.
- Provide reproducible runnable builds, emulator evidence and separately labeled
  physical-device evidence; never equate a mockup or host test with hardware support.
- Review an authenticated update and recovery design: trusted provenance,
  signature/integrity verification, authenticated delivery where supported,
  version/rollback policy, staged rollout, interrupted-update recovery and a known
  good fallback. Isolate legacy endpoints and state their cryptographic limits.
- Test failure and rollback paths before enabling delivery. No unreviewed automatic
  daily updates, silent permission expansion or arbitrary downloaded-code execution.
- Keep live access, deployment, data collection and outbound sending behind their
  existing explicit authorization gates. Documentation does not deploy a service.

These requirements are not implemented by the current Python CLI/static HTML
prototype; a release candidate must supply evidence before claiming them.

### Evidence-led maintenance loop

1. Collect reproducible bug reports and voluntary feedback, initially using
   synthetic examples rather than private communications.
2. If usage measurement is later implemented, require explicit opt-in, minimal
   aggregate counters and documented purposes, retention/deletion and withdrawal.
   Do not collect message contents, credentials, religious attributes or device
   serial numbers. Do not treat aggregation as proof of anonymity.
3. Prioritize security vulnerabilities and unsafe behavior above popularity; then
   weigh accessibility, UI/UX friction, actual demand and maintenance cost.
4. Review bounded changes, test regressions and supported configurations, stage
   releases, document changes and rollback, and monitor verified outcomes only
   within approved operations.
5. Reassess stale/unsupported adapters; communicate limits instead of manufacturing
   coverage or promising that every requested service will be supported.

No telemetry service, update backend or always-on worker is introduced by this
specification. Ongoing improvement is a goal; review/development is limited to
available resources. Do not advertise uninterrupted 24/7 operation, an SLA or a
fixed release cadence without an actually staffed and verified operational basis.
Security and privacy apply equally regardless of popularity or theme selection.

## Licensing

First-party software and accompanying technical documentation use MPL-2.0, as
scoped in `NOTICE.md`; contributions to Covered Software use those same terms.
No separate CLA or copyright assignment is required here. SVG artwork is excluded
from the software grant under `assets/BRANDING.md`. Preserve notices and audit
third-party provenance. Licensing does not establish foundation status or endorsement.

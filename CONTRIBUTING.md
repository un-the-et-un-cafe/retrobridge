# Contributing to Retrobridge

This public source, pre-release pilot is preparing a process for a future community.
Repository publication is not a production launch. Do not add collaborators,
contact organizations or change visibility without owner approval. Outreach remains gated on the new platform's v1.0 release and
specific recipient/content authorization; no endorsement is implied.

## What exists today

An offline Python standard-library prototype uses synthetic device profiles,
fixed RSS/text fixtures and HTML 3-friendly output. No live connector, authentication,
newsletter collection, email sending, IRC connection, Atom parser or WhatsApp
integration is implemented. Mockups show concepts, not working integrations.

## Useful proposals

- An exact device model and introduction date, with a reliable source. Eligibility
  is introduction on or before 1996-10-29 (at least 30 years old as of 2026-10-29),
  not any machine vaguely described as a 1996 model.
- Reproducible emulator or physical-hardware tests with synthetic data.
- An adapter using authorized interfaces, with rights/API restrictions documented.
- Accessibility, text encoding, bandwidth or offline usability improvements.

Use the device and adapter templates. A proposal does not confer support status.
Never attach ROMs, proprietary firmware, credentials, private messages, personal
email addresses, serial numbers, network identifiers or unlicensed datasets.
State how rights and interface authorization will be confirmed; do not assume them.

## Development and review

1. Agree a narrow issue scope with a maintainer; use a separate branch.
2. Keep legacy output read-only and inputs bounded. Never execute user suggestions.
3. Add synthetic tests and document what was and was not tested.
4. Run `python3 -m unittest discover -s tests -v` from the repository root.
5. Submit a draft change for review; do not self-merge or deploy without authority.
6. After an approved source change, run the private backup and clean-restore checks
   documented in README. Update the backup allowlist when intentionally adding files.

Review is based on reproducibility, safety, legality of supplied material, user
benefit and maintenance capacity, rather than personal status or donations. Optional visual themes do not change permissions or service access.

## Licensing and contributor rights

First-party Covered Software and its technical documentation use MPL-2.0; see
[LICENSE](LICENSE) and [NOTICE.md](NOTICE.md) for terms and scope. Contributions
to those files must be provided under the same MPL-2.0 terms. No separate CLA,
assignment of copyright or additional contributor contract is required here.

Only submit work you are authorized to license; record authorship and provenance.
Preserve existing copyright/license notices and identify third-party material and
its terms. Add the MPL-2.0 SPDX identifier and Exhibit A notice to new first-party
source files where the format permits. For formats without comments, maintain the
scope notice. Do not add an Exhibit B secondary-license incompatibility designation.

SVG branding is excluded from the software grant; see `assets/BRANDING.md`.
Licensing does not authorize account access, deployment, outreach or spending.

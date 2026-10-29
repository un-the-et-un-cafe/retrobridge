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

A project license has not yet been selected or approved. No open-source license,
redistribution permission or rights transfer is promised by these instructions.
Do not solicit external code contributions until the owner settles the license
and contribution terms. For internal proposals, record authorship and provenance;
only include material the author is authorized to provide. Licensing is a release
blocker, not an implicit invitation to copy third-party code.

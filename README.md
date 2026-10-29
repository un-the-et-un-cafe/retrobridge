# RetroBridge — nonprofit retrocomputing pilot

Offline Python 3.11+ standard-library prototype. No connected service accounts, listener, deployment, live feeds, actual sending or personal data. All fixtures
are invented, including device archetypes: these are not verified hardware claims.
Only profiles introduced **on or before 1996-10-29** qualify as at least 30 years
old on 2026-10-29. Exact model dates must be sourced before adding real devices.

## Try it

```
python3 -m unittest discover -s tests -v
python3 retrobridge.py catalog
python3 retrobridge.py rss
python3 retrobridge.py text
python3 retrobridge.py html > /tmp/retrobridge-classic.html
python3 retrobridge.py html --theme blue-thread > /tmp/retrobridge-blue.html
```

Open generated HTML locally, not on a public host. No server is included; a future
preview must bind only to loopback and remain private. The HTML 3-friendly subset
uses tables, ASCII content and body colors, not scripts, CSS or external assets.
Actual legacy browser/hardware compatibility has not been tested. Paper & Ink and
Blue Thread are original theme labels (not a trademark-clearance claim). Blue
Thread is an optional blue/white palette. Theme selection does not affect permissions.

## Architecture / threat model

Future design: authenticated modern connectors -> trusted modern gateway ->
sanitation, bounded plain text -> isolated legacy client. The gateway is a trust
boundary, not a transparent end-to-end encryption relay. Plaintext serial/IRC or
legacy HTTP links are not end-to-end encrypted. Do not pass credentials or private
messages to those links. Keep the legacy network segmented and read-only.

Implemented adapters consume only fixed local synthetic fixtures. No URL fetcher,
socket listener, shell execution, arbitrary commands or remote content execution
exists. RSS is limited to 64 KiB, UTF-8, 20 titles and 240 ASCII characters per
field; DTD/entities and NULs are rejected. XML content and text are untrusted data.
IRC-style output is an inert transcript, not an IRC client. HTML fields are escaped.

Suggestions are inert, pending-review records; only a reviewer can mark a decision.
The role functions are a **policy demonstration, not authentication**: roles cannot
be accepted from untrusted callers in production. There is no shared assistant
account, tool access, administrative right to private content, or execution path
for even accepted suggestions. No WhatsApp connector or personal WhatsApp sync is
implemented or promised; an official business messaging API is not personal sync.

Schemas design optional device/interests fields, separate feedback contact consent,
explicit newsletter opt-in, pending double-opt-in confirmation, and unsubscribe.
Nothing is collected or sent. Email shape validation is not address verification.
Only minimal optional preferences are designed. Before a real service, implement identity,
rate limits, authorization, token expiry, deletion/retention, consent evidence,
provider policy review and an independent security review. No secret/provider
configuration is present. Do not enter real user data in this pilot.

## Private backup and recovery

After each reviewed source change, and before ending a development session:

```
python3 scripts/backup.py backup /tmp/retrobridge-backup-UNIQUE
python3 scripts/backup.py restore /tmp/retrobridge-backup-UNIQUE /tmp/retrobridge-restored-UNIQUE
cd /tmp/retrobridge-restored-UNIQUE
python3 -m unittest discover -s tests -v
```

The explicit allowlist snapshots only reviewed source, synthetic fixtures, schemas,
tests and docs into a new single-commit Git bundle plus SHA-256 manifest. It does
**not** back up original Git history/config, credentials, user data, caches, logs,
ignored files or arbitrary new files. Source files must still be reviewed for
accidental secrets; a filename allowlist cannot detect a secret pasted into code.
Bundle and restored file checksums are verified; restore refuses existing targets,
extra files and symlinks, and does not execute restored code. Only restore trusted
backups: a checksum detects corruption, not malicious replacement of both files.

Save both files together to an authorized private durable store. A local copy alone
is not durable, nor is it encrypted by this script. The repository scripts do not schedule themselves. A separately authorized daily
backup check preserves versioned private archives outside this repository. Remote source control does not replace a verified recovery backup; repeat the above
procedure after meaningful development changes.

## Verification limits

Unit tests cover exact age cutoff, XML rejection/limits, transcript framing, HTML
escaping/themes, explicit consent, optional fields and role policy. They do not
validate real hardware, transport encryption, live integrations, authentication,
production data retention, or JSON Schema conformance beyond JSON parsing. Backup
and clean restore plus running the tests from restored source are separate checks.

## Outreach gate

No invitation or email is authorized before this new platform v1.0 ships. Any
future organizational invitation is gated on that release and confirmed recipient/content authorization; no endorsement is implied.
No real email addresses are stored in this repository. Newsletter enrollment still
requires explicit consent and double opt-in; a known owner address is not consent.

## Client visual concept

Generated visual concepts and printable layouts are retained separately in the
private project archive rather than included in this source checkpoint.
The design depicts example/future adapters, not working connections. The prototype
only implements the offline subset above (not Atom, email or WhatsApp integration).

## Preparing community contributions

See [CONTRIBUTING.md](CONTRIBUTING.md), the [support evidence matrix](docs/SUPPORT_MATRIX.md),
[governance and roadmap](docs/GOVERNANCE_AND_ROADMAP.md), and [security reporting](SECURITY.md).
Device and adapter issue templates request synthetic, non-identifying evidence.
Licensing and external contribution terms remain pending; no open-source grant or
public launch is implied. The source repository is public by owner authorization. Backups, private project
correspondence, credentials and user data are not published.

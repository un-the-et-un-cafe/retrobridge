# Offline durable inbox pilot

**Experimental development candidate, 2026-10-30. Synthetic data only.** This adds a
small persistence boundary for one explicitly selected Telegram-shaped channel.
It does not connect to Telegram, create a bot, accept credentials, fetch files,
send messages, run a server, or change the native Mac client. The native client
still shows its offline catalog; integrating this contract is a later test gate.

## Run without an account

From the repository root, using the existing Python standard library:

```sh
python3 -m unittest discover -s tests -p test_inbox.py -v
python3 inbox_demo.py ./synthetic-inbox-001
```

Choose a new path under a trusted, local, owned parent. The demo refuses an
existing destination and reads only `fixtures/telegram-synthetic.json`. Its
channel ID is invented, not an authorized real channel. No real content belongs
in this pilot. A live integration requires a separately authorized channel,
provider-policy review, access controls, secret handling, transport review,
maintenance ownership and explicit approval.

Verified host: Python 3.12.14, SQLite 3.53.1, Linux. Installed-runtime security
patch assurance is not established here. No packages or executables were fetched
or installed for this increment. No XML is used by the new inbox.

## Store before confirmation

Telegram confirms an update when a later `getUpdates` call supplies a higher
offset; pending updates are retained for at most 24 hours. Requested update-type
filters can still leave older other-type updates in the queue. IDs can become
nonsequential after a long idle period. These are design inputs, not evidence of
live interoperability. [Official Bot API](https://core.telegram.org/bots/api#getupdates)

1. Read `Inbox.poll_plan()`. It is an inert description, not a network call.
   `offset=None` means **omit** the offset in a future transport; do not send null
   or a negative offset. Its limit is 100 and its explicit selection is
   `channel_post` plus `edited_channel_post`.
2. Give `accept_response()` the bounded response bytes, that exact requested
   offset and a trusted observation time (integer Unix seconds).
3. Validate the entire batch before writing. In one `BEGIN IMMEDIATE` transaction,
   recheck the current cursor, deduplicate, insert content/dispositions, and update
   the next offset and last-success time. Only return the new offset after commit.
4. A subsequent transport may use only the **committed** plan. Never derive an
   offset from received JSON alone, an exception, a partially processed batch,
   or a vintage client's page cursor.

If the process dies before commit, the batch and cursor remain uncommitted. If it
dies after commit but before the caller sees success, reopen and use the stored
cursor. Exact event replays do not add duplicate rows. Reusing an ID with changed
canonical content rejects the batch. Stale poll plans, invalid inputs, full stores
and database errors do not authorize confirmation. A future transport must stop
and surface errors, not skip malformed updates or raise limits automatically.

Every event receives bounded JSON/envelope validation. Supported channel posts
also receive explicit identity, date, text, edit and protection-flag checks.
Unknown types are **not fully Telegram-schema validated**: their bounded object
payload is omitted and only a digest/type/disposition is recorded. Unselected
channels likewise do not persist message text. These disposition rows let a
future bot-specific poller account for deliberately unselected updates without
claiming they were delivered to the inbox. There is no live bot ownership yet.

Selected-channel non-text and protected posts get visible unsupported indicators,
not media downloads or copied protected text. Text is retained up to the accepted
limit. Additional metadata/formatting is omitted with an indicator. Edits append
a separate event linked by message ID; they do not silently replace original text.
Deletion synchronization, reactions, threads and a complete chat archive are not
implemented. Content digests are integrity/dedup keys, not anonymization.

Unseen IDs below the committed offset fail closed for manual reconciliation.
This conservative pilot does not automatically reset offsets after long idleness,
drop pending updates, switch webhooks, or infer loss from an ID gap. Those policies
must be resolved before a real poller exists.

## Bounded client contract: `retrobridge-inbox/1`

`Inbox.page(now=..., after=0, through=None, limit=5)` returns one ASCII JSON object
followed by LF, **at most 4096 bytes**. This is a proposed local gateway interface,
not a running HTTP/serial endpoint or a native-client parser.

| Field | Meaning |
| --- | --- |
| `contract` | Exactly `retrobridge-inbox/1`; reject unknown versions |
| `read_only` | Always true; no reply, send, execute, delete or upstream-read operation |
| `through` | Snapshot high-water sequence; reuse unchanged on subsequent pages |
| `next_after` | Last returned sequence when another visible item exists; null at end |
| `items` | At most five items, stable ascending local arrival sequence |
| `warnings` | Fixed machine-readable warnings; clients must not silently hide them |

An item contains bounded integer `seq`; decimal ASCII **strings** `update_id`,
`message_id`, `posted_at` (up to 16 digits, never floating-point numbers); `kind`
(`channel_post` or `edited_channel_post`); `status` (`text` or `unsupported`);
`detail`; `text`; and boolean `encoding_loss` / `truncated`. The local `seq` is
independent of provider ID gaps. `text` is an inert, single-line, printable ASCII
preview of at most 160 characters. CR/LF/tab become spaces; other non-ASCII or
control characters become `?`. Both conversion and truncation are signaled.
Accepted full text remains in the modern store; this pilot has no full-message
endpoint. Quotes and backslashes use normal JSON escaping. Treat text only as
data, never terminal control, markup, commands or executable instructions.
Provider IDs and timestamps must stay as strings in a vintage client: they can
exceed 32-bit `long`. Only local sequence/page counts need small integer parsing.

Page arguments are bounded integers: `limit=1..5`, `after/through=0..1000`.
`through=None` starts a new snapshot. New events cannot appear midway through an
existing snapshot. Page reads do not change Telegram offsets or mark messages
read. Tokens are not authenticated capabilities; do not expose this API to
untrusted callers. A future transport must authenticate clients and enforce the
same bounds independently.
Here "read-only" describes client operations, not a filesystem read-only database
connection: opening `Inbox` can initialize schema or recover a pending journal.

Warnings always include `history_not_complete` and
`trusted_gateway_plaintext_not_e2ee`. Before first success, `not_yet_polled` is
also present. A 24-hour-or-longer observation gap produces
`outage_history_may_be_unavailable`; once observed on a successful poll, it remains
stored across restart. This warns about a retention risk, not proven message loss.
Empty successful polls update the observation time without inventing an offset.
Clock regression relative to last success is rejected. Observation times must
come from a trusted gateway clock, not message timestamps or client input.

## Limits and trust boundaries

- Input: UTF-8 bytes <=256 KiB, <=100 updates, nesting <=16, <=8192 JSON nodes,
  <=64 keys per object / 64 characters per key, <=1000 elements per array,
  <=16 KiB per string. Duplicate keys, invalid Unicode, nonfinite numbers and
  oversized numeric tokens are rejected. Finite decimals are allowed as ignored
  metadata (e.g. coordinates); IDs and control fields must be exact integers,
  never booleans or floats. Provider update/message IDs are bounded to
  0..4503599627370494 (message IDs start at 1); selected channel IDs are
  -4503599627370494..-1. Observation/message times are 0..253402300799.
  Accepted text is 1..4096 Unicode code points.
- Store: <=1000 unique event/disposition rows, no automatic pruning. SQLite uses
  4096-byte pages, 2048-page **main-database** cap (8 MiB), rollback DELETE journal,
  and synchronous EXTRA. Settings are read back and checked. Journal overhead and
  total filesystem usage are not a hard disk quota. Long texts can exhaust the
  database before 1000 rows; that is an explicit stop, not silent deletion.
- Storage is plaintext. Private directory mode 0700 is checked; new databases
  are created with mode 0600, and existing database/journal files must have no
  group/world permissions. Symlinks, hardlinks and unexpected entries are rejected.
  The caller must own a trusted parent path. This is not a race-proof sandbox
  against a malicious process with the same OS user identity. Imported/untrusted
  databases and network filesystems are outside scope.
- SQLite transactions/flush settings provide the intended atomicity boundary,
  but depend on filesystem locking and durable flushes. Process-crash tests are
  not a power-cut or damaged-storage certification. See SQLite's
  [atomic commit description](https://www.sqlite.org/atomiccommit.html) and
  [synchronous settings](https://www.sqlite.org/pragma.html#pragma_synchronous).
- The modern gateway can read plaintext. This is **not end-to-end encrypted**.
  A future plaintext serial/legacy-network link would need separate isolation
  and explicit consent. No secrets should reach a vintage client.

## Evidence and remaining gates

Synthetic tests cover before/after-commit process termination and reopen/replay;
transaction rollback; exact/conflicting duplicates; stale plans across two
connections; real SQLite page-limit exhaustion; capacity rollback; malformed,
oversized, wrong-type and nonfinite input; unsupported media/location/protected
indicators; unselected-channel text nonpersistence; append-only edits; ASCII and
preview limits; stable pagination across new arrivals; read-only cursors; outage
warnings; ID gaps; and private-path checks. No fault test executes external input.

Not tested/implemented: live Telegram access or authentication, actual provider
retention, network retries/rate limits, production backups/retention/deletion,
power loss, same-user adversarial filesystem races, native client integration,
new emulator tests, or physical vintage hardware. Native-client evidence remains separate from this receiving contract. No Mac
binary is included, produced or delivered by this increment.

### Receiving-side reference

The experimental [client state reference](CLIENT_INBOX_REFERENCE.md) now validates
synthetic gateway pages and exercises paging, cancellation and stale responses.
It is Python on the modern host, not the native Mac client or a live transport.

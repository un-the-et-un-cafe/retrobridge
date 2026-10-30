# Read-only inbox client reference

Experimental offline development increment, 30 October 2026. `inbox_client.py` is a
modern-host Python reference model for a future vintage client, **not** a native
Mac/Windows implementation, transport, renderer or running service. It uses no
accounts, credentials, network operations or new dependencies. All tests use
synthetic content. Existing native client source and binaries are unchanged.

## Purpose and state transitions

The durable gateway already emits `retrobridge-inbox/1`. This increment exercises
the receiving side before porting it to a constrained client:

1. `Client.refresh()` returns an inert request plan: generation, after=0,
   through=None, limit=5. Only after/through/limit belong in a future gateway
   request. Generation is a client-local correlation value, not an access token.
2. The caller obtains a page through a separately reviewed transport. In these
   tests it calls `Inbox.page()` directly. No transport exists in this module.
3. `complete(generation, raw_bytes)` validates the entire page before replacing
   the current view. It retains only one page of at most five items/4096 bytes.
4. `next_page()` pins the accepted high-water mark and advances only to the
   accepted cursor. New arrivals cannot enter an existing snapshot. Refresh
   intentionally starts a new snapshot.
5. A second refresh supersedes the earlier request. Cancel invalidates the
   pending generation but preserves the last accepted page. Stale, duplicate or
   cancelled completions fail closed. Repeated Next while a request is pending
   is rejected. Malformed pages leave the old view and cursor intact; the caller
   must surface the failure, then retry, cancel or refresh deliberately.

The model is single-threaded. Generations have arbitrary-precision Python
integers; a native port must define overflow handling before reuse. It does not
persist state, accumulate message history or confirm provider updates. Opening
the gateway's SQLite store remains a separate operation with its own trust model.

## Strict receiving contract

Validation rejects unknown contract versions, missing/extra fields, false
read-only flags, duplicate JSON keys, non-ASCII wire bytes, escaped control or
non-ASCII preview characters, oversized pages/items, wrong scalar types, unknown
status/detail/warning codes, noncanonical decimal IDs and nonmonotonic cursors.
Both privacy/history warnings are mandatory. Large provider IDs remain strings;
they are range checked on the modern host and never converted into native
32-bit quantities here. Unsupported content remains an explicit indicator.
Returned state is copied so a UI cannot accidentally mutate stored cursors.

The shared bounded JSON decoder is imported from `inbox.py`; no separate parser
dependency is introduced. The byte ceiling is checked before parsing. Content is
inert data, not HTML, terminal commands, markup or executable instructions.
No logger records rejected content, and errors use fixed messages.

Strict rejection of new fields or warning codes is intentional: a future gateway
contract change needs coordinated client review rather than silently hiding
security or fidelity information. This validator does not authenticate a gateway,
prove source authenticity or protect against a malicious same-process caller.
The gateway still sees plaintext; this is not end-to-end encryption.

The snapshot high-water mark also counts deliberately ignored/unselected events.
Therefore a terminal page may end before `through`, or contain no visible items
at all. The validator must accept those cases. This contract cannot prove that a
malicious or faulty gateway did not omit eligible items; `next_after=null` trusts
the gateway's completeness assertion. The mandatory incomplete-history warning
remains visible. A stronger proof would require a separately versioned protocol.

## Verification

From the repository root:

```sh
python3 -m unittest discover -s tests -v
```

56 tests pass on the existing Python 3.12.14 runtime: 43 previous tests plus 13
new client tests (with field-mutation subcases). New coverage includes actual
gateway-to-client pages, snapshot pagination while new events arrive, first-poll
warnings, protected-content indicators, high IDs, ASCII/truncation flags,
cancel/repeated refresh/repeated Next, duplicate completions, invalid-response
atomicity, copied state, unknown fields and malformed/oversized data.

This is not evidence of live Telegram interoperability, native GUI rendering,
network authentication, physical hardware compatibility, power-loss recovery or
platform patch assurance. No fresh dependencies, emulator runs or native builds
were performed. Next gate: independently review this receiving contract before
porting a bounded decoder and display state to a selected native target.

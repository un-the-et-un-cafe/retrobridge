# Device and adapter support evidence

These are evidence labels, not guarantees. A maintainer records the exact revision,
test date and limitations for every change in status. Labels may coexist: maintained
is an ongoing commitment, not a substitute for emulator or hardware evidence.

| Label | Minimum evidence | Does not establish |
| --- | --- | --- |
| Proposed | Exact model/profile, sourced introduction date, capabilities and a bounded test plan | Compatibility or availability |
| Emulator-tested | Emulator/version, legally supplied environment, config, revision, reproducible steps and synthetic output | Physical hardware compatibility |
| Hardware-tested | Exact model/variant, relevant OS/config, revision, steps, date and synthetic results | All variants, peripherals or networks |
| Maintained | Named willing maintainer, supported scope, regression procedure, review date and known limitations | A response-time promise or permanent support |

A maintainer may mark evidence **stale**, **blocked**, or **retired**, preserving its
history and reason. Never promote a device solely from a screenshot or generated
mockup. Do not publish identifying photos/metadata, serial numbers, MAC/IP addresses,
license keys or actual user communications as evidence.

## Current pilot inventory

| Component | Present status | Evidence and limits |
| --- | --- | --- |
| Synthetic 1985 terminal profile | Proposed archetype only | Invented, not an actual device |
| Synthetic 1993 dial-up profile | Proposed archetype only | Invented, not an actual device |
| Synthetic 1996 early-web profile | Proposed archetype only | Invented, not an actual device |
| RSS/text to IRC-style transcript | Offline host unit-tested | Fixed local synthetic fixtures; no IRC transport |
| HTML catalog | Offline host unit-tested | Escaping and theme checks; no legacy browser certification |
| Visual client design | Concept | Static generated image and print PDF; no connected integrations |
| Email, Atom, WhatsApp Business | Unimplemented concepts | No connector or personal-account sync |

No physical device or emulator has been tested in this pilot. Host unit tests do
not qualify any device for the emulator-tested or hardware-tested labels.

# SPDX-License-Identifier: MPL-2.0
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""Offline, read-only synthetic pilot. Python 3.11+, standard library only."""
import argparse
import datetime as dt
import html
import json
from pathlib import Path
import re
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parent
AS_OF = dt.date(2026, 10, 29)
CUTOFF = dt.date(1996, 10, 29)
THEMES = {'classic': ('Paper & Ink', '#FFFFFF', '#000000'),
          'blue-thread': ('Blue Thread (optional blue and white palette)', '#FFFFFF', '#143D73')}


def eligible(profile):
    return dt.date.fromisoformat(profile['introduced']) <= CUTOFF


def catalog():
    data = json.loads((ROOT / 'fixtures/catalog.json').read_text())
    return {**data, 'devices': [p for p in data['devices'] if eligible(p)]}


def clean(text, limit=240):
    # ASCII output, strip IRC/control characters, fold whitespace, cap each field.
    return ' '.join(''.join(c if 32 <= ord(c) <= 126 else ' ' for c in text).split())[:limit]


def rss_items(raw):
    if len(raw) > 65536:
        raise ValueError('Feed exceeds offline pilot limit')
    # Decode strictly first; disallow DTD/entities, including UTF-16 bypasses.
    text = raw.decode('utf-8')
    if '\x00' in text or re.search(r'<!\s*(DOCTYPE|ENTITY)', text, re.I):
        raise ValueError('DTD/entities forbidden')
    root = ET.fromstring(text)
    if root.tag != 'rss':
        raise ValueError('Only simple RSS supported')
    return [clean(item.findtext('title', 'Untitled')) for item in root.findall('./channel/item')[:20]]


def transcript(items):
    # Not a socket connection or outbound IRC command stream.
    return '\n'.join('[retro-news] ' + clean(item) for item in items) + '\n'


def render(theme='classic'):
    title, bg, fg = THEMES[theme]
    data = catalog()
    rows = ''.join('<TR><TD>%s</TD><TD>%s</TD><TD>%s</TD></TR>' % tuple(html.escape(str(v), quote=True) for v in
        (p['name'], p['introduced'], ', '.join(p['capabilities']))) for p in data['devices'])
    adapters = ''.join('<LI>%s: %s</LI>' % (html.escape(a['name']), html.escape(a['purpose'])) for a in data['adapters'])
    return ('<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 3.2 Final//EN">\n'
        '<HTML><HEAD><TITLE>RetroBridge offline pilot</TITLE></HEAD>'
        '<BODY BGCOLOR="%s" TEXT="%s"><H1>RetroBridge</H1><P>%s</P>'
        '<P>Synthetic examples only. Read-only offline pilot. Cutoff: 1996-10-29.</P>'
        '<TABLE BORDER="1"><TR><TH>Device profile</TH><TH>Introduced</TH><TH>Capabilities</TH></TR>%s</TABLE>'
        '<H2>Adapter concepts</H2><UL>%s</UL><P>No signup collection or sending is enabled.</P></BODY></HTML>') % (bg, fg, html.escape(title), rows, adapters)


def validate_signup(record):
    allowed = {'email', 'newsletter_opt_in', 'consent_text_version', 'device', 'interests'}
    if set(record) - allowed:
        raise ValueError('Unexpected field')
    if record.get('newsletter_opt_in') is not True or record.get('consent_text_version') != 'pilot-v1':
        raise ValueError('Explicit opt-in and version required')
    email = record.get('email')
    if not isinstance(email, str) or not re.fullmatch(r'[^\s@]+@[^\s@]+\.[^\s@]+', email) or len(email) > 254:
        raise ValueError('Invalid email shape')
    if 'device' in record and (not isinstance(record['device'], str) or len(record['device']) > 120):
        raise ValueError('Invalid device')
    if 'interests' in record and (not isinstance(record['interests'], list) or len(record['interests']) > 10 or
            any(not isinstance(s, str) or len(s) > 80 for s in record['interests'])):
        raise ValueError('Invalid interests')
    return True  # No storage, collection, identity verification or sending.


def suggest(role, text):
    if role not in {'contributor', 'reviewer'}:
        raise PermissionError('Contributor or reviewer role required')
    return {'text': clean(text, 500), 'status': 'pending-review', 'executable': False}


def review(role, suggestion, decision):
    if role != 'reviewer':
        raise PermissionError('Reviewer role required')
    if decision not in {'accepted', 'rejected'}:
        raise ValueError('Unknown decision')
    return {**suggestion, 'status': decision, 'executable': False}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('command', choices=['catalog', 'rss', 'text', 'html'])
    p.add_argument('--theme', choices=list(THEMES), default='classic')
    args = p.parse_args()
    if args.command == 'catalog':
        print(json.dumps(catalog(), indent=2))
    elif args.command == 'html':
        print(render(args.theme))
    elif args.command == 'rss':
        print(transcript(rss_items((ROOT / 'fixtures/news.xml').read_bytes())), end='')
    else:
        print(transcript((ROOT / 'fixtures/news.txt').read_text().splitlines()), end='')

if __name__ == '__main__':
    main()

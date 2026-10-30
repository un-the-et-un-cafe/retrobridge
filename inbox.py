# SPDX-License-Identifier: MPL-2.0
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""Offline synthetic Telegram-shaped inbox. No transport or credentials.

Only a committed poll_plan() offset may be used for a subsequent poll.
SQLite durability depends on the filesystem honoring locking and flushes.
"""
import hashlib
import json
import math
import os
from pathlib import Path
import sqlite3
import stat

MAX_RESPONSE = 256 * 1024
MAX_BATCH = 100
MAX_TEXT = 4096
MAX_EVENTS = 1000
MAX_ID = (1 << 52) - 2
MAX_TIME = 253402300799
OUTAGE_SECONDS = 24 * 60 * 60
MAX_PAGE_BYTES = 4096


class Rejected(ValueError):
    """The entire response was rejected; do not confirm it upstream."""


def integer(value, low=0, high=MAX_ID):
    if type(value) is not int or not low <= value <= high:
        raise Rejected('integer outside contract')
    return value


def _pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise Rejected('duplicate JSON key')
        result[key] = value
    return result


def _no_number(_):
    raise Rejected('non-finite JSON number')


def _json_float(text):
    # Coordinates and other unsupported metadata may contain finite decimals.
    # IDs, dates and all control fields still require exact integers separately.
    if len(text) > 32:
        raise Rejected('JSON decimal too long')
    value = float(text)
    if not math.isfinite(value):
        raise Rejected('non-finite JSON number')
    return value


def _json_integer(text):
    if len(text) > 17:
        raise Rejected('JSON integer too large')
    return integer(int(text), -MAX_ID, MAX_ID)


def _bounded_json(raw):
    if type(raw) is not bytes or len(raw) > MAX_RESPONSE:
        raise Rejected('response must be bounded bytes')
    try:
        text = raw.decode('utf-8', errors='strict')
        # Limit nesting before handing the input to the recursive JSON parser.
        quoted = escaped = False
        depth = 0
        for char in text:
            if quoted:
                if escaped:
                    escaped = False
                elif char == '\\':
                    escaped = True
                elif char == '"':
                    quoted = False
            elif char == '"':
                quoted = True
            elif char in '[{':
                depth += 1
                if depth > 16:
                    raise Rejected('JSON nesting limit')
            elif char in ']}':
                depth -= 1
        value = json.loads(text, object_pairs_hook=_pairs,
                           parse_int=_json_integer, parse_float=_json_float,
                           parse_constant=_no_number)
        todo = [value]
        nodes = 0
        while todo:
            item = todo.pop()
            nodes += 1
            if nodes > 8192:
                raise Rejected('JSON node limit')
            if isinstance(item, dict):
                if len(item) > 64 or any(len(k) > 64 for k in item):
                    raise Rejected('JSON object limit')
                todo.extend(item.keys())
                todo.extend(item.values())
            elif isinstance(item, list):
                if len(item) > 1000:
                    raise Rejected('JSON array limit')
                todo.extend(item)
            elif isinstance(item, str):
                if len(item.encode('utf-8', errors='strict')) > 16384:
                    raise Rejected('JSON string limit')
        return value
    except (UnicodeError, json.JSONDecodeError, RecursionError) as exc:
        raise Rejected('invalid JSON encoding or structure') from exc


def _event(update, channel_id):
    if type(update) is not dict or 'update_id' not in update or len(update) != 2:
        raise Rejected('update requires one payload')
    uid = integer(update['update_id'])
    kind = next(k for k in update if k != 'update_id')
    payload = update[kind]
    if type(payload) is not dict:
        raise Rejected('update payload must be an object')
    digest = hashlib.sha256(json.dumps(update, sort_keys=True,
                                     separators=(',', ':')).encode()).hexdigest()
    record = dict(update_id=uid, digest=digest, kind=kind, outcome='ignored',
                  message_id=None, posted_at=None, text=None, detail='unselected_type')
    if kind not in ('channel_post', 'edited_channel_post'):
        return record
    mid = integer(payload.get('message_id'), 1)
    posted = integer(payload.get('date'), 0, MAX_TIME)
    chat = payload.get('chat')
    if type(chat) is not dict or chat.get('type') != 'channel':
        raise Rejected('channel post requires channel identity')
    cid = integer(chat.get('id'), -MAX_ID, -1)
    if 'text' in payload and (type(payload['text']) is not str or
                             not 1 <= len(payload['text']) <= MAX_TEXT):
        raise Rejected('invalid or oversized message text')
    if 'has_protected_content' in payload and type(payload['has_protected_content']) is not bool:
        raise Rejected('invalid protection flag')
    if 'edit_date' in payload:
        integer(payload['edit_date'], 0, MAX_TIME)
    if cid != channel_id:
        record['detail'] = 'unselected_channel'
        return record
    record.update(message_id=mid, posted_at=posted, outcome='unsupported',
                  detail='non_text')
    if payload.get('has_protected_content'):
        record['detail'] = 'protected_content'
    elif 'text' in payload:
        plain_fields = {'message_id', 'date', 'edit_date', 'chat', 'text'}
        record.update(outcome='text', text=payload['text'],
                      detail='extra_fields_omitted' if set(payload) - plain_fields else '')
    return record


def parse_response(raw, channel_id):
    response = _bounded_json(raw)
    if (type(response) is not dict or set(response) != {'ok', 'result'} or
            response['ok'] is not True or type(response['result']) is not list or
            len(response['result']) > MAX_BATCH):
        raise Rejected('not a bounded successful poll response')
    # Validate every event, including duplicates and unselected types/channels.
    return [_event(update, channel_id) for update in response['result']]


def _display(text):
    """Inert single-line ASCII, not a command stream, HTML or terminal control."""
    value = ''.join(c if ' ' <= c <= '~' else ' ' if c in '\r\n\t' else '?'
                    for c in text)
    return value[:160], value != text, len(value) > 160


class Inbox:
    """One explicitly selected synthetic channel per private local store.

    The caller owns a trusted parent directory. This is not a hostile same-UID
    filesystem sandbox. Do not open imported databases or use shared directories.
    """
    def __init__(self, directory, channel_id):
        self.channel_id = integer(channel_id, -MAX_ID, -1)
        directory = Path(directory)
        directory.mkdir(mode=0o700, exist_ok=True)
        info = directory.lstat()
        if (not stat.S_ISDIR(info.st_mode) or info.st_uid != os.getuid() or
                stat.S_IMODE(info.st_mode) != 0o700):
            raise Rejected('store requires an owned private directory')
        path = directory / 'inbox.sqlite3'
        # Sidecars are only allowed when regular, private and owned too.
        for child in directory.iterdir():
            info = child.lstat()
            if (child.name not in ('inbox.sqlite3', 'inbox.sqlite3-journal') or
                    not stat.S_ISREG(info.st_mode) or info.st_nlink != 1 or
                    info.st_uid != os.getuid() or stat.S_IMODE(info.st_mode) & 0o077):
                raise Rejected('unexpected or unsafe store entry')
        if not path.exists():
            fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
            os.close(fd)
        self.db = sqlite3.connect(path, timeout=1, isolation_level=None)
        try:
            for pragma in ('trusted_schema=OFF', 'journal_mode=DELETE',
                           'synchronous=EXTRA', 'page_size=4096',
                           'max_page_count=2048', 'temp_store=MEMORY'):
                self.db.execute('PRAGMA ' + pragma)
            settings = {'trusted_schema': 0, 'journal_mode': 'delete',
                        'synchronous': 3, 'page_size': 4096, 'max_page_count': 2048}
            if any(self.db.execute('PRAGMA '+k).fetchone()[0] != v for k, v in settings.items()):
                raise Rejected('required SQLite settings unavailable')
            self.db.execute('BEGIN IMMEDIATE')
            self.db.execute('CREATE TABLE IF NOT EXISTS state '
                            '(singleton INTEGER PRIMARY KEY CHECK(singleton=1), '
                            'version INTEGER, channel_id INTEGER, next_offset INTEGER, '
                            'last_success INTEGER, outage_seen INTEGER NOT NULL)')
            self.db.execute('CREATE TABLE IF NOT EXISTS events '
                            '(seq INTEGER PRIMARY KEY, update_id INTEGER UNIQUE NOT NULL, '
                            'digest TEXT NOT NULL, kind TEXT NOT NULL, outcome TEXT NOT NULL, '
                            'message_id INTEGER, posted_at INTEGER, text TEXT, detail TEXT NOT NULL)')
            self.db.execute('INSERT OR IGNORE INTO state VALUES (1,1,?,NULL,NULL,0)', (channel_id,))
            if self.db.execute('SELECT version,channel_id FROM state').fetchall() != [(1, channel_id)]:
                raise Rejected('store version or selected channel mismatch')
            self.db.execute('COMMIT')
        except BaseException:
            self.db.close()
            raise

    def close(self):
        self.db.close()

    def poll_plan(self):
        """Inert request description only; never issues a request or confirms data."""
        offset = self.db.execute('SELECT next_offset FROM state').fetchone()[0]
        return {'offset': offset, 'limit': MAX_BATCH,
                'allowed_updates': ['channel_post', 'edited_channel_post']}

    def accept_response(self, raw, requested_offset, observed_at, *, _fault=None):
        """Commit whole validated batch + cursor, then return a safe next offset.

        _fault is solely an in-process test hook; never sourced from input data.
        Replays require a matching digest. Unknown old IDs fail closed rather
        than silently discarding possible content after an identifier reset.
        """
        if requested_offset is not None:
            integer(requested_offset, 0, MAX_ID + 1)
        integer(observed_at, 0, MAX_TIME)
        events = parse_response(raw, self.channel_id)
        self.db.execute('BEGIN IMMEDIATE')
        try:
            offset, last, outage = self.db.execute(
                'SELECT next_offset,last_success,outage_seen FROM state').fetchone()
            if requested_offset != offset:
                raise Rejected('stale poll plan; reread committed cursor')
            if last is not None and observed_at < last:
                raise Rejected('observation clock moved backwards')
            count = self.db.execute('SELECT count(*) FROM events').fetchone()[0]
            for event in events:
                uid = event['update_id']
                prior = self.db.execute('SELECT digest FROM events WHERE update_id=?', (uid,)).fetchone()
                if prior:
                    if prior[0] != event['digest']:
                        raise Rejected('conflicting replay')
                    continue
                if offset is not None and uid < offset:
                    raise Rejected('unseen old identifier; manual reconciliation required')
                if count >= MAX_EVENTS:
                    raise Rejected('store full; no automatic deletion or confirmation')
                self.db.execute('INSERT INTO events '
                                '(update_id,digest,kind,outcome,message_id,posted_at,text,detail) '
                                'VALUES (:update_id,:digest,:kind,:outcome,:message_id,:posted_at,:text,:detail)', event)
                count += 1
            if _fault:
                _fault('after_content')
            next_offset = max([e['update_id'] + 1 for e in events] +
                              ([offset] if offset is not None else []), default=None)
            outage = int(bool(outage or (last is not None and observed_at - last >= OUTAGE_SECONDS)))
            self.db.execute('UPDATE state SET next_offset=?,last_success=?,outage_seen=?',
                            (next_offset, observed_at, outage))
            if _fault:
                _fault('before_commit')
            self.db.execute('COMMIT')
        except BaseException:
            if self.db.in_transaction:
                self.db.execute('ROLLBACK')
            raise
        if _fault:
            _fault('after_commit')
        return next_offset

    def page(self, *, now, after=0, through=None, limit=5):
        """Return a stable snapshot page, without marking messages read upstream."""
        integer(now, 0, MAX_TIME)
        integer(after, 0, MAX_EVENTS)
        integer(limit, 1, 5)
        if through is not None:
            integer(through, 0, MAX_EVENTS)
        self.db.execute('BEGIN')
        try:
            last, outage = self.db.execute('SELECT last_success,outage_seen FROM state').fetchone()
            high = self.db.execute('SELECT coalesce(max(seq),0) FROM events').fetchone()[0]
            if through is None:
                through = high
            if through > high or after > through:
                raise Rejected('invalid page cursor')
            if last is not None and now < last:
                raise Rejected('observation clock moved backwards')
            rows = self.db.execute('SELECT seq,update_id,kind,outcome,message_id,posted_at,text,detail '
                                   "FROM events WHERE seq>? AND seq<=? AND outcome!='ignored' "
                                   'ORDER BY seq LIMIT ?', (after, through, limit + 1)).fetchall()
            items = []
            for seq, uid, kind, outcome, mid, posted, text, detail in rows[:limit]:
                preview, replaced, shortened = _display(text or '[unsupported content]')
                # Provider IDs/times exceed classic 32-bit longs: keep decimal text.
                items.append(dict(seq=seq, update_id=str(uid), message_id=str(mid), posted_at=str(posted),
                                  kind=kind, status=outcome, detail=detail, text=preview,
                                  encoding_loss=replaced, truncated=shortened))
            warnings = ['history_not_complete', 'trusted_gateway_plaintext_not_e2ee']
            if last is None:
                warnings.append('not_yet_polled')
            if outage or (last is not None and now - last >= OUTAGE_SECONDS):
                warnings.append('outage_history_may_be_unavailable')
            result = dict(contract='retrobridge-inbox/1', through=through,
                          next_after=items[-1]['seq'] if len(rows) > limit else None,
                          items=items, warnings=warnings, read_only=True)
            wire = (json.dumps(result, ensure_ascii=True, separators=(',', ':')) + '\n').encode('ascii')
            if len(wire) > MAX_PAGE_BYTES:
                raise Rejected('page encoding budget exceeded')
            return wire
        finally:
            self.db.execute('ROLLBACK')

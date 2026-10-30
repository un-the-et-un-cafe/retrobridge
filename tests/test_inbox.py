# SPDX-License-Identifier: MPL-2.0
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

import inbox as r

CHANNEL = -1000000000001


def event(uid=10, text='Synthetic hello', *, channel=CHANNEL, kind='channel_post'):
    return {'update_id': uid, kind: {'message_id': uid + 1, 'date': 100,
                                   'chat': {'id': channel, 'type': 'channel'}, 'text': text}}


def response(*events):
    return json.dumps({'ok': True, 'result': list(events)}, ensure_ascii=False).encode()


class InboxTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.path = Path(self.temp.name) / 'store'
        self.store = r.Inbox(self.path, CHANNEL)

    def tearDown(self):
        self.store.close()
        self.temp.cleanup()

    def accept(self, *events, now=100):
        return self.store.accept_response(response(*events), self.store.poll_plan()['offset'], now)

    def page(self, **kwargs):
        return json.loads(self.store.page(now=kwargs.pop('now', 100), **kwargs))

    def unchanged_on_rejection(self, raw):
        before = self.store.poll_plan()
        rows = self.store.db.execute('SELECT * FROM events').fetchall()
        with self.assertRaises(r.Rejected):
            self.store.accept_response(raw, before['offset'], 100)
        self.assertEqual(before, self.store.poll_plan())
        self.assertEqual(rows, self.store.db.execute('SELECT * FROM events').fetchall())

    def test_initial_state_and_empty_poll(self):
        self.assertIsNone(self.store.poll_plan()['offset'])
        self.assertIn('not_yet_polled', self.page()['warnings'])
        self.assertIsNone(self.accept())
        self.assertNotIn('not_yet_polled', self.page()['warnings'])

    def test_content_and_offset_survive_reopen(self):
        self.assertEqual(self.accept(event()), 11)
        self.store.close()
        self.store = r.Inbox(self.path, CHANNEL)
        self.assertEqual(self.store.poll_plan()['offset'], 11)
        self.assertEqual(self.page()['items'][0]['text'], 'Synthetic hello')
        self.assertEqual(self.store.db.execute('PRAGMA integrity_check').fetchone(), ('ok',))

    def test_exact_replay_and_duplicate_in_batch(self):
        self.accept(event(), event())
        self.accept(event())
        self.assertEqual(len(self.page()['items']), 1)
        self.assertEqual(self.store.poll_plan()['offset'], 11)

    def test_conflicting_replay_rolls_back_whole_batch(self):
        self.accept(event())
        self.unchanged_on_rejection(response(event(11), event(10, 'different')))

    def test_invalid_later_event_does_not_store_earlier_content(self):
        self.unchanged_on_rejection(response(event(), {'update_id': True, 'channel_post': {}}))

    def test_every_duplicate_is_validated(self):
        self.accept(event())
        self.unchanged_on_rejection(response({'update_id': 10, 'channel_post': []}))

    def test_unselected_channel_content_never_persisted(self):
        self.accept(event(text='DO_NOT_PERSIST', channel=-1000000000002))
        self.assertEqual(self.page()['items'], [])
        self.assertEqual(self.store.db.execute('SELECT text,detail FROM events').fetchone(),
                         (None, 'unselected_channel'))
        self.assertNotIn(b'DO_NOT_PERSIST', (self.path/'inbox.sqlite3').read_bytes())

    def test_unselected_type_recorded_without_payload(self):
        self.accept({'update_id': 10, 'message': {'text': 'DO_NOT_PERSIST'}})
        self.assertEqual(self.page()['items'], [])
        self.assertEqual(self.store.db.execute('SELECT text,detail FROM events').fetchone(),
                         (None, 'unselected_type'))
        self.assertEqual(self.store.poll_plan()['offset'], 11)

    def test_unsupported_media_is_visible_but_not_saved(self):
        value = event()
        del value['channel_post']['text']
        value['channel_post']['photo'] = [{'file_id': 'NEVER_DOWNLOAD'}]
        self.accept(value)
        item = self.page()['items'][0]
        self.assertEqual((item['status'], item['detail']), ('unsupported', 'non_text'))
        self.assertNotIn('NEVER_DOWNLOAD', json.dumps(item))

    def test_unsupported_location_finite_decimals_do_not_wedge_batch(self):
        value = event()
        del value['channel_post']['text']
        value['channel_post']['location'] = {'latitude': 12.25, 'longitude': -34.5}
        self.accept(value, event(11))
        self.assertEqual(self.page()['items'][0]['detail'], 'non_text')
        self.assertEqual(self.store.poll_plan()['offset'], 12)
        for number in (b'1e999', b'1.23456789012345678901234567890123456789'):
            self.unchanged_on_rejection(b'{"ok":true,"result":[{"update_id":12,"x":{"n":'+number+b'}}]}')

    def test_protected_content_not_copied(self):
        value = event(text='PROTECTED_SYNTHETIC')
        value['channel_post']['has_protected_content'] = True
        self.accept(value)
        self.assertEqual(self.page()['items'][0]['detail'], 'protected_content')
        self.assertEqual(self.store.db.execute('SELECT text FROM events').fetchone(), (None,))

    def test_edit_is_append_only_not_silent_overwrite(self):
        original = event(10)
        edited = event(11, 'Edited synthetic text', kind='edited_channel_post')
        edited['edited_channel_post']['message_id'] = 11
        edited['edited_channel_post']['edit_date'] = 101
        self.accept(original, edited)
        items = self.page()['items']
        self.assertEqual(len(items), 2)
        self.assertEqual(items[0]['message_id'], items[1]['message_id'])
        self.assertEqual(items[1]['kind'], 'edited_channel_post')

    def test_text_omissions_sanitization_and_budget(self):
        value = event(text='\x1b[31m\r\n/exec\t\u202e\u00e9' + 'x'*300)
        value['channel_post']['entities'] = []
        self.accept(value)
        item = self.page()['items'][0]
        self.assertEqual(item['detail'], 'extra_fields_omitted')
        self.assertTrue(item['encoding_loss'])
        self.assertTrue(item['truncated'])
        self.assertEqual(len(item['text']), 160)
        self.assertTrue(all(' ' <= c <= '~' for c in item['text']))
        self.assertEqual(self.store.db.execute('SELECT text FROM events').fetchone()[0], value['channel_post']['text'])

    def test_text_and_batch_limits(self):
        self.unchanged_on_rejection(response(event(text='x'*(r.MAX_TEXT+1))))
        self.unchanged_on_rejection(response(*[event(i) for i in range(101)]))
        self.unchanged_on_rejection(b' '*(r.MAX_RESPONSE+1))
        self.accept(event(text='x'*r.MAX_TEXT))

    def test_json_rejects_duplicates_numbers_encoding_depth_and_shape(self):
        cases = [b'{"ok":true,"ok":true,"result":[]}', b'{"ok":1,"result":[]}',
                 b'{"ok":false,"result":[]}', b'{"ok":true,"result":[],"extra":0}',
                 b'{"ok":true,"result":[NaN]}', b'{"ok":true,"result":[1.5]}',
                 b'{"ok":true,"result":[999999999999999999999999]}', b'\xff',
                 b'{"ok":true,"result":["\\ud800"]}', b'['*17+b']'*17,
                 response({'update_id': 1}), response({'update_id': 1, 'x': {}, 'y': {}}),
                 response({'update_id': 1, 'x': []}), b'{}{}', b'null']
        for raw in cases:
            with self.subTest(raw=raw[:70]):
                self.unchanged_on_rejection(raw)

    def test_semantic_fields_reject_wrong_types(self):
        for key, bad in [('message_id', True), ('date', -1), ('text', 12), ('text', ''),
                         ('has_protected_content', 1), ('edit_date', False), ('chat', [])]:
            value = event()
            value['channel_post'][key] = bad
            with self.subTest(key=key, bad=bad):
                self.unchanged_on_rejection(response(value))

    def test_stale_poll_response_cannot_confirm_unseen_content(self):
        old = self.store.poll_plan()['offset']
        self.accept(event())
        with self.assertRaises(r.Rejected):
            self.store.accept_response(response(event(11)), old, 100)
        self.assertEqual(len(self.page()['items']), 1)

    def test_two_writers_recheck_cursor_inside_transaction(self):
        other = r.Inbox(self.path, CHANNEL)
        try:
            plan = other.poll_plan()
            self.accept(event())
            with self.assertRaises(r.Rejected):
                other.accept_response(response(event(11)), plan['offset'], 100)
            self.assertEqual(other.poll_plan()['offset'], 11)
            self.assertEqual(len(self.page()['items']), 1)
        finally:
            other.close()

    def test_unseen_old_identifier_requires_reconciliation(self):
        self.accept(event(100))
        self.unchanged_on_rejection(response(event(1)))

    def test_id_gap_not_loss_and_outage_warning_sticky(self):
        self.accept(event(10))
        self.accept(event(10000), now=101)
        self.assertNotIn('outage_history_may_be_unavailable', self.page(now=101)['warnings'])
        self.assertIn('outage_history_may_be_unavailable', self.page(now=101+r.OUTAGE_SECONDS)['warnings'])
        self.accept(now=101+r.OUTAGE_SECONDS)
        self.accept(now=102+r.OUTAGE_SECONDS)
        self.assertIn('outage_history_may_be_unavailable', self.page(now=102+r.OUTAGE_SECONDS)['warnings'])

    def test_clock_regression_rejected(self):
        self.accept(event())
        with self.assertRaises(r.Rejected):
            self.accept(event(11), now=99)
        with self.assertRaises(r.Rejected):
            self.page(now=99)
        self.assertEqual(self.store.poll_plan()['offset'], 11)

    def test_snapshot_pagination_is_bounded_and_read_only(self):
        self.accept(*[event(i, '\U0001f600'*4096) for i in range(10, 17)])
        before = self.store.poll_plan()
        first = self.page()
        self.accept(event(17))
        second = self.page(after=first['next_after'], through=first['through'])
        self.assertEqual([i['update_id'] for i in first['items']+second['items']], [str(i) for i in range(10, 17)])
        self.assertIsNone(second['next_after'])
        self.assertEqual(before['offset']+1, self.store.poll_plan()['offset'])
        self.assertLessEqual(len(self.store.page(now=100)), r.MAX_PAGE_BYTES)
        self.assertEqual(len(self.page()['items']), 5)

    def test_page_skips_ignored_events_without_losing_next_visible(self):
        self.accept(event(10), event(11, channel=-123), event(12))
        first = self.page(limit=1)
        second = self.page(limit=1, after=first['next_after'], through=first['through'])
        self.assertEqual(second['items'][0]['update_id'], '12')
        self.assertIsNone(second['next_after'])

    def test_page_parameters_fail_closed(self):
        for kwargs in ({'limit': 0}, {'limit': 6}, {'after': True}, {'after': 1}, {'through': 1}):
            with self.subTest(kwargs=kwargs), self.assertRaises(r.Rejected):
                self.page(**kwargs)
        self.assertFalse(self.store.db.in_transaction)

    def test_provider_ids_and_timestamps_remain_exact_decimal_strings(self):
        value = event(r.MAX_ID - 1)
        value['channel_post']['date'] = r.MAX_TIME
        self.accept(value)
        item = self.page()['items'][0]
        self.assertEqual(item['update_id'], str(r.MAX_ID - 1))
        self.assertEqual(item['message_id'], str(r.MAX_ID))
        self.assertEqual(item['posted_at'], str(r.MAX_TIME))
        self.assertIs(type(item['seq']), int)

    def test_capacity_rolls_back_whole_batch(self):
        self.accept(event())
        with patch.object(r, 'MAX_EVENTS', 2):
            self.unchanged_on_rejection(response(event(11), event(12)))

    def test_sqlite_full_never_advances_cursor(self):
        # A real SQLITE_FULL failure at SQLite's enforced page-count boundary.
        self.store.db.execute('PRAGMA max_page_count=3')
        raw = response(*[event(i, 'x'*4096) for i in range(10, 20)])
        with self.assertRaises(sqlite3.OperationalError):
            self.store.accept_response(raw, None, 100)
        self.assertIsNone(self.store.poll_plan()['offset'])
        self.assertEqual(self.page()['items'], [])

    def test_content_and_cursor_rollback_on_injected_exception(self):
        for target in ('after_content', 'before_commit'):
            def fail(stage):
                if stage == target:
                    raise RuntimeError('synthetic failure')
            with self.subTest(stage=target), self.assertRaises(RuntimeError):
                self.store.accept_response(response(event()), None, 100, _fault=fail)
            self.assertIsNone(self.store.poll_plan()['offset'])
            self.assertEqual(self.page()['items'], [])

    def test_process_crash_before_and_after_commit(self):
        # This is process termination, not a power-loss or failing-hardware test.
        code = '''import os,sys
from inbox import Inbox
db=Inbox(sys.argv[1], -1000000000001)
def crash(stage):
    if stage == sys.argv[2]: os._exit(73)
db.accept_response(sys.argv[3].encode(), None, 100, _fault=crash)
'''
        for target in ('after_content', 'before_commit', 'after_commit'):
            with self.subTest(stage=target):
                path = Path(self.temp.name)/target
                run = subprocess.run([sys.executable, '-c', code, str(path), target,
                                      response(event()).decode()], timeout=10,
                                     cwd=Path(r.__file__).parent, capture_output=True)
                self.assertEqual(run.returncode, 73, run.stderr)
                db = r.Inbox(path, CHANNEL)
                try:
                    committed = target == 'after_commit'
                    self.assertEqual(db.poll_plan()['offset'], 11 if committed else None)
                    self.assertEqual(len(json.loads(db.page(now=100))['items']), int(committed))
                    db.accept_response(response(event()), db.poll_plan()['offset'], 100)
                    self.assertEqual(len(json.loads(db.page(now=100))['items']), 1)
                    self.assertEqual(db.db.execute('PRAGMA integrity_check').fetchone(), ('ok',))
                finally:
                    db.close()

    def test_store_private_and_channel_pinned(self):
        self.assertEqual(self.path.stat().st_mode & 0o777, 0o700)
        self.assertEqual((self.path/'inbox.sqlite3').stat().st_mode & 0o777, 0o600)
        with self.assertRaises(r.Rejected):
            r.Inbox(self.path, -1000000000002)
        self.assertEqual(self.store.db.execute('SELECT channel_id FROM state').fetchone()[0], CHANNEL)

    def test_store_rejects_symlink_hardlink_and_shared_directory(self):
        link = Path(self.temp.name)/'link'
        link.symlink_to(self.path, target_is_directory=True)
        with self.assertRaises(r.Rejected): r.Inbox(link, CHANNEL)
        shared = Path(self.temp.name)/'shared'
        shared.mkdir(mode=0o755)
        with self.assertRaises(r.Rejected): r.Inbox(shared, CHANNEL)
        alien = self.path/'alien'
        alien.write_text('synthetic')
        with self.assertRaises(r.Rejected): r.Inbox(self.path, CHANNEL)
        alien.unlink()
        hardlink = Path(self.temp.name)/'linked-database'
        os.link(self.path/'inbox.sqlite3', hardlink)
        with self.assertRaises(r.Rejected): r.Inbox(self.path, CHANNEL)


if __name__ == '__main__':
    unittest.main()

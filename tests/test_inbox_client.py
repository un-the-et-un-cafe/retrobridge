# SPDX-License-Identifier: MPL-2.0
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
import copy
import json
from pathlib import Path
import tempfile
import unittest

from inbox import Inbox, Rejected
from inbox_client import Client, validate_page
from test_inbox import CHANNEL, event, response


class ClientTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.store = Inbox(Path(self.temp.name) / 'store', CHANNEL)
        self.client = Client()

    def tearDown(self):
        self.store.close()
        self.temp.cleanup()

    def accept(self, *events):
        self.store.accept_response(response(*events), self.store.poll_plan()['offset'], 100)

    def finish(self, request):
        raw = self.store.page(now=100, after=request['after'], through=request['through'])
        return self.client.complete(request['generation'], raw)

    def test_empty_before_poll_preserves_warnings(self):
        page = self.finish(self.client.refresh())
        self.assertEqual(page['items'], [])
        self.assertIn('not_yet_polled', page['warnings'])
        with self.assertRaises(Rejected):
            self.client.next_page()

    def test_terminal_visible_page_can_end_before_ignored_high_water(self):
        self.accept(event(10), event(11, channel=CHANNEL - 1))
        page = self.finish(self.client.refresh())
        self.assertEqual(page['through'], 2)
        self.assertEqual(page['items'][-1]['seq'], 1)
        self.assertIsNone(page['next_after'])

    def test_all_ignored_snapshot_has_empty_terminal_page(self):
        self.accept(event(10, channel=CHANNEL - 1))
        page = self.finish(self.client.refresh())
        self.assertEqual(page['through'], 1)
        self.assertEqual(page['items'], [])
        self.assertIsNone(page['next_after'])

    def test_snapshot_paging_new_arrivals_and_refresh(self):
        self.accept(*(event(i) for i in range(10, 22)))
        first = self.finish(self.client.refresh())
        self.assertEqual(len(first['items']), 5)
        self.accept(event(22))
        seen = [i['seq'] for i in first['items']]
        while self.client.page['next_after'] is not None:
            page = self.finish(self.client.next_page())
            self.assertEqual(page['through'], first['through'])
            seen.extend(i['seq'] for i in page['items'])
        self.assertEqual(seen, list(range(1, 13)))
        self.assertEqual(self.finish(self.client.refresh())['through'], 13)
        self.assertEqual(self.store.poll_plan()['offset'], 23)

    def test_cancel_and_older_refresh_cannot_overwrite(self):
        self.accept(event())
        first = self.client.refresh()
        second = self.client.refresh()
        wire = self.store.page(now=100)
        with self.assertRaises(Rejected):
            self.client.complete(first['generation'], wire)
        self.client.complete(second['generation'], wire)
        before = self.client.page
        pending = self.client.refresh()
        self.client.cancel()
        with self.assertRaises(Rejected):
            self.client.complete(pending['generation'], wire)
        self.assertEqual(before, self.client.page)

    def test_duplicate_completion_and_repeated_next(self):
        self.accept(*(event(i) for i in range(10, 17)))
        request = self.client.refresh()
        self.finish(request)
        with self.assertRaises(Rejected):
            self.finish(request)
        self.client.next_page()
        with self.assertRaises(Rejected):
            self.client.next_page()

    def test_invalid_response_is_atomic_and_retryable(self):
        self.accept(event())
        self.finish(self.client.refresh())
        before = self.client.page
        request = self.client.refresh()
        with self.assertRaises(Rejected):
            self.client.complete(request['generation'], b'{}')
        self.assertEqual(before, self.client.page)
        self.finish(request)

    def test_returned_data_cannot_change_state(self):
        self.accept(event())
        page = self.finish(self.client.refresh())
        page['through'] = 999
        page['items'][0]['text'] = 'modified'
        self.assertNotEqual(page, self.client.page)

    def test_large_ids_ascii_conversion_and_unsupported(self):
        e = event(4503599627370493, 'a\n雪' + 'b' * 200)
        protected = event(4503599627370494)
        protected['channel_post']['message_id'] = 4503599627370494
        protected['channel_post']['has_protected_content'] = True
        self.accept(e, protected)
        page = self.finish(self.client.refresh())
        a, b = page['items']
        self.assertEqual(a['update_id'], '4503599627370493')
        self.assertTrue(a['encoding_loss'])
        self.assertTrue(a['truncated'])
        self.assertEqual(b['detail'], 'protected_content')

    def test_reject_contract_field_mutations(self):
        self.accept(event())
        page = json.loads(self.store.page(now=100))
        bad_values = {
            'contract': ['unknown', None, 1], 'read_only': [False, 1],
            'through': [True, -1, 1001, '1'],
            'next_after': [True, 0, 1, 2, '1'],
            'items': [{}, None, page['items'] * 6],
            'warnings': [[], ['history_not_complete'], ['unknown'],
                         page['warnings'] + [page['warnings'][0]]],
        }
        for field, values in bad_values.items():
            for value in values:
                with self.subTest(field=field, value=value):
                    bad = copy.deepcopy(page)
                    bad[field] = value
                    with self.assertRaises(Rejected):
                        validate_page(json.dumps(bad).encode())

    def test_reject_item_mutations(self):
        self.accept(event())
        page = json.loads(self.store.page(now=100))
        bad_values = {
            'seq': [0, 2, True, '1'],
            'update_id': [10, '01', '-1', '1.0', '1e2', '9' * 17, '٤'],
            'message_id': ['0'], 'posted_at': ['253402300800'],
            'kind': ['unknown', {}], 'status': ['unknown'],
            'detail': ['unknown'], 'text': ['', 'x' * 161, '\n', '\x1b[2J', '雪'],
            'encoding_loss': [0, 'false'], 'truncated': [1, None],
        }
        for field, values in bad_values.items():
            for value in values:
                with self.subTest(field=field, value=value):
                    bad = copy.deepcopy(page)
                    bad['items'][0][field] = value
                    with self.assertRaises(Rejected):
                        validate_page(json.dumps(bad).encode())

    def test_invalid_encodings_duplicate_keys_and_bounds(self):
        for raw in [b'', b' ' * 4097, b'\xff', b'{"x":1,"x":2}',
                    b'[' * 17 + b']' * 17, b'{"x":NaN}', '{}']:
            with self.subTest(raw=str(raw)[:40]), self.assertRaises(Rejected):
                validate_page(raw)

    def test_wrong_snapshot_and_nonmonotonic_items(self):
        self.accept(event(10), event(11))
        raw = self.store.page(now=100)
        with self.assertRaises(Rejected):
            validate_page(raw, through=1)
        page = json.loads(raw)
        page['items'].reverse()
        with self.assertRaises(Rejected):
            validate_page(json.dumps(page).encode())


if __name__ == '__main__':
    unittest.main()

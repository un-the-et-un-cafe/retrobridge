# SPDX-License-Identifier: MPL-2.0
"""Offline reference client state. No sockets, credentials or native UI.

One bounded page is retained. Request generations prevent a cancelled or older
response from changing the visible snapshot. This is not authentication.
"""
import json

from inbox import MAX_ID, MAX_TIME, Rejected, _bounded_json, integer

WARNINGS = {'history_not_complete', 'trusted_gateway_plaintext_not_e2ee',
            'not_yet_polled', 'outage_history_may_be_unavailable'}
REQUIRED = {'history_not_complete', 'trusted_gateway_plaintext_not_e2ee'}
ITEM_FIELDS = {'seq', 'update_id', 'message_id', 'posted_at', 'kind', 'status',
               'detail', 'text', 'encoding_loss', 'truncated'}


def _decimal(value, low, high):
    if (type(value) is not str or not 1 <= len(value) <= 16 or
            any(c not in '0123456789' for c in value) or
            (len(value) > 1 and value[0] == '0')):
        raise Rejected('invalid decimal text')
    integer(int(value), low, high)


def validate_page(raw, *, after=0, through=None):
    """Validate the entire proposed gateway page before exposing any content."""
    integer(after, 0, 1000)
    if through is not None:
        integer(through, after, 1000)
    if type(raw) is not bytes or not 1 <= len(raw) <= 4096:
        raise Rejected('invalid page size')
    if any(b > 127 for b in raw):
        raise Rejected('page must be ASCII JSON')
    page = _bounded_json(raw)
    if (type(page) is not dict or set(page) !=
            {'contract', 'read_only', 'through', 'next_after', 'items', 'warnings'} or
            page['contract'] != 'retrobridge-inbox/1' or page['read_only'] is not True):
        raise Rejected('unsupported client contract')
    high = integer(page['through'], after, 1000)
    if through is not None and high != through:
        raise Rejected('snapshot changed')
    warnings = page['warnings']
    if (type(warnings) is not list or not 2 <= len(warnings) <= 4 or
            any(type(w) is not str or w not in WARNINGS for w in warnings) or
            len(set(warnings)) != len(warnings) or not REQUIRED <= set(warnings)):
        raise Rejected('missing or unknown warning')
    items = page['items']
    if type(items) is not list or len(items) > 5:
        raise Rejected('too many items')
    previous = after
    for item in items:
        if type(item) is not dict or set(item) != ITEM_FIELDS:
            raise Rejected('invalid item shape')
        previous = integer(item['seq'], previous + 1, high)
        _decimal(item['update_id'], 0, MAX_ID)
        _decimal(item['message_id'], 1, MAX_ID)
        _decimal(item['posted_at'], 0, MAX_TIME)
        if item['kind'] not in ('channel_post', 'edited_channel_post'):
            raise Rejected('unknown item kind')
        if item['status'] == 'text':
            if item['detail'] not in ('', 'extra_fields_omitted'):
                raise Rejected('unknown text detail')
        elif item['status'] == 'unsupported':
            if (item['detail'] not in ('non_text', 'protected_content') or
                    item['text'] != '[unsupported content]'):
                raise Rejected('invalid unsupported indicator')
        else:
            raise Rejected('unknown item status')
        if (type(item['text']) is not str or not 1 <= len(item['text']) <= 160 or
                any(not ' ' <= c <= '~' for c in item['text']) or
                type(item['encoding_loss']) is not bool or type(item['truncated']) is not bool):
            raise Rejected('invalid display text or flags')
    next_after = page['next_after']
    if next_after is not None:
        integer(next_after, after + 1, high)
        if not items or next_after != previous or next_after >= high:
            raise Rejected('nonadvancing page cursor')
    return page


class Client:
    """Inert request plans and atomic visible-page replacement only."""
    def __init__(self):
        self._generation = 0
        self._pending = None
        self._page = None

    @property
    def page(self):
        # Callers cannot mutate stored cursors through a returned dictionary.
        return None if self._page is None else json.loads(json.dumps(self._page))

    def _request(self, after, through):
        self._generation += 1
        self._pending = (self._generation, after, through)
        return {'generation': self._generation, 'after': after,
                'through': through, 'limit': 5}

    def refresh(self):
        return self._request(0, None)

    def next_page(self):
        if self._pending is not None:
            raise Rejected('request already pending')
        if self._page is None or self._page['next_after'] is None:
            raise Rejected('no next page')
        return self._request(self._page['next_after'], self._page['through'])

    def cancel(self):
        self._generation += 1
        self._pending = None

    def complete(self, generation, raw):
        if (type(generation) is not int or self._pending is None or
                generation != self._pending[0]):
            raise Rejected('stale client response')
        _, after, through = self._pending
        # Invalid input leaves the last accepted page intact. Caller can cancel
        # or refresh; malformed content never advances a cursor.
        page = validate_page(raw, after=after, through=through)
        self._page = page
        self._pending = None
        return self.page

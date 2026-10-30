# SPDX-License-Identifier: MPL-2.0
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""Run only the fixed synthetic inbox fixture; never fetches or sends anything."""
import argparse
from pathlib import Path
import sys
from inbox import Inbox, MAX_RESPONSE


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory', type=Path, help='new private synthetic-store directory')
    args = parser.parse_args()
    if args.directory.exists() or args.directory.is_symlink():
        parser.error('demo requires a new directory; no existing data is overwritten')
    store = Inbox(args.directory, -1000000000001)
    try:
        with (Path(__file__).parent/'fixtures/telegram-synthetic.json').open('rb') as src:
            raw = src.read(MAX_RESPONSE + 1)
        store.accept_response(raw, store.poll_plan()['offset'], 1000)
        sys.stdout.buffer.write(store.page(now=1000))
    finally:
        store.close()


if __name__ == '__main__':
    main()

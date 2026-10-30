"""Print local Codex main-chat activity as JSON, without changing Codex files."""
import argparse
from datetime import datetime, timezone
import json
import time

from codex_activity import read_chat_activity
from codex_titles import read_chat_titles


def snapshot():
    activity = read_chat_activity()
    running = {} if activity is None else {
        session: row for session, row in activity.items()
        if row.get('status') == 'inProgress' and row.get('completed_at') is None
    }
    names = read_chat_titles(running)
    return {
        'observed_at': datetime.now(timezone.utc).isoformat(),
        'available': activity is not None,
        'active_count': None if activity is None else len(running),
        'active_chats': None if activity is None else [
            {'session_id': session, 'name': names.get(session), **row}
            for session, row in running.items()
        ],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--watch', action='store_true')
    parser.add_argument('--interval', type=float, default=2.0)
    args = parser.parse_args()
    if args.interval <= 0:
        parser.error('--interval must be greater than zero')
    try:
        while True:
            result = snapshot()
            print(json.dumps(result, ensure_ascii=False), flush=True)
            if not args.watch:
                return 0 if result['available'] else 1
            time.sleep(args.interval)
    except KeyboardInterrupt:
        return 0


if __name__ == '__main__':
    raise SystemExit(main())

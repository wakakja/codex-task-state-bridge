"""Read current local Codex main-chat turn status without reading chat items."""
import os
import sqlite3
from pathlib import Path


def _latest_database(home,prefix):
    candidates=[]
    for path in home.glob(prefix+'_*.sqlite'):
        version=path.stem.removeprefix(prefix+'_')
        if version.isdigit() and path.is_file():
            candidates.append((int(version),path))
    return max(candidates,key=lambda value:value[0])[1] if candidates else None


def _connect(path):
    connection=sqlite3.connect(path.resolve().as_uri()+'?mode=ro',uri=True,timeout=.1)
    try:
        connection.execute('PRAGMA query_only=ON')
    except sqlite3.Error:
        connection.close()
        raise
    return connection


def _main_chat_ids(database):
    connection=_connect(database)
    try:
        columns={row[1] for row in connection.execute('PRAGMA table_info(threads)')}
        if not {'id','thread_source','agent_path','archived'}<=columns:
            return None
        optional=('source','thread_source','agent_path','archived')
        fields=','.join(name if name in columns else 'NULL AS '+name for name in optional)
        ids=set()
        for session_id,source,thread_source,agent_path,archived in connection.execute('SELECT id,'+fields+' FROM threads'):
            if archived!=0 or agent_path or thread_source!='user':
                continue
            source=str(source or '').lower()
            if 'subagent' in source or 'guardian_review' in source:
                continue
            if isinstance(session_id,str) and session_id:
                ids.add(session_id)
        has_edges=connection.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='thread_spawn_edges'").fetchone()
        if has_edges:
            ids.difference_update(row[0] for row in connection.execute('SELECT child_thread_id FROM thread_spawn_edges'))
        return ids
    finally:
        connection.close()


def read_chat_activity()->dict[str,dict] | None:
    """Return each main chat's latest recorded turn, including terminal states.

    None means unavailable/locked/unsupported and must not be treated as no
    active chats. Reads use the live WAL and never inspect message content.
    """
    connection=None
    try:
        home=Path(os.environ.get('CODEX_HOME') or Path.home()/'.codex').expanduser()
        history=_latest_database(home,'thread_history')
        state=_latest_database(home,'state')
        if history is None or state is None:
            return None
        main_ids=_main_chat_ids(state)
        if main_ids is None:
            return None
        if not main_ids:
            return {}
        connection=_connect(history)
        columns={row[1] for row in connection.execute('PRAGMA table_info(thread_turns)')}
        if not {'thread_id','turn_id','status','rollout_ordinal','completed_at'}<=columns:
            return None
        ids=sorted(main_ids)
        activity={}
        for offset in range(0,len(ids),100):
            batch=ids[offset:offset+100]
            placeholders=','.join('?' for _ in batch)
            query=(f'SELECT t.thread_id,t.turn_id,t.status,t.completed_at FROM thread_turns t '
                   f'WHERE t.thread_id IN ({placeholders}) AND NOT EXISTS '
                   '(SELECT 1 FROM thread_turns newer WHERE newer.thread_id=t.thread_id '
                   'AND newer.rollout_ordinal>t.rollout_ordinal)')
            for session_id,turn_id,status,completed_at in connection.execute(query,batch):
                activity[session_id]={'turn_id':turn_id,'status':status,
                                      'completed_at':completed_at}
        return activity
    except (OSError,sqlite3.Error,ValueError):
        return None
    finally:
        if connection is not None:
            connection.close()

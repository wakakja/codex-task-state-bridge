"""Read the names of specified local Codex chats without reading messages."""
import os
import sqlite3
from pathlib import Path


def read_chat_titles(session_ids)->dict[str,str]:
    """Return available display names keyed by Codex session id.

    Connections stay read-only and use the live WAL so newly created or renamed
    chats remain visible. Missing databases, schema changes and locks are benign.
    """
    session_ids=list(dict.fromkeys(value for value in session_ids
                                  if isinstance(value,str) and value))
    if not session_ids:
        return {}
    connection=None
    try:
        home=Path(os.environ.get('CODEX_HOME') or Path.home()/'.codex').expanduser()
        databases=[]
        for path in home.glob('state_*.sqlite'):
            version=path.stem.removeprefix('state_')
            if version.isdigit() and path.is_file():
                databases.append((int(version),path))
        if not databases:
            return {}
        database=max(databases,key=lambda item:item[0])[1]
        connection=sqlite3.connect(database.resolve().as_uri()+'?mode=ro',
                                   uri=True,timeout=.1)
        connection.execute('PRAGMA query_only=ON')
        columns={row[1] for row in connection.execute('PRAGMA table_info(threads)')}
        if 'id' not in columns or not {'name','title'}&columns:
            return {}
        name_column='name' if 'name' in columns else 'NULL'
        title_column='title' if 'title' in columns else 'NULL'
        names={}
        for offset in range(0,len(session_ids),100):
            ids=session_ids[offset:offset+100]
            placeholders=','.join('?' for _ in ids)
            query=f'SELECT id,{name_column},{title_column} FROM threads WHERE id IN ({placeholders})'
            for session_id,name,title in connection.execute(query,ids):
                for value in (name,title):
                    display=' '.join(value.split()) if isinstance(value,str) else ''
                    if display:
                        names[session_id]=display
                        break
        return names
    except (OSError,sqlite3.Error,ValueError):
        return {}
    finally:
        if connection is not None:
            connection.close()

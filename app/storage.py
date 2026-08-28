import sqlite3
import uuid
import json
import threading
from datetime import datetime, timezone
from app.config import get_db_path


def now_iso():
    return datetime.now(timezone.utc).isoformat()


class storage:
    def __init__(self):
        self.path = get_db_path()
        self.conn = sqlite3.connect(self.path, check_same_thread=False)
        self.conn.execute("pragma foreign_keys = on")
        self.init_db()

    def init_db(self):
        cur = self.conn.cursor()
        cur.execute("""
            create table if not exists conversations (
                id text primary key,
                title text not null,
                created_at text not null,
                updated_at text not null
            )
        """)
        cur.execute("""
            create table if not exists messages (
                id text primary key,
                conversation_id text not null,
                role text not null,
                content text not null,
                timestamp text not null,
                foreign key (conversation_id) references conversations(id) on delete cascade
            )
        """)
        self.conn.commit()

    def create_conversation(self, title="new conversation"):
        conv_id = str(uuid.uuid4())
        ts = now_iso()
        self.conn.execute(
            "insert into conversations (id, title, created_at, updated_at) values (?, ?, ?, ?)",
            (conv_id, title, ts, ts)
        )
        self.conn.commit()
        return conv_id

    def list_conversations(self, search=None):
        cur = self.conn.cursor()
        if search:
            like = "%" + search + "%"
            cur.execute(
                "select id, title, created_at, updated_at from conversations where title like ? order by updated_at desc",
                (like,)
            )
        else:
            cur.execute(
                "select id, title, created_at, updated_at from conversations order by updated_at desc"
            )
        rows = cur.fetchall()
        return [
            {"id": r[0], "title": r[1], "created_at": r[2], "updated_at": r[3]}
            for r in rows
        ]

    def rename_conversation(self, conv_id, title):
        self.conn.execute(
            "update conversations set title = ?, updated_at = ? where id = ?",
            (title, now_iso(), conv_id)
        )
        self.conn.commit()

    def delete_conversation(self, conv_id):
        self.conn.execute("delete from messages where conversation_id = ?", (conv_id,))
        self.conn.execute("delete from conversations where id = ?", (conv_id,))
        self.conn.commit()
        threading.Thread(target=self._scrub, daemon=True).start()

    def _scrub(self):
        try:
            c = sqlite3.connect(self.path, timeout=30)
            try:
                c.execute("pragma busy_timeout=30000")
                c.execute("pragma wal_checkpoint(truncate)")
                c.execute("vacuum")
                c.execute("pragma wal_checkpoint(truncate)")
                c.commit()
            finally:
                c.close()
        except Exception:
            pass

    def touch_conversation(self, conv_id):
        self.conn.execute(
            "update conversations set updated_at = ? where id = ?",
            (now_iso(), conv_id)
        )
        self.conn.commit()

    def get_messages(self, conv_id):
        cur = self.conn.cursor()
        cur.execute(
            "select id, role, content, timestamp from messages where conversation_id = ? order by timestamp asc",
            (conv_id,)
        )
        rows = cur.fetchall()
        return [
            {"id": r[0], "role": r[1], "content": r[2], "timestamp": r[3]}
            for r in rows
        ]

    def add_message(self, conv_id, role, content):
        msg_id = str(uuid.uuid4())
        ts = now_iso()
        self.conn.execute(
            "insert into messages (id, conversation_id, role, content, timestamp) values (?, ?, ?, ?, ?)",
            (msg_id, conv_id, role, content, ts)
        )
        self.touch_conversation(conv_id)
        return {"id": msg_id, "role": role, "content": content, "timestamp": ts}

    def delete_last_assistant_message(self, conv_id):
        cur = self.conn.cursor()
        cur.execute(
            "select id from messages where conversation_id = ? and role = 'assistant' order by timestamp desc limit 1",
            (conv_id,)
        )
        row = cur.fetchone()
        if row:
            self.conn.execute("delete from messages where id = ?", (row[0],))
            self.conn.commit()

    def export_conversation(self, conv_id, filepath):
        cur = self.conn.cursor()
        cur.execute("select title, created_at, updated_at from conversations where id = ?", (conv_id,))
        row = cur.fetchone()
        if not row:
            raise ValueError("conversation not found")
        data = {
            "id": conv_id,
            "title": row[0],
            "created_at": row[1],
            "updated_at": row[2],
            "messages": self.get_messages(conv_id)
        }
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def import_conversation(self, filepath):
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        conv_id = str(uuid.uuid4())
        ts = now_iso()
        title = data.get("title", "imported conversation")
        self.conn.execute(
            "insert into conversations (id, title, created_at, updated_at) values (?, ?, ?, ?)",
            (conv_id, title, ts, ts)
        )
        for m in data.get("messages", []):
            msg_id = str(uuid.uuid4())
            self.conn.execute(
                "insert into messages (id, conversation_id, role, content, timestamp) values (?, ?, ?, ?, ?)",
                (msg_id, conv_id, m.get("role", "user"), m.get("content", ""), m.get("timestamp", ts))
            )
        self.conn.commit()
        return conv_id

import os
import re
import math
import json
import time
import threading
import sqlite3

import requests

try:
    import pymupdf
except ImportError:
    import fitz as pymupdf

STOPWORDS = frozenset("""
a about above after again against all am an and any are aren't as at be because been before being below between both
but by can can't cannot could couldn't did didn't do does doesn't doing don't down during each few for from further
had hadn't has hasn't have haven't having he he'd he'll he's her here here's hers herself him himself his how how's i
i'd i'll i'm i've if in into is isn't it it's its itself let's me more most mustn't my myself no nor not of off on
once only or other ought our ours ourselves out over own same shan't she she'd she'll she's should shouldn't so some
such than that that's the their theirs them themselves then there there's these they they'd they'll they're they've
this those through to too under until up very was wasn't we we'd we'll we're we've were weren't what what's when
when's where where's which while who who's whom why why's with won't would wouldn't you you'd you'll you're you've
your yours yourself yourselves
""".split())

K1 = 1.8
B = 0.75
CHUNK_SIZE = 1100
CHUNK_OVERLAP = 120
BM25_CANDIDATES = 60
EMBED_RELINK = 40


def tokenize(text):
    return [t for t in re.findall(r"[a-z0-9']+", text.lower()) if len(t) > 1]


def get_default_rag_source_dir():
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(os.path.dirname(here), "cbt")


class rag_index:
    def __init__(self, db_path, source_dir=None):
        self.db_path = db_path
        self.source_dir = source_dir or get_default_rag_source_dir()
        self._lock = threading.Lock()
        self._ready = False
        self._doc_len = {}
        self._build_conn = sqlite3.connect(db_path, check_same_thread=False)
        self._build_conn.execute("pragma journal_mode=wal")
        self._build_conn.execute("pragma busy_timeout=30000")
        self._init_tables()

    def _init_tables(self):
        cur = self._build_conn.cursor()
        cur.execute("""
            create table if not exists rag_chunks (
                id integer primary key autoincrement,
                source text not null,
                page integer,
                text text not null,
                doc_len integer not null
            )
        """)
        cur.execute("""
            create table if not exists rag_terms (
                chunk_id integer not null,
                term text not null,
                tf integer not null
            )
        """)
        cur.execute("create index if not exists idx_rag_terms_term on rag_terms (term)")
        cur.execute("create index if not exists idx_rag_terms_chunk on rag_terms (chunk_id)")
        cur.execute("create table if not exists rag_meta (key text primary key, value text)")
        self._build_conn.commit()

    def _file_signature(self, path):
        st = os.stat(path)
        return "%d|%d" % (int(st.st_mtime), st.st_size)

    def _chunks(self, text):
        out = []
        for para in re.split(r"\n+", text):
            para = re.sub(r"\s+", " ", para).strip()
            if not para:
                continue
            while len(para) > CHUNK_SIZE:
                cut = para[:CHUNK_SIZE]
                sp = cut.rfind(" ")
                if sp < CHUNK_SIZE * 0.5:
                    sp = CHUNK_SIZE
                out.append(cut[:sp].strip())
                para = para[sp:]
            if para.strip():
                out.append(para.strip())
        return out

    def _index_pdf(self, path):
        doc = pymupdf.open(path)
        try:
            rows = []
            page = 1
            for i in range(doc.page_count):
                text = doc.load_page(i).get_text()
                for chunk in self._chunks(text):
                    counts = {}
                    for t in tokenize(chunk):
                        if t in STOPWORDS:
                            continue
                        counts[t] = counts.get(t, 0) + 1
                    rows.append((os.path.abspath(path), page, chunk, counts))
                page += 1
            return rows
        finally:
            doc.close()

    def _rebuild_one(self, path, meta_key):
        try:
            rows = self._index_pdf(path)
        except Exception:
            return
        cur = self._build_conn.cursor()
        cur.execute("delete from rag_chunks where source = ?", (os.path.abspath(path),))
        cur.execute("delete from rag_terms where chunk_id not in (select id from rag_chunks)")
        term_rows = []
        for src, pg, txt, counts in rows:
            cur.execute(
                "insert into rag_chunks (source, page, text, doc_len) values (?, ?, ?, ?)",
                (src, pg, txt, len(counts))
            )
            rid = cur.lastrowid
            for t, tf in counts.items():
                term_rows.append((rid, t, tf))
        cur.executemany("insert into rag_terms (chunk_id, term, tf) values (?, ?, ?)", term_rows)
        cur.execute(
            "insert or replace into rag_meta (key, value) values (?, ?)",
            (meta_key, "%s|%d" % (self._file_signature(path), len(rows)))
        )
        self._build_conn.commit()

    def background_build(self):
        with self._lock:
            self._scan_and_build()
            self._load_stats()
            self._ready = True

    def _scan_and_build(self):
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        if not os.path.isdir(self.source_dir):
            return
        cur = self._build_conn.cursor()
        for name in os.listdir(self.source_dir):
            if not name.lower().endswith(".pdf"):
                continue
            path = os.path.join(self.source_dir, name)
            meta_key = "file|" + os.path.abspath(path)
            sig = self._file_signature(path)
            row = cur.execute("select value from rag_meta where key = ?", (meta_key,)).fetchone()
            if row:
                old_sig, old_count = row[0].rsplit("|", 1)
                if old_sig == sig:
                    try:
                        cnt = cur.execute(
                            "select count(*) from rag_chunks where source = ?",
                            (os.path.abspath(path),)
                        ).fetchone()[0]
                        if cnt == int(old_count):
                            continue
                    except Exception:
                        continue
            self._rebuild_one(path, meta_key)

    def _load_stats(self):
        cur = self._build_conn.cursor()
        total = cur.execute("select count(*), coalesce(avg(doc_len), 0) from rag_chunks").fetchone()
        self._n = total[0]
        self._avgdl = total[1] or 1
        rows = cur.execute("select id, doc_len from rag_chunks").fetchall()
        self._doc_len = {i: d for i, d in rows}
        self._ready = bool(self._n)

    def _bm25(self, query, limit=BM25_CANDIDATES):
        if not self._ready:
            return []
        terms = [t for t in tokenize(query) if t not in STOPWORDS]
        if not terms:
            return []
        conn = sqlite3.connect(self.db_path)
        candidates = {}
        found_docs = 0
        try:
            for term in set(terms):
                rows = conn.execute(
                    "select chunk_id, tf from rag_terms where term = ?", (term,)
                ).fetchall()
                df = len(rows)
                if not df:
                    continue
                idf = math.log(1 + (self._n - df + 0.5) / (df + 0.5))
                for cid, tf in rows:
                    cand = candidates.get(cid)
                    if cand is None:
                        cand = candidates[cid] = {}
                        found_docs += 1
                    cand[term] = (tf, idf)
                if found_docs > 4000:
                    break
            if not candidates:
                return []
            scores = []
            for cid, termdict in candidates.items():
                dl = self._doc_len.get(cid, self._avgdl)
                denom = K1 * (1 - B + B * dl / self._avgdl)
                s = 0.0
                for tf, idf in termdict.values():
                    s += idf * (tf * (K1 + 1)) / (tf + denom)
                scores.append((s, cid))
            scores.sort(key=lambda x: x[0], reverse=True)
            return scores[:limit]
        finally:
            conn.close()

    def _fetch(self, cids):
        if not cids:
            return []
        conn = sqlite3.connect(self.db_path)
        try:
            ph = ",".join("?" * len(cids))
            rows = conn.execute(
                "select id, source, page, text from rag_chunks where id in (" + ph + ")",
                list(cids)
            ).fetchall()
        finally:
            conn.close()
        by_id = {i: (src, pg, txt) for i, src, pg, txt in rows}
        out = []
        for cid in cids:
            item = by_id.get(cid)
            if item:
                out.append({"id": cid, "source": item[0], "page": item[1], "text": item[2]})
        return out

    def _embed(self, url, model, texts, timeout=60):
        r = requests.post(
            url.rstrip("/") + "/api/embed",
            json={"model": model, "input": texts},
            timeout=timeout
        )
        if r.status_code != 200:
            raise RuntimeError("embed request failed: %d" % r.status_code)
        return r.json().get("embeddings", [])

    def _cosine(self, a, b):
        dot = sum(x * y for x, y in zip(a, b))
        na = math.sqrt(sum(x * x for x in a)) or 1.0
        nb = math.sqrt(sum(x * x for x in b)) or 1.0
        return dot / (na * nb)

    def retrieve(self, query, top_k=5, url=None, embed_model=None):
        if not query or not self._ready:
            return []
        bm25 = self._bm25(query, EMBED_RELINK if (url and embed_model) else BM25_CANDIDATES)
        if not bm25:
            return []
        cids = [c for _, c in bm25]
        results = self._fetch(cids)
        bm25_score = dict(zip(cids, [s for s, _ in bm25]))
        if url and embed_model:
            try:
                texts = [r["text"] for r in results]
                embs = self._embed(url, embed_model, [query] + texts)
                if embs and len(embs) == len(results) + 1:
                    qv = embs[0]
                    for r, dv in zip(results, embs[1:]):
                        r["score"] = self._cosine(qv, dv)
                    results.sort(key=lambda x: x["score"], reverse=True)
                else:
                    for r in results:
                        r["score"] = bm25_score.get(r["id"], 0.0)
            except Exception:
                for r in results:
                    r["score"] = bm25_score.get(r["id"], 0.0)
                results.sort(key=lambda x: x["score"], reverse=True)
        else:
            for r in results:
                r["score"] = bm25_score.get(r["id"], 0.0)
            results.sort(key=lambda x: x["score"], reverse=True)
        return results[:top_k]

    def format_context(self, results):
        if not results:
            return ""
        parts = []
        for r in results:
            src = os.path.basename(r["source"])
            loc = "p%d" % r["page"] if r["page"] else ""
            parts.append("[%s%s]" % (src, " " + loc if loc else ""))
            parts.append(r["text"].strip() or "(no text)")
        return "\n\n".join(parts)
"""Thin, defensive client for a Databricks Genie space.

Facts this is built around (Databricks docs):
  * Conversation API allows ~5 questions per minute per workspace (POSTs only) -> sliding-window limiter below.
  * Each query result returns at most 5,000 rows.
  * Results can arrive as inline `data_array` or as presigned `external_links` (EXTERNAL_LINKS disposition) -> both are handled.
  * Attachments carry the generated SQL (`attachment.query.query`) and/or text (`attachment.text.content`).
"""
import datetime
import io
import json
import threading
import time
from collections import deque
from dataclasses import dataclass, field
from typing import Optional

import pandas as pd

MAX_ROWS = 5000


class GenieError(RuntimeError):
    pass


@dataclass
class GenieAnswer:
    question: str
    text: str = ""
    sql: str = ""
    description: str = ""
    df: Optional[pd.DataFrame] = None
    conversation_id: str = ""
    message_id: str = ""
    truncated: bool = False
    seconds: float = 0.0
    notes: list = field(default_factory=list)


class RateLimiter:
    """Sliding window: at most `max_calls` per `period` seconds, shared by every thread/session in the process."""

    def __init__(self, max_calls=4, period=60.0):
        self.max_calls, self.period = max_calls, period
        self.calls = deque()
        self.lock = threading.Lock()

    def acquire(self):
        while True:
            with self.lock:
                now = time.monotonic()
                while self.calls and now - self.calls[0] >= self.period:
                    self.calls.popleft()
                if len(self.calls) < self.max_calls:
                    self.calls.append(now)
                    return
                wait = self.period - (now - self.calls[0]) + 0.25
            time.sleep(max(wait, 0.25))


LIMITER = RateLimiter(max_calls=4, period=60.0)   # 4 of the 5 allowed, leaving one for the "Ask Genie" page


def _val(x):
    """Enum or plain string -> plain string."""
    return str(getattr(x, "value", x) or "")


def _rows_from_link(link_url, fmt, columns):
    import requests
    r = requests.get(link_url, timeout=120)          # presigned URL: no Databricks auth header
    r.raise_for_status()
    fmt = fmt.upper()
    if fmt == "ARROW_STREAM":
        import pyarrow as pa
        return pa.ipc.open_stream(io.BytesIO(r.content)).read_all().to_pandas()
    if fmt == "CSV":
        return pd.read_csv(io.BytesIO(r.content), header=None, names=columns, dtype=str)
    return pd.DataFrame(json.loads(r.content), columns=columns)   # JSON_ARRAY


def statement_to_df(w, sr):
    """Turn a StatementResponse (inline or external links, one or many chunks) into a DataFrame of strings/typed values."""
    manifest = getattr(sr, "manifest", None)
    cols_info = list(getattr(getattr(manifest, "schema", None), "columns", None) or [])
    columns = [c.name for c in cols_info]
    if not columns:
        raise GenieError("Genie returned a result without a column schema")
    fmt = _val(getattr(manifest, "format", "JSON_ARRAY")) or "JSON_ARRAY"
    total = int(getattr(manifest, "total_chunk_count", 1) or 1)
    frames = []
    chunk = getattr(sr, "result", None)
    for i in range(total):
        if i > 0:
            chunk = w.statement_execution.get_statement_result_chunk_n(sr.statement_id, i)
        if chunk is None:
            continue
        inline = getattr(chunk, "data_array", None)
        links = getattr(chunk, "external_links", None) or []
        if inline is not None:
            frames.append(pd.DataFrame(inline, columns=columns))
        for ln in links:
            frames.append(_rows_from_link(ln.external_link, fmt, columns))
    if not frames:
        # last resort: ask the statement API directly (some SDK versions only expose the id on the Genie result)
        sid = getattr(sr, "statement_id", None)
        if sid:
            full = w.statement_execution.get_statement(sid)
            res = getattr(full, "result", None)
            inline = getattr(res, "data_array", None)
            if inline is not None:
                frames.append(pd.DataFrame(inline, columns=columns))
    df = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame(columns=columns)
    df.attrs["types"] = {c.name: _val(getattr(c, "type_name", "STRING")).upper() for c in cols_info}
    return df


class GenieSource:
    def __init__(self, space_id, client=None):
        if client is None:
            from databricks.sdk import WorkspaceClient   # credentials come from the Databricks Apps environment
            client = WorkspaceClient()
        self.w, self.space_id = client, space_id

    def _failure_detail(self, conv, mid):
        """Genie only says 'FAILED' from the waiter; the reason lives on the message (error.type / error.error / text attachments)."""
        try:
            m = self.w.genie.get_message(self.space_id, conv, mid)
        except Exception as e:
            return f"(could not read the failed message: {e})"
        parts = []
        err = getattr(m, "error", None)
        if err is not None:
            parts.append(f"{_val(getattr(err, 'type', ''))}: {getattr(err, 'error', err)}".strip(": "))
        for att in (getattr(m, "attachments", None) or []):
            t = getattr(att, "text", None)
            if t is not None and getattr(t, "content", None):
                parts.append(f"Genie said: {t.content}")
        return " | ".join(parts) or f"status {_val(getattr(m, 'status', ''))} with no error detail (try the same question in the Genie space UI)"

    def _send(self, question, conversation_id):
        g = self.w.genie
        starter = getattr(g, "create_message" if conversation_id else "start_conversation", None)
        if starter is None:                      # older SDKs / test doubles: blocking call only
            if conversation_id:
                return g.create_message_and_wait(self.space_id, conversation_id, question)
            return g.start_conversation_and_wait(self.space_id, question)
        waiter = starter(self.space_id, conversation_id, question) if conversation_id else starter(self.space_id, question)
        try:
            return waiter.result(timeout=datetime.timedelta(minutes=10))
        except Exception as e:
            conv = getattr(waiter, "conversation_id", None) or conversation_id
            mid = getattr(waiter, "message_id", None)
            detail = self._failure_detail(conv, mid) if conv and mid else str(e)
            err = GenieError(f"{detail}")
            err.retryable = "no error detail" in detail     # no reason given = likely transient; a named reason (missing table...) is not
            raise err from e

    def ask(self, question, conversation_id=None, retries=3):
        t0 = time.time()
        last = None
        for attempt in range(retries):
            LIMITER.acquire()
            try:
                msg = self._send(question, conversation_id)
                break
            except Exception as e:     # the API does not retry for us
                last = e
                s = str(e).lower()
                transient = any(k in s for k in ("429", "rate", "too many", "exhausted", "throttl", "timeout", "503"))
                if (transient or getattr(e, "retryable", False)) and attempt < retries - 1:
                    time.sleep((15 if transient else 5) * (attempt + 1))
                    continue
                raise GenieError(f"Genie request failed: {e}") from e
        else:
            raise GenieError(f"Genie request failed: {last}")
        err = getattr(msg, "error", None)
        if err:
            raise GenieError(f"Genie could not answer: {getattr(err, 'error', err)}")
        conv = getattr(msg, "conversation_id", "") or conversation_id or ""
        mid = getattr(msg, "message_id", None) or getattr(msg, "id", "")
        ans = GenieAnswer(question=question, conversation_id=conv, message_id=mid)
        att_id = None
        for att in (getattr(msg, "attachments", None) or []):
            q, t = getattr(att, "query", None), getattr(att, "text", None)
            if q is not None and att_id is None:
                att_id = getattr(att, "attachment_id", None) or getattr(att, "id", None)
                ans.sql, ans.description = getattr(q, "query", "") or "", getattr(q, "description", "") or ""
            elif t is not None:
                ans.text = (ans.text + "\n" + (getattr(t, "content", "") or "")).strip()
        if att_id:
            try:
                res = self.w.genie.get_message_attachment_query_result(self.space_id, conv, mid, att_id)
            except Exception:
                # expired attachment: re-run its SQL once
                res = self.w.genie.execute_message_attachment_query(self.space_id, conv, mid, att_id)
            sr = getattr(res, "statement_response", None)
            if sr is None:
                raise GenieError("Genie returned no statement response for the query attachment")
            ans.df = statement_to_df(self.w, sr)
            import re
            m_lim = re.search(r"\blimit\s+(\d+)", ans.sql or "", re.I)
            if m_lim and "select" in (ans.sql or "").lower() and ans.question.lower().startswith("show all"):
                ans.notes.append(f"Genie added LIMIT {m_lim.group(1)} to the SQL, so this table may be incomplete. Add 'no row limit' guidance in the space instructions.")
            ans.truncated = len(ans.df) >= MAX_ROWS
            if ans.truncated:
                ans.notes.append(f"Result reached Genie's {MAX_ROWS:,}-row limit and may be incomplete.")
        ans.seconds = time.time() - t0
        return ans

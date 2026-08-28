import json
import requests
from PyQt5.QtCore import QThread, pyqtSignal


def test_connection(url, timeout=3):
    try:
        r = requests.get(url.rstrip("/") + "/api/tags", timeout=timeout)
    except requests.exceptions.RequestException:
        return False, []
    if r.status_code != 200:
        return False, []
    try:
        data = r.json()
    except ValueError:
        return False, []
    return True, data.get("models", [])


def model_exists(url, model_name):
    ok, models = test_connection(url)
    if not ok:
        return False
    names = [m.get("name", "") for m in models]
    for n in names:
        if n == model_name or n.startswith(model_name + ":"):
            return True
    return False


class chatworker(QThread):
    token_received = pyqtSignal(str)
    finished_ok = pyqtSignal()
    failed = pyqtSignal(str)
    sources_ready = pyqtSignal(list)

    def __init__(self, url, model, messages, temperature, context_length, max_tokens, stream,
                 rag_index=None, rag_top_k=5, rag_embed_model="nomic-embed-text", parent=None):
        super().__init__(parent)
        self.url = url
        self.model = model
        self.messages = messages
        self.temperature = temperature
        self.context_length = context_length
        self.max_tokens = max_tokens
        self.stream = stream
        self.rag = rag_index
        self.rag_top_k = rag_top_k
        self.rag_embed_model = rag_embed_model
        self._stop = False

    def stop(self):
        self._stop = True

    def run(self):
        if not self.model:
            self.failed.emit("no model configured, set one in settings")
            return

        sources = []
        if self.rag is not None:
            query = ""
            for m in reversed(self.messages):
                if m.get("role") == "user":
                    query = m.get("content", "")
                    break
            if query:
                hits = self.rag.retrieve(
                    query,
                    top_k=self.rag_top_k,
                    url=self.url,
                    embed_model=self.rag_embed_model
                )
                context_block = self.rag.format_context(hits) if hits else ""
                if context_block:
                    instruction = (
                        "You have offline reference material from psychology and CBT textbooks to draw on. "
                        "Use it only when it is relevant and helpful to the person you are talking to. "
                        "Explain any technique you borrow from it in simple, warm, plain language. "
                        "Never mention that you are reading from files or references. "
                        "If the material does not fit the conversation, ignore it.\n\n" + context_block
                    )
                    self.messages.insert(1, {"role": "system", "content": instruction})
                if hits:
                    sources = [
                        {"source": h.get("source", ""), "page": h.get("page")}
                        for h in hits
                    ]
        self.sources_ready.emit(sources)

        payload = {
            "model": self.model,
            "messages": self.messages,
            "stream": self.stream,
            "options": {
                "temperature": self.temperature,
                "num_ctx": self.context_length,
                "num_predict": self.max_tokens
            }
        }
        try:
            resp = requests.post(
                self.url.rstrip("/") + "/api/chat",
                json=payload,
                stream=self.stream,
                timeout=120
            )
        except requests.exceptions.ConnectionError:
            self.failed.emit("could not connect to ollama at " + self.url)
            return
        except requests.exceptions.Timeout:
            self.failed.emit("connection to ollama timed out")
            return
        except requests.exceptions.RequestException as e:
            self.failed.emit(str(e))
            return

        if resp.status_code == 404:
            self.failed.emit("model not found: " + self.model)
            return
        if resp.status_code != 200:
            self.failed.emit("ollama returned status " + str(resp.status_code))
            return

        got_any = False
        try:
            for line in resp.iter_lines():
                if self._stop:
                    resp.close()
                    return
                if not line:
                    continue
                try:
                    data = json.loads(line.decode("utf-8"))
                except (json.JSONDecodeError, UnicodeDecodeError):
                    continue
                if "error" in data:
                    self.failed.emit(str(data["error"]))
                    return
                msg = data.get("message", {})
                content = msg.get("content", "")
                if content:
                    got_any = True
                    self.token_received.emit(content)
                if data.get("done"):
                    break
        except requests.exceptions.RequestException as e:
            self.failed.emit(str(e))
            return

        if not got_any:
            self.failed.emit("received an empty response from ollama")
            return

        self.finished_ok.emit()

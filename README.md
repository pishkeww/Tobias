# Tobias - The [Anal]yst-The[rapist]

A private, fully local CBT-based companion for people who are scared, anxious, or embarrassed about the idea of going to a therapist.

It runs entirely on your own machine — nothing leaves your PC. Tobias offers two quiet, local ways to help:

- **Conversations** — talk with Tobias, who uses cognitive behavioural therapy (CBT) concepts to support you.
- **Journal** — a private writing space where you can jot down your thoughts as plain `.txt` files, with no analysis or chatbot involved. When you choose, you can "Reflect with Tobias" to bring one entry into a conversation.

Tobias talks only to [Ollama](https://ollama.com) running locally, and optionally uses a local RAG pipeline that searches a folder of psychology/CBT textbooks so answers can be grounded in evidence-based material.
## About the Name

The name *Tobias* is inspired by Tobias Fünke from *Arrested Development*.

Fans of the show may understand why an AI companion for talking things through seemed like an appropriate tribute.

## Project structure

```
Tobias - The [Anal]yst-The[rapist]/
  main.py                  entry point
  app/
    config.py               settings load/save, data paths, model choices
    journal.py              journal storage (.txt), search, history
    prompts.py              local guided journal prompts (no LLM, no network)
    reflections.py          local pinned-reflection storage (JSON)
    storage.py              sqlite conversation storage
    system_prompt.py        default persona prompt
    ollama_client.py        ollama http client + streaming worker thread
    rag.py                  textbook RAG: pdf extraction, indexing, BM25 + optional embedding rerank
    gui/
      main_window.py         top-level window, wires everything together
      sidebar.py             mode navigation (Conversations / Journal / Reflections), lists
      input_area.py           message box, send/stop
      message_widget.py       chat bubble, markdown, copy/regenerate/pin
      journal_view.py         journal editor with autosave, guided prompts, Reflect
      reflections_view.py     Reflections cards (saved thoughts)
      settings_dialog.py      settings panel + connection test + model selector
      style.py                warm theme stylesheet
  requirements.txt
  start.bat
  Modelfile
  data/                      created automatically on first run
    conversations.db         conversations, messages, and the RAG index
    settings.json
    reflections.json         your pinned reflections (created on first pin)
    journals/                your journal entries as plain .txt files
```

## What's stored, and where

Everything lives in the `data/` folder next to the app:

- `data/conversations.db` — a SQLite database with every conversation and message, plus the RAG index built from the PDFs in `cbt/`.
- `data/settings.json` — your Ollama URL, selected model, temperature, context length, maximum output tokens, system prompt, streaming toggle, and RAG settings.
- `data/reflections.json` — the thoughts you've chosen to pin (created on your first pin, empty afterwards).
- `data/journals/*.txt` — your journal entries, stored as plain human-readable text files (e.g. `2026-08-29_09-15-42.txt`) so you can open or back them up with any text editor.

Nothing is sent anywhere except to `http://localhost:11434` (your local Ollama). There is no telemetry, no analytics, and no automatic uploads. Pinning a reflection, revealing a guided prompt, or reflecting on selected journal entries never involves the network — only the LLM ever leaves the device (and only the messages you send). Journal entries are only ever read when you explicitly reflect on them; they are never embedded into RAG or loaded at start-up.

## 1. Required software (Windows)

- **Python 3.10+** — https://www.python.org/downloads/ (check "Add python.exe to PATH" during install)
- **Ollama for Windows** — https://ollama.com/download

## 2. Install Ollama and pull the models

Install Ollama, then pull the models you want to use. The app ships with a selection you switch between in **Settings**:

- **HelpingAI 9B** (recommended, the default): `ollama pull vortex/helpingai-9b`
- **Qwen3 8B**: `ollama pull qwen3:8b`
- **Qwen2.5 3B** (lightweight, for lower-end PCs): `ollama pull qwen2.5:3b`

Optional — for better, semantic RAG ranking, also pull an embedding model:

```
ollama pull nomic-embed-text
```

Without it, RAG falls back to plain keyword (BM25) search automatically.

## 3. Start Ollama and verify it's running

Ollama normally starts automatically after install and runs in the background:

```
curl http://localhost:11434/api/tags
```

If you get a JSON list of your models, Ollama is running. Or open `http://localhost:11434` in a browser — you should see "Ollama is running".

## 4. (Optional) Build a custom persona model

If you want a bundled persona, build it from the `Modelfile`:

```
ollama create my-therapist -f Modelfile
```

The app already ships a therapy persona in its system prompt, so this is optional.

## 5. Install the app

From a Command Prompt in the project folder:

```
start.bat
```

This creates a virtual environment in `venv\`, installs `requirements.txt`, and launches the app. On later runs, just double-click `start.bat` again.

Manually:

```
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

## 6. Configure the model in the GUI

Open **Settings** (at the bottom of the sidebar) and use the **model** dropdown to switch between the installed models:

- **HelpingAI 9B — Recommended** (`vortex/helpingai-9b`)
- **Qwen3 8B** (`qwen3:8b`)
- **Qwen2.5 3B — Lightweight** (`qwen2.5:3b`)

Your choice is saved automatically and used by all future replies (normal chats, streaming, and journal reflection). If a response is currently generating, the selector is temporarily disabled until it finishes. If the selected model isn't installed, the status bar shows "model unavailable" and sending shows a friendly error instead of crashing.

Other RAG options in Settings:

- **use textbook context (RAG)** — on/off switch for retrieving textbook passages.
- **rag context chunks** — how many retrieved passages are injected on each reply.
- **rag embed model** — the Ollama embedding model used to rerank results (leave as `nomic-embed-text`).

The textbook folder itself is managed behind the scenes (it defaults to the `cbt/` folder next to the app, or the path saved in your settings) and isn't shown in the GUI. Add or remove PDFs there and the index is rebuilt automatically.

## 7. Journal mode

- Choose **Journal** in the sidebar to open a distraction-free writing space.
- Entries autosave to `data/journals/` (a **Save** button is also available) as plain `.txt` files, about a second after you stop typing and when you close the app.
- Browse past entries in the sidebar (grouped Today / Yesterday / This week / Older) and search them locally.
- When you want to talk about what you wrote, click **Reflect with Tobias** — it starts a new conversation with that entry and Tobias replies.

### Guided prompts

If you don't know how to start, click **"Need a starting point?"** near the editor. A warm, unobtrusive prompt appears (e.g. *"What's been taking up the most space in your mind lately?"*). It uses a **local, static list** — no LLM and no network.

- **"Try another prompt"** shows a different one.
- The prompt is shown separately and never overwrites your text. Use **"Use this"** to insert it into your entry only if you want to; otherwise **Close** hides it.

## 8. Reflections (pinned thoughts)

Pinned reflections are thoughts you explicitly choose to save for later:

- In any conversation, find a Tobias reply and click **pin**. Its text is saved locally.
- Open **Reflections** in the sidebar to see saved thoughts as quiet cards with the date and where they came from ("Saved from a conversation · August 28").
- Click **remove** (or right-click an item in the sidebar) to unpin.
- Duplicate pins of the same text are prevented automatically.
- Everything stays in `data/reflections.json` on your device. Nothing is auto-pinned — you decide.

## 9. Reflect on selected journal entries

You stay in control of what Tobias ever sees:

- In **Journal**, click **Select** to enter selection mode, then check the entries you want (an action bar appears: **Reflect on selected (N)**). Exit with the same button.
- When you reflect, only the explicitly selected files are read (never loaded at start-up, never added to RAG). The selected entries are passed to the model as context in a new conversation, together with a note that this is an interpretation, not a diagnosis.
- Tobias looks for repeated themes, important moments, shifts in perspective, and connections, and asks whether it feels accurate — using tentative language, never clinical claims.
- After the reflection you can keep talking in the same conversation.

Context-length safety: when your selected entries are long, they are bounded and truncated (with an explicit `[truncated]` marker) before being sent, so a huge entry never freezes the UI or starves the context window.

## 10. Running fully offline

Once you've installed Python, Ollama, the models, and the pip packages, everything is local. You can disconnect from the internet and run `start.bat` — it will work exactly the same, including model responses, RAG-backed answers, conversations, journal, search, export, and import.

## How the app talks to Ollama

`app/ollama_client.py` sends requests to `POST /api/chat` with:

- `model` — the model selected in Settings
- `messages` — system prompt, then the full conversation history, then the new user message
- `stream` — true/false
- `options` — temperature, `num_ctx`, `num_predict`

When RAG is enabled, the worker retrieves relevant textbook passages (BM25, optionally reranked by an embedding model) and injects them as an extra system message. Streaming runs on a background `QThread` so the UI stays responsive and the **Stop** button can interrupt generation. Connection status is checked via `GET /api/tags`, which also confirms whether the configured model exists.

## Cloning / moving to another PC

The repo should contain only the code (`app/`, `main.py`, `requirements.txt`, `start.bat`, `Modelfile`, README). Exclude local, machine-specific data from version control with a `.gitignore`:

```
venv/
data/
__pycache__/
*.pyc
.DS_Store
```

A cloner then: installs Python + Ollama, pulls the models, and runs `start.bat` (which auto-creates the venv and installs dependencies). Their own `data/`, journals, and `cbt/` books are created locally.

## Troubleshooting

**Status bar says "disconnected"** — Ollama isn't running or the URL is wrong. Check with `curl http://localhost:11434/api/tags`.

**Status bar says "connected, model unavailable"** — the selected model isn't installed. Run `ollama pull <name>`.

**"model not found" when sending** — same as above; the selected model doesn't match `ollama list`.

**RAG never adds context** — make sure "use textbook context (RAG)" is checked and the `cbt/` folder (or your configured path) has PDFs. The index builds in the background after start-up.

**App won't start / import errors** — delete the `venv` folder and re-run `start.bat`.

**Journal entries not appearing** — they are saved to `data/journals/` as `.txt` and autosave after you stop typing. Typing in Journal mode always creates a new entry file even if you didn't press "+ New entry".

**Therapy privacy note** — Tobias is a supportive tool for reflection and practice, not a licensed therapist, a crisis line, or a replacement for professional care. If you are in immediate danger, contact a real-world crisis service.

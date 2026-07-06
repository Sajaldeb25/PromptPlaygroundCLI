# Prompt Playground CLI

A command-line tool for experimenting with AI prompts, saving them as reusable templates, and tracking interaction results via the [Groq API](https://console.groq.com).

Type prompts in a chat-style loop, reuse saved templates, and export a full history of every interaction.

## Features

- **Chat loop** — Send prompts and get AI responses with token usage
- **Templates** — Save, load, list, and delete named prompts
- **Logging** — Auto-log every interaction (prompt, response, model, tokens, timestamp)
- **Export** — Download history as JSON or CSV
- **Settings** — Switch models, temperature, max tokens, and system prompt per session

## Requirements

- Python 3.10+
- A free [Groq API key](https://console.groq.com)

## Quick Start

```bash
# Enter the project
cd PromptPlaygroundCLI

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate        # Linux/macOS
# venv\Scripts\activate         # Windows

# Install dependencies
pip install -r requirements.txt

# Configure API key
cp .env.example .env
# Edit .env and set: GROQ_API_KEY=your_key_here

# Run
python3 playground.py
```

## How to Use

The app starts directly in a **slash-command chat loop**. Type a normal message to chat with the AI, or use `/commands` for everything else.

### Basic chat

```
Prompt Playground v1.0
Type /help for commands

You: What is the capital of France?
AI: Paris is the capital of France.
   Tokens: 12 | Model: llama-3.3-70b-versatile
```

### Save and reuse prompts

```
You: Explain recursion in one sentence.
AI: Recursion is when a function calls itself...

You: /save recursion_one_liner
Saved as "recursion_one_liner"

You: /list
Saved templates:
  1. recursion_one_liner: Explain recursion in one sentence.

You: /load recursion_one_liner
Loaded "recursion_one_liner": Explain recursion in one sentence.
```

`/load` shows a preview only — it does **not** auto-send to the API. Type your prompt after loading, or send a new one.

### Change settings

```
You: /config
```

You will be prompted to update:

| Setting | How to change |
|---------|---------------|
| Model | `1` = mixtral, `2` = llama2, `3` = gemma (or type the key name) |
| Temperature | Float between `0.0` and `2.0` |
| Max tokens | Positive integer |
| System prompt | Any text, or `clear` to remove |

Press **Enter** on any prompt to keep the current value.

### View and export history

```
You: /history
Recent interactions:
  [13:45] — -> "Paris is the capital of France."

You: /export
Export format (json/csv) [json]: csv
Logs exported to logs_2026-07-04.csv
```

### Exit

```
You: /exit
Goodbye!
```

Or press **Ctrl+C** at any time.

## Slash Commands

| Command | Description |
|---------|-------------|
| `/save <name>` | Save your last sent prompt as a template |
| `/load <name>` | Load a template (preview only, sets logging context) |
| `/list` | List all saved templates |
| `/delete <name>` | Delete a template |
| `/history` | Show the 10 most recent interactions |
| `/export` | Export all logs to JSON or CSV |
| `/config` | Change model, temperature, max tokens, system prompt |
| `/help` | Show available commands |
| `/exit` | Exit the playground |

## Models

| Key | Groq Model ID | Notes |
|-----|---------------|-------|
| `mixtral` | `qwen/qwen3-32b` | Fast, capable general model |
| `llama2` | `llama-3.3-70b-versatile` | Default — strong all-round model |
| `gemma` | `llama-3.1-8b-instant` | Lightweight, fast responses |

Switch models during a session with `/config`.

## Data Files

All data is stored at the **project root** (next to `playground.py`), regardless of your current working directory.

| File | Created when | Purpose |
|------|--------------|---------|
| `templates.json` | First `/save` | Saved prompt templates |
| `logs.json` | First chat message | Full interaction history |
| `logs_YYYY-MM-DD.json` | `/export` (JSON) | Exported log snapshot |
| `logs_YYYY-MM-DD.csv` | `/export` (CSV) | Exported log snapshot |

### `templates.json` format

```json
{
  "geography_question": "What is the capital of France?",
  "recursion_one_liner": "Explain recursion in one sentence."
}
```

### `logs.json` entry format

```json
{
  "timestamp": "2026-07-04 13:45:00",
  "template": "geography_question",
  "user": "What is the capital of France?",
  "response": "Paris is the capital of France.",
  "model": "llama-3.3-70b-versatile",
  "tokens": 12,
  "temperature": 0.7
}
```

`template` is `null` when no template was loaded for that interaction.

## Project Structure

```
PromptPlaygroundCLI/
├── playground.py              # Entry point → PromptPlaygroundApp().run()
├── prompt_playground/         # Main Python package
│   ├── config.py              # Paths, MODELS, HELP_TEXT
│   ├── models.py              # ChatSettings, SessionState
│   ├── storage/               # TemplateStore, LogStore (JSON I/O)
│   ├── services/              # ChatService, TemplateService, LogService
│   └── cli/                   # PromptPlaygroundApp, CommandHandler, SettingsUI
├── templates.json             # Auto-created on first /save
├── logs.json                  # Auto-created on first chat
├── requirements.txt
├── .env.example
├── README.md                  # This file — usage guide
├── ARCHITECTURE.md            # Technical architecture reference
└── Plan.md                    # Original implementation plan
```

For class diagrams, dependency rules, and per-file API details, see **[ARCHITECTURE.md](ARCHITECTURE.md)**.

## Architecture (summary)

The app uses a **layered package** design:

| Layer | Location | Role |
|-------|----------|------|
| Entry | `playground.py` | Thin launcher |
| CLI | `prompt_playground/cli/` | REPL, slash commands, terminal I/O |
| Services | `prompt_playground/services/` | Business logic, Groq adapter |
| Storage | `prompt_playground/storage/` | JSON file repositories |
| Config | `prompt_playground/config.py`, `models.py` | Constants and shared state |

```
playground.py → PromptPlaygroundApp → CommandHandler / ChatService
                                    → TemplateService / LogService
                                    → TemplateStore / LogStore → *.json
```

## Troubleshooting

| Problem | Solution |
|---------|----------|
| `GROQ_API_KEY not set` | Copy `.env.example` to `.env` and add your key |
| `API error: Invalid API Key` | Check your key at [console.groq.com](https://console.groq.com) |
| `no prompt to save` | Send a chat message before using `/save` |
| `template not found` | Use `/list` to see available template names |
| `python: command not found` | Use `python3` instead |
| `ModuleNotFoundError: prompt_playground` | Run from project root; ensure `playground.py` is present |

## License

MIT

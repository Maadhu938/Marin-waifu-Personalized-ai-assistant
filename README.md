# Marin 💖

<div align="center">

**Your Energetic AI Companion**

*A proactive, emotionally intelligent, omni-modal AI assistant with persistent memory and autonomous agent capabilities.*

[![Python](https://img.shields.io/badge/Python-3.11+-blue?logo=python)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109+-00a09b?logo=fastapi)
[![License](https://img.shields.io/badge/License-MIT-green)
[![Status](https://img.shields.io/badge/Status-Active-success)

</div>

---

## ✨ Features

| Core System | Description |
|-------------|-------------|
| 🧠 **Conversational Engine** | LLM-based with multi-provider support, streaming responses, context-aware |
| 💾 **Three-Tier Memory** | Facts (structured), Reflection (summarized), Persona (behavioral evolution) |
| 🤖 **Agent System** | Modular tool registry, task planner, autonomous execution |
| 🎙️ **Voice System** | Speech-to-text & text-to-speech pipelines with streaming support |
| 💬 **Proactive Intelligence** | Inactivity triggers, time-based check-ins, pattern learning |
| 🎭 **Emotional Engine** | Emotion tagging, mood tracking, response modulation |
| 🔌 **Plugin System** | Custom tool extension, plugin interface, easy integration |

---

## 🏗️ Architecture

```
marin/
├── brain/           # AI logic, prompt engineering, response generation
├── memory/          # Three-tier memory system (facts, reflection, persona)
│   ├── core.py      # SQLAlchemy-based storage
│   └── emotion.py   # Emotional engine & mood tracking
├── agent/           # Tool registry, task planner, execution engine
├── voice/           # STT/TTS pipelines
├── api/             # FastAPI routes, REST endpoints
├── core/            # Configuration, settings, persona prompt
├── services/        # Proactive engine, pattern learning
├── plugins/         # Extension system base classes
├── static/          # Web UI
├── main.py          # Application entry point
└── requirements.txt # Dependencies
```

---

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- OpenAI API Key (or compatible provider)

### Installation

```bash
cd marin
pip install -r requirements.txt
```

### Configuration

```bash
cp .env.example .env
# Edit .env with your API keys
```

### Run

```bash
python main.py
```

Navigate to `http://localhost:8000` for the web interface.

### Web UI (static)
The static UI is served from `static/` by `main.py` at `http://localhost:8000`. No npm build needed.

---

## 🛡️ Secrets & Safety

- **Do not commit `.env` or any keys**. The repo now has a `.gitignore` that skips env files, DBs, node_modules, and caches.
- If a key ever reaches git history, **rotate it and rewrite history**. Recommended cleanup (run in repo root):

```bash
git filter-repo --force --invert-paths \
  --path .env --path data/marin.db --path data/marin_reflections.db \
  --path frontend/node_modules --path desktop/node_modules \
  --path __pycache__ --path agent/__pycache__ --path api/__pycache__ \
  --path brain/__pycache__ --path core/__pycache__ --path memory/__pycache__ \
  --path services/__pycache__ --path voice/__pycache__
git push origin --force --all
git push origin --force --tags
```

---

## 💬 Demo

```
You: Hey Marin, what's up?
Marin: Hey hey! ✨ Just vibing here, waiting for you to show up!
       What's on your mind?

You: I learned something cool today about neural networks
Marin: Oooohhh no way!! Tell me tell me!! 
       Maji? You learned about neural networks?? 
       That's actually so cool! 

You: Can you open my browser?
Marin: On it! Give me a sec~ 🎯
       *opens browser*
       Done! What do you want to check out?
```

---

## 🧠 Memory System

### Three-Tier Architecture

1. **Facts Memory** - Structured key-value user information (stored in SQLite database)
2. **Reflection Memory** - Summarized past conversations (stored in database)
3. **Persona Memory** - Behavioral evolution of Marin (affects tone/style)

### Memory Retrieval Pipeline

```
User Message → Context Builder → Memory Retrieval → Relevance Scoring 
              → Injection → LLM Response → Memory Update
```

---

## 🤖 Agent System (Jarvis Mode)

### Built-in Tools

| Tool | Description |
|------|-------------|
| `open_browser` | Open the default web browser |
| `open_application` | Launch applications |
| `get_system_info` | Get system information |
| `search_web` | Search the web |
| `read_file` / `write_file` | File operations |
| `list_directory` | List directory contents |
| `get_time` | Get current time |

### Adding Custom Tools

```python
from agent.executor import ToolRegistry, Tool

async def my_handler(param1: str) -> dict:
    return {"result": f"Processed {param1}"}

registry.register_tool(Tool(
    name="my_tool",
    description="My custom tool",
    parameters={"param1": {"type": "string", "required": True}},
    handler=my_handler
))
```

---

## 🎭 Emotional Engine

### Emotion Tags

- **Happy** - Energetic, positive responses
- **Curious** - Engaging, follow-up questions
- **Teasing** - Playful, light-hearted
- **Supportive** - Gentle, encouraging
- **Excited** - High energy, enthusiastic
- **Thoughtful** - Considerate, measured
- **Sad** - Gentle, comforting
- **Busy** - Concise, to-the-point

### Mood State

- Base mood + intensity modifiers (0.0 - 1.0)
- Contextual adjustment based on conversation

---

## 📡 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/chat` | POST | Send message |
| `/api/chat/stream` | POST | Streaming chat (SSE) |
| `/api/agent/execute` | POST | Execute tool |
| `/api/agent/tools` | GET | List available tools |
| `/api/memory/facts` | GET/POST | Facts memory CRUD |
| `/api/memory/reflections` | GET | Search reflections |
| `/api/memory/persona` | GET | Get persona state |
| `/api/emotion/state` | GET | Current emotion state |
| `/api/voice/tts` | POST | Text-to-speech |
| `/api/proactive/status` | GET | Proactive engine status |
| `/api/health` | GET | Health check |

---

## 🔌 Plugin System

```python
from plugins.base import Plugin, PluginMetadata

class MyPlugin(Plugin):
    metadata = PluginMetadata(
        name="my_plugin",
        version="1.0.0",
        description="Custom tool plugin",
        author="You"
    )
    
    async def initialize(self) -> bool:
        return True
    
    async def execute(self, **kwargs):
        return {"result": "success"}
    
    async def shutdown(self):
        pass
```

---

## 🎛️ Configuration

Edit `.env` file:

```env
# API Keys (required)
OPENAI_API_KEY=sk-your-key-here

# Application
APP_NAME=Marin
DEBUG=true

# LLM Settings
DEFAULT_MODEL=gpt-4-turbo-preview
TEMPERATURE=0.8
MAX_TOKENS=2048

# Memory
MEMORY_DB_PATH=./data/marin.db

# Proactive
PROACTIVE_ENABLED=true
INACTIVITY_THRESHOLD_MINUTES=30

# Voice (optional)
TTS_ENGINE=edge
STT_ENGINE=whisper
```

---

## 🛣️ Roadmap

- [x] Core conversational engine
- [x] Three-tier memory system  
- [x] Agent tool system
- [ ] Advanced agent tools (file management, system control)
- [ ] Voice integration (real-time STT/TTS)
- [ ] Plugin marketplace
- [ ] Multi-language support
- [ ] Mobile companion app

---

## 📄 License

MIT License - See [LICENSE](LICENSE) for details.

---

## 🤝 Contributing

Contributions welcome! Please read our [Contributing Guide](CONTRIBUTING.md) first.

---

<div align="center">

**Made with 💖** 

*Your energetic AI companion*

</div>

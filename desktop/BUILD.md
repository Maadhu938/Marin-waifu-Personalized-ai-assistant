# Marin Desktop - Build Instructions

## Quick Start (Run without building)

1. Start the backend server:
```bash
cd marin
python main.py
```

2. Open browser at `http://localhost:8001` for full UI

---

## Build Desktop App (Tauri)

### Prerequisites
- Node.js & npm
- Rust (for Tauri)
- Python

### Steps

1. Install Tauri CLI:
```bash
cd marin/desktop
npm install
```

2. Run in development:
```bash
npm run dev
```

3. Build for Windows:
```bash
npm run build
```

---

## Project Structure

```
marin/
├── desktop/          # Tauri desktop app
│   ├── src/main.rs  # Rust entry point
│   ├── index.html   # Floating character UI
│   ├── tauri.conf.json
│   └── package.json
├── static/           # Full web UI
├── brain/           # AI engine
├── memory/          # Memory system
├── agent/           # System tools
├── voice/           # TTS/STT
├── api/             # REST endpoints
└── main.py          # Python backend
```

---

## Features

- **Floating Anime Character** - Draggable, always-on-top
- **Chat Interface** - Full conversation UI
- **Voice TTS** - Anime girl voice output
- **System Tools** - Open apps, browser, files
- **Memory** - Remembers user info
- **Emotions** - Happy, curious, teasing moods
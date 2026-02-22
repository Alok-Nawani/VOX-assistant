# VOX Assistant 🎙️🦊

A powerful, privacy-first, modular voice assistant framework designed seamlessly for macOS. Engineered as a proactive digital companion with deep system integration, extending far beyond simple query-response functions.

**Core Philosophy:** Vox doesn't just "assist"; it "operates" directly alongside you. 

---

## ✨ Features

- **Offline-First Capabilities:** Built with local STT (faster-whisper) and continuous edge wake-word listening (`pvporcupine`).
- **Neural Reasoning Engine:** Fully integrated with Google's Gemini models for rich conversational context, memory-aware reasoning, and intent framing.
- **Deep System Kernel Access:** Native macOS system management (open/close apps, control volume, adjust brightness, capture optical data via screenshots).
- **Communication Pipelines:** Full WhatsApp Desktop automation and secure Email SMTP synchronization.
- **Smart Rate-Limit Balancing:** Built on `gemini-flash-lite-latest` for high-frequency processing without hitting quota ceilings.
- **Multi-Turn Contextual Awareness:** Capable of maintaining extended conversational sessions (e.g., sequentially asking for missing message recipients and intent). 
- **Modular Skill Architecture:** Dynamically loads specialized skills (Weather, File Ops, System Control, Media Control, Calendar).
- **Full GUI Dashboard:** A React-based web dashboard providing visual feedback and system telemetry of what Vox is actively processing.

---

## 🚀 Quick Start

1. **Clone the repository**
   ```bash
   git clone https://github.com/Alok-Nawani/VOX-assistant.git
   cd VOX-assistant
   ```

2. **Create a virtual environment:**
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   ```

3. **Install dependencies:**
   *(Ensure you have system-level dependencies for PyAudio and standard macOS build tools).*
   ```bash
   pip install -r requirements.txt
   ```

4. **Copy and configure settings:**
   ```bash
   cp configs/settings.example.env .env
   # Edit .env with your Google Gemini API Key, Email settings, and Porcupine access key
   ```

5. **Run the API & Voice Engine:**
   ```bash
   uvicorn apps.api.main:app --host 0.0.0.0 --port 8000
   ```

6. **(Optional) Run the Web Dashboard:**
   ```bash
   cd apps/webapp
   npm install
   npm run dev
   ```

7. **Say "Hey Vox" and start talking!**

---

## 🛠️ Available Capabilities (Skills)

### 💻 System Control
- *"Open [App Name]" / "Close [App Name]"*
- *"Set volume to [0-100]%" / "Mute"*
- *"Set screen brightness to [10-100]%"*
- *"Take a screenshot"* / *"Analyze my screen"*

### 📱 Communication (WhatsApp & Email)
- *"Send an email"* -> Vox will initiate a conversational flow to ask for recipient and message.
- *"Send a WhatsApp message to [Name] telling them [Message]"*
- Neural framing automatically crafts messages based on conversational vibe (cheerful, serious, professional) directly in the first person. 

### ☁️ Weather & Environment
- *"What's the weather like in [City]?"*

### 📁 File Operations
- *"Find all files named [Query]"*
- *"Read [Filename]"*

### 🎵 Media Control
- *"Play/Pause the music"*
- *"Next track"* / *"Previous song"*

*(More specialized skills are continuously added via the `core/skills` module).*

---

## 🏗️ Project Structure

```text
vox-assistant/
  apps/
    cli/                # Command-line testing interface
    api/                # FastAPI backend & websocket listener
    webapp/             # React/Vite native telemetry dashboard
  core/
    ai/                 # Gemini Integration, NLP, and intelligent Framer
    io/                 # Audio I/O, Porcupine Wake Word, Faster-Whisper
    skills/             # Specialized modular skills (WhatsApp, Email, Sys Control)
    memory/             # Context management and background chron jobs
    system/             # Deep OS hooks (AppleScript handlers)
    tools/              # Email Managers, Automation drivers 
    orchestrator/       # Central processing, routing, and intent derivation
  configs/              # Secure settings loading
  data/                 # Cache, local DBs, and secure Vault
```

---

## 🤝 Contributing

1. Check the Issues for planned features.
2. Fork and create a feature branch.
3. Keep the "Personality" consistent: Vox is a calm, articulate digital officer, not an excitable chatbot.
4. Submit a pull request.

---

## 📜 License

MIT License - See the `LICENSE` file for details. 

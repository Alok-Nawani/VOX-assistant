# Vox Assistant

A privacy-first, modular voice assistant for macOS with extensible skills.

## Features

- Offline-first with local STT (faster-whisper) and wake word detection
- Extensible skills architecture
- Natural conversation with local LLM fallback
- Memory and context awareness
- Secure by design with granular permissions

## Quick Start

1. Clone the repository
2. Create a virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Copy and configure settings:
```bash
cp configs/settings.example.env .env
# Edit .env with your settings
```

5. Run the CLI app:
```bash
python apps/cli/main.py
```

6. Say "Hey Vox" and start talking!

## Available Commands

- System Control
  - "Open [app name]"
  - "Set volume to [0-100]%"
  
- Reminders (coming soon)
  - "Remind me to [task] at [time]"
  - "List my reminders"
  
- More skills coming soon!

## Project Structure

```
vox-assistant/
  apps/
    cli/                # Command-line interface
    macos-gui/          # Native GUI app (coming soon)
  core/
    io/                 # Audio I/O, STT, TTS
    nlp/                # Intent parsing, LLM integration
    skills/            # Modular capabilities
    memory/            # Context and user data
    tools/             # Utility functions
    orchestrator/      # Command routing and execution
  configs/             # Settings and skill definitions
  tests/               # Test suite
  data/                # Knowledge base, logs
  scripts/             # Development utilities
```

## Contributing

1. Check the Issues for planned features
2. Fork and create a feature branch
3. Write tests for your changes
4. Submit a pull request

## License

MIT License - See LICENSE file for details

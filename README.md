# Alfred

**Alfred** is a lightweight, menu-bar utility agent for macOS. It is designed to be your seamless, silent helper for utilitarian tasks, keeping your digital life organized and converted.
<img width="1169" height="935" alt="Screenshot 2026-02-11 at 11 15 01 AM" src="https://github.com/user-attachments/assets/b1b9a364-3a05-4a33-976a-3fd0208e9ffb" />


## Core Philosophy
*   **Invisible:** Lives in the menu bar. Out of sight until needed.
*   **Fast:** Instant startup, minimal memory footprint (Native SwiftUI frontend, Python CLI backend).
*   **Private:** Uses local AI by default (Ollama) or connect to cloud providers (OpenAI, Anthropic, Google) with your own API keys.
*   **Capable:** Leverages powerful system tools (`ffmpeg`, `pandoc`) and Python scripting to handle any file format or organization task.

## Key Features
1.  **Smart Organizer:** "Cleanup my Desktop" - Moves screenshots, installers, and documents to appropriate folders.
2.  **Universal Converter:** "Convert this to PDF/MP3/GIF" - Handles image, document, and media conversions using the best tool for the job.
3.  **AI-Powered Renaming:** Automatically rename files based on their content using AI.
4.  **File Summarization:** Get quick summaries of text files, documents, and code.
5.  **Flexible AI:** Choose from 100+ AI providers - use local models (Ollama) or cloud APIs (OpenAI, Anthropic, Google, and more).

## Prerequisites

### For Local AI (Recommended for Privacy)
*   **Ollama:** Install from [ollama.com](https://ollama.com)
*   **Model:** Pull a recommended model: `ollama pull qwen2.5-coder:1.5b`

### For Cloud AI (Optional)
*   **OpenAI:** Get API key from [platform.openai.com](https://platform.openai.com)
*   **Anthropic:** Get API key from [console.anthropic.com](https://console.anthropic.com)
*   **Google:** Get API key from [ai.google.dev](https://ai.google.dev)

See [AI_PROVIDERS.md](AI_PROVIDERS.md) for detailed setup instructions.

## Quick Start

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/yourusername/Alfred.git
   cd Alfred
   ```

2. **Set up Python backend:**
   ```bash
   cd cli
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

3. **Configure AI provider:**
   ```bash
   # Copy example config
   cp .env.example .env
   
   # Edit .env and set your preferred provider
   # For Ollama (local, default):
   AI_PROVIDER=ollama
   AI_MODEL=qwen2.5-coder:1.5b
   
   # Or for OpenAI:
   AI_PROVIDER=openai
   AI_MODEL=gpt-4o-mini
   OPENAI_API_KEY=sk-your-key-here
   ```

4. **Test the CLI:**
   ```bash
   python alfred.py --help
   python alfred.py summarize README.md
   ```

5. **Build the macOS app (optional):**
   ```bash
   ./dev.sh
   ```

## Usage Examples

### CLI Commands
```bash
# Summarize a file
python alfred.py summarize document.txt

# Rename files intelligently
python alfred.py rename photo.jpg
python alfred.py rename *.png

# Convert files
python alfred.py convert video.mov mp4
python alfred.py convert document.docx pdf

# Organize files
python alfred.py organize ~/Downloads

# Convert data formats
python alfred.py convert-data data.json csv
python alfred.py convert-data data.csv json
```

### Switching AI Providers
Simply edit `cli/.env` to switch providers instantly:

```bash
# Use local Ollama (fast, private)
AI_PROVIDER=ollama
AI_MODEL=qwen2.5-coder:1.5b

# Use OpenAI GPT-4
AI_PROVIDER=openai
AI_MODEL=gpt-4o-mini
OPENAI_API_KEY=sk-...

# Use Anthropic Claude
AI_PROVIDER=anthropic
AI_MODEL=claude-3-5-sonnet-20241022
ANTHROPIC_API_KEY=sk-ant-...
```

See [EXAMPLES_AI_SWITCHING.md](EXAMPLES_AI_SWITCHING.md) for more examples.

## Tech Stack
*   **Frontend:** [SwiftUI](https://developer.apple.com/xcode/swiftui/) (Swift) - Native macOS menu bar application.
*   **Backend:** Python (Typer + Rich + LiteLLM) - Compiled to a single binary using PyInstaller.
*   **AI:** [LiteLLM](https://github.com/BerriAI/litellm) - Unified interface for 100+ LLM providers.
*   **Conversion Tools:** FFmpeg (media), Pandoc (documents), Pillow (images).

## Project Structure
```
Alfred/
├── cli/                    # Python backend (The Brain)
│   ├── alfred.py          # Main CLI application
│   ├── requirements.txt   # Python dependencies
│   ├── .env              # Configuration (AI provider, API keys)
│   └── tests/            # Test suite (159 tests)
├── swift-alfred/          # SwiftUI frontend (The Face)
│   └── Alfred/
│       ├── AlfredApp.swift
│       └── ContentView.swift
├── AI_PROVIDERS.md        # AI provider setup guide
├── EXAMPLES_AI_SWITCHING.md  # Usage examples
└── dev.sh                # Build script
```

## Testing

Run the comprehensive test suite (159 tests):

```bash
cd cli
source venv/bin/activate
pytest tests/ -v
```

## Documentation
*   **[AI_PROVIDERS.md](AI_PROVIDERS.md)** - Complete guide to setting up Ollama, OpenAI, Anthropic, and Google AI
*   **[EXAMPLES_AI_SWITCHING.md](EXAMPLES_AI_SWITCHING.md)** - 10 practical examples of provider switching
*   **[CHANGELOG_AI_SDK.md](CHANGELOG_AI_SDK.md)** - Technical details of the LiteLLM migration
*   **[AGENTS.md](AGENTS.md)** - Guidelines for AI agents working on this project

## Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Run tests (`pytest tests/`)
4. Commit changes (`git commit -s -m "Add amazing feature"`)
5. Push to branch (`git push origin feature/amazing-feature`)
6. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments
*   **[Ollama](https://ollama.com)** - Local LLM runtime
*   **[LiteLLM](https://github.com/BerriAI/litellm)** - Universal LLM API
*   **[FFmpeg](https://ffmpeg.org)** - Media conversion
*   **[Pandoc](https://pandoc.org)** - Document conversion

# Alfred

**Alfred** is a lightweight, menu-bar utility agent for macOS. Your seamless, silent helper for file conversion, organization, renaming, and AI-powered tasks — all from the menu bar.

<img width="1169" height="935" alt="Alfred menu bar screenshot" src="https://github.com/user-attachments/assets/b1b9a364-3a05-4a33-976a-3fd0208e9ffb" />

## Core Philosophy

- **Invisible:** Lives in the menu bar. Out of sight until needed.
- **Fast:** Native SwiftUI frontend, Python backend — instant startup.
- **Private:** Uses local AI by default (Ollama), or connect to cloud providers (OpenAI, Anthropic, Google) with your own API keys.
- **Self-contained:** Ships with a full embedded Python runtime. No Python, Homebrew, or pip required to run.

---

## Installation

### Option A — Download the pre-built app (recommended)

1. Download `Alfred.app.zip` from the [Releases](https://github.com/yourusername/Alfred/releases) page.
2. Unzip and drag **Alfred.app** to your `/Applications` folder.
3. Double-click to launch. Alfred appears in your menu bar.
4. *(First launch only)* macOS may show a security prompt — go to **System Settings → Privacy & Security → Open Anyway**.

> No Python, no Homebrew, no pip. Everything is bundled inside the app.

### Option B — Build from source

**Requirements (developer machine only, not needed by end users):**
- macOS 13 or later (Apple Silicon — ARM64)
- Xcode Command Line Tools: `xcode-select --install`
- Internet access (first run downloads ~45 MB standalone Python)

> **Intel Mac users:** `build.sh` defaults to the `aarch64` (Apple Silicon) Python build. Edit the `PYTHON_ARCH` variable at the top of `build.sh` to `x86_64-apple-darwin` before running.

```bash
# 1. Clone
git clone https://github.com/yourusername/Alfred.git
cd Alfred

# 2. (Optional) configure AI provider
cp cli/.env.example cli/.env
# Edit cli/.env — see AI Configuration below

# 3. Build everything (downloads Python, installs deps, builds Swift app)
./build.sh

# 4. Launch
open swift-alfred/Alfred.app
```

`build.sh` handles everything automatically:
- Downloads a relocatable Python 3.13 runtime (cached after first run)
- Creates a venv inside `Alfred.app` and installs all Python dependencies
- Copies `alfred.py` into the bundle
- Builds the Swift app
- The result is a fully self-contained `Alfred.app` — zip it up and share it

For subsequent builds after code changes:
```bash
./build.sh          # incremental (uses cached Python)
./build.sh --clean  # full rebuild from scratch
```

---

## AI Configuration

Alfred uses [LiteLLM](https://github.com/BerriAI/litellm) to support 100+ AI providers. Edit `cli/.env` before building:

```bash
# Local AI (default — private, no API key needed)
AI_PROVIDER=ollama
AI_MODEL=qwen3:4b
OLLAMA_API_BASE=http://localhost:11434

# OpenAI
AI_PROVIDER=openai
AI_MODEL=gpt-5-mini   # or gpt-5.2 for flagship
OPENAI_API_KEY=sk-...

# Anthropic Claude
AI_PROVIDER=anthropic
AI_MODEL=claude-sonnet-4-6
ANTHROPIC_API_KEY=sk-ant-...

# Google Gemini
AI_PROVIDER=google
AI_MODEL=gemini-2.5-pro   # or gemini-3-pro-preview (preview)
GOOGLE_API_KEY=your-google-api-key-here
```

For Ollama (local AI): install from [ollama.com](https://ollama.com), then `ollama pull qwen3:4b`.

See [AI_PROVIDERS.md](AI_PROVIDERS.md) for full details.

---

## Features

### 1. Universal Converter — no external tools required

Alfred ships with Python libraries that handle common conversions natively. Optional tools (ffmpeg, pandoc) are used when available and extend the format list further.

#### Images — via Pillow (bundled)
All formats interconvertible with no external tools:

| From | To |
|------|-----|
| PNG | JPG, WebP, BMP, GIF, TIFF, ICO, PDF |
| JPG | PNG, WebP, BMP, GIF, TIFF, ICO, PDF |
| WebP | PNG, JPG, BMP, GIF |
| HEIC/HEIF | JPG, PNG |
| GIF | PNG, JPG, WebP |
| BMP, TIFF | PNG, JPG |

#### Audio — via pydub (bundled)
Common audio conversions with no ffmpeg required:

| Format | Converts to |
|--------|-------------|
| MP3 | WAV, FLAC, OGG |
| WAV | MP3, FLAC, OGG, AAC, M4A |
| FLAC | MP3, WAV, OGG |
| OGG | MP3, WAV |
| M4A, AAC | MP3, WAV |

> Install ffmpeg for video conversion and extended audio formats: `alfred install ffmpeg`

#### Documents — via fpdf2 + python-docx + markdown (bundled)
No pandoc or system tools required:

| From | To |
|------|-----|
| Markdown (.md) | HTML, PDF, DOCX, EPUB |
| Plain text (.txt) | HTML, PDF, DOCX |
| HTML | PDF, DOCX, EPUB |
| DOCX | PDF, TXT |

> Install pandoc for extended document support: `alfred install pandoc`

#### Data — via PyYAML, openpyxl, toml (bundled)
All data conversions are pure Python, no external tools:

| From | To |
|------|-----|
| JSON | CSV, YAML, XLSX, TOML |
| CSV | JSON, XLSX |
| YAML | JSON |
| XLSX | CSV, JSON |
| TOML | JSON |

### 2. Smart Organizer

Organize files by category or natural language instructions:
- "Move all screenshots from last week to a Screenshots folder"
- "Sort by file type"
- Vision-capable: analyzes image content to organize photos by subject

### 3. AI-Powered Renaming

Renames files based on content. For images, uses vision models to describe what's in the photo. For documents, reads the content.

### 4. File Summarization

Summarize any text file, document, or code file in 3 bullet points.

### 5. Command Mode

Natural-language shell commands — type what you want done, Alfred generates and runs the code.

---

## CLI Usage

Alfred also works as a standalone CLI (inside the venv):

```bash
cd cli
source venv/bin/activate

# Convert files
python alfred.py convert photo.heic jpg
python alfred.py convert document.md pdf
python alfred.py convert data.json yaml
python alfred.py convert spreadsheet.xlsx csv

# Organize
python alfred.py organize ~/Downloads
python alfred.py organize ~/Downloads --instructions "group by year" --confirm

# Rename
python alfred.py rename *.jpg --confirm

# Summarize
python alfred.py summarize report.pdf

# AI command
python alfred.py ask "compress all images in this folder to 80% quality" ~/Photos
```

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | SwiftUI — native macOS menu bar app (NSStatusItem) |
| Backend | Python 3.13 — Typer CLI + Rich output |
| AI | LiteLLM — unified interface for 100+ LLM providers |
| Python runtime | [python-build-standalone](https://github.com/indygreg/python-build-standalone) — embedded in the .app |
| Images | Pillow + pillow-heif |
| Audio | pydub |
| Documents | fpdf2, python-docx, markdown, ebooklib |
| Data | PyYAML, openpyxl, toml |
| Optional tools | ffmpeg (video/audio), pandoc (advanced docs) |

---

## Project Structure

```
Alfred/
├── build.sh                  # Build script — assembles self-contained Alfred.app
├── cli/
│   ├── alfred.py             # Python CLI backend (all conversion + AI logic)
│   ├── requirements.txt      # Python dependencies (bundled into .app by build.sh)
│   ├── .env.example          # AI provider configuration template
│   └── tests/                # Test suite (160 tests)
├── swift-alfred/
│   ├── Sources/Alfred/
│   │   ├── AlfredApp.swift   # App entry point, menu bar NSStatusItem
│   │   └── AlfredView.swift  # SwiftUI UI — uses bundle-relative Python paths
│   ├── Alfred.app/           # Pre-built app bundle (populated by build.sh)
│   └── Package.swift
├── AI_PROVIDERS.md
└── EXAMPLES_AI_SWITCHING.md
```

---

## Testing

```bash
cd cli
source venv/bin/activate
pytest tests/ -v
# 160 tests
```

---

## Distributing Alfred.app

After running `./build.sh`, the `.app` is fully self-contained:

```bash
# Zip for sharing
zip -r Alfred.zip swift-alfred/Alfred.app

# Or copy to Applications
cp -R swift-alfred/Alfred.app /Applications/Alfred.app
```

For notarization (App Store / Gatekeeper signing), sign all bundled `.so` files and the app:

```bash
find swift-alfred/Alfred.app -name "*.so" -o -name "*.dylib" | while read f; do
    codesign --force --sign "Developer ID Application: Your Name (TEAMID)" "$f"
done
codesign --force --deep --sign "Developer ID Application: Your Name (TEAMID)" swift-alfred/Alfred.app
xcrun notarytool submit Alfred.zip --apple-id you@example.com --team-id TEAMID --wait
xcrun stapler staple swift-alfred/Alfred.app
```

---

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Run tests: `cd cli && pytest tests/`
4. Commit: `git commit -s -m "Add my feature"`
5. Push and open a Pull Request

---

## Documentation

- [AI_PROVIDERS.md](AI_PROVIDERS.md) — Ollama, OpenAI, Anthropic, Google setup
- [EXAMPLES_AI_SWITCHING.md](EXAMPLES_AI_SWITCHING.md) — provider switching examples
- [AGENTS.md](AGENTS.md) — guidelines for AI agents working on this project

---

## License

MIT License — see [LICENSE](LICENSE).

## Acknowledgments

- [python-build-standalone](https://github.com/indygreg/python-build-standalone) — relocatable Python runtime
- [Ollama](https://ollama.com) — local LLM runtime
- [LiteLLM](https://github.com/BerriAI/litellm) — universal LLM API
- [Pillow](https://python-pillow.org) — image processing
- [pydub](https://github.com/jiaaro/pydub) — audio conversion
- [fpdf2](https://py-pdf.github.io/fpdf2/) — pure-Python PDF generation
- [FFmpeg](https://ffmpeg.org) — media conversion (optional)
- [Pandoc](https://pandoc.org) — document conversion (optional)

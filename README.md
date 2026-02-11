# Alfred

**Alfred** is a lightweight, menu-bar utility agent for macOS. It is designed to be your seamless, silent helper for utilitarian tasks, keeping your digital life organized and converted.

## Core Philosophy
*   **Invisible:** Lives in the menu bar. Out of sight until needed.
*   **Fast:** Instant startup, minimal memory footprint (Native SwiftUI frontend, Python CLI backend).
*   **Private:** Uses local AI (Ollama) to process your tasks securely on your machine.
*   **Capable:** Leverages powerful system tools (`ffmpeg`, `pandoc`) and Python scripting to handle any file format or organization task.

## Key Features
1.  **Smart Organizer:** "Cleanup my Desktop" - Moves screenshots, installers, and documents to appropriate folders.
2.  **Universal Converter:** "Convert this to PDF/MP3/GIF" - Handles image, document, and media conversions using the best tool for the job.
3.  **Local & Private:** Runs entirely locally using [Ollama](https://ollama.com). No data leaves your machine.

## Prerequisites
*   **Ollama:** You must have [Ollama](https://ollama.com) installed and running.
*   **Model:** Pull the recommended model: `ollama pull qwen2.5-coder:1.5b`

## Tech Stack
*   **Frontend:** [SwiftUI](https://developer.apple.com/xcode/swiftui/) (Swift) - Native macOS menu bar application.
*   **Backend:** Python (Typer + Requests) - Compiled to a single binary using PyInstaller.
*   **AI:** Ollama (Local LLM).

## Project Structure
*   `cli/`: The Python backend (The Brain).
*   `swift-alfred/`: The native SwiftUI frontend (The Face).

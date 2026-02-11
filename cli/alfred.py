import os
import csv
import subprocess
import sys
import tempfile
import typer
import requests
import json
import logging
import re as _re
import shutil
import time
import stat
from typing import Optional, List
from pathlib import Path
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, DownloadColumn, TransferSpeedColumn
from dotenv import load_dotenv, find_dotenv
from shutil import which
from litellm import completion

# --- GLOBAL CONFIG (configurable for testing) ---
_CONFIG = {
    "LOG_FILE": os.path.expanduser("~/Desktop/alfred_debug.log"),
    "AI_PROVIDER": "ollama",  # Options: ollama, openai, anthropic, google, etc.
    "AI_MODEL": "qwen3:4b",  # Model name (format depends on provider)
    "OLLAMA_API_BASE": "http://localhost:11434",  # For Ollama only
    "TEMPERATURE": 0.2,
    "APP_SUPPORT_DIR": Path.home() / "Library/Application Support/Alfred",
}

def _init_config():
    """Initialize configuration from environment. Call this at app startup."""
    # Load environment variables
    dotenv_path = find_dotenv(usecwd=True)
    if dotenv_path:
        load_dotenv(dotenv_path)
    
    # Override config from env
    _CONFIG["AI_PROVIDER"] = os.getenv("AI_PROVIDER", _CONFIG["AI_PROVIDER"])
    _CONFIG["AI_MODEL"] = os.getenv("AI_MODEL", _CONFIG["AI_MODEL"])
    _CONFIG["OLLAMA_API_BASE"] = os.getenv("OLLAMA_API_BASE", _CONFIG["OLLAMA_API_BASE"])
    _CONFIG["TEMPERATURE"] = float(os.getenv("TEMPERATURE", str(_CONFIG["TEMPERATURE"])))
    
    # Set up logging
    logging.basicConfig(
        filename=_CONFIG["LOG_FILE"],
        level=logging.DEBUG,
        format="%(asctime)s - %(levelname)s - %(message)s"
    )
    
    # Create tool directories
    local_bin_dir = _CONFIG["APP_SUPPORT_DIR"] / "bin"
    local_bin_dir.mkdir(parents=True, exist_ok=True)
    
    # Add local bin to PATH
    os.environ["PATH"] = f"{local_bin_dir}:{os.environ.get('PATH', '')}"

# Accessors for config values
def get_local_bin_dir() -> Path:
    return _CONFIG["APP_SUPPORT_DIR"] / "bin"

def get_ai_provider() -> str:
    return _CONFIG["AI_PROVIDER"]

def get_ai_model() -> str:
    return _CONFIG["AI_MODEL"]

def get_ollama_api_base() -> str:
    return _CONFIG["OLLAMA_API_BASE"]

def get_temperature() -> float:
    return _CONFIG["TEMPERATURE"]

console = Console()

TOOLS_URLS = {
    "ffmpeg": "https://evermeet.cx/ffmpeg/ffmpeg-7.1.zip",
    "pandoc": "https://github.com/jgm/pandoc/releases/download/3.6.3/pandoc-3.6.3-x86_64-macOS.zip",
}

# ============================================================
# UTILITIES
# ============================================================

def _human_size(nbytes: int) -> str:
    size = float(nbytes)
    for unit in ["B", "KB", "MB", "GB"]:
        if size < 1024:
            return f"{size:.0f} {unit}" if unit == "B" else f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} TB"


def check_command_availability(cmd: str) -> bool:
    local_tool = get_local_bin_dir() / cmd
    if local_tool.exists() and os.access(local_tool, os.X_OK):
        return True
    return which(cmd) is not None


def get_llm_response(prompt: str, image_paths: Optional[List[str]] = None, retries: int = 2) -> str:
    """Get LLM response using LiteLLM (supports multiple providers and vision).
    
    Args:
        prompt: Text prompt for the model
        image_paths: Optional list of image file paths for vision models
        retries: Number of retry attempts
    
    Returns:
        str: Model response
    """
    import base64
    
    provider = get_ai_provider()
    model_name = get_ai_model()
    temperature = get_temperature()
    
    # Build full model identifier for LiteLLM
    if provider == "ollama":
        model = f"ollama/{model_name}"
        api_base = get_ollama_api_base()
    elif provider == "openai":
        model = f"openai/{model_name}"  # e.g., openai/gpt-4o
        api_base = None
    elif provider == "anthropic":
        model = f"anthropic/{model_name}"  # e.g., anthropic/claude-3-5-sonnet-20241022
        api_base = None
    elif provider == "google" or provider == "gemini":
        # Handle both "gemini-2.5-flash" and "gemini/gemini-2.5-flash" formats
        if not model_name.startswith("gemini/"):
            model = f"gemini/{model_name}"
        else:
            model = model_name
        api_base = None
    else:
        # For custom providers, assume format is already correct
        model = model_name
        api_base = None
    
    logging.info(f"Using {provider} provider with model {model}")
    
    for attempt in range(retries + 1):
        try:
            # Build message content
            if image_paths and len(image_paths) > 0:
                # Vision request with images
                content_parts = [{"type": "text", "text": prompt}]
                
                # Add images
                for img_path in image_paths[:5]:  # Limit to 5 images
                    if not os.path.exists(img_path):
                        logging.warning(f"Image not found: {img_path}")
                        continue
                    
                    # Read and encode image
                    with open(img_path, "rb") as f:
                        img_data = base64.b64encode(f.read()).decode("utf-8")
                    
                    # Detect image type
                    ext = Path(img_path).suffix.lower()
                    mime_map = {
                        ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
                        ".png": "image/png", ".gif": "image/gif",
                        ".webp": "image/webp", ".bmp": "image/bmp"
                    }
                    mime_type = mime_map.get(ext, "image/jpeg")
                    
                    content_parts.append({
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:{mime_type};base64,{img_data}"
                        }
                    })
                
                message_content = content_parts
            else:
                # Text-only request
                message_content = prompt
            
            # Build completion request
            kwargs = {
                "model": model,
                "messages": [{"role": "user", "content": message_content}],
                "temperature": temperature,
                "timeout": 120
            }
            
            # Add api_base for Ollama
            if api_base:
                kwargs["api_base"] = api_base
            
            response = completion(**kwargs)
            content = response.choices[0].message.content.strip()
            
            # Strip <think> tags if present
            content = _re.sub(r"<think>.*?</think>", "", content, flags=_re.DOTALL).strip()
            logging.debug(f"LLM Response: {content[:300]}...")
            return content
            
        except Exception as e:
            error_msg = str(e).lower()
            
            # Check for connection errors
            if "connection" in error_msg or "connect" in error_msg:
                if attempt < retries:
                    console.print(f"[yellow]Connection failed, retrying ({attempt+1}/{retries+1})...[/yellow]")
                    time.sleep(2)
                    continue
                console.print(f"[bold red]Error:[/bold red] Cannot connect to {provider}. Check configuration.")
                return f"Error: Cannot connect to {provider}"
            
            # Check for timeout
            elif "timeout" in error_msg:
                if attempt < retries:
                    console.print(f"[yellow]Timeout, retrying ({attempt+1}/{retries+1})...[/yellow]")
                    continue
                return "Error: Request timed out"
            
            # Other errors
            else:
                logging.error(f"LLM Error: {e}", exc_info=True)
                if attempt < retries:
                    console.print(f"[yellow]Error occurred, retrying ({attempt+1}/{retries+1})...[/yellow]")
                    time.sleep(1)
                    continue
                return f"Error: {e}"
    
    return "Error: Failed after retries"


def extract_code_block(response: str) -> tuple:
    for lang in ["python", "bash", "sh"]:
        marker = f"```{lang}"
        if marker in response:
            try:
                code = response.split(marker, 1)[1].split("```", 1)[0].strip()
                if code:
                    return (lang if lang != "sh" else "bash", code)
            except IndexError:
                continue
    return (None, None)


DANGEROUS_PATTERNS = [
    "rm -rf /", "rm -rf ~", "mkfs", "dd if=", ":(){",
    "chmod -R 777 /", "> /dev/sda", "shutdown", "reboot",
]
DANGEROUS_REGEXES = [
    _re.compile(r"curl\s+.*\|\s*(sh|bash)", _re.IGNORECASE),
    _re.compile(r"wget\s+.*\|\s*(sh|bash)", _re.IGNORECASE),
]


def execute_shell_command(command: str) -> bool:
    """Execute a shell command with safety checks. Returns True on success, False on failure/block."""
    logging.info(f"Executing: {command}")
    cmd_lower = command.lower().strip()
    for p in DANGEROUS_PATTERNS:
        if p in cmd_lower:
            console.print(f"[bold red]Blocked:[/bold red] Dangerous command detected.")
            return False
    for r in DANGEROUS_REGEXES:
        if r.search(cmd_lower):
            console.print(f"[bold red]Blocked:[/bold red] Dangerous command detected.")
            return False

    console.print(f"[blue]$ {command}[/blue]")
    try:
        env = os.environ.copy()
        env["PATH"] = f"{get_local_bin_dir()}:{env.get('PATH', '')}"
        
        result = subprocess.run(
            command, 
            shell=True, 
            check=True, 
            text=True, 
            capture_output=True, 
            timeout=300,
            env=env
        )
        if result.stdout:
            console.print(result.stdout.rstrip())
        console.print("[green]Done.[/green]")
        return True
    except subprocess.TimeoutExpired:
        console.print("[bold red]Timed out (5 min limit).[/bold red]")
        return False
    except subprocess.CalledProcessError as e:
        logging.error(f"Command failed: {e.stderr}")
        console.print(f"[red]{e.stderr.rstrip()}[/red]")
        return False


def execute_python_script(script_content: str) -> bool:
    """Execute Python script in temp file. Returns True on success, False on failure."""
    logging.info("Executing Python script")
    logging.debug(f"Script:\n{script_content}")
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as tmp:
        tmp.write(script_content)
        tmp_path = tmp.name
    python_exe = which("python3") or which("python")
    if not python_exe:
        console.print("[bold red]Error:[/bold red] No Python interpreter found.")
        return False
    try:
        result = subprocess.run([python_exe, tmp_path], check=True, text=True, capture_output=True)
        if result.stdout:
            console.print(result.stdout.rstrip())
        console.print("[green]Done.[/green]")
        return True
    except subprocess.CalledProcessError as e:
        logging.error(f"Script failed: {e.stderr}")
        console.print(f"[red]{e.stderr.rstrip()}[/red]")
        return False
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


EXTENSION_CATEGORIES = {
    "Images": {".png", ".jpg", ".jpeg", ".gif", ".bmp", ".tiff", ".webp", ".svg", ".ico", ".heic", ".heif"},
    "Documents": {".pdf", ".doc", ".docx", ".txt", ".rtf", ".odt", ".pages", ".tex", ".md", ".rst", ".epub"},
    "Spreadsheets": {".csv", ".xlsx", ".xls", ".tsv", ".ods", ".numbers"},
    "Audio": {".mp3", ".wav", ".flac", ".ogg", ".aac", ".m4a", ".wma", ".opus"},
    "Video": {".mp4", ".avi", ".mkv", ".mov", ".webm", ".flv", ".wmv", ".m4v"},
    "Archives": {".zip", ".tar", ".gz", ".bz2", ".rar", ".7z", ".xz", ".dmg", ".iso"},
    "Code": {".py", ".js", ".ts", ".html", ".css", ".java", ".c", ".cpp", ".h", ".swift", ".go", ".rs", ".rb", ".sh"},
    "Data": {".json", ".xml", ".yaml", ".yml", ".toml", ".sql", ".db", ".sqlite"},
    "Presentations": {".ppt", ".pptx", ".key", ".odp"},
    "Design": {".psd", ".ai", ".sketch", ".fig", ".xd"},
}


def _categorize_file(filename: str) -> str:
    ext = Path(filename).suffix.lower()
    for category, extensions in EXTENSION_CATEGORIES.items():
        if ext in extensions:
            return category
    return "Other"


def _json_to_yaml_simple(obj, indent: int = 0) -> list:
    lines = []
    prefix = "  " * indent
    if isinstance(obj, dict):
        for k, v in obj.items():
            if isinstance(v, (dict, list)):
                lines.append(f"{prefix}{k}:")
                lines.extend(_json_to_yaml_simple(v, indent + 1))
            else:
                val = "true" if v is True else "false" if v is False else "null" if v is None else str(v)
                if isinstance(v, str) and (':' in v or '#' in v or '\n' in v):
                    val = f'"{v}"'
                lines.append(f"{prefix}{k}: {val}")
    elif isinstance(obj, list):
        for item in obj:
            if isinstance(item, (dict, list)):
                lines.append(f"{prefix}-")
                lines.extend(_json_to_yaml_simple(item, indent + 1))
            else:
                lines.append(f"{prefix}- {item}")
    else:
        lines.append(f"{prefix}{obj}")
    return lines


def _xml_to_dict(element) -> dict:
    result: dict = {}
    if element.attrib:
        result["@attributes"] = dict(element.attrib)
    for child in element:
        child_data = _xml_to_dict(child)
        tag = child.tag
        if tag in result:
            if not isinstance(result[tag], list):
                result[tag] = [result[tag]]
            result[tag].append(child_data)
        else:
            result[tag] = child_data
    if element.text and element.text.strip():
        if result:
            result["#text"] = element.text.strip()
        else:
            return element.text.strip()  # type: ignore[return-value]
    return result


def _convert_data(input_file: str, ext: str, target: str, output_path: str):
    """Deterministic data file conversion using Python stdlib."""
    key = f"{ext}->.{target}"
    logging.info(f"Data conversion: {key}")

    if ext == ".json" and target == "csv":
        with open(input_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        if isinstance(data, dict): data = [data]
        if not isinstance(data, list) or len(data) == 0:
            console.print("[red]Error: JSON must be a list or dict for CSV conversion.[/red]")
            return False
        
        # Handle list of primitives (convert to single-column CSV)
        if not isinstance(data[0], dict):
            with open(output_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(["value"])  # Header
                for item in data:
                    writer.writerow([item])
            return True
        
        # Handle list of dicts (standard case)
        headers = list(data[0].keys())
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=headers)
            writer.writeheader()
            for row in data:
                writer.writerow(row)
        return True

    elif ext == ".csv" and target == "json":
        with open(input_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            data = list(reader)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return True

    # Pass-through for other data types (simplified for now)
    console.print(f"[red]Error: No built-in converter for {ext} -> .{target}[/red]")
    return False


# Output format capabilities
SIPS_FORMATS = {"jpeg", "jpg", "png", "tiff", "tif", "bmp", "gif", "pict", "pdf", "heic"}
AFCONVERT_FORMATS = {"aac", "m4a", "wav", "aiff", "aif", "caf"}
TEXTUTIL_FORMATS = {"txt", "html", "rtf", "rtfd", "doc", "docx", "wordml", "odt", "webarchive"} # No PDF output
PANDOC_FORMATS = {"html", "pdf", "docx", "md", "rst", "tex", "epub", "txt", "rtf"}
FFMPEG_FORMATS = {"mp3", "wav", "aac", "m4a", "flac", "ogg", "mp4", "avi", "mkv", "mov", "webm", "gif"}
MAGICK_FORMATS = {"jpg", "jpeg", "png", "gif", "webp", "bmp", "tiff", "ico", "svg", "pdf"}

def _tool_supports_target(tool: str, target: str) -> bool:
    """Check if a specific tool supports the target output format."""
    target = target.lower()
    if tool == "python": return True # Assumed specific logic handles it
    if tool == "sips": return target in SIPS_FORMATS
    if tool == "afconvert": return target in AFCONVERT_FORMATS
    if tool == "textutil": return target in TEXTUTIL_FORMATS
    if tool == "pandoc": return target in PANDOC_FORMATS
    if tool == "ffmpeg": return target in FFMPEG_FORMATS
    if tool == "magick": return target in MAGICK_FORMATS
    return False

def _resolve_tool(tool_list: list[str]) -> str | None:
    for tool in tool_list:
        if tool == "python": return "python"
        elif tool == "sips": return "sips"
        elif tool == "afconvert": return "afconvert"
        elif tool == "textutil": return "textutil"
        elif tool == "ffmpeg" and check_command_availability("ffmpeg"): return "ffmpeg"
        elif tool == "magick" and (check_command_availability("magick") or check_command_availability("convert")): return "magick"
        elif tool == "pandoc" and check_command_availability("pandoc"): return "pandoc"
    return None


CONVERSION_MAP: dict[str, list[str]] = {
    # --- Data ---
    ".json->.csv": ["python"], ".csv->.json": ["python"],
    # --- Images ---
    ".png->.jpg": ["sips", "magick"], ".jpg->.png": ["sips", "magick"],
    ".png->.webp": ["magick"], ".webp->.png": ["magick", "sips"],
    # --- Audio ---
    ".wav->.aac": ["afconvert", "ffmpeg"], ".wav->.m4a": ["afconvert", "ffmpeg"],
    ".mp3->.wav": ["ffmpeg", "afconvert"], ".wav->.mp3": ["ffmpeg"],
    # --- Video ---
    ".mp4->.mp3": ["ffmpeg"], ".mp4->.wav": ["ffmpeg"],
    # --- Documents ---
    ".txt->.html": ["textutil", "pandoc"], ".docx->.pdf": ["pandoc"],
    ".md->.html": ["pandoc"], ".md->.pdf": ["pandoc"],
}

SIPS_FORMAT_ALIAS = {"jpg": "jpeg", "jpeg": "jpeg", "png": "png", "tiff": "tiff"}
AFCONVERT_FORMATS_MAP = {"aac": "aac ", "m4a": "m4af", "wav": "WAVE", "aiff": "AIFF"}



# ============================================================
# CLI APP
# ============================================================

app = typer.Typer(help="Alfred: Your Native Utility Agent")


@app.command()
def install(tool: str):
    """Download and install a tool locally (ffmpeg, pandoc)."""
    if tool not in TOOLS_URLS:
        console.print(f"[red]Error: Unknown tool '{tool}'.[/red]")
        console.print(f"[dim]Available: {', '.join(TOOLS_URLS.keys())}[/dim]")
        raise typer.Exit(1)
    
    url = TOOLS_URLS[tool]
    console.print(f"[blue]Downloading {tool}...[/blue]")
    
    zip_path = Path(tempfile.gettempdir()) / f"{tool}.zip"
    local_bin_dir = get_local_bin_dir()
    try:
        with requests.get(url, stream=True) as r:
            r.raise_for_status()
            total_size = int(r.headers.get('content-length', 0))
            
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                DownloadColumn(),
                TransferSpeedColumn(),
                console=console
            ) as progress:
                task = progress.add_task(f"Fetching {tool}", total=total_size)
                with open(zip_path, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        f.write(chunk)
                        progress.update(task, advance=len(chunk))
        
        console.print("[blue]Extracting...[/blue]")
        import zipfile
        with zipfile.ZipFile(zip_path, 'r') as z:
            bin_name = tool
            found = False
            for name in z.namelist():
                if name.endswith(f"/{tool}") or name == tool:
                    source = z.open(name)
                    target_path = local_bin_dir / tool
                    with open(target_path, 'wb') as target:
                        shutil.copyfileobj(source, target)
                    st = os.stat(target_path)
                    os.chmod(target_path, st.st_mode | stat.S_IEXEC)
                    found = True
                    break
            
            if not found:
                for name in z.namelist():
                    if f"bin/{tool}" in name:
                        source = z.open(name)
                        target_path = local_bin_dir / tool
                        with open(target_path, 'wb') as target:
                            shutil.copyfileobj(source, target)
                        st = os.stat(target_path)
                        os.chmod(target_path, st.st_mode | stat.S_IEXEC)
                        found = True
                        break

            if found:
                console.print(f"[green]Successfully installed {tool}![/green]")
            else:
                console.print(f"[red]Error: Could not find binary in zip archive.[/red]")
                
    except Exception as e:
        console.print(f"[red]Install failed: {e}[/red]")
    finally:
        if zip_path.exists():
            zip_path.unlink()


@app.command()
def convert(input_file: str, target_format: str):
    logging.info(f"Convert: {input_file} -> {target_format}")

    if not os.path.exists(input_file):
        console.print(f"[red]Error: File not found: {input_file}[/red]")
        raise typer.Exit(1)

    ext = os.path.splitext(input_file)[1].lower()
    target = target_format.lower().strip().lstrip(".")
    output_path = os.path.splitext(input_file)[0] + f".{target}"
    key = f"{ext}->.{target}"

    tool_list = CONVERSION_MAP.get(key)

    if tool_list is None:
        # Heuristic guess
        all_media = EXTENSION_CATEGORIES.get("Audio", set()) | EXTENSION_CATEGORIES.get("Video", set())
        all_images = EXTENSION_CATEGORIES.get("Images", set())
        all_docs = EXTENSION_CATEGORIES.get("Documents", set())

        if ext in all_media or f".{target}" in all_media:
            tool_list = ["ffmpeg", "afconvert"]
        elif ext in all_images or f".{target}" in all_images:
            tool_list = ["sips", "magick"]
        elif ext in all_docs or f".{target}" in all_docs:
            tool_list = ["textutil", "pandoc"]
        else:
            console.print(f"[red]Error: Don't know how to convert {ext} -> .{target}[/red]")
            raise typer.Exit(1)

    # Filter candidates by capability (does tool support output format?)
    capable_tools = [t for t in tool_list if _tool_supports_target(t, target)]
    
    if not capable_tools:
        # Fallback for PDF documents if textutil was suggested but can't do it
        if f".{target}" in EXTENSION_CATEGORIES["Documents"] and target == "pdf":
             capable_tools = ["pandoc"]
        else:
             console.print(f"[red]Error: No known tool can convert {ext} -> .{target}[/red]")
             raise typer.Exit(1)

    tool = _resolve_tool(capable_tools)
    if tool is None:
        needed = [t for t in capable_tools if t in TOOLS_URLS]
        if needed:
            console.print(f"[NEED_INSTALL] {needed[0]}")
            console.print(f"[yellow]Missing tool: {needed[0]}. You can install it via the UI.[/yellow]")
        else:
            console.print(f"[red]Error: No available tool for {ext} -> .{target}[/red]")
        raise typer.Exit(1)

    console.print(f"[blue]Converting:[/blue] {Path(input_file).name} -> .{target} [dim](using {tool})[/dim]")

    success = False
    if tool == "python":
        ok = _convert_data(input_file, ext, target, output_path)
        if not ok: raise typer.Exit(1)
        success = True
    elif tool == "sips":
        sips_fmt = SIPS_FORMAT_ALIAS.get(target)
        if not sips_fmt:
            console.print(f"[red]Error: sips output .{target} not supported[/red]")
            raise typer.Exit(1)
        execute_shell_command(f'sips -s format {sips_fmt} "{input_file}" --out "{output_path}"')
        success = True
    elif tool == "afconvert":
        af_fmt = AFCONVERT_FORMATS_MAP.get(target)
        if not af_fmt:
            console.print(f"[red]Error: afconvert output .{target} not supported[/red]")
            raise typer.Exit(1)
        cmd = f'afconvert -f {af_fmt} -d {af_fmt.strip()} "{input_file}" "{output_path}"'
        if target in ("aac", "m4a"):
            cmd = f'afconvert -f m4af -d aac "{input_file}" "{output_path}"'
        execute_shell_command(cmd)
        success = True
    elif tool == "textutil":
        tu_fmt = target if target in TEXTUTIL_FORMATS else None
        if not tu_fmt:
            console.print(f"[red]Error: textutil output .{target} not supported[/red]")
            raise typer.Exit(1)
        execute_shell_command(f'textutil -convert {tu_fmt} -output "{output_path}" "{input_file}"')
        success = True
    elif tool == "ffmpeg":
        execute_shell_command(f'ffmpeg -y -i "{input_file}" "{output_path}"')
        success = True
    elif tool == "pandoc":
        execute_shell_command(f'pandoc "{input_file}" -o "{output_path}"')
        success = True
    elif tool == "magick":
        magick_cmd = "magick" if check_command_availability("magick") else "convert"
        execute_shell_command(f'{magick_cmd} "{input_file}" "{output_path}"')
        success = True

    if success and os.path.exists(output_path):
        size = os.path.getsize(output_path)
        if size > 0:
            console.print(f"[green]Output:[/green] {output_path} ({_human_size(size)})")
        else:
            console.print(f"[yellow]Warning: Output file is empty.[/yellow]")


@app.command()
def organize(
    path: str,
    instructions: str = typer.Option("", "--instructions", "-i"),
    confirm: bool = typer.Option(False, "--confirm"),
):
    """Organize files in a folder."""
    if not os.path.isdir(path):
        console.print(f"[red]Error: Directory not found: {path}[/red]")
        raise typer.Exit(1)

    all_files = [f for f in os.listdir(path) if not f.startswith('.') and os.path.isfile(os.path.join(path, f))]
    if not all_files:
        console.print("[yellow]Folder is empty. Nothing to organize.[/yellow]")
        return

    if instructions.strip():
        plan = _ai_organize_plan(path, all_files, instructions)
    else:
        plan = {}
        for f in all_files:
            cat = _categorize_file(f)
            if cat not in plan: plan[cat] = []
            plan[cat].append(f)

    if not plan:
        console.print("[yellow]No files to move.[/yellow]")
        return

    total_moves = sum(len(files) for files in plan.values())
    console.print(f"\n[bold]Plan:[/bold] Move {total_moves} file(s) into {len(plan)} folder(s):\n")
    for folder, files in sorted(plan.items()):
        console.print(f"  [blue]{folder}/[/blue]")
        for f in files[:5]: console.print(f"    {f}")
        if len(files) > 5: console.print(f"    [dim]... and {len(files)-5} more[/dim]")

    if not confirm:
        console.print("\n[yellow]This is a preview. Re-run with --confirm to execute.[/yellow]")
        return

    console.print("")
    moved = 0
    for folder, files in plan.items():
        dest_dir = os.path.join(path, folder)
        os.makedirs(dest_dir, exist_ok=True)
        for f in files:
            src, dst = os.path.join(path, f), os.path.join(dest_dir, f)
            if os.path.exists(src) and not os.path.exists(dst):
                shutil.move(src, dst)
                moved += 1
    console.print(f"[green]Done. Moved {moved} file(s).[/green]")


def _ai_organize_plan(path: str, files: list, instructions: str) -> dict:
    # Detect image files for vision analysis
    image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp'}
    image_files = [f for f in files if Path(f).suffix.lower() in image_extensions]
    image_paths = [os.path.join(path, f) for f in image_files if os.path.exists(os.path.join(path, f))]
    
    if instructions:
        # User provided specific instructions - ONLY follow those
        if image_paths:
            prompt = f"""SYSTEM: You are a file organizer with vision capabilities. Output ONLY valid JSON.

FOLDER: "{path}"
FILES: {files[:100]}
USER INSTRUCTIONS: {instructions}

I'm showing you the actual images so you can see their CONTENT (not just filenames).
Analyze what's actually IN each image to make better organization decisions.

CRITICAL RULES:
1. Follow ONLY the user's specific instructions above
2. Use the image content (what you SEE in the images) to make decisions
3. Only move files that match the user's request based on their content
4. Leave all other files untouched (do NOT include them in the JSON)
5. If the user mentions a date, also look at image metadata/content for temporal clues
6. Return only the files requested, nothing else

OUTPUT FORMAT: JSON where keys are folder names and values are lists of filenames.
Example: {{"vacation_photos": ["IMG_1234.jpg", "IMG_5678.jpg"]}}
"""
        else:
            prompt = f"""SYSTEM: You are a file organizer. Output ONLY valid JSON.
FOLDER: "{path}"
FILES: {files[:100]}
USER INSTRUCTIONS: {instructions}

CRITICAL RULES:
1. Follow ONLY the user's specific instructions above
2. Only move files that match the user's request
3. Leave all other files untouched (do NOT include them in the JSON)
4. If the user mentions a date like "nov1st" or "nov 1", look for files from late October or early November
5. Return only the files requested, nothing else

OUTPUT FORMAT: JSON where keys are folder names and values are lists of filenames.
Example: {{"folder_name": ["file1.jpg", "file2.jpeg"]}}
"""
    else:
        # No specific instructions - organize everything by category
        if image_paths:
            prompt = f"""SYSTEM: You are a file organizer with vision capabilities. Output ONLY valid JSON.

FOLDER: "{path}"
FILES: {files[:100]}

I'm showing you the actual images so you can analyze their CONTENT.
Look at what's in each image and organize them into meaningful categories based on what you SEE.

TASK: Organize all files into logical category-based subfolders.
- For images: Use content-based categories (e.g., "Nature", "People", "Screenshots", "Memes", etc.)
- For other files: Use type-based categories (Documents, Videos, Music, etc.)

OUTPUT FORMAT: JSON where keys are folder names and values are lists of filenames.
Example: {{"Nature_Photos": ["sunset.jpg"], "Screenshots": ["screen1.png"], "Documents": ["report.pdf"]}}
"""
        else:
            prompt = f"""SYSTEM: You are a file organizer. Output ONLY valid JSON.
FOLDER: "{path}"
FILES: {files[:100]}
TASK: Organize all files into logical category-based subfolders (Images, Documents, Videos, etc.).
OUTPUT FORMAT: JSON where keys are folder names and values are lists of filenames.
"""
    
    # Use vision if we have images (limit to 10 for performance)
    response = get_llm_response(prompt, image_paths=image_paths[:10] if image_paths else None)
    try:
        cleaned = response.strip().replace("```json", "").replace("```", "")
        plan = json.loads(cleaned)
        if isinstance(plan, dict): return plan
    except (json.JSONDecodeError, ValueError, KeyError) as e:
        logging.warning(f"Failed to parse AI organize plan: {e}")
    return {}


@app.command()
def summarize(paths: List[str]):
    """Summarize files using AI."""
    if not paths:
        console.print("[red]Error: No files.[/red]")
        raise typer.Exit(1)
    
    contents = []
    for p in paths:
        if not os.path.isfile(p): continue
        try:
            with open(p, 'r', encoding='utf-8', errors='replace') as f:
                contents.append(f"FILE: {Path(p).name}\n{f.read(4000)}")
        except (OSError, IOError) as e:
            logging.warning(f"Failed to read file {p}: {e}")
        
    if not contents:
        console.print("[red]No readable files.[/red]")
        return

    console.print(f"[blue]Summarizing {len(contents)} file(s)...[/blue]")
    prompt = f"Summarize these files in 3 bullet points:\n\n{chr(10).join(contents)}"
    console.print(f"\n{get_llm_response(prompt)}")


@app.command()
def rename(
    paths: List[str],
    confirm: bool = typer.Option(False, "--confirm"),
):
    """Rename files using AI suggestions."""
    files = [p for p in paths if os.path.isfile(p)]
    if not files:
        console.print("[red]Error: No valid files.[/red]")
        raise typer.Exit(1)
    
    filenames = [Path(f).name for f in files[:30]]
    
    # Detect image files for vision analysis
    image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp'}
    image_files = [f for f in files if Path(f).suffix.lower() in image_extensions]
    
    if image_files:
        # Use vision model to analyze images
        prompt = f"""SYSTEM: You are a file renaming assistant with vision capabilities.

Analyze the provided images and suggest descriptive, clean filenames based on their CONTENT.
- Look at what's actually IN the image (objects, scenes, people, text, etc.)
- Create meaningful names that describe the image content
- Keep original file extensions
- Use underscores or hyphens for spaces
- Keep names concise (2-4 words maximum)

Current filenames: {filenames}

OUTPUT: Valid JSON map with "old_filename": "new_filename" pairs.
Example: {{"IMG_1234.jpg": "sunset_beach.jpg", "photo.png": "golden_retriever.png"}}
"""
        console.print(f"[blue]Analyzing {len(image_files)} image(s) with vision...[/blue]")
        response = get_llm_response(prompt, image_paths=image_files[:5])  # Limit to 5 images
    else:
        # Text-only prompt for non-image files
        prompt = f"""SYSTEM: File renamer. Output valid JSON map "old_name": "new_name".
FILES: {filenames}
TASK: Suggest clean names. Keep extensions.
"""
        console.print(f"[blue]Analyzing {len(files)} file(s)...[/blue]")
        response = get_llm_response(prompt)
    
    try:
        cleaned = response.strip().replace("```json", "").replace("```", "")
        renames = json.loads(cleaned)
    except (json.JSONDecodeError, ValueError) as e:
        console.print(f"[red]Error: AI failed to plan renames: {e}[/red]")
        return

    plan = []
    for p in files:
        old = Path(p).name
        if old in renames and renames[old] != old:
            plan.append((p, str(Path(p).parent / renames[old]), old, renames[old]))
            
    if not plan:
        console.print("[green]No renames needed.[/green]")
        return

    console.print("\n[bold]Plan:[/bold]")
    for _, _, old, new in plan:
        console.print(f"  {old} -> [green]{new}[/green]")

    if not confirm:
        console.print("\n[yellow]Preview only. Use --confirm to execute.[/yellow]")
        return

    count = 0
    for old_path, new_path, _, _ in plan:
        if not os.path.exists(new_path):
            os.rename(old_path, new_path)
            count += 1
    console.print(f"\n[green]Renamed {count} files.[/green]")


@app.command()
def ask(
    query: str = typer.Argument(..., help="Query"),
    paths: List[str] = typer.Argument(None),
):
    context = f"\nFiles: {paths}" if paths else ""
    prompt = f"Write code for: {query}{context}\nOutput ONLY ```python or ```bash block."
    response = get_llm_response(prompt)
    
    lang, code = extract_code_block(response)
    if lang == "python": execute_python_script(code)
    elif lang == "bash": execute_shell_command(code)
    else: console.print(f"[yellow]{response}[/yellow]")


if __name__ == "__main__":
    _init_config()
    app()

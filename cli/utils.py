"""
DEPRECATED: This module is not used by the main alfred.py CLI.
It was an earlier experiment using Gemini via litellm.
The active backend uses Ollama directly (see alfred.py).
Kept for reference only. Safe to delete.
"""

import os
import subprocess
import sys
from typing import Optional
from rich.console import Console
from rich.markdown import Markdown
from litellm import completion  # type: ignore[import-untyped]
from dotenv import load_dotenv, find_dotenv

# Try to find .env file explicitly
dotenv_path = find_dotenv(usecwd=True)
if not dotenv_path:
    # Fallback to looking in the directory of the executable (for frozen app)
    exe_dir = os.path.dirname(sys.executable)
    potential_path = os.path.join(exe_dir, ".env")
    if os.path.exists(potential_path):
        dotenv_path = potential_path

if dotenv_path:
    load_dotenv(dotenv_path)

console = Console()

def get_llm_response(prompt: str, model: str = "gemini/gemini-2.0-flash") -> str:
    """
    Get a response from the LLM. 
    Defaults to Gemini 2.0 Flash as it's fast and efficient.
    Users can set their own keys in .env
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        console.print(f"[bold red]Debug:[/bold red] Looking for .env at: {dotenv_path}")
        console.print(f"[bold red]Debug:[/bold red] Executable: {sys.executable}")
        console.print("[bold red]Error:[/bold red] GEMINI_API_KEY not found in environment.")
        return "Error: No API Key"

    try:
        response = completion(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            api_key=api_key,
            stream=False 
        ) # type: ignore
        
        # Type safe access
        if response and response.choices and len(response.choices) > 0: # type: ignore
            content = response.choices[0].message.content # type: ignore
            return content if content else "Error: Empty response"
        return "Error: No response choices"
    except Exception as e:
        console.print(f"[bold red]LLM Error:[/bold red] {str(e)}")
        return f"Error: {str(e)}"

def check_command_availability(command: str) -> bool:
    """Check if a system command is available."""
    from shutil import which
    return which(command) is not None

def execute_shell_command(command: str):
    """Execute a shell command with rich output."""
    console.print(f"[bold blue]Running:[/bold blue] [green]{command}[/green]")
    try:
        result = subprocess.run(
            command, 
            shell=True, 
            check=True, 
            text=True, 
            capture_output=True
        )
        console.print("[bold green]Success![/bold green]")
        if result.stdout:
            console.print(result.stdout)
    except subprocess.CalledProcessError as e:
        console.print(f"[bold red]Command Failed:[/bold red]")
        console.print(e.stderr)

def execute_python_script(script_content: str):
    """Execute a temporary python script."""
    import tempfile
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as tmp:
        tmp.write(script_content)
        tmp_path = tmp.name
    
    console.print(f"[bold blue]Running Python Script:[/bold blue] [dim]{tmp_path}[/dim]")
    try:
        subprocess.run([sys.executable, tmp_path], check=True)
        console.print("[bold green]Script Execution Successful![/bold green]")
    except subprocess.CalledProcessError:
        console.print("[bold red]Script Execution Failed![/bold red]")
    finally:
        os.remove(tmp_path)

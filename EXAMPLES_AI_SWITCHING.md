# AI Provider Switching Examples

This guide shows practical examples of switching between different AI providers in Alfred.

## Example 1: Start with Ollama (Free, Local)

**Initial Setup:**
```bash
# 1. Install and start Ollama
brew install ollama
ollama pull qwen3:4b
ollama serve  # Run in separate terminal

# 2. Configure Alfred (.env)
AI_PROVIDER=ollama
AI_MODEL=qwen3:4b
OLLAMA_API_BASE=http://localhost:11434
```

**Test it:**
```bash
cd cli
source venv/bin/activate

# Summarize a file
python alfred.py summarize README.md

# Organize files with AI
python alfred.py organize ~/Downloads --instructions "put PDFs in Documents"

# Ask AI to help
python alfred.py ask "write a hello world in python"
```

## Example 2: Switch to OpenAI for Better Quality

When you need higher quality responses:

**Update `.env`:**
```bash
# Get API key from https://platform.openai.com/api-keys
AI_PROVIDER=openai
AI_MODEL=gpt-5-mini  # fast and affordable; use gpt-5.2 for best quality
TEMPERATURE=0.2

OPENAI_API_KEY=sk-proj-...
```

**Same commands work automatically:**
```bash
# No code changes needed!
python alfred.py summarize longdocument.pdf
python alfred.py rename IMG_*.jpg --confirm
```

## Example 3: Switch to Claude for Long Documents

For analyzing large files or precise instructions:

**Update `.env`:**
```bash
AI_PROVIDER=anthropic
AI_MODEL=claude-haiku-4-5  # Fast and affordable; use claude-sonnet-4-6 for best quality
TEMPERATURE=0.2

ANTHROPIC_API_KEY=sk-ant-...
```

**Perfect for:**
```bash
# Summarize long documents
python alfred.py summarize report1.md report2.md report3.md

# Complex file organization
python alfred.py organize ~/Documents --instructions "organize by project and date, create meaningful folder names"
```

## Example 4: Use Google Gemini (Free Tier)

**Update `.env`:**
```bash
AI_PROVIDER=google
AI_MODEL=gemini-2.5-flash
TEMPERATURE=0.2

GOOGLE_API_KEY=AIza...
```

**Test with:**
```bash
python alfred.py summarize *.txt
```

## Example 5: Switch on the Fly (Command Line Override)

No need to edit `.env` - override for a single command:

```bash
# Use GPT-5.2 for one command
AI_PROVIDER=openai AI_MODEL=gpt-5.2 python alfred.py ask "complex task"

# Use Claude for another
AI_PROVIDER=anthropic AI_MODEL=claude-sonnet-4-6 python alfred.py summarize bigfile.pdf

# Back to Ollama
AI_PROVIDER=ollama AI_MODEL=llama3.2 python alfred.py organize ~/Downloads
```

## Example 6: Compare Providers

Test the same task with different providers:

```bash
# Create test file
echo "What is the capital of France?" > test.txt

# Test with different providers
AI_PROVIDER=ollama AI_MODEL=qwen3:4b python alfred.py summarize test.txt
AI_PROVIDER=openai AI_MODEL=gpt-5-mini python alfred.py summarize test.txt
AI_PROVIDER=anthropic AI_MODEL=claude-haiku-4-5 python alfred.py summarize test.txt
AI_PROVIDER=google AI_MODEL=gemini-2.5-flash python alfred.py summarize test.txt
```

## Example 7: Multi-Provider Workflow

Use different providers for different tasks:

**`.env` (default: Ollama for cheap tasks):**
```bash
AI_PROVIDER=ollama
AI_MODEL=qwen3:4b
OLLAMA_API_BASE=http://localhost:11434

# Also set these for when you need them
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
```

**Workflow:**
```bash
# Quick organization: Use Ollama (free)
python alfred.py organize ~/Desktop

# Important document: Use Claude (high quality)
AI_PROVIDER=anthropic AI_MODEL=claude-sonnet-4-6 \
  python alfred.py summarize important_report.pdf

# Batch rename: Use GPT-5 mini (fast, good)
AI_PROVIDER=openai AI_MODEL=gpt-5-mini \
  python alfred.py rename *.jpg --confirm
```

## Example 8: Development vs Production

**Development (`.env.dev`):**
```bash
# Use free local model for development
AI_PROVIDER=ollama
AI_MODEL=qwen3:4b
TEMPERATURE=0.3  # More creative for testing
```

**Production (`.env.prod`):**
```bash
# Use reliable cloud provider for production
AI_PROVIDER=openai
AI_MODEL=gpt-5-mini   # or gpt-5.2 for maximum quality
TEMPERATURE=0.1  # More deterministic
OPENAI_API_KEY=sk-...
```

**Switch between them:**
```bash
# Development
cp .env.dev .env
python alfred.py ...

# Production
cp .env.prod .env
python alfred.py ...
```

## Example 9: Cost Optimization

Optimize for cost vs quality:

```bash
# Free: Ollama (local)
AI_PROVIDER=ollama AI_MODEL=qwen3:4b

# Cheap: Gemini Flash (free tier: 1M tokens/day)
AI_PROVIDER=google AI_MODEL=gemini-2.5-flash

# Balanced: GPT-5-mini ($0.25/$2.00 per 1M)
AI_PROVIDER=openai AI_MODEL=gpt-5-mini

# Premium: Claude Sonnet 4.6 ($3/$15 per 1M)
AI_PROVIDER=anthropic AI_MODEL=claude-sonnet-4-6
```

## Example 10: Fallback Strategy

Create a script with automatic fallback:

```bash
#!/bin/bash
# smart-alfred.sh

# Try Ollama first (free)
AI_PROVIDER=ollama AI_MODEL=qwen3:4b python alfred.py "$@" 2>/dev/null

# If Ollama fails, try Gemini (free tier)
if [ $? -ne 0 ]; then
  echo "Ollama unavailable, trying Gemini..."
  AI_PROVIDER=google AI_MODEL=gemini-2.5-flash python alfred.py "$@" 2>/dev/null
fi

# If Gemini fails, use OpenAI (paid)
if [ $? -ne 0 ]; then
  echo "Gemini unavailable, using OpenAI..."
  AI_PROVIDER=openai AI_MODEL=gpt-5-mini python alfred.py "$@"
fi
```

**Usage:**
```bash
chmod +x smart-alfred.sh
./smart-alfred.sh summarize document.pdf
```

## Tips for Choosing Providers

### When to use Ollama:
- ✅ Development and testing
- ✅ Privacy-sensitive data
- ✅ Unlimited free usage
- ✅ No internet required
- ❌ Requires local GPU/CPU resources

### When to use OpenAI:
- ✅ Production applications
- ✅ Need high reliability
- ✅ Complex reasoning tasks
- ✅ Excellent documentation
- ❌ Costs money per token

### When to use Anthropic Claude:
- ✅ Long documents (200K context)
- ✅ Precise instructions
- ✅ Code generation
- ✅ Following complex rules
- ❌ Higher cost than GPT-4

### When to use Google Gemini:
- ✅ Free tier (generous limits)
- ✅ Fast responses
- ✅ Good value for money
- ✅ Multimodal capabilities
- ❌ Newer, less proven than GPT

## Monitoring Usage

Track which provider you're using:

```bash
# Check current config
cat cli/.env | grep AI_PROVIDER

# View logs
tail -f ~/Desktop/alfred_debug.log | grep "Using.*provider"
```

## Troubleshooting

**"Cannot connect to ollama"**
```bash
# Start Ollama
ollama serve

# Or switch to cloud provider
AI_PROVIDER=openai AI_MODEL=gpt-5-mini python alfred.py ...
```

**"API key error"**
```bash
# Check key is set
cat cli/.env | grep API_KEY

# Test key directly
curl https://api.openai.com/v1/models -H "Authorization: Bearer $OPENAI_API_KEY"
```

**Want to see what LiteLLM is doing?**
```bash
# Enable debug mode
export LITELLM_LOG=DEBUG
python alfred.py summarize test.txt
```

See `AI_PROVIDERS.md` for full documentation!

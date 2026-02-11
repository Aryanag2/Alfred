# AI Provider Configuration Guide

Alfred now supports multiple AI providers through [LiteLLM](https://litellm.ai), allowing you to switch between different models seamlessly.

## Supported Providers

- **Ollama** (local, free)
- **OpenAI** (GPT-4, GPT-3.5, etc.)
- **Anthropic** (Claude 3.5 Sonnet, Claude 3 Opus, etc.)
- **Google** (Gemini Pro, Gemini Flash, etc.)
- And 100+ more providers supported by LiteLLM

## Configuration

Edit `cli/.env` to configure your AI provider:

```bash
# Choose your provider
AI_PROVIDER=ollama  # Options: ollama, openai, anthropic, google

# Specify the model
AI_MODEL=qwen3:4b

# Set temperature (0.0 = deterministic, 1.0 = creative)
TEMPERATURE=0.2

# Provider-specific settings
OLLAMA_API_BASE=http://localhost:11434
```

## Provider Setup Examples

### 1. Ollama (Local, Free)

**Setup:**
```bash
# Install Ollama from https://ollama.ai
brew install ollama  # macOS

# Pull a model
ollama pull qwen3:4b
ollama pull llama3.2
ollama pull deepseek-r1

# Start Ollama
ollama serve
```

**Configuration (`cli/.env`):**
```bash
AI_PROVIDER=ollama
AI_MODEL=qwen3:4b
OLLAMA_API_BASE=http://localhost:11434
TEMPERATURE=0.2
```

**Popular Ollama Models:**
- `qwen3:4b` - Fast, multilingual (recommended)
- `llama3.2` - Meta's Llama 3.2
- `deepseek-r1` - DeepSeek R1 with reasoning
- `gemma2` - Google's Gemma 2
- `mistral` - Mistral AI

### 2. OpenAI (GPT-4, GPT-3.5)

**Setup:**
```bash
# Get API key from https://platform.openai.com/api-keys
```

**Configuration (`cli/.env`):**
```bash
AI_PROVIDER=openai
AI_MODEL=gpt-4o  # or gpt-4o-mini, gpt-3.5-turbo
TEMPERATURE=0.2

# Add your API key
OPENAI_API_KEY=sk-...
```

**Available Models:**
- `gpt-4o` - Latest GPT-4 Optimized
- `gpt-4o-mini` - Faster, cheaper GPT-4
- `gpt-3.5-turbo` - Fast and affordable
- `o1` - Advanced reasoning model

### 3. Anthropic (Claude)

**Setup:**
```bash
# Get API key from https://console.anthropic.com/
```

**Configuration (`cli/.env`):**
```bash
AI_PROVIDER=anthropic
AI_MODEL=claude-3-5-sonnet-20241022  # Latest Claude 3.5 Sonnet
TEMPERATURE=0.2

# Add your API key
ANTHROPIC_API_KEY=sk-ant-...
```

**Available Models:**
- `claude-3-5-sonnet-20241022` - Latest Sonnet (recommended)
- `claude-3-5-haiku-20241022` - Fast, affordable
- `claude-3-opus-20240229` - Most capable

### 4. Google (Gemini)

**Setup:**
```bash
# Get API key from https://aistudio.google.com/apikey
```

**Configuration (`cli/.env`):**
```bash
AI_PROVIDER=google
AI_MODEL=gemini-2.5-flash  # or gemini-2.5-pro
TEMPERATURE=0.2

# Add your API key
GOOGLE_API_KEY=...
```

**Available Models:**
- `gemini-2.5-flash` - Fast and efficient
- `gemini-2.5-pro` - More capable
- `gemini-1.5-pro` - Previous generation

## Switching Providers

To switch between providers, simply edit `cli/.env`:

### Switch from Ollama to OpenAI:
```bash
# Before (Ollama)
AI_PROVIDER=ollama
AI_MODEL=qwen3:4b

# After (OpenAI)
AI_PROVIDER=openai
AI_MODEL=gpt-4o
OPENAI_API_KEY=sk-...
```

### Switch from OpenAI to Claude:
```bash
# Before (OpenAI)
AI_PROVIDER=openai
AI_MODEL=gpt-4o

# After (Anthropic)
AI_PROVIDER=anthropic
AI_MODEL=claude-3-5-sonnet-20241022
ANTHROPIC_API_KEY=sk-ant-...
```

## Testing Your Configuration

Test your AI provider with a simple command:

```bash
cd cli
source venv/bin/activate

# Test with a file
python alfred.py summarize test.txt

# Test with rename
python alfred.py rename file1.txt file2.txt

# Test with ask
python alfred.py ask "What is 2+2?"
```

## Cost Comparison

| Provider | Model | Cost (per 1M tokens) | Speed | Notes |
|----------|-------|---------------------|-------|-------|
| Ollama | Any | **Free** (local) | Fast | Requires local GPU/CPU |
| OpenAI | gpt-4o-mini | $0.15/$0.60 | Very Fast | Best value |
| OpenAI | gpt-4o | $2.50/$10.00 | Fast | Most capable |
| Anthropic | claude-3-5-haiku | $0.80/$4.00 | Very Fast | Fast responses |
| Anthropic | claude-3-5-sonnet | $3.00/$15.00 | Fast | Excellent quality |
| Google | gemini-2.5-flash | Free tier | Very Fast | 1M tokens/day free |
| Google | gemini-2.5-pro | $1.25/$5.00 | Fast | Good value |

*Prices as of Feb 2025. Check provider websites for current pricing.*

## Recommendations

### For Local/Free:
- **Ollama + qwen3:4b** - Fast, no cost, privacy

### For Production/Quality:
- **OpenAI gpt-4o-mini** - Best cost/performance ratio
- **Anthropic Claude 3.5 Sonnet** - Excellent at following instructions
- **Google Gemini 2.5 Flash** - Free tier, very fast

### For Advanced Tasks:
- **OpenAI gpt-4o** - Complex reasoning
- **Anthropic Claude 3.5 Sonnet** - Long documents, precise instructions
- **Google Gemini 2.5 Pro** - Large context, multimodal

## Advanced: Environment Variables

You can override settings via environment variables:

```bash
# One-time override
AI_PROVIDER=anthropic AI_MODEL=claude-3-5-haiku-20241022 python alfred.py summarize file.txt

# Or set in your shell
export AI_PROVIDER=openai
export AI_MODEL=gpt-4o-mini
export OPENAI_API_KEY=sk-...
python alfred.py ...
```

## Troubleshooting

### "Cannot connect to [provider]"
- **Ollama**: Run `ollama serve` first
- **Cloud providers**: Check API key is set correctly

### "Model not found"
- **Ollama**: Run `ollama pull <model>` first
- **Cloud providers**: Check model name matches provider's documentation

### "API key error"
- Verify API key is set in `.env`
- Check key format (OpenAI: `sk-...`, Anthropic: `sk-ant-...`)
- Ensure no extra spaces or quotes

### Tests failing after switching providers
Update test fixtures in `cli/tests/conftest.py` if needed:
```python
alfred._CONFIG["AI_PROVIDER"] = "ollama"
alfred._CONFIG["AI_MODEL"] = "test-model"
```

## Implementation Details

Alfred uses [LiteLLM](https://github.com/BerriAI/litellm) for provider abstraction:
- Single unified API for all providers
- Automatic retry logic
- Consistent output format
- Easy provider switching

See `cli/alfred.py:get_llm_response()` for implementation.

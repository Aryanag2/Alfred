# AI Provider Configuration Guide

Alfred now supports multiple AI providers through [LiteLLM](https://litellm.ai), allowing you to switch between different models seamlessly.

## Supported Providers

- **Ollama** (local, free)
- **OpenAI** (GPT-5.2, GPT-5 mini, GPT-4.1, etc.)
- **Anthropic** (Claude Opus 4.6, Claude Sonnet 4.6, Claude Haiku 4.5, etc.)
- **Google** (Gemini 3 Pro (preview), Gemini 2.5 Pro, Gemini 2.5 Flash, etc.)
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
- `qwen3:4b` - Fast, multilingual (recommended default)
- `llama3.2` - Meta's Llama 3.2 (1B/3B, very lightweight)
- `deepseek-r1` - DeepSeek R1 with reasoning (1.5B–671B)
- `gemma3` - Google's Gemma 3 (vision-capable, 1B–27B)
- `mistral` - Mistral 7B

### 2. OpenAI (GPT-5.2, GPT-5 mini, GPT-4.1)

**Setup:**
```bash
# Get API key from https://platform.openai.com/api-keys
```

**Configuration (`cli/.env`):**
```bash
AI_PROVIDER=openai
AI_MODEL=gpt-5-mini  # or gpt-5.2, gpt-4.1
TEMPERATURE=0.2

# Add your API key
OPENAI_API_KEY=sk-...
```

**Available Models:**
- `gpt-5.2` - Flagship model: best coding and agentic tasks ($1.75/$14 per 1M)
- `gpt-5-mini` - Fast, cost-efficient GPT-5 ($0.25/$2 per 1M, recommended)
- `gpt-5-nano` - Fastest, cheapest GPT-5 ($0.05/? per 1M)
- `gpt-4.1` - Smartest non-reasoning model (previous gen)
- `gpt-4.1-mini` - Affordable GPT-4.1 (previous gen)

### 3. Anthropic (Claude)

**Setup:**
```bash
# Get API key from https://console.anthropic.com/
```

**Configuration (`cli/.env`):**
```bash
AI_PROVIDER=anthropic
AI_MODEL=claude-sonnet-4-6  # Latest Claude Sonnet
TEMPERATURE=0.2

# Add your API key
ANTHROPIC_API_KEY=sk-ant-...
```

**Available Models:**
- `claude-opus-4-6` - Most intelligent, best for complex tasks
- `claude-sonnet-4-6` - Best balance of speed and intelligence (recommended)
- `claude-haiku-4-5` - Fastest, most affordable

### 4. Google (Gemini)

**Setup:**
```bash
# Get API key from https://aistudio.google.com/apikey
```

**Configuration (`cli/.env`):**
```bash
AI_PROVIDER=google
AI_MODEL=gemini-2.5-flash  # or gemini-2.5-pro, gemini-3-pro-preview
TEMPERATURE=0.2

# Add your API key
GOOGLE_API_KEY=...
```

**Available Models:**
- `gemini-3-pro-preview` - Latest: advanced reasoning, 1M context, complex agentic tasks (Preview)
- `gemini-2.5-pro` - GA: high-capability reasoning and coding (recommended)
- `gemini-2.5-flash` - Fast, efficient, free tier available
- `gemini-2.5-flash-lite` - Ultra-efficient for high-throughput tasks
- `gemini-2.0-flash` - Previous generation, still solid

## Switching Providers

To switch between providers, simply edit `cli/.env`:

### Switch from Ollama to OpenAI:
```bash
# Before (Ollama)
AI_PROVIDER=ollama
AI_MODEL=qwen3:4b

# After (OpenAI)
AI_PROVIDER=openai
AI_MODEL=gpt-5-mini
OPENAI_API_KEY=sk-...
```

### Switch from OpenAI to Claude:
```bash
# Before (OpenAI)
AI_PROVIDER=openai
AI_MODEL=gpt-5-mini

# After (Anthropic)
AI_PROVIDER=anthropic
AI_MODEL=claude-sonnet-4-6
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
| OpenAI | gpt-5-nano | $0.05/? | Fastest | Most affordable GPT-5 |
| OpenAI | gpt-5-mini | $0.25/$2.00 | Very Fast | Best value (recommended) |
| OpenAI | gpt-5.2 | $1.75/$14.00 | Medium | Flagship: best coding/agentic |
| OpenAI | gpt-4.1-mini | $0.40/$1.60 | Very Fast | Previous gen, still solid |
| OpenAI | gpt-4.1 | $2.00/$8.00 | Fast | Previous gen flagship |
| Anthropic | claude-haiku-4-5 | $1.00/$5.00 | Very Fast | Fast, affordable |
| Anthropic | claude-sonnet-4-6 | $3.00/$15.00 | Fast | Best balance (recommended) |
| Anthropic | claude-opus-4-6 | $5.00/$25.00 | Moderate | Most intelligent |
| Google | gemini-2.5-flash | Free tier | Very Fast | 1M tokens/day free |
| Google | gemini-2.5-pro | $1.25/$10.00 | Fast | GA: top Gemini model |
| Google | gemini-3-pro-preview | TBD (preview) | Medium | Latest: 1M ctx, preview only |

*Prices as of Feb 2026. Check provider websites for current pricing.*

## Recommendations

### For Local/Free:
- **Ollama + qwen3:4b** - Fast, no cost, privacy

### For Production/Quality:
- **OpenAI gpt-5-mini** - Best cost/performance ratio for GPT-5 tier
- **Anthropic claude-sonnet-4-6** - Excellent at following instructions
- **Google gemini-2.5-flash** - Free tier, very fast

### For Advanced Tasks:
- **OpenAI gpt-5.2** - Best coding and agentic tasks, flagship model
- **Anthropic claude-opus-4-6** - Most intelligent, long documents, precise instructions
- **Google gemini-3-pro-preview** - Latest reasoning model, 1M token context (preview)
- **Google gemini-2.5-pro** - GA: large context, multimodal (stable choice)

## Advanced: Environment Variables

You can override settings via environment variables:

```bash
# One-time override
AI_PROVIDER=anthropic AI_MODEL=claude-haiku-4-5 python alfred.py summarize file.txt

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

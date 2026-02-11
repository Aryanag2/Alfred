# Changelog: Multi-Provider AI Support with LiteLLM

## Summary

Alfred now supports switching between **100+ AI providers** through LiteLLM integration, allowing you to easily switch between Ollama (local/free), OpenAI (GPT-4), Anthropic (Claude), Google (Gemini), and many more.

## Changes Made

### 1. Added LiteLLM Integration
- **File**: `cli/alfred.py`
- **Changed**: Replaced direct Ollama API calls with LiteLLM's unified interface
- **Function**: `get_llm_response()` now supports multiple providers
- **Benefit**: Single codebase works with any AI provider

### 2. New Configuration Options
- **File**: `cli/.env`
- **Added**:
  - `AI_PROVIDER` - Choose provider (ollama, openai, anthropic, google, etc.)
  - `AI_MODEL` - Specify model name
  - `TEMPERATURE` - Control response creativity (0.0-1.0)
  - `OLLAMA_API_BASE` - Ollama server URL
  - API key variables for cloud providers

**Before:**
```bash
OLLAMA_URL=http://localhost:11434/api/generate
OLLAMA_MODEL=qwen3:4b
```

**After:**
```bash
AI_PROVIDER=ollama
AI_MODEL=qwen3:4b
OLLAMA_API_BASE=http://localhost:11434
TEMPERATURE=0.2

# Optional: Set these for cloud providers
# OPENAI_API_KEY=sk-...
# ANTHROPIC_API_KEY=sk-ant-...
# GOOGLE_API_KEY=...
```

### 3. Updated Dependencies
- **File**: `cli/requirements.txt`
- **Added**: `litellm` - Universal LLM API client

### 4. Configuration Refactoring
- **Changed**: Internal config structure from `OLLAMA_*` to `AI_*`
- **Added**: Accessor functions:
  - `get_ai_provider()`
  - `get_ai_model()`
  - `get_ollama_api_base()`
  - `get_temperature()`
- **Removed**: `get_ollama_url()`, `get_ollama_model()`

### 5. Test Suite Updates
- **File**: `cli/tests/conftest.py`
- **Changed**: Mock fixtures to work with LiteLLM
- **Updated**: `mock_ollama()` fixture now mocks LiteLLM's `completion()` function
- **Result**: All 159 tests passing ✅

### 6. Documentation
- **Added**: `AI_PROVIDERS.md` - Comprehensive guide for all providers
- **Added**: `EXAMPLES_AI_SWITCHING.md` - 10 practical examples
- **Added**: `CHANGELOG_AI_SDK.md` - This file

## Migration Guide

### For Existing Users (Ollama)

Your existing setup continues to work! Just update `.env`:

**Old `.env`:**
```bash
OLLAMA_URL=http://localhost:11434/api/generate
OLLAMA_MODEL=qwen3:4b
```

**New `.env`:**
```bash
AI_PROVIDER=ollama
AI_MODEL=qwen3:4b
OLLAMA_API_BASE=http://localhost:11434
```

Everything else works exactly the same.

### Switching to OpenAI

```bash
# Update .env
AI_PROVIDER=openai
AI_MODEL=gpt-4o-mini
OPENAI_API_KEY=sk-...

# Same commands work
python alfred.py summarize file.txt
```

## Supported Providers

| Provider | Models | Cost | Setup |
|----------|--------|------|-------|
| **Ollama** | llama3.2, qwen3, deepseek-r1, etc. | Free | Local installation |
| **OpenAI** | gpt-4o, gpt-4o-mini, o1 | Paid | API key |
| **Anthropic** | claude-3-5-sonnet, claude-3-5-haiku | Paid | API key |
| **Google** | gemini-2.5-pro, gemini-2.5-flash | Free tier | API key |
| **Azure OpenAI** | gpt-4, gpt-3.5 | Paid | Deployment |
| **AWS Bedrock** | Various | Paid | AWS credentials |
| **Cohere** | command-r, command-r-plus | Paid | API key |
| **Groq** | llama3, mixtral | Free tier | API key |
| **...** | 100+ more | Varies | See LiteLLM docs |

Full list: https://docs.litellm.ai/docs/providers

## Benefits

### 1. **Flexibility**
Switch providers without changing code:
```bash
# Development: Free local
AI_PROVIDER=ollama AI_MODEL=qwen3:4b

# Production: Reliable cloud
AI_PROVIDER=openai AI_MODEL=gpt-4o
```

### 2. **Cost Optimization**
Use the right model for each task:
- Quick tasks → Ollama (free)
- Important tasks → Claude Sonnet (best quality)
- Batch processing → GPT-4o-mini (best value)

### 3. **Reliability**
Fallback to different providers if one is down

### 4. **Testing**
Test with cheap/free models, deploy with premium models

### 5. **Privacy**
Use Ollama for sensitive data (100% local)

## Breaking Changes

### ⚠️ Environment Variables

**Removed:**
- `OLLAMA_URL` → Use `OLLAMA_API_BASE` and `AI_PROVIDER=ollama`
- `OLLAMA_MODEL` → Use `AI_MODEL`

**If you have existing scripts:**
```bash
# Before
export OLLAMA_URL=http://localhost:11434/api/generate
export OLLAMA_MODEL=qwen3:4b

# After
export AI_PROVIDER=ollama
export AI_MODEL=qwen3:4b
export OLLAMA_API_BASE=http://localhost:11434
```

### ✅ No Code Changes Required

All CLI commands work exactly the same:
```bash
# Still works!
python alfred.py convert file.png jpg
python alfred.py organize ~/Downloads
python alfred.py summarize report.pdf
python alfred.py rename *.jpg --confirm
python alfred.py ask "help me with this"
```

## Testing

All tests passing after migration:
```bash
$ cd cli && pytest tests/ -v
159 passed in 6.37s ✅
```

## Next Steps

1. **Try different providers** - See `EXAMPLES_AI_SWITCHING.md`
2. **Read full docs** - See `AI_PROVIDERS.md`
3. **Optimize costs** - Use free/cheap models for development
4. **Share feedback** - Let us know which providers work best!

## Technical Details

### LiteLLM Integration

LiteLLM provides a unified OpenAI-compatible interface:

```python
from litellm import completion

# Works with any provider
response = completion(
    model="ollama/qwen3:4b",  # or openai/gpt-4o, anthropic/claude-3-5-sonnet, etc.
    messages=[{"role": "user", "content": "Hello"}],
    temperature=0.2,
    api_base="http://localhost:11434"  # Only for Ollama
)

content = response.choices[0].message.content
```

See implementation in `alfred.py:get_llm_response()` (line ~91)

### Provider-Specific Configuration

Each provider uses standard environment variables:
- **OpenAI**: `OPENAI_API_KEY`
- **Anthropic**: `ANTHROPIC_API_KEY`
- **Google**: `GOOGLE_API_KEY`
- **Azure**: `AZURE_API_KEY`, `AZURE_API_BASE`, `AZURE_API_VERSION`

LiteLLM handles all the API differences automatically!

## Acknowledgments

- [LiteLLM](https://github.com/BerriAI/litellm) - Universal LLM client
- [Vercel AI SDK](https://sdk.vercel.ai) - Inspiration for provider abstraction
- All the AI model providers for their amazing APIs

---

**Version**: 0.2.0  
**Date**: February 2025  
**Author**: Alfred Team

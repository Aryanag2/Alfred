# How to Verify LiteLLM is Working

## Quick Verification Methods

### Method 1: Run Verification Script (Easiest)
```bash
cd cli
source venv/bin/activate
python verify_litellm.py
```

**Expected Output:**
```
============================================================
Testing LiteLLM with Gemini 2.5 Flash
============================================================

✓ Provider: gemini
✓ Model: gemini/gemini-2.5-flash
✓ API Key: AIzaSy...****

📡 Sending test request to LiteLLM...

✅ SUCCESS! Response received:
   LiteLLM is working!

✓ Model used: gemini-2.5-flash
✓ Tokens used: 38

============================================================
🎉 LiteLLM is working correctly!
============================================================
```

✅ If you see this, LiteLLM is working!

---

### Method 2: Test with Alfred CLI
```bash
cd cli
source venv/bin/activate

# Simple test
python alfred.py ask "Say hello in 3 words"

# File summarization test
echo "This is a test file for LiteLLM verification" > test.txt
python alfred.py summarize test.txt
```

**Expected:** You should see AI-generated responses from Gemini.

---

### Method 3: Python Interactive Test
```bash
cd cli
source venv/bin/activate
python3
```

Then run:
```python
from litellm import completion
import os
from dotenv import load_dotenv

load_dotenv()

response = completion(
    model="gemini/gemini-2.5-flash",
    messages=[{"role": "user", "content": "Hello!"}],
    api_key=os.getenv("GOOGLE_API_KEY")
)

print(response.choices[0].message.content)
```

**Expected:** You should see a greeting response from Gemini.

---

### Method 4: Check Configuration
```bash
cd cli
cat .env
```

**Verify these settings exist:**
```bash
AI_PROVIDER=gemini
AI_MODEL=gemini/gemini-2.5-flash
TEMPERATURE=0.7
GOOGLE_API_KEY=your-google-api-key-here
```

---

### Method 5: Check Available Models
```bash
cd cli
source venv/bin/activate
python3 -c "from litellm import model_list; print('LiteLLM loaded successfully')"
```

**Expected:** Should print "LiteLLM loaded successfully" without errors.

---

## Troubleshooting

### Issue: ModuleNotFoundError: No module named 'litellm'
**Solution:**
```bash
cd cli
source venv/bin/activate
pip install litellm
```

### Issue: API Key Error
**Check:**
```bash
cd cli
source venv/bin/activate
python3 -c "import os; from dotenv import load_dotenv; load_dotenv(); print(os.getenv('GOOGLE_API_KEY'))"
```

Should print your API key. If it prints `None`, your .env file is not loaded correctly.

### Issue: Model Not Found
**Test available models:**
```bash
curl -s "https://generativelanguage.googleapis.com/v1beta/models?key=YOUR_API_KEY" | python3 -m json.tool | grep '"name"'
```

---

## Common LiteLLM Commands

### List Supported Providers
```python
from litellm import provider_list
print(provider_list)
```

### Check Model Cost
```python
from litellm import completion_cost
import litellm

response = litellm.completion(
    model="gemini/gemini-2.5-flash",
    messages=[{"role": "user", "content": "Hi"}]
)

cost = completion_cost(completion_response=response)
print(f"Cost: ${cost:.6f}")
```

### Enable Debug Logging
```python
import litellm
litellm.set_verbose = True

# Now all calls will show debug info
response = litellm.completion(...)
```

---

## Verification Checklist

- [ ] LiteLLM package installed (`pip list | grep litellm`)
- [ ] .env file exists with GOOGLE_API_KEY
- [ ] API key is valid (40-50 characters, starts with "AIza")
- [ ] Model name is correct (gemini/gemini-2.5-flash)
- [ ] Python venv is activated
- [ ] No import errors when running verification script
- [ ] Test API call completes successfully

---

## Quick Health Check Command

Run this one-liner to check everything:
```bash
cd cli && source venv/bin/activate && python verify_litellm.py
```

**Pass:** LiteLLM is working ✅  
**Fail:** See troubleshooting section above ❌

---

## LiteLLM UI (Optional)

**Note:** LiteLLM UI currently has compatibility issues with Python 3.14.

**Alternative:** Use the verification script and Alfred CLI instead. They work perfectly!

If you really need the UI, you can:
1. Create a Python 3.11 or 3.12 virtual environment
2. Install litellm[proxy] there
3. Run the proxy server

But it's not necessary - the core LiteLLM library works great in Alfred!

---

## Success Indicators

When LiteLLM is working correctly:

1. ✅ Verification script passes
2. ✅ Alfred CLI commands respond with AI output
3. ✅ No import errors in Python
4. ✅ API calls complete in 1-5 seconds
5. ✅ Responses are relevant and well-formatted

---

## What LiteLLM Does in Alfred

LiteLLM is the core AI library that:
- Connects to Gemini (and 100+ other AI providers)
- Handles authentication with API keys
- Formats requests in the correct format
- Parses responses into usable text
- Manages retries and error handling
- Tracks token usage and costs

**In Alfred, LiteLLM powers:**
- File summarization
- Smart file renaming
- File organization
- Natural language queries
- All AI features

---

**Created:** February 10, 2025  
**Last Updated:** February 10, 2025  
**Status:** ✅ LiteLLM Working

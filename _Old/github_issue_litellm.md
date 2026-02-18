# LiteLLM Proxy fails to start on Python 3.14 due to uvloop incompatibility

## Description
LiteLLM Proxy server fails to start on Python 3.14 due to `uvloop` package incompatibility. The proxy crashes with `ImportError: cannot import name 'BaseDefaultEventLoopPolicy' from 'asyncio.events'`.

## Environment
- **Python Version:** 3.14.2
- **LiteLLM Version:** 1.81.10
- **uvicorn Version:** 0.31.1
- **uvloop Version:** 0.21.0 (cannot downgrade - won't compile on Python 3.14)
- **OS:** macOS 15.0 (arm64)
- **Installation:** `pip install 'litellm[proxy]'`

## Steps to Reproduce

1. Install Python 3.14.2
2. Create virtual environment:
   ```bash
   python3.14 -m venv venv
   source venv/bin/activate
   ```
3. Install LiteLLM with proxy:
   ```bash
   pip install 'litellm[proxy]'
   ```
4. Create minimal config file (`litellm_config.yaml`):
   ```yaml
   model_list:
     - model_name: test-model
       litellm_params:
         model: gemini/gemini-2.5-flash
         api_key: test-key
   ```
5. Start proxy:
   ```bash
   litellm --config litellm_config.yaml --port 4000
   ```

## Expected Behavior
LiteLLM proxy should start successfully and serve on port 4000.

## Actual Behavior
Proxy crashes immediately with the following error:

```
Traceback (most recent call last):
  File "/path/to/venv/bin/litellm", line 7, in <module>
    sys.exit(run_server())
  File "/path/to/venv/lib/python3.14/site-packages/click/core.py", line 1485, in __call__
    return self.main(*args, **kwargs)
  File "/path/to/venv/lib/python3.14/site-packages/litellm/proxy/proxy_cli.py", line 850, in run_server
    uvicorn.run(**uvicorn_args, workers=num_workers)
  File "/path/to/venv/lib/python3.14/site-packages/uvicorn/main.py", line 579, in run
    server.run()
  File "/path/to/venv/lib/python3.14/site-packages/uvicorn/server.py", line 64, in run
    self.config.setup_event_loop()
  File "/path/to/venv/lib/python3.14/site-packages/uvicorn/config.py", line 475, in setup_event_loop
    loop_setup: Callable | None = import_from_string(LOOP_SETUPS[self.loop])
  File "/path/to/venv/lib/python3.14/site-packages/uvicorn/importer.py", line 19, in import_from_string
    module = importlib.import_module(module_str)
  File "/opt/homebrew/Cellar/python@3.14/3.14.2_1/Frameworks/Python.framework/Versions/3.14/lib/python3.14/importlib/__init__.py", line 88, in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
  File "/path/to/venv/lib/python3.14/site-packages/uvicorn/loops/uvloop.py", line 3, in <module>
    import uvloop
  File "/path/to/venv/lib/python3.14/site-packages/uvloop/__init__.py", line 6, in <module>
    from asyncio.events import BaseDefaultEventLoopPolicy as __BasePolicy
ImportError: cannot import name 'BaseDefaultEventLoopPolicy' from 'asyncio.events'
```

## Root Cause Analysis

1. **Python 3.14 API Changes:** Python 3.14 removed `BaseDefaultEventLoopPolicy` from `asyncio.events`
2. **uvloop 0.21.0:** Latest uvloop version tries to import the removed class
3. **uvloop 0.20.x:** Cannot compile on Python 3.14 (C extension compilation errors)
4. **uvicorn dependency:** LiteLLM proxy uses uvicorn, which defaults to uvloop for better performance

## Attempted Workarounds

### ❌ Downgrade uvloop to 0.20.x
```bash
pip install 'uvloop<0.21'
```
**Result:** Fails to compile on Python 3.14 with C extension errors:
```
error: call to undeclared function '_PyInterpreterState_GetConfig'
error: call to undeclared function '_PyDict_SetItem_KnownHash'
error: too few arguments to function call '_PyLong_AsByteArray'
```

### ❌ Set UVICORN_LOOP_TYPE environment variable
```bash
UVICORN_LOOP_TYPE=asyncio litellm --config config.yaml
```
**Result:** Still attempts to import uvloop, same error occurs.

### ❌ Uninstall uvloop
```bash
pip uninstall uvloop
```
**Result:** LiteLLM proxy dependencies require uvloop.

## Current Workarounds

### ✅ Option 1: Use Docker (Recommended)
```bash
docker run \
  -v $(pwd)/litellm_config.yaml:/app/config.yaml \
  -p 4000:4000 \
  ghcr.io/berriai/litellm:main-latest \
  --config /app/config.yaml
```

### ✅ Option 2: Use Python 3.11 or 3.12
```bash
pyenv install 3.12.0
python3.12 -m venv venv
source venv/bin/activate
pip install 'litellm[proxy]'
litellm --config config.yaml
```

## Impact

**Severity:** Medium
- **Core LiteLLM library:** ✅ Works fine on Python 3.14 (direct API calls work)
- **LiteLLM Proxy/UI:** ❌ Completely broken on Python 3.14
- **Workarounds:** Available but require Docker or older Python versions

## Suggested Solutions

### Short-term (Quick Fix)
1. **Add CLI flag to disable uvloop:**
   ```bash
   litellm --config config.yaml --loop-type asyncio
   ```
   Or expose uvicorn's `--loop none` option through LiteLLM CLI.

2. **Make uvloop optional dependency:**
   - Don't fail if uvloop import fails
   - Fallback to standard asyncio

### Long-term (Ideal)
1. **Update uvicorn dependency:**
   - Wait for uvicorn to support Python 3.14 without uvloop requirement
   - Or switch to alternative ASGI server

2. **Pin uvloop version range:**
   - Document Python 3.14 incompatibility in requirements
   - Add Python version check with helpful error message

## Related Issues
- uvloop issue: https://github.com/MagicStack/uvloop/issues/609 (Python 3.14 support)
- uvicorn issue: https://github.com/encode/uvicorn/issues/2511 (uvloop optional)

## Additional Context

**Note:** The core LiteLLM library (without proxy) works perfectly on Python 3.14:
```python
from litellm import completion

response = completion(
    model="gemini/gemini-2.5-flash",
    messages=[{"role": "user", "content": "Hello"}]
)
print(response.choices[0].message.content)  # Works fine!
```

Only the proxy server (which uses uvicorn/uvloop) is affected.

## Verification

To verify this issue on Python 3.14:
```bash
python3 --version  # Should show 3.14.x
pip install 'litellm[proxy]'
litellm --model gpt-3.5-turbo  # Will crash
```

---

**Would appreciate:** 
- Adding Python 3.14 to CI/CD testing
- Making uvloop optional or providing fallback
- Documentation noting Python 3.14 incompatibility until fixed

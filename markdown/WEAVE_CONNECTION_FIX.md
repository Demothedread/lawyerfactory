# Weave/WandB Connection Fix

## Issue

**Error**: `NameResolutionError: Could not initialize Tavily: HTTPSConnectionPool(host='api.wandb.ai', port=443): Max retries exceeded with url: /graphql`

**Root Cause**: The `tavily_integration.py` module was calling `weave.init()` during import, which attempted to connect to Weights & Biases (wandb.ai) for observability. This blocked the entire Tavily integration from initializing when:
- Network connectivity to wandb.ai was unavailable
- WandB API was unreachable
- Firewall/proxy blocked the connection

## Solution

Wrapped the `weave.init()` call in a try-except block to make it optional and non-blocking:

### File: `/src/lawyerfactory/research/tavily_integration.py`

**Before** (lines 73-74):
```python
# Initialize Weave for observability
if weave:
    weave.init(project_name="lawyerfactory-research")
```

**After** (lines 73-79):
```python
# Initialize Weave for observability (optional - don't block on connection errors)
if weave:
    try:
        weave.init(project_name="lawyerfactory-research")
        logger.info("Weave observability initialized")
    except Exception as e:
        logger.warning(f"Weave initialization failed (non-critical): {e}")
```

## Impact

### ✅ Positive Changes
- Tavily integration now initializes successfully even without wandb.ai connectivity
- Research functionality works independently of observability tools
- Graceful degradation: observability is optional, not required
- Clear logging indicates whether Weave is available

### ⚠️ Trade-offs
- Weave observability features (request tracing, performance monitoring) will be disabled if connection fails
- Users who need Weave tracking must ensure wandb.ai connectivity

## Testing

### Verify Fix Works

1. **Without WandB Connection** (simulated network failure):
   ```bash
   # Block wandb.ai in /etc/hosts or firewall
   ./launch.sh
   # Should start successfully with warning: "Weave initialization failed (non-critical)"
   ```

2. **With WandB Connection** (normal operation):
   ```bash
   # Ensure WANDB_API_KEY is set (optional)
   export WANDB_API_KEY=your_key_here
   ./launch.sh
   # Should start with: "Weave observability initialized"
   ```

3. **Integration Test**:
   ```bash
   # Test Tavily research without Weave
   curl -X POST http://localhost:5000/api/research/execute \
     -H "Content-Type: application/json" \
     -d '{"case_id": "test", "evidence_id": "test_evidence", "keywords": ["test"]}'
   # Should execute successfully regardless of Weave status
   ```

## Related Files

- `/src/lawyerfactory/research/tavily_integration.py` - Fixed Weave initialization
- `/src/lawyerfactory/agents/research/research.py` - Imports TavilyResearchIntegration
- `/apps/api/server.py` - Flask server that loads research module on startup

## Future Considerations

1. **Configuration Option**: Add `ENABLE_WEAVE_OBSERVABILITY` environment variable for explicit control
2. **Alternative Observability**: Consider OpenTelemetry or built-in Flask logging as alternatives
3. **Conditional Import**: Make `weave` import fully optional with graceful fallback

## Deployment Notes

- **Production**: Ensure this fix is deployed before enabling Tavily research features
- **Environment**: No new environment variables required; `WANDB_API_KEY` remains optional
- **Monitoring**: Check logs for "Weave initialization failed" warnings to identify connectivity issues

---

**Fixed**: 2025-01-16  
**Severity**: Critical (blocking feature)  
**Resolution**: Non-blocking observability initialization

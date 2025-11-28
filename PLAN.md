# Plan: Add reasoning_key Support for openai_legacy Provider

## Problem Statement
Kimi CLI does not currently support passing the `reasoning_key` parameter to OpenAI-compatible providers that inject reasoning content in custom fields (e.g., `"reasoning": ...`). This limits compatibility with certain OpenAI-compatible APIs.

## Required Changes

### 1. Configuration Model Enhancement
**File:** `src/kimi_cli/config.py`

Add `reasoning_key` field to the `LLMProvider` class to allow users to specify the custom field name for reasoning content.

**Change:**
```python
class LLMProvider(BaseModel):
    """LLM provider configuration."""

    type: ProviderType
    base_url: str
    api_key: SecretStr
    custom_headers: dict[str, str] | None = None
    reasoning_key: str | None = None  # NEW FIELD
    """Custom field key for reasoning content in OpenAI-compatible APIs"""
```

### 2. OpenAI Legacy Provider Initialization
**File:** `src/kimi_cli/llm.py`

Update the `openai_legacy` case in the `create_llm()` function to pass the `reasoning_key` parameter to the `OpenAILegacy` constructor.

**Change:**
```python
case "openai_legacy":
    from kosong.contrib.chat_provider.openai_legacy import OpenAILegacy

    chat_provider = OpenAILegacy(
        model=model.model,
        base_url=provider.base_url,
        api_key=provider.api_key.get_secret_value(),
        reasoning_key=provider.reasoning_key,  # NEW PARAMETER
    )
```

### 3. Optional: Environment Variable Support
**File:** `src/kimi_cli/llm.py`

Update `augment_provider_with_env_vars()` to support `reasoning_key` via environment variables for dynamic configuration.

**Change:**
```python
case "openai_legacy":
    # ... existing env var handling ...
    if reasoning_key := os.getenv("OPENAI_REASONING_KEY"):
        provider.reasoning_key = reasoning_key
        applied["OPENAI_REASONING_KEY"] = reasoning_key
```

## Implementation Steps

1. **Update Configuration Model**
   - Add `reasoning_key` field to `LLMProvider` class
   - Update docstring and type hints

2. **Modify Provider Factory**
   - Update `create_llm()` to pass `reasoning_key` to OpenAILegacy constructor

3. **Optional: Environment Variable Support**
   - Add support for `OPENAI_REASONING_KEY` environment variable

4. **Validation and Testing**
   - Test with a mock OpenAI-compatible API that uses custom reasoning fields
   - Verify configuration loading and serialization
   - Ensure backward compatibility (provider works without `reasoning_key`)

5. **Documentation**
   - Update AGENTS.md with `reasoning_key` usage examples
   - Add configuration examples to README or docs

## Usage Example

### Configuration File (`~/.kimi/config.json`)

```json
{
  "providers": {
    "deepseek-chat": {
      "type": "openai_legacy",
      "base_url": "https://api.deepseek.com/v1",
      "api_key": "sk-your-api-key-here",
      "reasoning_key": "reasoning_content"
    }
  },
  "models": {
    "deepseek-coder": {
      "provider": "deepseek-chat",
      "model": "deepseek-coder",
      "max_context_size": 64000,
      "capabilities": ["thinking"]
    }
  },
  "default_model": "deepseek-coder"
}
```

### Environment Variable Alternative

```bash
export OPENAI_REASONING_KEY="reasoning_content"
```

## Technical Details

The `reasoning_key` parameter is used to:

1. **Send Reasoning Content**: When creating messages with reasoning/thinking content, the specified key is included in the message payload
2. **Extract Reasoning Content**: When receiving responses, the provider looks for reasoning content under the specified custom field name

This enables compatibility with OpenAI-compatible APIs that deviate from the standard OpenAI format by using custom field names for reasoning content.

## Testing Checklist

- [ ] Configuration file loads with `reasoning_key` field
- [ ] Configuration file validates correctly
- [ ] Provider initializes with `reasoning_key` parameter
- [ ] API calls include custom reasoning field when specified
- [ ] API responses correctly extract reasoning content from custom field
- [ ] Backward compatibility: provider works without `reasoning_key`
- [ ] Environment variable override works correctly

## Impact Assessment

- **Breaking Changes**: None - this is an additive feature
- **Backward Compatibility**: Fully maintained - `reasoning_key` is optional
- **Dependencies**: No new dependencies required
- **Performance**: No performance impact

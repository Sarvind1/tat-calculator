# Migration Guide: From Monolithic to Modular TAT Calculator

## Overview

The TAT Calculator has been refactored from a single monolithic file (`tat_calculator.py`) into a modular structure with 4 specialized modules. This improves maintainability, testability, and code organization.

## Module Mapping

The original `tat_calculator.py` has been split into:

1. **`models_config.py`**
   - All Pydantic models (ProcessFlow, StageConfig, etc.)
   - Configuration loading and validation functions

2. **`expression_evaluator.py`**
   - Expression evaluation logic
   - Custom functions (max, add_days, cond)
   - Date parsing utilities

3. **`stage_calculator.py`**
   - Core stage calculation logic
   - Memoization implementation
   - Precedence vs actual comparison

4. **`tat_processor.py`**
   - TAT orchestration for all stages
   - Result formatting
   - Excel export functionality

5. **`tat_calculator_main.py`**
   - Main entry point that coordinates all modules
   - Backward compatibility layer

## Migration Steps

### For Users

No changes required! The system maintains backward compatibility:

```python
# Old way still works:
from tat_calculator import TATCalculator

# New way (recommended):
from tat_calculator_main import TATCalculator

# Both work identically
calculator = TATCalculator()
results = calculator.process_batch(df)
```

### For Developers

When making changes:

1. **Configuration changes**: Only edit `stages_config.json`
2. **Expression functions**: Edit `expression_evaluator.py`
3. **Calculation logic**: Edit `stage_calculator.py`
4. **Output formats**: Edit `tat_processor.py`

## Key Benefits

1. **Single Responsibility**: Each module has one clear purpose
2. **Easier Testing**: Test individual components in isolation
3. **Better Maintainability**: Changes are localized to relevant modules
4. **Improved Readability**: Smaller, focused files are easier to understand
5. **Reusability**: Components can be used independently

## Backward Compatibility

The old `tat_calculator.py` file remains in the repository for backward compatibility. The `run_tat_calculation.py` script automatically tries the new modular version first, falling back to the old version if needed.

## Important Notes

- All functionality remains the same
- No changes to `stages_config.json` format
- Excel input/output formats unchanged
- JSON output structure unchanged

## Future Deprecation

The monolithic `tat_calculator.py` will be maintained for 3 months (until September 2025) and then deprecated. Please update any custom scripts to use `tat_calculator_main.py` instead.

# Commits Guide - TAT Calculator Project

## Overview
This document tracks significant changes and provides guidance for commit messages in the TAT Calculator project.

## Commit Message Format
```
[Type] Brief description of change

- Detailed bullet point 1
- Detailed bullet point 2
- Impact or reason for change
```

## Change Types
- **Fix**: Bug fixes and corrections
- **Feature**: New functionality
- **Refactor**: Code restructuring without behavior change
- **Config**: Changes to stages_config.json
- **Docs**: Documentation updates
- **Performance**: Performance improvements

## Recent Changes Log

### 2025-06-26: Fix delay calculation to use target_date from stage_calculations
**Type**: Fix  
**Files Modified**: `delay_calculator.py`  
**Commit SHA**: 8750a230e2fb6ebe2b38a0f8b78c9eb8b08f1dcf

**Issue**: Delay calculations were incorrectly using `stage_result["timestamp"]` as the target timestamp, which represents the final calculated completion time rather than the target date for delay analysis.

**Solution**: 
- Modified `calculate_stage_delay()` to extract `target_date` from stage calculation details
- Changed from using `stage_result["timestamp"]` to `stage_result["calculation"]["target_date"]`
- Added robust target timestamp extraction logic with fallback support
- Maintained backward compatibility for different calculation result structures
- Enhanced error handling and logging for missing target_date fields

**Impact**: 
- Delay calculations now use the correct baseline (target_date) for comparison
- More accurate delay analysis and reporting
- Better alignment between TAT calculations and delay analysis
- Improved transparency in delay calculation methodology

**Code Changes**:
```python
# Before (INCORRECT):
target_timestamp = stage_result.get("timestamp")

# After (CORRECT):
target_timestamp = self._extract_target_timestamp(stage_result)
# which extracts from stage_result["calculation"]["target_date"]
```

## Development Guidelines

### Before Making Changes
1. Review the project_brain.md for architecture understanding
2. Check existing code patterns and naming conventions
3. Ensure changes align with modular structure principles

### Change Process
1. Make targeted, specific changes
2. Test changes on sample data
3. Update relevant documentation
4. Commit with descriptive message following the format above
5. Update this commits_guide.md with change details

### Configuration Changes
- Most business logic changes should be in `stages_config.json`
- Code changes should only be for new features or bug fixes
- Always validate configuration after changes

### Testing Approach
- Test with `ts_small.xlsx` first
- Verify calculations match expected results
- Check JSON output structure remains consistent
- Ensure Excel export functionality works

## Future Improvements Tracking

### Planned Enhancements
- [ ] Enhanced delay reporting with trend analysis
- [ ] Performance optimization for large datasets
- [ ] Additional custom functions in expression evaluator
- [ ] Automated testing framework

### Known Issues
- None currently identified

---

**Note**: This guide should be updated after every significant change to maintain project history and development patterns.


# TAT Calculator Logic Alignment - Fix Summary

## Issue Identified
After commit `f185c4974185bdf01487f0bc911e63116b6d6956`, subsequent commits introduced a modular structure that inadvertently changed the core calculation logic in `stage_calculator.py`, deviating from the original `tat_calculator.py` implementation.

## Key Differences Fixed

### 1. **Fallback Calculation Timing**
**Original Logic (tat_calculator.py):**
- If no precedence_timestamp is available, immediately use fallback calculation
- Fallback is used as an early exit condition

**Previous Modular Logic (stage_calculator.py - WRONG):**
- Fallback was only used at the very end if all other methods failed
- This changed the priority sequence

**Fixed Logic:**
```python
# 2. ORIGINAL LOGIC: If no precedence, use fallback IMMEDIATELY
if not precedence_timestamp:
    fallback_result, fallback_formula = self.expression_evaluator.evaluate_expression(
        stage.fallback_calculation.expression, po_row
    )
    if fallback_result:
        final_timestamp = fallback_result + timedelta(days=stage.lead_time)
        calc_details["method"] = "fallback"
        # Cache result and return (ORIGINAL LOGIC)
        result = (final_timestamp, calc_details)
        self.calculated_adjustments[stage_id] = result
        return result
```

### 2. **Lead Time Application**
**Original Logic:**
- Lead time applied differently based on calculation method
- `precedence_timestamp` stored WITHOUT lead time
- Lead time added when creating final timestamp

**Fixed Logic:**
```python
# Store precedence without lead time (ORIGINAL)
precedence_timestamp = base_timestamp  # WITHOUT lead time here

# Apply lead time when creating final result (ORIGINAL)
if precedence_over_actual:
    final_timestamp = precedence_timestamp + timedelta(days=stage.lead_time)
```

### 3. **Priority Sequence**
**Original Priority:**
1. Calculate precedence (if available)
2. **If no precedence → immediate fallback (early exit)**
3. If precedence available → compare with actual
4. Choose max(precedence, actual) with proper lead time application

**Fixed Logic maintains this exact sequence.**

## Files Modified

### `stage_calculator.py` - PRIMARY FIX
- Restored original fallback timing logic
- Fixed lead time application to match original
- Maintained exact priority sequence from commit f185c4974185bdf01487f0bc911e63116b6d6956
- Added detailed comments marking "ORIGINAL LOGIC" sections

### Other Files (Already Aligned)
- `tat_calculator.py` - **UNCHANGED** (preserves original logic)
- `tat_calculator_main.py` - Good (proper modular wrapper)
- `tat_processor.py` - Good (maintains compatibility)
- `run_tat_calculation.py` - Good (has fallback mechanism)

## Verification Steps

### 1. **Logic Consistency Test**
```python
# Both should produce identical results for the same input
from tat_calculator import TATCalculator as OriginalTAT
from tat_calculator_main import TATCalculator as ModularTAT

original = OriginalTAT("stages_config.json")
modular = ModularTAT("stages_config.json")

# Test with same PO data
result1 = original.calculate_tat(po_row)
result2 = modular.calculate_tat(po_row)

# Compare timestamps for each stage
for stage_id in result1['stages']:
    assert result1['stages'][stage_id]['timestamp'] == result2['stages'][stage_id]['timestamp']
```

### 2. **Fallback Logic Test**
```python
# Create a PO with no preceding stages available
# Should immediately use fallback calculation
test_po = pd.Series({
    'po_razin_id': 'TEST_001',
    'po_created_date': datetime(2025, 6, 1),
    # Missing all other timestamp fields
})

result = calculator.calculate_tat(test_po)
# Check that stages used fallback method correctly
```

### 3. **Lead Time Application Test**
```python
# Verify lead times are applied correctly based on calculation method
# Check calc_details["lead_time_applied"] matches stage configuration
```

## Benefits of This Fix

1. **Preserves Original Logic**: Core calculation behavior remains identical to commit f185c4974185bdf01487f0bc911e63116b6d6956
2. **Maintains Modularity**: Code organization benefits are preserved
3. **Backward Compatibility**: Original `tat_calculator.py` still works
4. **Forward Compatibility**: Modular system works with delay analysis and other new features

## Usage

### Option 1: Use Original Monolithic Version
```python
from tat_calculator import TATCalculator
calculator = TATCalculator("stages_config.json")
```

### Option 2: Use Fixed Modular Version  
```python
from tat_calculator_main import TATCalculator
calculator = TATCalculator("stages_config.json")
```

### Option 3: Use Runner (Recommended)
```python
# Automatically chooses best available version
python run_tat_calculation.py
```

## Confidence Level
- **HIGH**: The fix addresses the core logical differences
- **VERIFIED**: Original calculation precedence restored
- **TESTED**: Modular structure maintains compatibility
- **FUTURE-PROOF**: Changes are minimal and preserve both old and new functionality


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
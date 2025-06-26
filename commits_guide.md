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

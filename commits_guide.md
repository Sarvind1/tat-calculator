# TAT Calculator - Commits Guide

## Latest Changes (January 2025)

### Refactoring: Simplified TAT Calculation Logic
**Date**: 2025-01-XX
**Branch**: main

#### Changes Made:
1. **Modified `stage_calculator.py`**:
   - Simplified calculation logic to use Method (Projected/Actual/Adjusted)
   - Added target_timestamp, actual_timestamp, final_timestamp fields
   - Removed complex precedence logic
   - Added delay calculation only for Actual/Adjusted methods

2. **Deleted `delay_calculator.py`**:
   - Integrated delay calculation into stage_calculator.py

3. **Modified `tat_processor.py`**:
   - Updated to handle new calculation structure
   - Modified output generation for 5-tab Excel format

4. **Modified `tat_calculator_main.py`**:
   - Removed delay calculator imports and calls
   - Simplified main orchestration logic

#### Key Logic Changes:
- Method = "Projected" when no actual_field
- Method = "Actual" when actual_field exists and current >= preceding
- Method = "Adjusted" when actual_field exists but preceding > current
- Target = max(preceding.final_timestamp) + lead_time
- Final = Target (if Projected) or Actual (if Actual/Adjusted)
- Delay = Target - Actual (only for Actual/Adjusted)

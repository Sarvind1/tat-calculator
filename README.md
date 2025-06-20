# TAT Calculator System

A comprehensive Turn Around Time (TAT) calculation system for Purchase Order workflows with support for conditional dependencies and dynamic expressions.

## Key Features

- **Configuration-driven** stage definitions with JSON
- **Dynamic expression evaluation** supporting conditional logic
- **Dependency graph validation** with circular dependency detection
- **Conditional stage dependencies** using expressions like `if(pi_applicable == 1, [5], [2])`
- **Comprehensive audit trails** with transparent reasoning
- **Excel export capability** for results

## Recent Fix: Conditional Dependencies

The system now supports conditional dependencies in stage configurations. For example, Stage 8 can depend on different stages based on PO data:

```json
{
  "8": {
    "name": "08. PRD Pending",
    "preceding_stage": "if(pi_applicable == 1, [5], [2])",
    ...
  }
}
```

### How it Works

1. **Expression Evaluation**: The `_evaluate_expression` method now accepts a `return_type` parameter:
   - `"datetime"` - For date calculations (default)
   - `"stage_list"` - For stage dependency expressions

2. **Conditional Logic**: The `if()` function evaluates conditions and returns appropriate stage lists:
   - `if(pi_applicable == 1, [5], [2])` - If PI is applicable, depend on stage 5, else stage 2

3. **Type Handling**: The system automatically converts numeric stage IDs to strings for consistency

## Installation

```bash
pip install pandas numpy openpyxl pydantic
```

## Usage

### Basic Usage

```python
from tat_calculator import TATCalculator
import pandas as pd

# Initialize calculator
calculator = TATCalculator()

# Load your PO data
df = pd.read_excel('your_po_data.xlsx')

# Process batch
results = calculator.process_batch(df)

# Export results
calculator.export_to_excel(df, results, 'output_with_tat.xlsx')
```

### Testing Conditional Dependencies

```python
# Run the test script
python test_conditional_dependencies.py
```

## Configuration Structure

The `stages_config.json` defines business rules for each stage:

```json
{
  "stages": {
    "1": {
      "name": "01. PO Approval Pending",
      "actual_timestamp": "po_approval_date",
      "preceding_stage": null,
      "process_flow": {
        "critical_path": true,
        "team_owner": "Procurement"
      },
      "fallback_calculation": {
        "expression": "po_created_date"
      },
      "lead_time": 2
    }
  }
}
```

### Key Fields

- **preceding_stage**: Can be:
  - `null` - No dependencies
  - `["1", "2"]` - Simple list of dependencies
  - `"if(condition, [list1], [list2])"` - Conditional expression

- **actual_timestamp**: Field name for actual timestamp in PO data
- **fallback_calculation**: Expression for fallback calculation
- **lead_time**: Expected duration in days

## Calculation Priority

For each stage, the system calculates timestamps using this priority:

1. **Precedence-based**: Max of preceding stages + lead time
2. **Actual timestamp**: If available and later than precedence
3. **Fallback calculation**: If no precedence or actual available

## Supported Functions in Expressions

- `max(date1, date2, ...)` - Returns latest datetime
- `add_days(date, days)` - Adds days to a date
- `if(condition, true_val, false_val)` - Conditional evaluation

## Architecture

```
├── tat_calculator.py          # Core calculation engine
├── stages_config.json         # Stage configuration
├── test_conditional_dependencies.py  # Test script
└── README.md                  # This file
```

## Error Handling

- **Circular Dependencies**: Detected during initialization
- **Missing Fields**: Logged with warnings, calculation continues
- **Invalid Expressions**: Caught and logged, fallback used

## Example Output

```json
{
  "po_id": "PO-TEST-001",
  "stages": {
    "8": {
      "name": "08. PRD Pending",
      "timestamp": "2025-06-15T00:00:00",
      "calculation": {
        "method": "precedence_only",
        "decision": "No actual timestamp available, using precedence calculation"
      },
      "dependencies": [
        {
          "stage_id": "5",
          "stage_name": "05. PI Payment Pending"
        }
      ]
    }
  }
}
```

## Contributing

When adding new features:
1. Update the Pydantic models if needed
2. Add appropriate test cases
3. Update the configuration documentation
4. Ensure backward compatibility

## License

This project follows standard open-source licensing practices.

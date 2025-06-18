# TAT Calculator System

A comprehensive Python system for calculating Purchase Order (PO) stage timestamps using configurable business logic, replacing complex Excel formulas with maintainable, auditable code.

## Features

- **Enhanced Output Format**: Clear, structured insights instead of verbose formulas
- **Excel Export**: Save calculated timestamps alongside original data
- **Configuration-Driven**: All business logic externalized in JSON
- **Dynamic Expression Evaluation**: Support for complex calculations
- **Dependency Management**: Automatic resolution with cycle detection
- **Comprehensive Analytics**: Team workload, critical path, completion rates

## Quick Start

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Add your Excel file** (rename to `ts_small.xlsx` or update the filename in `run_tat_calculation.py`)

3. **Run the calculator:**
   ```bash
   python run_tat_calculation.py
   ```

## Output Files

- **JSON Results**: Structured calculation results with business insights
- **Excel Export**: Original data + calculated timestamps for all 31 stages
- **Analytics**: Comprehensive reports on delays, efficiency, and data quality

## Configuration

All 31 stages are pre-configured in `stages_config.json` with:
- Stage dependencies and lead times
- Team ownership and process types
- Fallback calculations for missing data
- Critical path identification

## Enhanced Output Format

Instead of verbose nested formulas, get clear insights:

```json
{
  "summary": {
    "completion_rate": 90.32,
    "methods_used": {
      "actual_over_precedence": 5,  // Delays detected
      "precedence_over_actual": 3   // Early completions
    }
  },
  "calculation": {
    "method": "actual_over_precedence",
    "decision": "Actual timestamp is later than calculated precedence",
    "actual_date": "2025-06-15T00:00:00",
    "precedence_date": "2025-06-13T00:00:00"
  }
}
```

## Business Intelligence

Automatically identifies:
- 🚨 Critical path delays
- 🚀 Process efficiency gains  
- 📊 Team bottlenecks
- 📈 Data quality issues

## Repository Structure

```
tat-calculator/
├── tat_calculator.py      # Core calculation engine
├── stages_config.json     # 31-stage configuration
├── run_tat_calculation.py # Main runner with Excel export
├── requirements.txt       # Python dependencies
└── README.md             # This file
```

Transforms complex Excel formulas into business intelligence for operational excellence.

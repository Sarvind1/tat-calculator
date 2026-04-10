# TAT Calculator System

A comprehensive Python system for calculating Purchase Order (PO) stage timestamps using configurable business logic, replacing complex Excel formulas with maintainable, auditable code.

## Overview

The TAT (Turnaround Time) Calculator transforms PO processing workflows into transparent, dependency-driven calculations. Instead of maintaining complex Excel formulas, all business logic is externalized in JSON configuration, making it easy to audit, modify, and scale.

## Key Features

- **🗂️ Organized Output Structure** – Clean, segregated folders for all outputs (TAT results, delay analysis, Excel exports, logs)
- **📊 Enhanced Analytics** – Structured insights with delay analysis, team workload, and critical path identification
- **⚙️ Configuration-Driven** – All business logic externalized in JSON for easy modifications
- **🧮 Dynamic Expression Evaluation** – Support for complex calculations with custom functions
- **🔗 Dependency Management** – Automatic resolution with cycle detection and memoization
- **📈 Comprehensive Reports** – Completion rates, delay analysis, team bottlenecks, data quality metrics
- **🔍 Full Auditability** – Transparent reasoning for every calculated timestamp

## Quick Start

### 1. Prerequisites

- Python 3.8+
- Virtual environment (recommended)

### 2. Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/tat-calculator.git
cd tat-calculator

# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy and configure environment file
cp .env.example .env
# Edit .env with your configuration if needed
```

### 3. Prepare Your Data

Add your Excel file containing PO data to the project root. The system expects columns with PO identifiers and stage timestamps.

### 4. Run the Calculator

```bash
python run_tat_calculation.py
```

Or with a specific Excel file:

```bash
python run_tat_calculation.py --input your_file.xlsx --config stages_config.json
```

## Output Structure

All outputs are automatically organized into clean folders:

```
outputs/
├── tat_results/           # TAT calculation JSON results
├── delay_results/         # Delay analysis JSON results  
├── excel_exports/         # Excel files (exports, reports)
├── csv_files/            # Processed CSV data files
└── logs/                 # Application logs and errors
```

## Configuration

All stages are pre-configured in `stages_config.json` with:
- Stage dependencies and lead times
- Team ownership and process types
- Fallback calculations for missing data
- Critical path identification

Example stage configuration:

```json
{
  "stage_1": {
    "name": "PO Received",
    "actual_timestamp": "po_received_date",
    "preceding_stage": null,
    "lead_time": 0,
    "process_flow": {
      "critical_path": true,
      "process_type": "receiving",
      "team_owner": "Procurement"
    },
    "fallback_calculation": {
      "expression": "po_created_date"
    }
  }
}
```

## Architecture

The system uses a **modular architecture** with:
- **Configuration-driven design** – All business logic in JSON
- **Dependency graph (DAG)** – Automatic resolution with cycle detection
- **Memoization** – Efficient calculations for complex dependencies
- **Expression evaluation** – Dynamic, safe parsing using Python AST
- **Organized outputs** – Clean folder structure for all generated files

### Core Modules

- **tat_calculator_main.py** – Main coordinator
- **models_config.py** – Data models and configuration
- **expression_evaluator.py** – Expression evaluation engine
- **stage_calculator.py** – Core TAT calculations
- **tat_processor.py** – Batch processing
- **delay_calculator.py** – Delay analysis

## Usage Examples

### Basic Calculation

```python
from tat_calculator_main import TATCalculatorMain
import pandas as pd

# Initialize
calculator = TATCalculatorMain()
calculator.setup()

# Process single PO
po_data = pd.Series({
    'po_razin_id': 'PO123',
    'po_received_date': '2025-06-01',
    # ... other columns
})

result = calculator.processor.calculate_tat(po_data)
print(result)
```

### Batch Processing

```python
# Process entire Excel file
calculator = TATCalculatorMain(excel_file='ts_small_1.xlsx')
calculator.setup()
results = calculator.run()
```

## Folder Management

Use the built-in folder manager for maintenance:

```bash
python folder_manager.py
```

Options include:
- Create folder structure
- Clean old files
- Archive results
- Generate structure reports

## Output Examples

### TAT Results
```json
{
  "po_id": "PO123",
  "calculation_date": "2025-06-15T10:30:00",
  "stages": {
    "stage_1": {
      "name": "PO Received",
      "adjusted_timestamp": "2025-06-01T00:00:00",
      "calculation_details": {
        "method": "actual_timestamp",
        "actual_date": "2025-06-01T00:00:00"
      }
    }
  }
}
```

### Delay Analysis
```json
{
  "stage_id": "stage_2",
  "target_timestamp": "2025-06-05T00:00:00",
  "actual_timestamp": "2025-06-07T00:00:00",
  "delay_days": 2.0,
  "delay_status": "delayed",
  "team_responsible": "Quality"
}
```

## Business Intelligence

The system automatically identifies:
- 🚨 Critical path delays
- 🚀 Process efficiency gains  
- 📊 Team bottlenecks
- 📈 Data quality issues
- ⏰ Stages requiring attention

## Repository Structure

```
tat-calculator/
├── tat_calculator.py           # Original monolithic version
├── tat_calculator_main.py      # Main coordinator
├── models_config.py            # Data models & config
├── expression_evaluator.py     # Expression engine
├── stage_calculator.py         # Core calculations
├── tat_processor.py            # Batch processing
├── delay_calculator.py         # Delay analysis
├── stage_config_validator.py   # Configuration validator
├── run_tat_calculation.py      # Main runner
├── folder_manager.py           # Output management
├── stages_config.json          # 31-stage configuration
├── requirements.txt            # Python dependencies
├── .env.example                # Environment template
├── .gitignore                  # Git ignore rules
├── README.md                   # This file
└── outputs/                    # Generated outputs (auto-created)
```

## Dependencies

- pandas – Data processing
- openpyxl – Excel file handling
- pydantic – Data validation
- numpy – Numerical operations

See `requirements.txt` for complete list.

## Development

### Running Tests

```bash
pytest tests/
```

### Configuration Validation

```bash
python stage_config_validator.py
```

## Troubleshooting

### Excel File Issues
- Ensure Excel file has headers in the first row
- Check column names match configuration
- Verify date formats are consistent

### Dependency Errors
- Run `python stage_config_validator.py` to check configuration
- Verify all referenced columns exist in Excel file
- Check for circular dependencies between stages

### Performance Issues
- For large files (>100k rows), consider processing in batches
- Check available system memory
- Review stage configuration for complex expressions

## License

[Add your license here]

## Contact

For issues, questions, or suggestions, please open an issue on GitHub.

---

**Transforms complex Excel formulas into organized business intelligence for operational excellence.**

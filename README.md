# TAT Calculator

A Python-based system for calculating Turnaround Time (TAT) adjustments across Purchase Order (PO) processing workflow stages. Replaces complex Excel formulas with configurable, maintainable Python code that supports dynamic expressions, stage dependencies, and transparent reasoning.

## Features

- **Configurable Stage Processing**: Define workflow stages with dependencies, lead times, and fallback calculations
- **Dynamic Expression Evaluation**: Support for custom expressions and business logic in stage definitions
- **Comprehensive Reporting**: Generate results in JSON, Excel, and CSV formats
- **Validation Framework**: Built-in validation for configuration files and stage dependencies
- **Detailed Logging**: Track calculation logic and identify issues with full audit trails

## Tech Stack

- **Python 3.x**
- **Pandas**: Data processing and Excel handling
- **Pydantic**: Configuration validation and type safety
- **NumPy**: Numerical operations
- **Logging**: Comprehensive audit trails

## Setup

1. Clone the repository and navigate to the project directory:
   ```bash
   cd tat-calculator
   ```

2. Create a virtual environment and install dependencies:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

3. Configure your workflow stages in `stages_config.json`

4. Prepare your PO data in Excel format (e.g., `ts_big.xlsx`)

## Usage

Run the complete TAT calculation system:

```bash
python run_tat_calculation.py
```

This will:
- Load your Excel data
- Process each PO through configured stages
- Generate output files in `outputs/` directory:
  - `tat_results/`: Detailed calculation results (JSON)
  - `excel_exports/`: Analysis summaries (Excel)
  - `csv_files/`: Processed data (CSV)
  - `logs/`: Calculation logs and audit trails

Validate your configuration:

```bash
python stage_config_validator.py
```

## Configuration

Edit `stages_config.json` to define:
- Stage names and identifiers
- Dependencies between stages
- Lead time adjustments
- Fallback calculations for missing data
- Process flow metadata (critical path, team ownership, handoff points)

See `documentation/` for detailed configuration guides.

# TAT Calculator

A Python-based system for calculating adjusted turnaround times across configurable Purchase Order (PO) processing workflow stages. Replaces complex Excel formulas with maintainable, dependency-driven Python code that supports dynamic expressions and transparent reasoning.

## Key Features

- **Configurable Stage Workflow** – Define processing stages, dependencies, and lead times in JSON
- **Dynamic Expression Evaluation** – Support for custom expressions with fallback calculations
- **Dependency-Driven Calculations** – Automatic handling of sequential and parallel process dependencies
- **Comprehensive Reporting** – Output results in JSON, CSV, and Excel formats
- **Configuration Validation** – Built-in validator to check stages configuration for syntax and compatibility errors
- **Transparent Reasoning** – Clear logging and audit trails for all calculations

## Tech Stack

- **Python 3.x**
- **pandas** – Data processing and Excel I/O
- **pydantic** – Configuration validation and type checking
- **numpy** – Numerical operations

## Installation

1. Clone the repository
2. Create and activate a virtual environment:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Configuration

Edit `stages_config.json` to define your workflow stages with:
- Stage names and preceding dependencies
- Actual timestamp fields from your data
- Lead times (in days)
- Process flow metadata (critical path, team ownership, handoff points)
- Fallback calculation expressions

## Usage

Run the TAT calculation on your Excel data:

```bash
python run_tat_calculation.py
```

Results are generated in the `outputs/` directory:
- `tat_results/` – JSON output with detailed calculations
- `csv_files/` – Processed data in CSV format
- `excel_exports/` – Stage-level analysis in Excel
- `logs/` – Calculation logs and audit trails

## Validation

Validate your configuration before running calculations:

```bash
python -c "from stage_config_validator import StageConfigValidator; StageConfigValidator().validate_config_file('stages_config.json')"
```
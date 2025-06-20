"""
Script to list all available fields in the Excel data
"""

import pandas as pd
import sys

def analyze_excel_structure(file_path):
    """Analyze the structure of the Excel file"""
    try:
        # Read the Excel file
        df = pd.read_excel(file_path)
        
        print(f"Excel File Analysis: {file_path}")
        print("=" * 70)
        
        # Basic info
        print(f"\nDataFrame shape: {df.shape}")
        print(f"Number of rows: {len(df)}")
        print(f"Number of columns: {len(df.columns)}")
        
        # List all columns
        print("\nAll columns in the Excel file:")
        print("-" * 70)
        for i, col in enumerate(df.columns, 1):
            print(f"{i:3d}. {col}")
        
        # Check for specific fields related to our issue
        print("\n" + "-" * 70)
        print("Checking for specific fields:")
        
        fields_to_check = [
            'pi_applicable',
            'po_razin_id',
            'po_created_date',
            'po_approval_date',
            'supplier_confirmation_date',
            'pi_invoice_approval_date',
            'pi_payment_date',
            'receive_first_prd_date'
        ]
        
        for field in fields_to_check:
            if field in df.columns:
                print(f"✓ {field} - FOUND")
                # Show sample values
                non_null_values = df[field].dropna()
                if len(non_null_values) > 0:
                    print(f"  Sample values: {non_null_values.head(3).tolist()}")
            else:
                print(f"✗ {field} - NOT FOUND")
        
        # Check if there are any columns that might be pi_applicable with different naming
        print("\n" + "-" * 70)
        print("Columns that might be related to 'pi_applicable':")
        possible_pi_columns = [col for col in df.columns if 'pi' in col.lower() or 'applicable' in col.lower()]
        for col in possible_pi_columns:
            print(f"  - {col}")
            non_null_values = df[col].dropna()
            if len(non_null_values) > 0:
                print(f"    Sample values: {non_null_values.head(3).tolist()}")
        
        # Display first few rows of key columns
        print("\n" + "-" * 70)
        print("First 3 rows of data (selected columns):")
        display_cols = ['po_razin_id'] if 'po_razin_id' in df.columns else []
        display_cols.extend([col for col in fields_to_check if col in df.columns][:5])
        if display_cols:
            print(df[display_cols].head(3))
        
        return df
        
    except Exception as e:
        print(f"Error reading Excel file: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    # Check if filename provided as argument
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
    else:
        # Default file path
        file_path = "ts_small.xlsx"
    
    print(f"Analyzing: {file_path}")
    df = analyze_excel_structure(file_path)
    
    if df is not None:
        print("\n" + "=" * 70)
        print("Analysis complete!")
        print("\nTo use this with TAT Calculator:")
        print("1. Ensure all required fields are present in your Excel file")
        print("2. If 'pi_applicable' is missing, add it to enable conditional dependencies")
        print("3. Run: python -m tat_calculator your_file.xlsx")

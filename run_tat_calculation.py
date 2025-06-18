"""
Complete TAT Calculation Runner
==============================

This script runs the complete TAT calculation system on your Excel data
and generates comprehensive reports and analytics.
"""

import pandas as pd
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
import sys
import traceback

# Set up comprehensive logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('tat_calculation.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class TATRunner:
    """Complete TAT calculation runner with enhanced reporting"""
    
    def __init__(self, excel_file: str = "ts_small.xlsx", config_file: str = "stages_config.json"):
        self.excel_file = excel_file
        self.config_file = config_file
        self.df = None
        self.calculator = None
        self.results = []
        
    def setup(self):
        """Set up the calculator and load data"""
        logger.info("Setting up TAT calculation environment...")
        
        # Load Excel data
        self.load_excel_data()
        
        # Initialize calculator
        self.initialize_calculator()
        
        logger.info("Setup completed successfully!")
        
    def load_excel_data(self):
        """Load and prepare Excel data"""
        logger.info(f"Loading Excel file: {self.excel_file}")
        
        try:
            self.df = pd.read_excel(self.excel_file)
            logger.info(f"Loaded {len(self.df)} rows and {len(self.df.columns)} columns")
            
            # Clean column names
            self.df.columns = self.df.columns.str.strip()
            
            # Convert date columns
            self.convert_date_columns()
            
            # Validate required columns
            self.validate_required_columns()
            
        except Exception as e:
            logger.error(f"Error loading Excel file: {e}")
            raise
            
    def convert_date_columns(self):
        """Convert relevant columns to datetime"""
        date_columns = [
            'po_created_date', 'po_approval_date', 'supplier_confirmation_date',
            'pi_invoice_approval_date', 'pi_payment_date', 'receive_first_prd_date',
            'prd_reconfirmed_date', 'po_im_date_value', 'po_sm_date_value',
            'batch_created_ts', 'sm_signoff_ts', 'ci_invoice_approval_date',
            'ci_payment_date', 'qc_schedule_date', 'ffw_booking_ts', 'spd_ts',
            'stock_pickup_date', 'shipment_creation_date', 'shipment_in_transit_date',
            'bi_invoice_approval_date', 'bi_payment_date', 'ffwp_telex_release_date',
            'shipment_stock_delivery_date', 'item_receipt_date', 'actual_cargo_pick_up_date',
            'actual_shipping_date', 'actual_arrival_date', 'actual_delivery_date'
        ]
        
        for col in date_columns:
            if col in self.df.columns:
                original_type = self.df[col].dtype
                self.df[col] = pd.to_datetime(self.df[col], errors='coerce')
                
                missing_count = self.df[col].isna().sum()
                total_count = len(self.df)
                
                logger.info(f"Converted {col}: {original_type} -> datetime, "
                          f"{missing_count}/{total_count} missing ({missing_count/total_count*100:.1f}%)")
    
    def validate_required_columns(self):
        """Validate that required columns exist"""
        required_columns = ['po_razin_id', 'po_created_date']
        missing_columns = [col for col in required_columns if col not in self.df.columns]
        
        if missing_columns:
            raise ValueError(f"Missing required columns: {missing_columns}")
            
        logger.info("All required columns present")
    
    def initialize_calculator(self):
        """Initialize the TAT calculator"""
        logger.info(f"Initializing TAT Calculator with config: {self.config_file}")
        
        try:
            from tat_calculator import TATCalculator
            self.calculator = TATCalculator(self.config_file)
            logger.info("TAT Calculator initialized successfully")
            
        except ImportError:
            logger.error("TATCalculator not available. Please ensure tat_calculator.py is in the same directory.")
            raise
        except Exception as e:
            logger.error(f"Error initializing calculator: {e}")
            raise
    
    def run_calculations(self, sample_size: int = None):
        """Run TAT calculations on all or sample of POs"""
        if sample_size:
            df_to_process = self.df.head(sample_size)
            logger.info(f"Processing sample of {sample_size} POs")
        else:
            df_to_process = self.df
            logger.info(f"Processing all {len(df_to_process)} POs")
        
        self.results = []
        errors = []
        
        for index, row in df_to_process.iterrows():
            try:
                po_id = row.get('po_razin_id', f'Row_{index}')
                logger.info(f"Processing PO {index + 1}/{len(df_to_process)}: {po_id}")
                
                result = self.calculator.calculate_tat(row)
                self.results.append(result)
                
            except Exception as e:
                error_info = {
                    'index': index,
                    'po_id': row.get('po_razin_id', f'Row_{index}'),
                    'error': str(e),
                    'traceback': traceback.format_exc()
                }
                errors.append(error_info)
                logger.error(f"Error processing row {index}: {e}")
        
        logger.info(f"Completed calculations: {len(self.results)} successful, {len(errors)} errors")
        
        if errors:
            self.save_errors(errors)
        
        return self.results
    
    def save_errors(self, errors):
        """Save error details to file"""
        error_file = f"tat_errors_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(error_file, 'w') as f:
            json.dump(errors, f, indent=2)
        logger.info(f"Error details saved to: {error_file}")
    
    def save_results(self, filename_prefix: str = "tat_results"):
        """Save calculation results to JSON file"""
        if not self.results:
            logger.warning("No results to save")
            return
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{filename_prefix}_{timestamp}.json"
        
        with open(filename, 'w') as f:
            json.dump(self.results, f, indent=2, default=str)
        
        logger.info(f"Results saved to: {filename}")
        return filename
    
    def export_to_excel(self, filename_prefix: str = "tat_export"):
        """Export original data + calculated timestamps to Excel"""
        if not self.results:
            logger.warning("No results to export")
            return
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{filename_prefix}_{timestamp}.xlsx"
        
        self.calculator.export_to_excel(self.df, self.results, filename)
        return filename


def main():
    """Main execution function"""
    print("TAT Calculation System - Starting...")
    print("="*60)
    
    try:
        # Initialize runner
        runner = TATRunner()
        
        # Setup
        runner.setup()
        
        # Run calculations (start with sample for testing)
        sample_size = 5  # Process first 5 POs for testing
        print(f"\nRunning calculations on sample of {sample_size} POs...")
        results = runner.run_calculations(sample_size=sample_size)
        
        if results:
            # Save results
            results_file = runner.save_results()
            
            # Export to Excel
            excel_file = runner.export_to_excel()
            
            print(f"\nFiles Generated:")
            print(f"- Results: {results_file}")
            print(f"- Excel Export: {excel_file}")
            print(f"- Logs: tat_calculation.log")
            
        print(f"\nTo process all POs, change sample_size=None in the run_calculations() call")
        print("TAT Calculation completed successfully!")
        
    except Exception as e:
        logger.error(f"Error in main execution: {e}")
        print(f"Error: {e}")
        print("See tat_calculation.log for detailed error information")


if __name__ == "__main__":
    main()

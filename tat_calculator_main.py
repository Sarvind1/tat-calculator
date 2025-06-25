"""
TAT Calculator Main Module
=========================

Main TATCalculator class that coordinates all sub-modules.
"""

import logging
from typing import List, Dict, Any
import pandas as pd
from models_config import load_config, validate_config
from expression_evaluator import ExpressionEvaluator
from stage_calculator import StageCalculator
from tat_processor import TATProcessor

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TATCalculator:
    """
    Core TAT calculation engine that processes PO data through configurable stages.
    
    This is the main entry point that coordinates all sub-modules:
    - Configuration management (models_config)
    - Expression evaluation (expression_evaluator)
    - Stage calculations (stage_calculator)
    - TAT processing and export (tat_processor)
    """
    
    def __init__(self, config_path: str = "stages_config.json"):
        """
        Initialize the TAT Calculator
        
        Args:
            config_path: Path to the stages configuration JSON file
        """
        # Load and validate configuration
        self.config = load_config(config_path)
        validate_config(self.config)
        
        # Initialize sub-components
        self.expression_evaluator = ExpressionEvaluator()
        self.stage_calculator = StageCalculator(self.config, self.expression_evaluator)
        self.tat_processor = TATProcessor(self.config, self.stage_calculator)
        
        logger.info(f"TAT Calculator initialized with {len(self.config.stages)} stages")
    
    def calculate_tat(self, po_row: pd.Series) -> Dict[str, Any]:
        """
        Calculate TAT for all stages of a PO
        
        Args:
            po_row: Pandas Series containing PO data
            
        Returns:
            Dictionary with complete TAT calculation results
        """
        return self.tat_processor.calculate_tat(po_row)
    
    def process_batch(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """
        Process multiple POs in batch
        
        Args:
            df: DataFrame containing multiple PO rows
            
        Returns:
            List of TAT calculation results
        """
        return self.tat_processor.process_batch(df)
    
    def export_to_excel(self, df: pd.DataFrame, results: List[Dict[str, Any]], output_file: str):
        """
        Export original data + calculated timestamps to Excel
        
        Args:
            df: Original DataFrame
            results: TAT calculation results
            output_file: Output Excel file path
        """
        self.tat_processor.export_to_excel(df, results, output_file)
    
    # Convenience methods for backward compatibility
    def _get_date_value(self, field_name: str, po_row: pd.Series):
        """Legacy method for backward compatibility"""
        return self.expression_evaluator.get_date_value(field_name, po_row)
    
    def _evaluate_expression(self, expression: str, po_row: pd.Series):
        """Legacy method for backward compatibility"""
        return self.expression_evaluator.evaluate_expression(expression, po_row)
    
    def calculate_adjusted_timestamp(self, stage_id: str, po_row: pd.Series):
        """Legacy method for backward compatibility"""
        return self.stage_calculator.calculate_adjusted_timestamp(stage_id, po_row)


if __name__ == "__main__":
    print("TAT Calculator System - Modularized Version")
    print("Usage:")
    print("1. calculator = TATCalculator()")
    print("2. results = calculator.process_batch(df)")
    print("3. calculator.export_to_excel(df, results, 'output.xlsx')")

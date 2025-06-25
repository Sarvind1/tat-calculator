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
from delay_calculator import DelayCalculator

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
    - Delay analysis (delay_calculator)
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
        self.delay_calculator = DelayCalculator(self.config)
        
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
    
    def calculate_delay(self, tat_result: Dict[str, Any], po_row: pd.Series) -> Dict[str, Any]:
        """
        Calculate delays for all stages based on TAT results
        
        Args:
            tat_result: TAT calculation result
            po_row: Original PO data row
            
        Returns:
            Dictionary with delay analysis
        """
        return self.delay_calculator.calculate_all_delays(tat_result, po_row)
    
    def process_batch(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """
        Process multiple POs in batch
        
        Args:
            df: DataFrame containing multiple PO rows
            
        Returns:
            List of TAT calculation results
        """
        return self.tat_processor.process_batch(df)
    
    def process_batch_with_delays(self, df: pd.DataFrame) -> tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Process multiple POs and calculate delays
        
        Args:
            df: DataFrame containing multiple PO rows
            
        Returns:
            Tuple of (TAT results, Delay results)
        """
        tat_results = self.process_batch(df)
        delay_results = []
        
        for i, tat_result in enumerate(tat_results):
            if 'error' not in tat_result:
                po_row = df.iloc[i]
                delay_result = self.calculate_delay(tat_result, po_row)
                delay_results.append(delay_result)
        
        return tat_results, delay_results
    
    def export_to_excel(self, df: pd.DataFrame, results: List[Dict[str, Any]], output_file: str):
        """
        Export original data + calculated timestamps to Excel
        
        Args:
            df: Original DataFrame
            results: TAT calculation results
            output_file: Output Excel file path
        """
        self.tat_processor.export_to_excel(df, results, output_file)
    
    def export_delay_report(self, delay_results: List[Dict[str, Any]], output_file: str):
        """
        Export delay analysis report to Excel
        
        Args:
            delay_results: List of delay analysis results
            output_file: Output Excel file path
        """
        self.delay_calculator.export_delay_report(delay_results, output_file)
    
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
    print("TAT Calculator System - Modularized Version with Delay Analysis")
    print("Usage:")
    print("1. calculator = TATCalculator()")
    print("2. tat_results, delay_results = calculator.process_batch_with_delays(df)")
    print("3. calculator.export_to_excel(df, tat_results, 'tat_output.xlsx')")
    print("4. calculator.export_delay_report(delay_results, 'delay_report.xlsx')")

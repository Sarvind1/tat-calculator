"""
TAT Processor Module
====================

Main TAT processing orchestrator with batch processing and export capabilities.
Updated to support organized output folder structure.
"""

import logging
from datetime import datetime
from typing import Dict, List, Any
from pathlib import Path
import pandas as pd
from models_config import StagesConfig
from stage_calculator import StageCalculator

logger = logging.getLogger(__name__)


class TATProcessor:
    """
    Orchestrates TAT calculations across all stages and handles output formatting.
    Now supports organized folder structure for outputs.
    """
    
    def __init__(self, config: StagesConfig, stage_calculator: StageCalculator):
        self.config = config
        self.stage_calculator = stage_calculator
        # Ensure organized output folders exist
        self._ensure_output_folders()
    
    def _ensure_output_folders(self):
        """Ensure all output folders exist"""
        folders = [
            'outputs/tat_results',
            'outputs/delay_results', 
            'outputs/excel_exports',
            'outputs/csv_files',
            'outputs/logs'
        ]
        
        for folder in folders:
            Path(folder).mkdir(parents=True, exist_ok=True)
    
    def calculate_tat(self, po_row: pd.Series) -> Dict[str, Any]:
        """
        Calculate TAT for all stages of a PO
        
        Args:
            po_row: Pandas Series containing PO data
            
        Returns:
            Dictionary with complete TAT calculation results
        """
        # Clear cache for new calculation
        self.stage_calculator.reset_cache()
        
        result = {
            "po_id": po_row.get('po_razin_id', 'Unknown'),
            "calculation_date": datetime.now().isoformat(),
            "summary": {
                "total_stages": len(self.config.stages),
                "calculated_stages": 0,
                "methods_used": {
                    "actual_only": 0,
                    "precedence_only": 0,
                    "actual_over_precedence": 0,
                    "precedence_over_actual": 0,
                    "fallback": 0,
                    "failed": 0
                }
            },
            "stages": {}
        }
        
        # Calculate each stage
        for stage_id, stage_config in self.config.stages.items():
            timestamp, calc_details = self.stage_calculator.calculate_adjusted_timestamp(stage_id, po_row)
            
            # Update summary statistics
            if timestamp:
                result["summary"]["calculated_stages"] += 1
            
            method = calc_details.get("method", "unknown") if isinstance(calc_details, dict) else "legacy"
            if method in result["summary"]["methods_used"]:
                result["summary"]["methods_used"][method] += 1
            
            # Create clean stage result
            stage_result = {
                "name": stage_config.name,
                "timestamp": timestamp.isoformat() if timestamp else None,
                "calculation": self._format_calculation_summary(calc_details, stage_config),
                "process_flow": {
                    "team_owner": stage_config.process_flow.team_owner,
                    "process_type": stage_config.process_flow.process_type,
                    "critical_path": stage_config.process_flow.critical_path,
                    "handoff_points": stage_config.process_flow.handoff_points
                },
                "dependencies": calc_details.get("dependencies", []) if isinstance(calc_details, dict) else []
            }
            
            result["stages"][stage_id] = stage_result
        
        # Calculate completion rate
        result["summary"]["completion_rate"] = round(
            result["summary"]["calculated_stages"] / result["summary"]["total_stages"] * 100, 2
        ) if result["summary"]["total_stages"] > 0 else 0
        
        return result
    
    def _format_calculation_summary(self, calc_details: Dict[str, Any], stage_config) -> Dict[str, Any]:
        """
        Format calculation details into a clean, readable summary
        
        Args:
            calc_details: Raw calculation details
            stage_config: Stage configuration
            
        Returns:
            Clean calculation summary
        """
        if not isinstance(calc_details, dict):
            return {"method": "legacy", "summary": str(calc_details)}
        
        method = calc_details.get("method", "unknown")
        
        summary = {
            "method": method,
            "source": calc_details.get("source"),
            "decision": calc_details.get("decision_reason"),
            "lead_time_days": calc_details.get("lead_time_applied", 0),
            "target_date": calc_details.get("target_date")
        }
        
        # Add method-specific details
        if method == "actual_over_precedence":
            summary.update({
                "actual_date": calc_details.get("actual_value"),
                "precedence_date": calc_details.get("precedence_value"),
                "reason": "Actual timestamp is later than calculated precedence"
            })
        elif method == "precedence_over_actual":
            summary.update({
                "actual_date": calc_details.get("actual_value"),
                "precedence_date": calc_details.get("precedence_value"), 
                "reason": "Calculated precedence is later than actual timestamp"
            })
        elif method == "precedence_only":
            summary.update({
                "precedence_date": calc_details.get("precedence_date"),
                "reason": "No actual timestamp available"
            })
        elif method == "actual_only":
            summary.update({
                "actual_field": calc_details.get("actual_field"),
                "reason": "No dependency chain available"
            })
        elif method == "fallback":
            summary.update({
                "target_date": calc_details.get("target_date"),
                "expression": calc_details.get("source"),
                "reason": "Using fallback calculation"
            })
        
        return summary
    
    def process_batch(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """
        Process multiple POs in batch
        
        Args:
            df: DataFrame containing multiple PO rows
            
        Returns:
            List of TAT calculation results
        """
        results = []
        
        for index, row in df.iterrows():
            try:
                result = self.calculate_tat(row)
                results.append(result)
                logger.info(f"Processed PO: {result['po_id']}")
            except Exception as e:
                logger.error(f"Error processing row {index}: {e}")
                results.append({
                    "po_id": row.get('po_razin_id', f'Row_{index}'),
                    "error": str(e),
                    "calculation_date": datetime.now().isoformat()
                })
        
        return results

    def export_to_excel(self, df: pd.DataFrame, results: List[Dict[str, Any]], output_file: str):
        """
        Export original data + calculated timestamps to Excel
        
        Args:
            df: Original DataFrame
            results: TAT calculation results
            output_file: Output Excel file path (should include organized folder path)
        """
        # Ensure the directory exists (in case called with custom path)
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Create a copy of the original dataframe
        export_df = df.copy()
        
        # Add calculated timestamps for each stage
        for result in results:
            if 'stages' not in result:
                continue
                
            po_id = result['po_id']
            po_index = export_df[export_df['po_razin_id'] == po_id].index
            
            if len(po_index) > 0:
                idx = po_index[0]
                
                # Add calculated timestamps
                for stage_id, stage_data in result['stages'].items():
                    # Use stage name instead of ID for column name
                    stage_name = stage_data['name']
                    col_name = f"{stage_name}_Date"
                    timestamp = stage_data['timestamp']
                    # Convert timestamp to date only
                    if timestamp:
                        date = pd.to_datetime(timestamp).date()
                        export_df.loc[idx, col_name] = date
                    else:
                        export_df.loc[idx, col_name] = None
        
        # Save to Excel
        export_df.to_excel(output_file, index=False)
        logger.info(f"Results exported to: {output_file}")
    
    def save_to_csv(self, df: pd.DataFrame, filename_prefix: str = "processed_data") -> str:
        """
        Save processed DataFrame to organized CSV folder
        
        Args:
            df: DataFrame to save
            filename_prefix: Prefix for filename
            
        Returns:
            Full path of saved file
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"outputs/csv_files/{filename_prefix}_{timestamp}.csv"
        
        # Ensure directory exists
        Path(filename).parent.mkdir(parents=True, exist_ok=True)
        
        df.to_csv(filename, index=False)
        logger.info(f"CSV saved to: {filename}")
        return filename

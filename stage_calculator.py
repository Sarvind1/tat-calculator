"""
Stage Calculator Module
=======================

Core calculation logic for individual stages with simplified method-based approach.
Methods: Projected, Actual, Adjusted
"""

import ast
import logging
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple, Any, List
import pandas as pd
from models_config import StageConfig, StagesConfig
from expression_evaluator import ExpressionEvaluator

logger = logging.getLogger(__name__)


class StageCalculator:
    """
    Calculates timestamps for individual stages using simplified logic:
    
    - Method: Projected/Actual/Adjusted
    - Target Timestamp: Based on preceding final_timestamp + lead_time
    - Actual Timestamp: From actual_field or preceding actual
    - Final Timestamp: Target (if Projected) or Actual (if Actual/Adjusted)
    - Delay: Target - Actual (only for Actual/Adjusted)
    """
    
    def __init__(self, config: StagesConfig, expression_evaluator: ExpressionEvaluator):
        self.config = config
        self.expression_evaluator = expression_evaluator
        self.calculated_adjustments: Dict[str, Tuple[Optional[datetime], Dict[str, Any]]] = {}
        # Link the evaluator to our cache
        self.expression_evaluator.set_calculated_adjustments(self.calculated_adjustments)
    
    def calculate_adjusted_timestamp(self, stage_id: str, po_row: pd.Series) -> Tuple[Optional[datetime], Dict[str, Any]]:
        """
        Calculate timestamps for a specific stage using simplified logic.
        
        Args:
            stage_id: ID of the stage to calculate
            po_row: PO data row
            
        Returns:
            Tuple of (final_timestamp, calculation_details)
        """
        # Check if already calculated (memoization)
        if stage_id in self.calculated_adjustments:
            return self.calculated_adjustments[stage_id]
        
        if stage_id not in self.config.stages:
            logger.error(f"Stage {stage_id} not found in configuration")
            return None, {"method": "error", "reason": f"Stage {stage_id} not found"}
        
        stage = self.config.stages[stage_id]
        
        # Initialize calculation details
        calc_details = {
            "method": None,
            "target_timestamp": None,
            "actual_timestamp": None,
            "final_timestamp": None,
            "delay": None,
            "lead_time_applied": stage.lead_time,
            "dependencies": [],
            "actual_field": stage.actual_timestamp,
            "precedence_method": None,
            "calculation_source": None  # New field to track how final was calculated
        }
        
        # 1. Get preceding stages and calculate target timestamp
        preceding_final_timestamps = []
        preceding_actual_timestamps = []
        has_projected_precedence = False
        
        if stage.preceding_stage:
            # Evaluate preceding stage expression
            result = self.expression_evaluator._eval_node(
                ast.parse(stage.preceding_stage, mode='eval').body, po_row
            )
            preceding_stage_ids = result if isinstance(result, list) else []
            
            # Process each preceding stage
            for prec_stage_id in preceding_stage_ids:
                prec_stage_id = str(prec_stage_id)
                if prec_stage_id in self.config.stages:
                    prec_timestamp, prec_details = self.calculate_adjusted_timestamp(prec_stage_id, po_row)
                    
                    if prec_timestamp and isinstance(prec_details, dict):
                        # Track final timestamps for target calculation
                        preceding_final_timestamps.append(prec_timestamp)
                        
                        # Track actual timestamps if available
                        if prec_details.get("actual_timestamp"):
                            preceding_actual_timestamps.append(
                                datetime.fromisoformat(prec_details["actual_timestamp"])
                            )
                        
                        # Check if any preceding stage is projected
                        if prec_details.get("method") == "Projected":
                            has_projected_precedence = True
                        
                        # Add to dependencies
                        calc_details["dependencies"].append({
                            "stage_id": prec_stage_id,
                            "stage_name": self.config.stages[prec_stage_id].name,
                            "timestamp": prec_timestamp.isoformat(),
                            "method": prec_details.get("method", "unknown")
                        })
        
        # Calculate target timestamp
        if preceding_final_timestamps:
            base_timestamp = max(preceding_final_timestamps)
            calc_details["target_timestamp"] = (base_timestamp + timedelta(days=stage.lead_time)).isoformat()
            calc_details["calculation_source"] = "precedence_based"
        else:
            # No preceding stages - use fallback for target
            fallback_result, _ = self.expression_evaluator.evaluate_expression(
                stage.fallback_calculation.expression, po_row
            )
            if fallback_result:
                calc_details["target_timestamp"] = (fallback_result + timedelta(days=stage.lead_time)).isoformat()
                calc_details["calculation_source"] = "fallback_based"
        
        # Set precedence method
        calc_details["precedence_method"] = "Projected" if has_projected_precedence else "Actual/Adjusted"
        
        # 2. Get actual timestamp if available
        current_actual_timestamp = None
        if stage.actual_timestamp:
            actual_result, _ = self.expression_evaluator.evaluate_expression(
                stage.actual_timestamp, po_row
            )
            if actual_result:
                current_actual_timestamp = actual_result
        
        # 3. Determine method and final timestamps
        if current_actual_timestamp:
            # Get max preceding actual timestamp
            max_preceding_actual = max(preceding_actual_timestamps) if preceding_actual_timestamps else None
            
            if max_preceding_actual and max_preceding_actual > current_actual_timestamp:
                # Use preceding actual - method is Adjusted
                calc_details["method"] = "Adjusted"
                calc_details["actual_timestamp"] = max_preceding_actual.isoformat()
                calc_details["final_timestamp"] = max_preceding_actual.isoformat()
                calc_details["calculation_source"] = "actual_from_precedence"
            else:
                # Use current actual - method is Actual
                calc_details["method"] = "Actual"
                calc_details["actual_timestamp"] = current_actual_timestamp.isoformat()
                calc_details["final_timestamp"] = current_actual_timestamp.isoformat()
                calc_details["calculation_source"] = "actual_from_field"
        else:
            # No actual timestamp - method is Projected
            calc_details["method"] = "Projected"
            calc_details["final_timestamp"] = calc_details["target_timestamp"]
            calc_details["calculation_source"] = calc_details["calculation_source"] + "_target" if calc_details["calculation_source"] else "target"
            # For projected, try to inherit preceding actual
            if preceding_actual_timestamps:
                calc_details["actual_timestamp"] = max(preceding_actual_timestamps).isoformat()
        
        # 4. Calculate delay only for Actual/Adjusted methods
        if calc_details["method"] in ["Actual", "Adjusted"] and calc_details["target_timestamp"] and calc_details["actual_timestamp"]:
            target_dt = datetime.fromisoformat(calc_details["target_timestamp"])
            actual_dt = datetime.fromisoformat(calc_details["actual_timestamp"])
            delay_days = (actual_dt - target_dt).days
            calc_details["delay"] = delay_days
        
        # Get final timestamp for return
        final_timestamp = None
        if calc_details["final_timestamp"]:
            final_timestamp = datetime.fromisoformat(calc_details["final_timestamp"])
        
        # Cache result
        result = (final_timestamp, calc_details)
        self.calculated_adjustments[stage_id] = result
        
        return result
    
    def reset_cache(self):
        """Clear the memoization cache for new calculations"""
        self.calculated_adjustments = {}
        self.expression_evaluator.set_calculated_adjustments(self.calculated_adjustments)

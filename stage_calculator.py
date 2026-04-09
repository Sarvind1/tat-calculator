"""
Stage Calculator Module
=======================

Core calculation logic for individual stages with simplified method-based approach.
Methods: Projected, Actual, Adjusted
"""

import ast
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple, Any, List
import pandas as pd
from models_config import StageConfig, StagesConfig
from expression_evaluator import ExpressionEvaluator


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
        self.expression_evaluator.set_calculated_adjustments(self.calculated_adjustments)
    
    def calculate_adjusted_timestamp(self, stage_id: str, po_row: pd.Series) -> Tuple[Optional[datetime], Dict[str, Any]]:
        print(f"\n--- Calculating stage: {stage_id} ---")
        
        if stage_id in self.calculated_adjustments:
            print(f"Using cached result for stage: {stage_id}")
            return self.calculated_adjustments[stage_id]
        
        if stage_id not in self.config.stages:
            print(f"ERROR: Stage {stage_id} not found in config.")
            return None, {"method": "error", "reason": f"Stage {stage_id} not found"}
        
        stage = self.config.stages[stage_id]
        print(f"Stage config loaded for {stage_id}: {stage.name}")
        
        # Evaluate lead_time dynamically from expression
        print(f"Evaluating lead_time expression: {stage.lead_time}")
        lead_time_days, lead_time_debug = self.expression_evaluator.evaluate_expression(str(stage.lead_time), po_row)
        print(f"Lead time evaluated to: {lead_time_days} (Debug: {lead_time_debug})")
        if not isinstance(lead_time_days, (int, float)):
            print(f"Lead time is not a number, defaulting to 0")
            lead_time_days = 0

        calc_details = {
            "method": None,
            "target_timestamp": None,
            "actual_timestamp": None,
            "final_timestamp": None,
            "delay": None,
            "lead_time_applied": lead_time_days,
            "dependencies": [],
            "actual_field": stage.actual_timestamp,
            "precedence_method": None,
            "calculation_source": None
        }
        
        preceding_final_timestamps = []
        preceding_actual_timestamps = []
        has_projected_precedence = False
        preceding_stage_ids = []
        
        if stage.preceding_stage:
            try:
                print(f"Evaluating preceding stage expression for {stage_id}: {stage.preceding_stage}")
                result = self.expression_evaluator._eval_node(
                    ast.parse(stage.preceding_stage, mode='eval').body, po_row
                )
                preceding_stage_ids = result if isinstance(result, list) else []
                print(f"Preceding stage IDs: {preceding_stage_ids}")
            except Exception as e:
                print(f"ERROR evaluating preceding stage for {stage_id}: {e}")
        
            for prec_stage_id in preceding_stage_ids:
                prec_stage_id = str(prec_stage_id)
                if prec_stage_id in self.config.stages:
                    print(f"Calculating preceding stage {prec_stage_id}")
                    prec_timestamp, prec_details = self.calculate_adjusted_timestamp(prec_stage_id, po_row)
                    
                    if prec_timestamp:
                        preceding_final_timestamps.append(prec_timestamp)
                        print(f"Preceding final timestamp for {prec_stage_id}: {prec_timestamp}")
                    
                    if prec_details.get("actual_timestamp"):
                        try:
                            actual_ts = datetime.fromisoformat(prec_details["actual_timestamp"])
                            preceding_actual_timestamps.append(actual_ts)
                            print(f"Preceding actual timestamp for {prec_stage_id}: {actual_ts}")
                        except Exception as e:
                            print(f"Invalid actual timestamp in stage {prec_stage_id}: {e}")
                    
                    if prec_details.get("method") == "Projected" or prec_details.get("precedence_method") == "Projected":
                        has_projected_precedence = True
                    
                    calc_details["dependencies"].append({
                        "stage_id": prec_stage_id,
                        "stage_name": self.config.stages[prec_stage_id].name,
                        "timestamp": prec_timestamp.isoformat() if prec_timestamp else None,
                        "method": prec_details.get("method", "unknown")
                    })
        
        # Calculate target timestamp
        if preceding_final_timestamps:
            base_timestamp = max(preceding_final_timestamps)
            print(f"Max preceding final timestamp: {base_timestamp}")
            calc_details["target_timestamp"] = (base_timestamp + timedelta(days=lead_time_days)).isoformat()
            calc_details["calculation_source"] = "precedence_based"
            print(f"Target timestamp (precedence based): {calc_details['target_timestamp']}")
        else:
            print("No valid preceding timestamps, evaluating fallback expression")
            try:
                fallback_result, fallback_debug = self.expression_evaluator.evaluate_expression(
                    stage.fallback_calculation.expression, po_row
                )
                print(f"Fallback expression evaluated to: {fallback_result} (Debug: {fallback_debug})")
                if fallback_result:
                    calc_details["target_timestamp"] = (fallback_result + timedelta(days=lead_time_days)).isoformat()
                    calc_details["calculation_source"] = "fallback_based"
                    print(f"Target timestamp (fallback): {calc_details['target_timestamp']}")
            except Exception as e:
                print(f"ERROR in fallback evaluation for {stage_id}: {e}")
        
        # Determine precedence method
        if preceding_stage_ids:
            calc_details["precedence_method"] = "Projected" if has_projected_precedence else "Actual/Adjusted"
        else:
            calc_details["precedence_method"] = "no precedence"
        
        # Evaluate actual timestamp
        current_actual_timestamp = None
        if stage.actual_timestamp:
            print(f"Evaluating actual timestamp for {stage_id}: {stage.actual_timestamp}")
            actual_result, actual_debug = self.expression_evaluator.evaluate_expression(
                stage.actual_timestamp, po_row
            )
            print(f"Actual timestamp evaluated to: {actual_result} (Debug: {actual_debug})")
            if actual_result:
                current_actual_timestamp = actual_result
                print(f"Actual timestamp: {current_actual_timestamp}")
        
        # Determine method and final timestamp
        if current_actual_timestamp:
            max_preceding_actual = max(preceding_actual_timestamps) if preceding_actual_timestamps else None
            if max_preceding_actual and max_preceding_actual > current_actual_timestamp:
                calc_details["method"] = "Adjusted"
                calc_details["actual_timestamp"] = max_preceding_actual.isoformat()
                calc_details["final_timestamp"] = max_preceding_actual.isoformat()
                calc_details["calculation_source"] = "actual_from_precedence"
                print("Method: Adjusted (preceding actual overrides current)")
            else:
                calc_details["method"] = "Actual"
                calc_details["actual_timestamp"] = current_actual_timestamp.isoformat()
                calc_details["final_timestamp"] = current_actual_timestamp.isoformat()
                calc_details["calculation_source"] = "actual_from_field"
                print("Method: Actual")
        else:
            calc_details["method"] = "Projected"
            calc_details["final_timestamp"] = calc_details["target_timestamp"]
            calc_details["calculation_source"] = (calc_details["calculation_source"] or "") + "_target"
            if preceding_actual_timestamps:
                calc_details["actual_timestamp"] = max(preceding_actual_timestamps).isoformat()
            print("Method: Projected (no actuals available)")
        
        # Calculate delay if applicable
        if calc_details["method"] in ["Actual", "Adjusted"] and calc_details["target_timestamp"] and calc_details["actual_timestamp"]:
            try:
                target_dt = datetime.fromisoformat(calc_details["target_timestamp"])
                actual_dt = datetime.fromisoformat(calc_details["actual_timestamp"])
                delay_days = (actual_dt - target_dt).days
                calc_details["delay"] = delay_days
                print(f"Delay: {delay_days} days")
            except Exception as e:
                print(f"ERROR calculating delay for {stage_id}: {e}")
        
        # Final timestamp return
        final_timestamp = None
        if calc_details["final_timestamp"]:
            try:
                final_timestamp = datetime.fromisoformat(calc_details["final_timestamp"])
                print(f"Final timestamp: {final_timestamp}")
            except Exception as e:
                print(f"ERROR parsing final timestamp for {stage_id}: {e}")
        
        result = (final_timestamp, calc_details)
        self.calculated_adjustments[stage_id] = result
        print(f"--- Finished calculation for stage: {stage_id} ---\n")
        return result
    
    def reset_cache(self):
        print("Resetting stage calculation cache")
        self.calculated_adjustments = {}
        self.expression_evaluator.set_calculated_adjustments(self.calculated_adjustments)

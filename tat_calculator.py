"""
TAT (Turnaround Time) Calculator System
=====================================

A comprehensive system for calculating adjusted timestamps for Purchase Order (PO) 
processing workflow stages using a configurable, dependency-driven approach.

This implementation replaces complex Excel formulas with maintainable Python code
that supports dynamic expressions, stage dependencies, and transparent reasoning.
"""

import json
import ast
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Union, Any
from pathlib import Path
import pandas as pd
from pydantic import BaseModel, Field, validator
import numpy as np

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ProcessFlow(BaseModel):
    """Process flow metadata for a stage"""
    critical_path: bool
    parallel_processes: List[str] = Field(default_factory=list)
    handoff_points: List[str] = Field(default_factory=list)
    process_type: str
    team_owner: str


class FallbackCalculation(BaseModel):
    """Fallback calculation configuration"""
    expression: str
    
    @validator('expression')
    def validate_expression(cls, v):
        """Validate that expression is not empty"""
        if not v.strip():
            raise ValueError("Expression cannot be empty")
        return v


class StageConfig(BaseModel):
    """Configuration for a single stage"""
    name: str
    actual_timestamp: Optional[str] = None
    preceding_stage: Optional[Union[str, List[str]]] = None
    process_flow: ProcessFlow
    fallback_calculation: FallbackCalculation
    lead_time: int = Field(ge=0, description="Lead time in days")
    
    @validator('preceding_stage')
    def validate_preceding_stage(cls, v):
        """Convert single string to list for consistency"""
        if isinstance(v, str) and not v.startswith('if('):
            return [v]
        return v


class StagesConfig(BaseModel):
    """Complete stages configuration"""
    stages: Dict[str, StageConfig]
    
    @validator('stages')
    def validate_stage_ids(cls, v):
        """Ensure all stage IDs are valid"""
        for stage_id in v.keys():
            if not stage_id.strip():
                raise ValueError("Stage ID cannot be empty")
        return v


class TATCalculator:
    """
    Core TAT calculation engine that processes PO data through configurable stages.
    
    Features:
    - Configuration-driven stage definitions
    - Dynamic expression evaluation with custom functions
    - Dependency resolution with cycle detection
    - Memoization for performance optimization
    - Comprehensive audit trails and reasoning
    """
    
    def __init__(self, config_path: str = "stages_config.json"):
        """
        Initialize the TAT Calculator
        
        Args:
            config_path: Path to the stages configuration JSON file
        """
        self.config = self._load_config(config_path)
        self._validate_config()
        self.calculated_adjustments: Dict[str, Tuple[Optional[datetime], Dict[str, Any]]] = {}
        
    def _load_config(self, config_path: str) -> StagesConfig:
        """Load and validate configuration from JSON file"""
        try:
            with open(config_path, 'r') as f:
                config_data = json.load(f)
            return StagesConfig(**config_data)
        except FileNotFoundError:
            logger.error(f"Configuration file not found: {config_path}")
            raise
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in configuration file: {e}")
            raise
        except Exception as e:
            logger.error(f"Error loading configuration: {e}")
            raise
    
    def _validate_config(self):
        """Validate configuration for circular dependencies"""
        # Build dependency graph
        graph = {}
        for stage_id, stage in self.config.stages.items():
            if isinstance(stage.preceding_stage, list):
                graph[stage_id] = stage.preceding_stage
            elif isinstance(stage.preceding_stage, str) and stage.preceding_stage.startswith('if('):
                # For conditional dependencies, we'll validate them during runtime
                graph[stage_id] = []
            else:
                graph[stage_id] = []
        
        # Check for cycles using DFS
        visited = set()
        rec_stack = set()
        
        def has_cycle(node):
            if node in rec_stack:
                return True
            if node in visited:
                return False
                
            visited.add(node)
            rec_stack.add(node)
            
            for neighbor in graph.get(node, []):
                if neighbor in graph and has_cycle(neighbor):
                    return True
            
            rec_stack.remove(node)
            return False
        
        for stage_id in graph:
            if stage_id not in visited:
                if has_cycle(stage_id):
                    raise ValueError(f"Circular dependency detected involving stage {stage_id}")
    
    def _get_date_value(self, field_name: str, po_row: pd.Series) -> Optional[datetime]:
        """
        Extract datetime value from PO data with robust handling
        
        Args:
            field_name: Name of the field to extract
            po_row: Pandas Series containing PO data
            
        Returns:
            datetime object or None if not available/valid
        """
        if field_name not in po_row.index:
            logger.warning(f"Field '{field_name}' not found in PO data")
            return None
            
        value = po_row[field_name]
        
        # Handle various data types
        if pd.isna(value) or value == "" or value == "NA":
            return None
            
        if isinstance(value, datetime):
            return value
            
        if isinstance(value, str):
            try:
                # Try common datetime formats
                for fmt in ["%Y-%m-%d", "%Y-%m-%d %H:%M:%S", "%m/%d/%Y", "%d/%m/%Y"]:
                    try:
                        return datetime.strptime(value, fmt)
                    except ValueError:
                        continue
                        
                # Try pandas datetime parsing as fallback
                return pd.to_datetime(value)
            except:
                logger.warning(f"Could not parse date from field '{field_name}': {value}")
                return None
                
        return None
    
    def _evaluate_expression(self, expression: str, po_row: pd.Series, return_type: str = "datetime") -> Tuple[Any, str]:
        """
        Evaluate dynamic expressions with custom functions
        
        Supported functions:
        - max(date1, date2, ...): Returns latest datetime
        - add_days(date, days): Adds days to a date
        - if(condition, true_val, false_val): Conditional evaluation
        
        Args:
            expression: Expression string to evaluate
            po_row: PO data for field resolution
            return_type: Expected return type ("datetime" or "stage_list")
            
        Returns:
            Tuple of (result, formula_description)
        """
        try:
            # Parse expression into AST
            tree = ast.parse(expression, mode='eval')
            result = self._eval_node(tree.body, po_row, return_type)
            
            if return_type == "stage_list":
                # For stage dependencies, ensure we return a list of strings
                if isinstance(result, list):
                    # Convert integers to strings
                    result = [str(item) for item in result]
                    return result, f"Evaluated: {expression} = {result}"
                elif result is not None:
                    # Single value, convert to list
                    return [str(result)], f"Evaluated: {expression} = [{result}]"
                else:
                    # If evaluation failed, return empty list
                    logger.warning(f"Expression evaluation returned None: {expression}")
                    return [], f"Evaluation failed: {expression} (returned None)"
            else:
                # For datetime expressions
                if isinstance(result, datetime):
                    return result, f"Calculation: {expression} = {result.strftime('%Y-%m-%d %H:%M:%S')}"
                else:
                    return None, f"Calculation failed: {expression}"
                
        except Exception as e:
            logger.error(f"Error evaluating expression '{expression}': {e}")
            if return_type == "stage_list":
                return [], f"Evaluation error: {expression} ({str(e)})"
            else:
                return None, f"Calculation error: {expression} ({str(e)})"
    
    def _eval_node(self, node: ast.AST, po_row: pd.Series, return_type: str = "datetime") -> Any:
        """Recursively evaluate AST nodes"""
        if isinstance(node, ast.Name):
            # Field name - look up in PO data
            value = po_row.get(node.id)
            # Handle missing fields gracefully
            if value is None and node.id not in po_row.index:
                logger.warning(f"Field '{node.id}' not found in PO data, treating as None")
                return None
            # For datetime return type, try to convert to datetime
            if return_type == "datetime" and value is not None and not isinstance(value, datetime):
                return self._get_date_value(node.id, po_row)
            return value
        
        elif isinstance(node, ast.Call):
            # Function call
            if isinstance(node.func, ast.Name):
                func_name = node.func.id
                
                if func_name == 'if':
                    # if(condition, true_val, false_val)
                    if len(node.args) == 3:
                        condition = self._eval_node(node.args[0], po_row, "raw")
                        # Handle None condition (e.g., missing field)
                        if condition is None:
                            logger.warning(f"Condition evaluated to None in if expression, defaulting to false branch")
                            condition = False
                        # Evaluate condition
                        if condition:
                            return self._eval_node(node.args[1], po_row, return_type)
                        else:
                            return self._eval_node(node.args[2], po_row, return_type)
                    return None
                
                elif func_name == 'max' and return_type == "datetime":
                    # For datetime max
                    args = [self._eval_node(arg, po_row, "datetime") for arg in node.args]
                    valid_dates = [arg for arg in args if isinstance(arg, datetime)]
                    return max(valid_dates) if valid_dates else None
                
                elif func_name == 'add_days' and return_type == "datetime":
                    # add_days function
                    if len(node.args) >= 2:
                        date_arg = self._eval_node(node.args[0], po_row, "datetime")
                        days_arg = self._eval_node(node.args[1], po_row, "raw")
                        if isinstance(date_arg, datetime) and isinstance(days_arg, (int, float)):
                            return date_arg + timedelta(days=int(days_arg))
                    return None
                
                else:
                    # For other functions, evaluate args with appropriate type
                    args = [self._eval_node(arg, po_row, "raw") for arg in node.args]
                    return args[0] if args else None
        
        elif isinstance(node, ast.List):
            # Support for list literals like [5], [2]
            return [self._eval_node(elt, po_row, "raw") for elt in node.elts]
        
        elif isinstance(node, ast.Compare):
            # Handle comparisons like pi_applicable == 1
            left = self._eval_node(node.left, po_row, "raw")
            # Handle None values in comparisons
            if left is None:
                logger.warning(f"Left side of comparison is None")
                return False
            
            if len(node.ops) == 1 and len(node.comparators) == 1:
                right = self._eval_node(node.comparators[0], po_row, "raw")
                op = node.ops[0]
                if isinstance(op, ast.Eq):
                    return left == right
                elif isinstance(op, ast.NotEq):
                    return left != right
                elif isinstance(op, ast.Lt):
                    return left < right if left is not None and right is not None else False
                elif isinstance(op, ast.LtE):
                    return left <= right if left is not None and right is not None else False
                elif isinstance(op, ast.Gt):
                    return left > right if left is not None and right is not None else False
                elif isinstance(op, ast.GtE):
                    return left >= right if left is not None and right is not None else False
            return False
        
        elif isinstance(node, ast.Constant):
            # Literal value
            return node.value
        
        elif isinstance(node, ast.Num):  # For older Python versions
            return node.n
        
        elif isinstance(node, ast.Str):  # For older Python versions
            return node.s
        
        else:
            raise ValueError(f"Unsupported AST node type: {type(node)}")
    
    def _extract_actual_field(self, expression: str) -> Optional[str]:
        """
        Extract the 'actual' field from a max() expression
        
        For expressions like "max(actual_field, fallback)", returns "actual_field"
        """
        try:
            tree = ast.parse(expression, mode='eval')
            if isinstance(tree.body, ast.Call) and isinstance(tree.body.func, ast.Name):
                if tree.body.func.id == 'max' and tree.body.args:
                    first_arg = tree.body.args[0]
                    if isinstance(first_arg, ast.Name):
                        return first_arg.id
        except:
            pass
        return None
    
    def calculate_adjusted_timestamp(self, stage_id: str, po_row: pd.Series) -> Tuple[Optional[datetime], Dict[str, Any]]:
        """
        Calculate adjusted timestamp for a specific stage using priority logic:
        
        1. Precedence-based calculation (from dependencies + lead time)
        2. Actual timestamp comparison (if available)
        3. Fallback calculation (last resort)
        
        Args:
            stage_id: ID of the stage to calculate
            po_row: PO data row
            
        Returns:
            Tuple of (calculated_timestamp, calculation_details)
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
            "source": None,
            "base_date": None,
            "lead_time_applied": stage.lead_time,
            "decision_reason": None,
            "dependencies": [],
            "actual_field": None,
            "actual_value": None,
            "precedence_value": None,
            "final_choice": None
        }
        
        # 1. Calculate precedence-based timestamp
        precedence_timestamp = None
        if stage.preceding_stage:
            dependencies = []
            preceding_timestamps = []
            
            # Handle different types of preceding_stage
            if isinstance(stage.preceding_stage, list):
                # Simple list of stage IDs
                preceding_stage_ids = stage.preceding_stage
            elif isinstance(stage.preceding_stage, str) and stage.preceding_stage.startswith('if('):
                # Expression that needs evaluation
                preceding_stage_ids, eval_formula = self._evaluate_expression(stage.preceding_stage, po_row, return_type="stage_list")
                logger.info(f"Stage {stage_id} conditional dependency: {eval_formula}")
                if not preceding_stage_ids:
                    logger.warning(f"Stage {stage_id} conditional dependency returned empty list")
                    calc_details["dependencies_error"] = f"Conditional dependency evaluation failed: {eval_formula}"
            else:
                # Single stage ID as string
                preceding_stage_ids = [stage.preceding_stage] if stage.preceding_stage else []
            
            # Calculate timestamps for all preceding stages
            for prec_stage_id in preceding_stage_ids:
                if prec_stage_id and prec_stage_id in self.config.stages:
                    prec_timestamp, prec_details = self.calculate_adjusted_timestamp(prec_stage_id, po_row)
                    if prec_timestamp:
                        preceding_timestamps.append(prec_timestamp)
                        dependencies.append({
                            "stage_id": prec_stage_id,
                            "stage_name": self.config.stages[prec_stage_id].name,
                            "timestamp": prec_timestamp.isoformat(),
                            "method": prec_details.get("method", "unknown") if isinstance(prec_details, dict) else "legacy"
                        })
            
            calc_details["dependencies"] = dependencies
            
            if preceding_timestamps:
                base_timestamp = max(preceding_timestamps)
                precedence_timestamp = base_timestamp + timedelta(days=stage.lead_time)
                calc_details["precedence_value"] = precedence_timestamp.isoformat()
                calc_details["base_date"] = base_timestamp.isoformat()
        
        # 2. Extract and get actual timestamp
        actual_timestamp = None
        actual_formula = None
        if stage.actual_timestamp:
            actual_timestamp, actual_formula = self._evaluate_expression(stage.actual_timestamp, po_row, return_type="datetime")
            calc_details["actual_field"] = stage.actual_timestamp
            if actual_timestamp:
                calc_details["actual_value"] = actual_timestamp.isoformat()
        
        # 3. Determine final timestamp and method
        final_timestamp = None
        
        if precedence_timestamp and actual_timestamp:
            if actual_timestamp >= precedence_timestamp:
                final_timestamp = actual_timestamp
                calc_details["method"] = "actual_over_precedence"
                calc_details["source"] = actual_formula
                calc_details["decision_reason"] = f"Actual date ({actual_timestamp.strftime('%Y-%m-%d')}) is later than precedence date ({precedence_timestamp.strftime('%Y-%m-%d')})"
                calc_details["final_choice"] = "actual"
            else:
                final_timestamp = precedence_timestamp
                calc_details["method"] = "precedence_over_actual"
                calc_details["source"] = f"Max of preceding stages + {stage.lead_time} days"
                calc_details["decision_reason"] = f"Precedence calculation ({precedence_timestamp.strftime('%Y-%m-%d')}) is later than actual ({actual_timestamp.strftime('%Y-%m-%d')})"
                calc_details["final_choice"] = "precedence"
        
        elif actual_timestamp:
            final_timestamp = actual_timestamp
            calc_details["method"] = "actual_only"
            calc_details["source"] = actual_formula
            calc_details["decision_reason"] = "Using actual timestamp (no precedence available)"
            calc_details["final_choice"] = "actual"
        
        elif precedence_timestamp:
            final_timestamp = precedence_timestamp
            calc_details["method"] = "precedence_only"
            calc_details["source"] = f"Max of preceding stages + {stage.lead_time} days"
            calc_details["decision_reason"] = "No actual timestamp available, using precedence calculation"
            calc_details["final_choice"] = "precedence"
        
        # 4. Fallback calculation if no valid timestamp
        if not final_timestamp:
            fallback_result, fallback_formula = self._evaluate_expression(
                stage.fallback_calculation.expression, po_row, return_type="datetime"
            )
            if fallback_result:
                final_timestamp = fallback_result + timedelta(days=stage.lead_time)
                calc_details["method"] = "fallback"
                calc_details["source"] = stage.fallback_calculation.expression
                calc_details["base_date"] = fallback_result.isoformat()
                calc_details["decision_reason"] = "No precedence or actual data available, using fallback expression"
                calc_details["final_choice"] = "fallback"
            else:
                calc_details["method"] = "failed"
                calc_details["decision_reason"] = "No valid calculation method available"
        
        # Cache result
        result = (final_timestamp, calc_details)
        self.calculated_adjustments[stage_id] = result
        
        return result
    
    def calculate_tat(self, po_row: pd.Series) -> Dict[str, Any]:
        """
        Calculate TAT for all stages of a PO
        
        Args:
            po_row: Pandas Series containing PO data
            
        Returns:
            Dictionary with complete TAT calculation results
        """
        # Clear cache for new calculation
        self.calculated_adjustments = {}
        
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
            timestamp, calc_details = self.calculate_adjusted_timestamp(stage_id, po_row)
            
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
    
    def _format_calculation_summary(self, calc_details: Dict[str, Any], stage_config: StageConfig) -> Dict[str, Any]:
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
            "lead_time_days": calc_details.get("lead_time_applied", 0)
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
                "base_date": calc_details.get("base_date"),
                "reason": "No actual timestamp available"
            })
        elif method == "actual_only":
            summary.update({
                "actual_field": calc_details.get("actual_field"),
                "reason": "No dependency chain available"
            })
        elif method == "fallback":
            summary.update({
                "base_date": calc_details.get("base_date"),
                "expression": calc_details.get("source"),
                "reason": "Using fallback calculation"
            })
        
        # Add any error information
        if "dependencies_error" in calc_details:
            summary["error"] = calc_details["dependencies_error"]
        
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
            output_file: Output Excel file path
        """
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


if __name__ == "__main__":
    print("TAT Calculator System - Enhanced with Excel Export")
    print("Usage:")
    print("1. calculator = TATCalculator()")
    print("2. results = calculator.process_batch(df)")
    print("3. calculator.export_to_excel(df, results, 'output.xlsx')")

"""
Expression Evaluation Engine
============================

Dynamic expression evaluation with custom functions for TAT calculations.
"""

import ast
import logging
from datetime import datetime, timedelta
from typing import Any, Optional, Tuple
import pandas as pd

logger = logging.getLogger(__name__)


class ExpressionEvaluator:
    """
    Evaluates dynamic expressions with custom functions.
    
    Supported functions:
    - max(date1, date2, ...): Returns latest datetime
    - add_days(date, days): Adds days to a date
    - cond(condition, true_val, false_val): Conditional evaluation
    """
    
    def __init__(self):
        self.calculated_adjustments = {}
    
    def set_calculated_adjustments(self, adjustments):
        """Set the calculated adjustments cache for stage references"""
        self.calculated_adjustments = adjustments
    
    def evaluate_expression(self, expression: str, po_row: pd.Series) -> Tuple[Optional[datetime], str]:
        """
        Evaluate dynamic expressions with custom functions
        
        Args:
            expression: Expression string to evaluate
            po_row: PO data for field resolution
            
        Returns:
            Tuple of (result_datetime, formula_description)
        """
        try:
            # Parse expression into AST
            tree = ast.parse(expression, mode='eval')
            result = self._eval_node(tree.body, po_row)
            
            if isinstance(result, datetime):
                return result, f"Calculation: {expression} = {result.strftime('%Y-%m-%d %H:%M:%S')}"
            else:
                return None, f"Calculation failed: {expression}"
                
        except Exception as e:
            logger.error(f"Error evaluating expression '{expression}': {e}")
            return None, f"Calculation error: {expression} ({str(e)})"
    
    def _eval_node(self, node: ast.AST, po_row: pd.Series) -> Any:
        """Recursively evaluate AST nodes"""
        if isinstance(node, ast.Name):
            var_name = node.id
            # Check if it's a stage reference
            if var_name.startswith('stage_'):
                print("Variable name is", var_name)
                stage_id = var_name.replace('stage_', '')
                if stage_id in self.calculated_adjustments:
                    timestamp, _ = self.calculated_adjustments[stage_id]
                    return timestamp  # Already a datetime or None
            
            return po_row.get(node.id)
        
        elif isinstance(node, ast.Constant):
            return node.value
        
        elif isinstance(node, ast.List):
            # Handle list literals like ['5'], ['2']
            return [self._eval_node(elt, po_row) for 
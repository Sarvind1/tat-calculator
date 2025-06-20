"""
Debug script to diagnose Stage 8 conditional dependency issue
"""

import pandas as pd
from datetime import datetime
from tat_calculator import TATCalculator
import json

# Create test data with different scenarios
test_scenarios = [
    {
        'name': 'Test 1: pi_applicable = 1',
        'data': {
            'po_razin_id': 'PO-TEST-001',
            'po_created_date': datetime(2025, 6, 1),
            'po_approval_date': datetime(2025, 6, 2),
            'supplier_confirmation_date': datetime(2025, 6, 3),
            'pi_invoice_approval_date': datetime(2025, 6, 5),
            'pi_payment_date': datetime(2025, 6, 8),
            'receive_first_prd_date': datetime(2025, 6, 10),
            'pi_applicable': 1
        }
    },
    {
        'name': 'Test 2: pi_applicable = 0',
        'data': {
            'po_razin_id': 'PO-TEST-002',
            'po_created_date': datetime(2025, 6, 1),
            'po_approval_date': datetime(2025, 6, 2),
            'supplier_confirmation_date': datetime(2025, 6, 3),
            'pi_invoice_approval_date': datetime(2025, 6, 5),
            'pi_payment_date': datetime(2025, 6, 8),
            'receive_first_prd_date': datetime(2025, 6, 10),
            'pi_applicable': 0
        }
    },
    {
        'name': 'Test 3: pi_applicable missing',
        'data': {
            'po_razin_id': 'PO-TEST-003',
            'po_created_date': datetime(2025, 6, 1),
            'po_approval_date': datetime(2025, 6, 2),
            'supplier_confirmation_date': datetime(2025, 6, 3),
            'pi_invoice_approval_date': datetime(2025, 6, 5),
            'pi_payment_date': datetime(2025, 6, 8),
            'receive_first_prd_date': datetime(2025, 6, 10)
            # pi_applicable is missing
        }
    }
]

# Initialize calculator
calculator = TATCalculator()

print("DEBUG: Stage 8 Conditional Dependency Analysis")
print("=" * 70)

# Get stage 8 configuration
stage_8_config = calculator.config.stages['8']
print(f"\nStage 8 Configuration:")
print(f"  Name: {stage_8_config.name}")
print(f"  Preceding Stage Expression: {stage_8_config.preceding_stage}")
print(f"  Actual Timestamp Field: {stage_8_config.actual_timestamp}")

# Test each scenario
for scenario in test_scenarios:
    print(f"\n{'-' * 70}")
    print(f"{scenario['name']}")
    print(f"{'-' * 70}")
    
    po_row = pd.Series(scenario['data'])
    
    # Clear cache for fresh calculation
    calculator.calculated_adjustments = {}
    
    # Test the expression evaluation directly
    print(f"\n1. Testing expression evaluation:")
    print(f"   Expression: {stage_8_config.preceding_stage}")
    print(f"   pi_applicable value: {po_row.get('pi_applicable', 'NOT FOUND')}")
    
    try:
        result, formula = calculator._evaluate_expression(
            stage_8_config.preceding_stage, 
            po_row, 
            return_type="stage_list"
        )
        print(f"   Evaluation result: {result}")
        print(f"   Formula: {formula}")
    except Exception as e:
        print(f"   ERROR in evaluation: {e}")
    
    # Calculate stage 8
    print(f"\n2. Calculating Stage 8:")
    try:
        timestamp, details = calculator.calculate_adjusted_timestamp("8", po_row)
        print(f"   Timestamp: {timestamp}")
        print(f"   Method: {details.get('method')}")
        print(f"   Dependencies: {details.get('dependencies')}")
        print(f"   Decision: {details.get('decision_reason')}")
        
        # Print full details for debugging
        print(f"\n   Full calculation details:")
        for key, value in details.items():
            print(f"     {key}: {value}")
            
    except Exception as e:
        print(f"   ERROR in calculation: {e}")
        import traceback
        traceback.print_exc()

# Additional debug: Test the expression components
print(f"\n{'-' * 70}")
print("ADDITIONAL DEBUG: Testing expression components")
print(f"{'-' * 70}")

test_data = pd.Series({
    'pi_applicable': 1,
    'test_field': 'test_value'
})

print("\nTesting individual components:")

# Test comparison
print("\n1. Testing comparison: pi_applicable == 1")
try:
    result, _ = calculator._evaluate_expression("pi_applicable == 1", test_data, return_type="raw")
    print(f"   Result: {result}")
except Exception as e:
    print(f"   ERROR: {e}")

# Test list literals
print("\n2. Testing list literal: [5]")
try:
    result, _ = calculator._evaluate_expression("[5]", test_data, return_type="stage_list")
    print(f"   Result: {result}")
except Exception as e:
    print(f"   ERROR: {e}")

# Test if function
print("\n3. Testing if function: if(1 == 1, [5], [2])")
try:
    result, _ = calculator._evaluate_expression("if(1 == 1, [5], [2])", test_data, return_type="stage_list")
    print(f"   Result: {result}")
except Exception as e:
    print(f"   ERROR: {e}")

print("\n" + "=" * 70)
print("DEBUG COMPLETE")

"""
Test script to verify TAT Calculator with conditional dependencies
"""

import pandas as pd
from datetime import datetime
from tat_calculator import TATCalculator

# Create test data
test_data = {
    'po_razin_id': 'PO-TEST-001',
    'po_created_date': datetime(2025, 6, 1),
    'po_approval_date': datetime(2025, 6, 2),
    'supplier_confirmation_date': datetime(2025, 6, 3),
    'pi_invoice_approval_date': datetime(2025, 6, 5),
    'pi_payment_date': datetime(2025, 6, 8),
    'receive_first_prd_date': datetime(2025, 6, 10),
    'pi_applicable': 1  # This will trigger the conditional logic in stage 8
}

# Create a pandas Series from the test data
po_row = pd.Series(test_data)

print("Test Data:")
print("-" * 50)
for key, value in test_data.items():
    print(f"{key}: {value}")
print("-" * 50)

# Initialize calculator
calculator = TATCalculator()

# Test stage 8 specifically (has conditional dependency)
print("\nTesting Stage 8 (with conditional dependency):")
print("Expression: if(pi_applicable == 1, [5], [2])")
print(f"pi_applicable = {test_data['pi_applicable']}")
print("Expected: Should depend on stage 5")

timestamp, details = calculator.calculate_adjusted_timestamp("8", po_row)

print(f"\nResult:")
print(f"Timestamp: {timestamp}")
print(f"Method: {details.get('method')}")
print(f"Dependencies: {details.get('dependencies')}")
print(f"Decision: {details.get('decision_reason')}")

# Test with pi_applicable = 0
test_data['pi_applicable'] = 0
po_row2 = pd.Series(test_data)

print("\n" + "="*70)
print("\nTesting Stage 8 with pi_applicable = 0:")
print("Expected: Should depend on stage 2")

# Clear cache for new calculation
calculator.calculated_adjustments = {}

timestamp2, details2 = calculator.calculate_adjusted_timestamp("8", po_row2)

print(f"\nResult:")
print(f"Timestamp: {timestamp2}")
print(f"Method: {details2.get('method')}")
print(f"Dependencies: {details2.get('dependencies')}")
print(f"Decision: {details2.get('decision_reason')}")

# Run full TAT calculation
print("\n" + "="*70)
print("\nRunning full TAT calculation:")
result = calculator.calculate_tat(po_row)

# Print summary
print(f"\nPO ID: {result['po_id']}")
print(f"Total Stages: {result['summary']['total_stages']}")
print(f"Calculated Stages: {result['summary']['calculated_stages']}")
print(f"Completion Rate: {result['summary']['completion_rate']}%")

# Print details for stages with interesting dependencies
print("\n" + "="*70)
print("\nStage Details (for stages with dependencies):")
for stage_id in ["1", "2", "5", "8"]:
    if stage_id in result['stages']:
        stage = result['stages'][stage_id]
        print(f"\n{stage['name']}:")
        print(f"  Timestamp: {stage['timestamp']}")
        print(f"  Method: {stage['calculation']['method']}")
        if stage['dependencies']:
            print(f"  Dependencies: {[dep['stage_name'] for dep in stage['dependencies']]}")

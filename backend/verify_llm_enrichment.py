import sys
import os
import json
from unittest.mock import MagicMock, patch

# Allow direct execution from backend/
sys.path.insert(0, os.path.dirname(__file__))

from services.llm_enrichment_service import LLMEnrichmentService

PASS = 0
FAIL = 0

def check(label, condition):
    global PASS, FAIL
    if condition:
        print(f"  [PASS] {label}")
        PASS += 1
    else:
        print(f"  [FAIL] {label}")
        FAIL += 1

def test_payload_with_locator_context():
    print("\n[1] Testing Payload with Locator Context")
    service = LLMEnrichmentService(api_key="fake")
    normalized = {
        "steps": [
            {
                "action": "click",
                "locator": {"strategy": "id", "value": "login_btn", "field_name": "btnLogin"},
                "method": "LoginPage.login"
            }
        ],
        "assertions": []
    }
    
    minimal = service._minimize_payload(normalized)
    
    check("Locator includes field_name", minimal['steps'][0]['locator'].get('field_name') == "btnLogin")
    check("Locator includes value", minimal['steps'][0]['locator'].get('value') == "login_btn")

def test_vocabulary_validation():
    print("\n[2] Testing Vocabulary Validation")
    service = LLMEnrichmentService(api_key="fake")
    original = {"steps": [{}]}
    
    # Valid vocabulary
    enriched_valid = {
        "test_type": "UI_LOGIN",
        "step_annotations": [{"index": 0, "label": "L1"}],
        "step_groups": [{"group": "A", "steps": [0]}]
    }
    errors = service._validate_enriched(original, enriched_valid)
    check("Accepts valid test_type", len(errors) == 0)

    # Invalid vocabulary
    enriched_invalid = {
        "test_type": "ARBITRARY_TYPE",
        "step_annotations": [{"index": 0, "label": "L1"}],
        "step_groups": [{"group": "A", "steps": [0]}]
    }
    errors = service._validate_enriched(original, enriched_invalid)
    check("Rejects invalid test_type", any("Illegal test_type" in e for e in errors))

def test_group_order_validation():
    print("\n[3] Testing Group Order Validation")
    service = LLMEnrichmentService(api_key="fake")
    original = {"steps": [{}, {}, {}]}
    
    # Valid order
    enriched_valid = {
        "test_type": "UI_LOGIN",
        "step_annotations": [{"index": i, "label": f"L{i}"} for i in range(3)],
        "step_groups": [
            {"group": "A", "steps": [0, 1]},
            {"group": "B", "steps": [2]}
        ]
    }
    errors = service._validate_enriched(original, enriched_valid)
    check("Accepts sequential groups", len(errors) == 0)

    # Reversed groups
    enriched_reversed = {
        "test_type": "UI_LOGIN",
        "step_annotations": [{"index": i, "label": f"L{i}"} for i in range(3)],
        "step_groups": [
            {"group": "A", "steps": [2]},
            {"group": "B", "steps": [0, 1]}
        ]
    }
    errors = service._validate_enriched(original, enriched_reversed)
    check("Rejects non-sequential group indices", any("violate execution order" in e for e in errors))

    # Jumbled indices within group
    enriched_jumbled = {
        "test_type": "UI_LOGIN",
        "step_annotations": [{"index": i, "label": f"L{i}"} for i in range(3)],
        "step_groups": [
            {"group": "A", "steps": [1, 0, 2]}
        ]
    }
    errors = service._validate_enriched(original, enriched_jumbled)
    check("Rejects jumbled indices within group", any("within a group are not sequential" in e for e in errors))

if __name__ == "__main__":
    test_payload_with_locator_context()
    test_vocabulary_validation()
    test_group_order_validation()
    
    print(f"\nFinal Results: {PASS} passed, {FAIL} failed")
    if FAIL > 0:
        sys.exit(1)

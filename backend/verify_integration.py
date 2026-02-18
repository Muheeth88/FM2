import sys
import os
import json
from unittest.mock import MagicMock, patch

# Allow direct execution from backend/
sys.path.insert(0, os.path.dirname(__file__))

from services.intent_extractor_service import IntentExtractorService
from database.db import Database

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

@patch('services.llm_enrichment_service.OpenAI')
def test_integration(mock_openai):
    print("\n[5] Testing IntentExtractorService Integration")
    
    # Setup mock response
    mock_client = MagicMock()
    mock_openai.return_value = mock_client
    
    resp = MagicMock()
    resp.choices = [MagicMock()]
    resp.choices[0].message.content = json.dumps({
        "feature_label": "Login Test",
        "test_type": "AUTH",
        "risk_flags": [],
        "step_groups": [{"group": "Login", "steps": [0]}],
        "step_annotations": [{"index": 0, "label": "Login to app"}]
    })
    mock_client.chat.completions.create.return_value = resp
    
    # Initialize service
    db_path = "test_integration.db"
    if os.path.exists(db_path): os.unlink(db_path)
    
    service = IntentExtractorService(db_path=db_path)
    
    # Mock data
    normalized = {
        "steps": [{"action": "navigate", "url": "http://test.com"}],
        "assertions": [{"operator": "equals"}],
        "locators": [],
        "lifecycle_hooks": [],
        "control_flow": []
    }
    
    # Inject normalized model into a mock feature process
    with patch.object(service.ast_extractor, 'parse_files', return_value={}):
        with patch.object(service.normalizer, 'normalize', return_value=normalized):
            with patch('services.intent_extractor_service.USE_LLM', True):
                result = service.process_feature("session_1", "feat_1", ["test.java"])
    
    print(f"  [INFO] Enriched Model Keys: {list(result['enriched_model'].keys())}")
    check("Enrichment called", mock_client.chat.completions.create.called)
    check("Enriched model returned", result.get("enriched_model") is not None)
    check("Enrichment status SUCCESS", result["enriched_model"].get("enrichment_status") == "SUCCESS")
    check("Has step_annotations", "step_annotations" in result["enriched_model"])
    check("Has step_groups", "step_groups" in result["enriched_model"])
    
    # Verify DB
    db = Database(db_path)
    row = db.fetchone("SELECT * FROM feature_intent WHERE feature_id = 'feat_1'")
    check("DB has enrichment_status", row.get("enrichment_status") == "SUCCESS")
    check("DB has enrichment_version", row.get("enrichment_version") == "v1")
    
    os.unlink(db_path)

if __name__ == "__main__":
    test_integration()
    print(f"\nFinal Results: {PASS} passed, {FAIL} failed")
    if FAIL > 0:
        sys.exit(1)

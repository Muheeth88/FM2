from services.intent_extractor_service import IntentExtractorService
import json
import os

def test_phase3():
    service = IntentExtractorService()
    
    # Session ID from previous turn
    session_id = "8411c0cc-3e1d-4ac4-a6df-fdf457f2d850"
    base_path = f"d:/Workspace/FM2/backend/workspaces/{session_id}/source"
    
    # 1. Verification of UI Test (SmokeTest) - Deep Inlining & Control Flow
    smoke_test_path = f"{base_path}/src/test/java/com/cogmento/testcases/web/smoke/SmokeTest.java"
    # To resolve POs, we need all java files in workspace
    java_files = []
    for root, dirs, files in os.walk(base_path):
        for f in files:
            if f.endswith('.java'):
                java_files.append(os.path.join(root, f))
    
    print(f"--- Processing SmokeTest.java ---")
    result_ui = service.process_feature(session_id, "feature-smoke", [smoke_test_path], java_files)
    model = result_ui.get('normalized_model', {})
    print(f"Steps count: {len(model.get('steps', []))}")
    print(f"Assertions count: {len(model.get('assertions', []))}")
    print(f"Control Flow count: {len(model.get('control_flow', []))}")
    if model.get('steps'):
        print(f"First action: {model['steps'][0]['action']} in {model['steps'][0].get('source_method', 'N/A')}")
    if model.get('control_flow'):
        print(f"CF Action: {model['control_flow'][0]['action']}, Condition: {model['control_flow'][0].get('condition', 'N/A')}")

    # 2. Verification of API Test - API Action Modeling
    api_test_path = f"{base_path}/src/test/java/com/cogmento/testcases/api/company/CreateCompanyAPITest.java"
    print(f"\n--- Processing CreateCompanyAPITest.java ---")
    result_api = service.process_feature(session_id, "feature-api", [api_test_path], java_files)
    api_model = result_api.get('normalized_model', {})
    api_steps = api_model.get('steps', [])
    print(f"API Steps count: {len(api_steps)}")
    for i, s in enumerate(api_steps):
        print(f"Step {i}: {s['action']}, method: {s.get('method')}, endpoint: {s.get('endpoint')}, src: {s.get('source_method')}")
    
    http_steps = [s for s in api_steps if s['action'] == 'http_request']
    print(f"HTTP Request actions: {len(http_steps)}")

    # 3. Verification of Empty Feature Pruning
    base_api_path = f"{base_path}/src/main/java/com/cogmento/pages/api/BaseAPI.java"
    print(f"\n--- Processing BaseAPI.java ---")
    result_empty = service.process_feature(session_id, "feature-empty", [base_api_path], java_files)
    print(f"Status: {result_empty.get('status')}, Reason: {result_empty.get('reason')}")

if __name__ == "__main__":
    test_phase3()

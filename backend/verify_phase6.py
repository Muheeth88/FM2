
import sys
import os
import json
import glob

# Add backend to path
sys.path.append(os.getcwd())

from services.intent_extractor_service import IntentExtractorService

def verify():
    base_dir = r"d:\Workspace\FM2\backend\workspaces\bcf6eec0-c938-44d8-a6e8-d838dcb2cf31\source\src"
    ui_test = os.path.join(base_dir, r"test\java\com\cogmento\testcases\web\deal\CreateDeal.java")
    api_test = os.path.join(base_dir, r"test\java\com\cogmento\testcases\api\company\CreateCompanyAPITest.java")
    
    workspace_files = glob.glob(os.path.join(base_dir, "**/*.java"), recursive=True)
    
    service = IntentExtractorService()
    
    lines = []
    lines.append("--- Phase 6 Verification Results ---")

    # 1. Verify UI Test (Expansion + Control Flow + Lifecycle)
    res_ui = service.process_feature(
        session_id="verify_ui",
        feature_id="ui_feat",
        file_paths=[ui_test],
        workspace_files=workspace_files
    )
    if res_ui.get("status") == "SKIPPED":
        lines.append(f"UI TEST ERROR: {res_ui.get('reason')}")
    else:
        normalized = res_ui['normalized_model']
        hooks = normalized.get('lifecycle_hooks', [])
        steps = normalized.get('steps', [])
        lines.append(f"UI Test Steps: {len(steps)}")
        lines.append(f"UI Lifecycle Hooks: {len(hooks)} (Normalized: {all(h['action'] in ('setup', 'teardown') for h in hooks)})")
        
    # 2. Verify API Test (Endpoint Resolution)
    res_api = service.process_feature(
        session_id="verify_api",
        feature_id="api_feat",
        file_paths=[api_test],
        workspace_files=workspace_files
    )
    if res_api.get("status") == "SKIPPED":
        lines.append(f"API TEST ERROR: {res_api.get('reason')}")
    else:
        normalized = res_api['normalized_model']
        steps = normalized.get('steps', [])
        api_steps = [s for s in steps if s['action'] == 'http_request']
        lines.append(f"API Test HTTP Steps: {len(api_steps)}")
        for i, s in enumerate(api_steps):
            lines.append(f"  Req {i+1}: {s.get('method')} {s.get('endpoint')}")
            if s.get('endpoint') != 'dynamic':
                lines.append(f"  PASS: Endpoint resolved to {s.get('endpoint')}")
            else:
                lines.append("  FAIL: Endpoint is still 'dynamic'")

    report = "\n".join(lines)
    print(report)
    with open("phase6_report.txt", "w") as f: f.write(report)

if __name__ == "__main__":
    verify()

import json
import logging
from typing import Dict, Any, List, Optional
from openai import OpenAI

logger = logging.getLogger(__name__)

import os

# ===============================
# CONFIG
# ===============================
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
MODEL = "gpt-4o-mini"
ENRICHMENT_VERSION = "v1"

class LLMEnrichmentService:
    def __init__(self, api_key: str = None, model: str = None):
        self.api_key = api_key or OPENAI_API_KEY
        self.model = model or MODEL
        self.client = OpenAI(api_key=self.api_key) if self.api_key else None

    def enrich(self, normalized_model: Dict[str, Any], retry_count: int = 0) -> Dict[str, Any]:
        """
        Enrich a normalized intent model using LLM.
        Includes payload minimization, strict validation, and retry logic.
        """
        if not self.client:
            logger.warning("LLM Enrichment skipped: No API key provided.")
            return None

        # 1. Payload Minimization
        minimal_payload = self._minimize_payload(normalized_model)
        
        # 2. Skip Logic (Basic check)
        if len(minimal_payload.get('steps', [])) == 0 and len(minimal_payload.get('assertions', [])) == 0:
            logger.info("Skipping enrichment: No steps or assertions found.")
            return None

        try:
            # 3. LLM Call
            prompt = self._build_prompt(minimal_payload)
            response = self.client.chat.completions.create(
                model=self.model,
                temperature=0,
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": self._get_system_prompt()},
                    {"role": "user", "content": prompt}
                ]
            )

            enriched_data = json.loads(response.choices[0].message.content)

            # 4. Strict Validation
            validation_errors = self._validate_enriched(normalized_model, enriched_data)
            if validation_errors:
                if retry_count < 1:
                    logger.warning(f"Validation failed, retrying... Errors: {validation_errors}")
                    return self.enrich(normalized_model, retry_count + 1)
                else:
                    logger.error(f"Validation failed after retry. Errors: {validation_errors}")
                    return {
                        "enrichment_status": "LLM_CONFLICT",
                        "validation_errors": validation_errors,
                        "raw_llm_output": enriched_data
                    }

            enriched_data["enrichment_status"] = "SUCCESS"
            enriched_data["enrichment_version"] = ENRICHMENT_VERSION
            return enriched_data

        except Exception as e:
            logger.error(f"LLM Enrichment Error: {e}")
            if retry_count < 1:
                return self.enrich(normalized_model, retry_count + 1)
            return {
                "enrichment_status": "LLM_ERROR",
                "error": str(e)
            }

    def _minimize_payload(self, normalized: Dict[str, Any]) -> Dict[str, Any]:
        """Strip noise like locators and source file paths for LLM efficiency."""
        return {
            "steps": [
                {
                    "action": s.get("action"),
                    "method": s.get("method"),
                    "endpoint": s.get("endpoint"),
                    "value": s.get("value")
                } for s in normalized.get("steps", [])
            ],
            "assertions": [
                {
                    "operator": a.get("operator"),
                    "left": a.get("left"),
                    "right": a.get("right"),
                    "condition": a.get("condition")
                } for a in normalized.get("assertions", [])
            ],
            "lifecycle": normalized.get("lifecycle_hooks", []),
            "control_flow": normalized.get("control_flow", [])
        }

    def _get_system_prompt(self) -> str:
        return """You are enhancing a canonical test intent model.
Rules:
- Do NOT add, remove, or modify steps.
- Do NOT modify locators or values.
- Only provide semantic metadata: feature_label, test_type, risk_flags, step_groups, step_annotations.
- Use step indices to reference original steps in step_groups.
- Classify test_type as one of: CRUD_CREATE, CRUD_READ, CRUD_UPDATE, CRUD_DELETE, AUTH, VALIDATION, API_INTEGRATION, UI_NAV.
- Keep output strictly in valid JSON format."""

    def _build_prompt(self, minimal_payload: Dict[str, Any]) -> str:
        return f"""Enhance this test intent model with semantic metadata:
{json.dumps(minimal_payload, indent=2)}

Return a JSON object with:
{{
  "feature_label": "Title of the test case",
  "test_type": "Classification",
  "risk_flags": ["list", "of", "detected", "risks"],
  "step_groups": [
    {{
      "group": "Group Name (e.g. Request/Verification)",
      "steps": [0, 1]
    }}
  ],
  "step_annotations": [
    {{
      "index": 0,
      "label": "Brief descriptive label for step 0"
    }}
  ]
}}"""

    def _validate_enriched(self, original: Dict[str, Any], enriched: Dict[str, Any]) -> List[str]:
        """Guardrails: ensure LLM didn't mutate core intent."""
        errors = []
        
        # 1. Step count check
        orig_steps = len(original.get("steps", []))
        
        # Check step_annotations count
        annotations = enriched.get("step_annotations", [])
        if len(annotations) != orig_steps:
                errors.append(f"Step count mismatch: expected {orig_steps}, got {len(annotations)} annotations")
        
        # Check if all indices are present and valid
        indices = [a.get("index") for a in annotations if isinstance(a, dict)]
        if sorted(indices) != list(range(orig_steps)):
            errors.append("Step indices in annotations are invalid or incomplete")

        # 2. Check step_groups coverage
        grouped_indices = []
        for group in enriched.get("step_groups", []):
            grouped_indices.extend(group.get("steps", []))
        
        if len(set(grouped_indices)) != orig_steps:
             errors.append("Step groups do not cover all original steps unique indices")
             
        # Verification that no core mutations happened (since we didn't send full steps, we check result structure)
        if "steps" in enriched:
            # LLM should not have returned a "steps" array with content, if it did, it might have tried to rewrite
            if isinstance(enriched["steps"], list) and len(enriched["steps"]) > 0:
                # If it's different from original (which we didn't even send full), it's a risk
                errors.append("LLM returned 'steps' array which was not requested and may imply rewrite")

        return errors

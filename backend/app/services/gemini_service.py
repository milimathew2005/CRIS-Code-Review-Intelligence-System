import json
import logging
from typing import Dict, Any
from google import genai
from google.genai import types
from backend.app.core.config import settings
from backend.app.schemas.review import ReviewReport

logger = logging.getLogger("cris.gemini_service")

class GeminiReviewService:
    """
    Service responsible for interacting with the Gemini API.
    - Utilizes the modern, unified `google-genai` client constructor.
    - Prompts Gemini 2.5 Flash using structured schema-enforcement parameters.
    - Catches and formats API timeouts, empty bodies, and schema validation failures.
    """
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or settings.GEMINI_API_KEY
        self.client = None
        
        if self.api_key:
            # Instantiate next-generation client
            self.client = genai.Client(api_key=self.api_key)
            logger.debug("Successfully initialized google-genai Client context")
        else:
            logger.warning("GEMINI_API_KEY not set. GeminiReviewService operating in mock fallback mode.")

    def generate_code_review(self, file_context: Dict[str, Any]) -> ReviewReport:
        """
        Orchestrates prompt creation, calls Gemini 2.5 Flash with response_schema
        constraint, and returns a verified ReviewReport.
        """
        filename = file_context.get("file", "unknown")
        
        if not self.client:
            # Return helper issue indicating missing key configuration
            return ReviewReport(
                filename=filename,
                issues=[
                    {
                        "issue_type": "Style",
                        "severity": "Low",
                        "line_number": 1,
                        "description": "Gemini API credentials not configured. Local verification mockup returned.",
                        "suggested_fix": "Add GEMINI_API_KEY variable settings in your local environment."
                    }
                ]
            )

        # System instructions enforcing categorization boundaries
        system_instruction = (
            "You are a Senior Code Reviewer named CRIS (Code Review Intelligence System).\n"
            "Analyze the provided pull request file context changes (diffs + AST metadata) and report code issues.\n\n"
            "STRICT RULES:\n"
            "1. Issue Categories: You must ONLY assign one of these values:\n"
            "   - 'Security': Vulnerabilities, secrets leaks, authentication breaches.\n"
            "   - 'Logic': Syntax errors, incorrect conditions, memory pointer bugs, null refs.\n"
            "   - 'Performance': High Big-O time complexity, resource leaks, unclosed streams.\n"
            "   - 'Style': Violations of formatting (PEP8), missing docstrings, complex constructs.\n"
            "2. Severities: You must ONLY select from: 'Critical', 'High', 'Medium', 'Low'.\n"
            "3. Outputs: Conforms strictly to the JSON schema. No free text, no markdown prefixes, no explanations."
        )

        user_prompt = (
            f"Review this file change metadata context:\n"
            f"{json.dumps(file_context, indent=2)}\n\n"
            f"Locate and describe potential code issues."
        )

        try:
            # Generate structured code review payload
            response = self.client.models.generate_content(
                model=settings.GEMINI_MODEL,
                contents=user_prompt,
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    response_mime_type="application/json",
                    response_schema=ReviewReport,
                    temperature=0.1  # Low temperature for highly deterministic review outputs
                )
            )

            if not response.text:
                raise ValueError("Received empty content generation response from Gemini API.")

            # Load response content and parse into Pydantic schema model
            parsed_data = json.loads(response.text)
            return ReviewReport(**parsed_data)

        except Exception as e:
            logger.error(f"Gemini generation or validation error: {str(e)}")
            # Return structured error model
            return ReviewReport(
                filename=filename,
                issues=[
                    {
                        "issue_type": "Logic",
                        "severity": "High",
                        "line_number": 1,
                        "description": f"Gemini API review execution failed: {str(e)}",
                        "suggested_fix": "Check local configuration or credentials settings."
                    }
                ]
            )

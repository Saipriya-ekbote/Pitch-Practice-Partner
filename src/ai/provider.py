"""
AI Provider abstraction, Demo Mode implementation, and Real Provider foundation for Pitch Practice Partner.
"""

import json
import logging
import os
import re
import urllib.request
import urllib.error
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)


@dataclass
class ProviderStatus:
    """Status metadata for an AI provider connection."""
    name: str
    is_connected: bool
    is_demo: bool
    status_message: str
    model_name: str = "demo-deterministic"


class AIProvider(ABC):
    """
    Abstract Base Class for AI conversational role-play providers.
    """

    @abstractmethod
    def get_status(self) -> ProviderStatus:
        """Return the current connection and operational status of the provider."""
        pass

    @abstractmethod
    def generate_roleplay_response(
        self,
        system_prompt: str,
        conversation_history: List[Dict[str, str]],
        user_message: str,
        scenario_context: Dict[str, Any],
    ) -> str:
        """
        Generate a persona-driven role-play response to the candidate's input.
        
        Args:
            system_prompt: Persona background, role, behavioral rules, and constraints.
            conversation_history: List of preceding turn dictionaries [{"role": ..., "content": ...}].
            user_message: The candidate's latest response.
            scenario_context: Metadata including persona details, scenario goals, difficulty, and turn count.
            
        Returns:
            The AI persona's conversational follow-up or reaction.
        """
        pass

    def generate_response(self, prompt: str, context: Optional[Dict[str, Any]] = None) -> str:
        """Backwards-compatible wrapper for single-prompt calls."""
        ctx = context or {}
        return self.generate_roleplay_response(
            system_prompt=ctx.get("system_prompt", ""),
            conversation_history=ctx.get("conversation_history", []),
            user_message=prompt,
            scenario_context=ctx,
        )


class DemoProvider(AIProvider):
    """
    Deterministic, context-aware Demo Mode provider for testing and development.
    
    Generates dynamic persona-specific responses by inspecting the user's actual input,
    the persona's concerns and objection tendencies, and the scenario objectives.
    Does NOT make external API calls or require credentials.
    """

    def __init__(self) -> None:
        self.provider_name = "Demo Mode Provider"

    def get_status(self) -> ProviderStatus:
        """Return the status of the demo provider."""
        return ProviderStatus(
            name="Demo Mode",
            is_connected=False,
            is_demo=True,
            status_message="Demo Mode — AI provider running deterministically without API key.",
            model_name="demo-rule-engine",
        )

    def generate_roleplay_response(
        self,
        system_prompt: str,
        conversation_history: List[Dict[str, str]],
        user_message: str,
        scenario_context: Dict[str, Any],
    ) -> str:
        """
        Generate a dynamic, context-aware demo response reflecting the selected persona,
        the candidate's answer, and the current conversation turn.
        """
        if not user_message or not user_message.strip():
            return "[DEMO MODE] I didn't catch that. Could you please share your response?"

        user_text = user_message.strip()
        user_lower = user_text.lower()

        persona_name = scenario_context.get("persona_name", "Interviewer")
        persona_role = scenario_context.get("persona_role", "Evaluator")
        difficulty = scenario_context.get("difficulty", "Intermediate")
        concerns = scenario_context.get("concerns", [])
        objections = scenario_context.get("objection_types", [])
        turn = scenario_context.get("turn_number", len(conversation_history) // 2 + 1)
        mode = scenario_context.get("mode", "")

        # 1. Check for very brief / vague answers
        if len(user_text.split()) < 6:
            return (
                f"[DEMO MODE] As the {persona_role}, that feels rather brief. "
                f"Could you elaborate with concrete details and explain your underlying rationale?"
            )

        # 2. Contextual keyword & theme detection matching persona concerns
        if any(w in user_lower for w in ["cost", "price", "budget", "roi", "expensive", "investment", "financial"]):
            if "persona_pitch" in str(scenario_context.get("persona_id", "")):
                return (
                    f"[DEMO MODE] You mentioned budget and financial impact. As {persona_name}, "
                    f"what is the expected payback timeline, and how do you calculate the return on investment?"
                )
            return (
                f"[DEMO MODE] You brought up cost considerations. How do you balance financial constraints "
                f"with long-term operational quality?"
            )

        if any(w in user_lower for w in ["security", "privacy", "leakage", "compliance", "gdpr", "vulnerability"]):
            return (
                f"[DEMO MODE] Regarding data security and compliance, what specific safeguards or validation "
                f"protocols do you implement to prevent unauthorized access?"
            )

        if any(w in user_lower for w in ["machine learning", "ml", "ai", "model", "llm", "neural", "deep learning"]):
            return (
                f"[DEMO MODE] You highlighted machine learning capabilities. How do you validate model accuracy, "
                f"and how does your solution handle hallucinations or non-deterministic edge cases?"
            )

        if any(w in user_lower for w in ["architecture", "scale", "latency", "distributed", "cache", "redis", "database"]):
            return (
                f"[DEMO MODE] Looking at the architectural trade-offs you described, how would this design "
                f"scale under a 10x sudden traffic spike, and what is your failover strategy?"
            )

        if any(w in user_lower for w in ["conflict", "disagreement", "team", "engineer", "deadline", "delay", "manage"]):
            return (
                f"[DEMO MODE] That addresses team dynamics. How did you ensure all stakeholders remained aligned, "
                f"and what specific measurable outcome resulted from your intervention?"
            )

        # 3. Dynamic reaction based on difficulty level & persona concerns
        primary_concern = concerns[0] if concerns else "clarity and execution rigor"
        primary_objection = objections[0] if objections else "insufficient evidence"

        if difficulty == "Advanced":
            return (
                f"[DEMO MODE] You stated: \"{user_text[:60]}...\". As {persona_name} ({persona_role}), "
                f"I must push back on that assumption regarding {primary_concern.lower()}. "
                f"What concrete evidence or benchmarks support your position against {primary_objection.lower()}?"
            )
        elif difficulty == "Beginner":
            return (
                f"[DEMO MODE] Thank you for explaining that. Building on what you just shared about \"{user_text[:40]}...\", "
                f"how would you summarize the primary takeaway in one key point?"
            )
        else:  # Intermediate
            return (
                f"[DEMO MODE] I see your point regarding your approach. However, focusing on {primary_concern.lower()}, "
                f"how would you handle unforeseen complications or alternative constraints?"
            )


class RealAIProvider(AIProvider):
    """
    Real AI Provider communicating with LLM endpoints (OpenAI, Gemini, Anthropic, or compatible HTTP APIs).
    
    Reads credentials from environment variables securely and provides robust error handling.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        provider_name: Optional[str] = None,
        model_name: Optional[str] = None,
        base_url: Optional[str] = None,
    ) -> None:
        self.provider_name = provider_name or os.getenv("AI_PROVIDER", "openai").lower()
        self.api_key = api_key or os.getenv("AI_API_KEY", "")
        self.model_name = model_name or os.getenv("AI_MODEL", "gpt-4o-mini")
        self.base_url = base_url or os.getenv("AI_BASE_URL", "https://api.openai.com/v1")
        self._demo_fallback = DemoProvider()

    def get_status(self) -> ProviderStatus:
        """Return operational status of the real provider."""
        if not self.api_key or not self.api_key.strip():
            return ProviderStatus(
                name=f"{self.provider_name.capitalize()} (Unconfigured)",
                is_connected=False,
                is_demo=True,
                status_message="No API key found in environment (AI_API_KEY). Running with Demo Provider fallback.",
                model_name=self.model_name,
            )

        masked_key = self.api_key[:4] + "..." + self.api_key[-3:] if len(self.api_key) > 8 else "***"
        return ProviderStatus(
            name=f"{self.provider_name.capitalize()}",
            is_connected=True,
            is_demo=False,
            status_message=f"Connected to {self.provider_name} API (Key: {masked_key})",
            model_name=self.model_name,
        )

    def generate_roleplay_response(
        self,
        system_prompt: str,
        conversation_history: List[Dict[str, str]],
        user_message: str,
        scenario_context: Dict[str, Any],
    ) -> str:
        """
        Execute API request to LLM provider. Falls back gracefully to DemoProvider upon failure.
        """
        if not self.api_key or not self.api_key.strip():
            logger.info("No API key configured for RealAIProvider; using DemoProvider fallback.")
            return self._demo_fallback.generate_roleplay_response(
                system_prompt, conversation_history, user_message, scenario_context
            )

        messages = [{"role": "system", "content": system_prompt}]
        for msg in conversation_history:
            messages.append({"role": msg.get("role", "user"), "content": msg.get("content", "")})
        messages.append({"role": "user", "content": user_message})

        try:
            # Standard OpenAI-compatible chat completions endpoint
            url = f"{self.base_url.rstrip('/')}/chat/completions"
            payload = json.dumps({
                "model": self.model_name,
                "messages": messages,
                "temperature": 0.7,
                "max_tokens": 350,
            }).encode("utf-8")

            req = urllib.request.Request(
                url,
                data=payload,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {self.api_key}",
                },
                method="POST",
            )

            with urllib.request.urlopen(req, timeout=20) as resp:
                result = json.loads(resp.read().decode("utf-8"))
                choice = result.get("choices", [{}])[0]
                content = choice.get("message", {}).get("content", "").strip()

                if not content:
                    logger.warning("Received empty content from AI provider.")
                    return "[AI Service Error: Empty response received. Falling back to Demo Mode.]\n\n" + self._demo_fallback.generate_roleplay_response(
                        system_prompt, conversation_history, user_message, scenario_context
                    )
                return content

        except urllib.error.HTTPError as e:
            logger.error("HTTP error calling AI provider: %s", e)
            return f"[AI Provider Connection Error ({e.code})]\n\n" + self._demo_fallback.generate_roleplay_response(
                system_prompt, conversation_history, user_message, scenario_context
            )
        except Exception as e:
            logger.error("Unexpected error communicating with AI provider: %s", e)
            return f"[AI Provider Error: {type(e).__name__}]\n\n" + self._demo_fallback.generate_roleplay_response(
                system_prompt, conversation_history, user_message, scenario_context
            )


def get_ai_provider() -> AIProvider:
    """
    Factory function returning the active AI provider based on environment variables.
    Defaults safely to DemoProvider if no valid API key is present.
    """
    provider_type = os.getenv("AI_PROVIDER", "demo").strip().lower()
    api_key = os.getenv("AI_API_KEY", "").strip()

    if provider_type != "demo" and api_key:
        return RealAIProvider(api_key=api_key, provider_name=provider_type)
    return DemoProvider()

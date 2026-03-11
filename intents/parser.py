#!/usr/bin/env python3
"""Intent parser — LLM classification via local Ollama with fallback."""

import json
import httpx
import asyncio
from typing import Optional

from .prompts import (
    ParsedIntent,
    IntentType,
    RiskLevel,
    INTENT_RISK_MAP,
    CONFIRM_REQUIRED,
    SYSTEM_PROMPT,
)

# Ollama config — local qwen2.5-coder via Ollama
OLLAMA_URL   = "http://localhost:11434/api/chat"
OLLAMA_MODEL = "qwen2.5-coder:7b-instruct-q4_K_M"
TIMEOUT_S    = 30


def _fallback_intent(user_input: str) -> ParsedIntent:
    """
    Regex-free keyword fallback when Ollama is unavailable.
    Keeps vault operable even with no LLM.
    """
    text = user_input.lower()

    if any(w in text for w in ["give", "grant", "access", "allow"]):
        intent = IntentType.GRANT_ACCESS
    elif any(w in text for w in ["revoke", "remove access", "deny"]):
        intent = IntentType.REVOKE_ACCESS
    elif any(w in text for w in ["who", "touched", "accessed", "audit", "log"]):
        intent = IntentType.AUDIT_QUERY
    elif any(w in text for w in ["rotate", "rotation"]):
        intent = IntentType.ROTATE_KEYS
    elif any(w in text for w in ["soc", "iso", "compliance", "ready", "audit report"]):
        intent = IntentType.COMPLIANCE_CHECK
    elif any(w in text for w in ["suspicious", "anomaly", "unusual", "weird"]):
        intent = IntentType.ANOMALY_DETECT
    elif any(w in text for w in ["delete", "remove", "drop"]):
        intent = IntentType.SECRET_DELETE
    elif any(w in text for w in ["set", "write", "update", "store"]):
        intent = IntentType.SECRET_WRITE
    elif any(w in text for w in ["get", "read", "show", "fetch", "what is"]):
        intent = IntentType.SECRET_READ
    elif any(w in text for w in ["list", "ls", "all keys", "all secrets"]):
        intent = IntentType.SECRET_LIST
    else:
        intent = IntentType.UNKNOWN

    risk = INTENT_RISK_MAP[intent]

    return ParsedIntent(
        intent=intent.value,
        confidence=0.4,   # Low confidence — fallback path
        risk=risk.value,
        args={},
        requires_confirm=(intent in CONFIRM_REQUIRED or risk == RiskLevel.HIGH),
        summary=f"[fallback] Detected intent: {intent.value}. Args require manual confirmation.",
    )


def _validate_and_repair(raw: dict, user_input: str) -> ParsedIntent:
    """
    Validate LLM output against schema.
    Repairs missing fields rather than crashing — LLM output is untrusted.
    """
    valid_intents = {i.value for i in IntentType}
    valid_risks   = {r.value for r in RiskLevel}

    intent_str = raw.get("intent", IntentType.UNKNOWN.value)
    if intent_str not in valid_intents:
        intent_str = IntentType.UNKNOWN.value

    intent = IntentType(intent_str)

    # Risk: trust LLM but floor it at the catalog minimum for safety
    llm_risk   = raw.get("risk", "low")
    catalog_risk = INTENT_RISK_MAP[intent].value
    risk_order = {"low": 0, "medium": 1, "high": 2}

    # Always use the higher of LLM-declared and catalog minimum
    if llm_risk not in valid_risks:
        llm_risk = catalog_risk
    resolved_risk = llm_risk if risk_order[llm_risk] >= risk_order[catalog_risk] else catalog_risk

    confidence = float(raw.get("confidence", 0.0))
    # Low confidence → escalate to confirm regardless of intent type
    requires_confirm = (
        raw.get("requires_confirm", False)
        or intent in CONFIRM_REQUIRED
        or confidence < 0.7
    )

    return ParsedIntent(
        intent=intent.value,
        confidence=confidence,
        risk=resolved_risk,
        args=raw.get("args", {}),
        requires_confirm=requires_confirm,
        summary=raw.get("summary", f"Execute {intent.value} based on: '{user_input}'"),
    )


async def parse_intent(user_input: str) -> ParsedIntent:
    """
    Parse natural language into a structured vault intent.

    Hits local Ollama (qwen2.5-coder). Falls back to keyword
    matching if Ollama is down — vault always stays operable.

    Args:
        user_input: Raw natural language from user (e.g. "give john access to staging")

    Returns:
        ParsedIntent dict — always valid, never raises
    """
    messages = [
        {"role": "user", "content": user_input}
    ]

    try:
        async with httpx.AsyncClient(timeout=TIMEOUT_S) as client:
            resp = await client.post(
                OLLAMA_URL,
                json={
                    "model":    OLLAMA_MODEL,
                    "messages": messages,
                    "system":   SYSTEM_PROMPT,
                    "stream":   False,
                    "options": {
                        "temperature": 0.0,   # Deterministic — this is a classifier
                        "num_predict": 256,
                    }
                }
            )
            resp.raise_for_status()

        data = resp.json()
        content = data["message"]["content"].strip()

        # Strip markdown fences if model wrapped output
        if content.startswith("```"):
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
            content = content.strip()

        raw = json.loads(content)
        return _validate_and_repair(raw, user_input)

    except httpx.ConnectError:
        # Ollama not running — silent fallback, vault stays up
        return _fallback_intent(user_input)

    except httpx.TimeoutException:
        return _fallback_intent(user_input)

    except (json.JSONDecodeError, KeyError):
        # LLM returned garbage — fallback
        return _fallback_intent(user_input)

    except Exception:
        return _fallback_intent(user_input)


def parse_intent_sync(user_input: str) -> ParsedIntent:
    """Sync wrapper for CLI contexts that aren't async."""
    return asyncio.run(parse_intent(user_input))

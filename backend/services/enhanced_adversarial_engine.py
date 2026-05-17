"""
Enhanced Layer 3 — Interactive Multi-Agent Debate Engine.

Runs a three-agent debate (Risk, Defense, Verdict) with explicit reasoning,
rebuttals, and real-time streaming of agent thought processes.
"""

from __future__ import annotations

import asyncio
import json
import logging
import time
from typing import Dict, List, Optional, Tuple

from backend.models.schemas import (
    Clause, ClauseCategory, DefenseAgentOutput,
    RiskAgentOutput, Severity, VerdictAgentOutput,
    ConsequenceChain, NegotiationSuggestion, BenchmarkComparison
)
from backend.utils.gemini_client import call_gemini

logger = logging.getLogger("lexguard.enhanced_adversarial_engine")

# Categories that trigger adversarial analysis
ADVERSARIAL_CATEGORIES: set[ClauseCategory] = {
    ClauseCategory.IP_TRANSFER, ClauseCategory.NON_COMPETE,
    ClauseCategory.ARBITRATION, ClauseCategory.LIABILITY_LIMITATION,
    ClauseCategory.DATA_COLLECTION, ClauseCategory.AUTO_RENEWAL,
    ClauseCategory.PAYMENT_PENALTY, ClauseCategory.INDEMNIFICATION,
    ClauseCategory.TERMINATION, ClauseCategory.JURISDICTION,
}

# Enhanced prompts with explicit reasoning requirements
_RISK_AGENT_PROMPT: str = """You are a strict legal adversary (Risk Agent). 
Interpret the following contract clause in the worst possible way for the person signing it.

**YOUR TASK:**
1. Identify every way this clause could be exploited against the signer
2. Reference exact phrases from the clause
3. Explain your reasoning step-by-step
4. Consider legal precedents and enforcement mechanisms
5. Think like a lawyer looking to maximize client liability

**OUTPUT FORMAT (JSON):**
{
    "risk_position": "Your adversarial interpretation",
    "key_phrases": ["exact phrase 1", "exact phrase 2"],
    "worst_case": "Worst-case scenario description",
    "reasoning": "Step 1: Identify ambiguous terms... Step 2: Analyze enforcement... Step 3: Consider precedents...",
    "confidence": 0.0-1.0,
    "legal_basis": "Legal principles supporting your interpretation"
}

Return only JSON."""

_DEFENSE_AGENT_PROMPT: str = """You are a legal defense counsel (Defense Agent).
Interpret the following contract clause in the most favorable way for the person signing it.

**YOUR TASK:**
1. Find every reasonable interpretation that protects the signer's interests
2. Reference exact protective phrases from the clause
3. Explain your reasoning step-by-step
4. Consider mitigating factors and legal protections
5. Think like a defense attorney minimizing client exposure

**OUTPUT FORMAT (JSON):**
{
    "defense_position": "Your favorable interpretation",
    "favorable_phrases": ["protective phrase 1", "protective phrase 2"],
    "best_case": "Best-case scenario description",
    "reasoning": "Step 1: Identify protective language... Step 2: Analyze limitations... Step 3: Consider defenses...",
    "confidence": 0.0-1.0,
    "legal_basis": "Legal principles supporting your interpretation"
}

Return only JSON."""

_VERDICT_AGENT_PROMPT: str = """You are a neutral legal analyst (Verdict Agent).
You received two opposing interpretations of a contract clause.

**YOUR TASK:**
1. Synthesize both perspectives into a final verdict
2. Assign severity (HIGH/MEDIUM/LOW) based on actual risk
3. Provide confidence score (0.0-1.0)
4. Explain in plain English (2-3 sentences)
5. Show your reasoning process explicitly
6. Consider real-world enforceability

**INPUT:**
- Original clause: {clause_text}
- Risk Agent position: {risk_position}
- Risk Agent reasoning: {risk_reasoning}
- Defense Agent position: {defense_position}
- Defense Agent reasoning: {defense_reasoning}

**OUTPUT FORMAT (JSON):**
{
    "verdict": "Your synthesized verdict",
    "severity": "HIGH|MEDIUM|LOW",
    "confidence": 0.0-1.0,
    "risk_category": "Category label",
    "plain_english": "Plain English explanation",
    "reasoning": "Step 1: Weigh risk arguments... Step 2: Consider defenses... Step 3: Assess real impact...",
    "key_findings": ["Finding 1", "Finding 2"],
    "recommendation": "What the signer should do"
}

Return only JSON."""

_REBUTTAL_PROMPT: str = """You are engaged in a legal debate about a contract clause.
You just heard the opposing agent's argument. Provide a rebuttal.

**YOUR TASK:**
1. Address specific points from the opposing argument
2. Strengthen your own position with additional evidence
3. Identify weaknesses in the opposing argument
4. Maintain your role perspective (Risk/Defense)

**OPPOSING ARGUMENT:**
{opposing_argument}

**YOUR CURRENT POSITION:**
{current_position}

**OUTPUT FORMAT (JSON):**
{
    "rebuttal": "Your rebuttal argument",
    "strengthened_position": "Your position after considering rebuttal",
    "new_evidence": ["Additional evidence 1", "Additional evidence 2"],
    "opposition_weaknesses": ["Weakness 1", "Weakness 2"],
    "reasoning": "Step-by-step rebuttal reasoning"
}

Return only JSON."""

_CONSEQUENCE_SIMULATION_PROMPT: str = """You are a consequence simulation engine.
Simulate the real-world consequences of signing a risky contract clause.

**INPUT:**
- Clause: {clause_text}
- Risk severity: {severity}
- Risk position: {risk_position}
- Signer profile: {signer_profile}

**YOUR TASK:**
1. Simulate trigger conditions
2. Map immediate consequences
3. Project downstream impacts
4. Describe worst-case scenario
5. Estimate probability and financial impact

**OUTPUT FORMAT (JSON):**
{
    "trigger_condition": "What triggers the negative outcome",
    "immediate_consequence": "What happens immediately",
    "downstream_impact": "Downstream effects over time",
    "worst_case_scenario": "Worst possible real-world outcome",
    "probability_estimate": "Low/Medium/High",
    "financial_impact_range": "$X - $Y",
    "timeline": "When consequences might occur",
    "mitigation_strategies": ["Strategy 1", "Strategy 2"]
}

Return only JSON."""

_PLAIN_ENGLISH_TRANSLATOR_PROMPT: str = """You are a legal jargon translator.
Translate complex legal language into plain, understandable English.

**INPUT:**
- Legal text: {legal_text}
- Context: {context}

**YOUR TASK:**
1. Identify and explain legal terms
2. Break down complex sentences
3. Provide simple analogies
4. Highlight what it means for the signer

**OUTPUT FORMAT (JSON):**
{
    "plain_translation": "Simple English version",
    "key_terms_explained": {
        "term1": "explanation1",
        "term2": "explanation2"
    },
    "analogies": ["Analogy 1", "Analogy 2"],
    "what_it_means": "What this means for you",
    "watch_out_for": ["Red flag 1", "Red flag 2"]
}

Return only JSON."""


def should_analyze(clause: Clause) -> bool:
    """Check if a clause should undergo enhanced adversarial analysis.

    Args:
        clause: Classified clause.

    Returns:
        True if clause qualifies for analysis.
    """
    if clause.category is None:
        return False
    return clause.category in ADVERSARIAL_CATEGORIES


async def run_risk_agent_with_reasoning(clause_text: str) -> Tuple[RiskAgentOutput, Dict]:
    """Run the Risk Agent with explicit reasoning display.

    Args:
        clause_text: The clause text to analyze.

    Returns:
        Tuple of (parsed output, raw reasoning data).
    """
    result = await call_gemini(
        prompt=clause_text,
        system_prompt=_RISK_AGENT_PROMPT,
        model_name="gemini-1.5-pro",
        temperature=0.4,
    )
    
    risk_output = RiskAgentOutput(
        risk_position=result.get("risk_position", ""),
        key_phrases=result.get("key_phrases", []),
        worst_case=result.get("worst_case", ""),
        reasoning=result.get("reasoning", ""),
    )
    
    return risk_output, result


async def run_defense_agent_with_reasoning(clause_text: str) -> Tuple[DefenseAgentOutput, Dict]:
    """Run the Defense Agent with explicit reasoning display.

    Args:
        clause_text: The clause text to analyze.

    Returns:
        Tuple of (parsed output, raw reasoning data).
    """
    result = await call_gemini(
        prompt=clause_text,
        system_prompt=_DEFENSE_AGENT_PROMPT,
        model_name="gemini-1.5-pro",
        temperature=0.4,
    )
    
    defense_output = DefenseAgentOutput(
        defense_position=result.get("defense_position", ""),
        favorable_phrases=result.get("favorable_phrases", []),
        best_case=result.get("best_case", ""),
        reasoning=result.get("reasoning", ""),
    )
    
    return defense_output, result


async def run_interactive_debate(
    clause_text: str,
    max_rounds: int = 2
) -> Tuple[RiskAgentOutput, DefenseAgentOutput, List[Dict]]:
    """Run an interactive debate between Risk and Defense agents.

    Args:
        clause_text: The clause text to debate.
        max_rounds: Maximum number of debate rounds.

    Returns:
        Tuple of (final risk output, final defense output, debate history).
    """
    debate_history = []
    
    # Initial positions
    risk_output, risk_raw = await run_risk_agent_with_reasoning(clause_text)
    defense_output, defense_raw = await run_defense_agent_with_reasoning(clause_text)
    
    debate_history.append({
        "round": 0,
        "risk": risk_raw,
        "defense": defense_raw,
        "type": "initial_positions"
    })
    
    # Debate rounds
    for round_num in range(1, max_rounds + 1):
        # Risk agent rebuttal
        risk_rebuttal_prompt = _REBUTTAL_PROMPT.format(
            opposing_argument=defense_output.defense_position,
            current_position=risk_output.risk_position
        )
        
        risk_rebuttal = await call_gemini(
            prompt=clause_text,
            system_prompt=risk_rebuttal_prompt,
            model_name="gemini-1.5-pro",
            temperature=0.3,
        )
        
        # Update risk position with rebuttal
        risk_output.risk_position = risk_rebuttal.get("strengthened_position", risk_output.risk_position)
        risk_output.reasoning += f"\n\nRound {round_num} Rebuttal: {risk_rebuttal.get('rebuttal', '')}"
        
        # Defense agent rebuttal
        defense_rebuttal_prompt = _REBUTTAL_PROMPT.format(
            opposing_argument=risk_output.risk_position,
            current_position=defense_output.defense_position
        )
        
        defense_rebuttal = await call_gemini(
            prompt=clause_text,
            system_prompt=defense_rebuttal_prompt,
            model_name="gemini-1.5-pro",
            temperature=0.3,
        )
        
        # Update defense position with rebuttal
        defense_output.defense_position = defense_rebuttal.get("strengthened_position", defense_output.defense_position)
        defense_output.reasoning += f"\n\nRound {round_num} Rebuttal: {defense_rebuttal.get('rebuttal', '')}"
        
        debate_history.append({
            "round": round_num,
            "risk_rebuttal": risk_rebuttal,
            "defense_rebuttal": defense_rebuttal,
            "type": "rebuttal"
        })
    
    return risk_output, defense_output, debate_history


async def run_verdict_agent_with_reasoning(
    clause_text: str,
    risk_output: RiskAgentOutput,
    defense_output: DefenseAgentOutput,
    debate_history: List[Dict]
) -> Tuple[VerdictAgentOutput, Dict]:
    """Run the Verdict Agent with access to full debate history.

    Args:
        clause_text: Original clause text.
        risk_output: Final Risk Agent output.
        defense_output: Final Defense Agent output.
        debate_history: Complete debate history.

    Returns:
        Tuple of (parsed verdict, raw reasoning data).
    """
    verdict_prompt = _VERDICT_AGENT_PROMPT.format(
        clause_text=clause_text,
        risk_position=risk_output.risk_position,
        risk_reasoning=risk_output.reasoning,
        defense_position=defense_output.defense_position,
        defense_reasoning=defense_output.reasoning
    )
    
    result = await call_gemini(
        prompt=json.dumps({"debate_history": debate_history}),
        system_prompt=verdict_prompt,
        model_name="gemini-1.5-pro",
        temperature=0.2,
    )
    
    verdict_output = VerdictAgentOutput(
        verdict=result.get("verdict", ""),
        severity=Severity(result.get("severity", "MEDIUM")),
        confidence=result.get("confidence", 0.5),
        risk_category=result.get("risk_category", "General"),
        plain_english=result.get("plain_english", ""),
        reasoning=result.get("reasoning", ""),
    )
    
    return verdict_output, result


async def simulate_consequences(
    clause_text: str,
    severity: Severity,
    risk_position: str,
    signer_profile: Dict
) -> Tuple[ConsequenceChain, Dict]:
    """Simulate real-world consequences of signing a risky clause.

    Args:
        clause_text: The clause text.
        severity: Risk severity.
        risk_position: Risk agent's position.
        signer_profile: Dictionary with signer information.

    Returns:
        Tuple of (consequence chain, raw simulation data).
    """
    simulation_prompt = _CONSEQUENCE_SIMULATION_PROMPT.format(
        clause_text=clause_text,
        severity=severity.value,
        risk_position=risk_position,
        signer_profile=json.dumps(signer_profile)
    )
    
    result = await call_gemini(
        prompt=clause_text,
        system_prompt=simulation_prompt,
        model_name="gemini-1.5-pro",
        temperature=0.3,
    )
    
    consequence_chain = ConsequenceChain(
        trigger_condition=result.get("trigger_condition", ""),
        immediate_consequence=result.get("immediate_consequence", ""),
        downstream_impact=result.get("downstream_impact", ""),
        worst_case_scenario=result.get("worst_case_scenario", ""),
    )
    
    return consequence_chain, result


async def translate_to_plain_english(
    legal_text: str,
    context: str = "contract clause"
) -> Dict:
    """Translate legal jargon into plain English.

    Args:
        legal_text: Legal text to translate.
        context: Context of the text.

    Returns:
        Dictionary with translation and explanations.
    """
    translation_prompt = _PLAIN_ENGLISH_TRANSLATOR_PROMPT.format(
        legal_text=legal_text,
        context=context
    )
    
    result = await call_gemini(
        prompt=legal_text,
        system_prompt=translation_prompt,
        model_name="gemini-1.5-flash",
        temperature=0.1,
    )
    
    return result


async def analyze_clause_with_debate(
    clause: Clause,
    signer_profile: Optional[Dict] = None
) -> Tuple[RiskAgentOutput, DefenseAgentOutput, VerdictAgentOutput, Dict]:
    """Enhanced clause analysis with interactive debate and explicit reasoning.

    Args:
        clause: The clause to analyze.
        signer_profile: Optional signer profile for consequence simulation.

    Returns:
        Tuple of (risk output, defense output, verdict output, full analysis data).
    """
    if signer_profile is None:
        signer_profile = {"occupation": "General", "experience": "Average"}
    
    start_time = time.time()
    
    # Run interactive debate
    risk_output, defense_output, debate_history = await run_interactive_debate(
        clause.text
    )
    
    # Get verdict
    verdict_output, verdict_raw = await run_verdict_agent_with_reasoning(
        clause.text, risk_output, defense_output, debate_history
    )
    
    # Simulate consequences for high severity
    consequence_data = None
    if verdict_output.severity == Severity.HIGH:
        consequence_chain, consequence_raw = await simulate_consequences(
            clause.text, verdict_output.severity, risk_output.risk_position, signer_profile
        )
        consequence_data = consequence_raw
    
    # Translate to plain English
    translation_data = await translate_to_plain_english(clause.text)
    
    # Compile full analysis
    full_analysis = {
        "clause_id": clause.id,
        "clause_text": clause.text,
        "category": clause.category.value if clause.category else None,
        "debate_history": debate_history,
        "risk_analysis": risk_output.model_dump(),
        "defense_analysis": defense_output.model_dump(),
        "verdict_analysis": verdict_output.model_dump(),
        "verdict_raw": verdict_raw,
        "consequence_simulation": consequence_data,
        "plain_english_translation": translation_data,
        "processing_time": time.time() - start_time,
        "signer_profile_used": signer_profile
    }
    
    logger.info(json.dumps({
        "service": "enhanced_adversarial_engine",
        "clause_id": clause.id,
        "severity": verdict_output.severity.value,
        "confidence": verdict_output.confidence,
        "processing_time": round(time.time() - start_time, 2),
        "debate_rounds": len(debate_history) - 1,
        "status": "success"
    }))
    
    return risk_output, defense_output, verdict_output, full_analysis


async def stream_analysis_events(
    clause: Clause,
    signer_profile: Optional[Dict] = None
):
    """Stream analysis events for real-time frontend updates.
    
    Yields analysis events at each stage of the debate.
    """
    if signer_profile is None:
        signer_profile = {"occupation": "General", "experience": "Average"}
    
    # Initial risk analysis
    risk_output, risk_raw = await run_risk_agent_with_reasoning(clause.text)
    yield {
        "type": "agent_analysis",
        "agent": "risk",
        "stage": "initial",
        "data": risk_raw,
        "clause_id": clause.id
    }
    
    # Initial defense analysis
    defense_output, defense_raw = await run_defense_agent_with_reasoning(clause.text)
    yield {
        "type": "agent_analysis",
        "agent": "defense",
        "stage": "initial",
        "data": defense_raw,
        "clause_id": clause.id
    }
    
    # Debate rounds
    for round_num in range(1, 3):  # 2 debate rounds
        # Risk rebuttal
        risk_rebuttal_prompt = _REBUTTAL_PROMPT.format(
            opposing_argument=defense_output.defense_position,
            current_position=risk_output.risk_position
        )
        
        risk_rebuttal = await call_gemini(
            prompt=clause.text,
            system_prompt=risk_rebuttal_prompt,
            model_name="gemini-1.5-pro",
            temperature=0.3,
        )
        
        yield {
            "type": "agent_rebuttal",
            "agent": "risk",
            "round": round_num,
            "data": risk_rebuttal,
            "clause_id": clause.id
        }
        
        # Defense rebuttal
        defense_rebuttal_prompt = _REBUTTAL_PROMPT.format(
            opposing_argument=risk_output.risk_position,
            current_position=defense_output.defense_position
        )
        
        defense_rebuttal = await call_gemini(
            prompt=clause.text,
            system_prompt=defense_rebuttal_prompt,
            model_name="gemini-1.5-pro",
            temperature=0.3,
        )
        
        yield {
            "type": "agent_rebuttal",
            "agent": "defense",
            "round": round_num,
            "data": defense_rebuttal,
            "clause_id": clause.id
        }
    
    # Final verdict
    verdict_prompt = _VERDICT_AGENT_PROMPT.format(
        clause_text=clause.text,
        risk_position=risk_output.risk_position,
        risk_reasoning=risk_output.reasoning,
        defense_position=defense_output.defense_position,
        defense_reasoning=defense_output.reasoning
    )
    
    verdict_raw = await call_gemini(
        prompt=json.dumps({"final_positions": {
            "risk": risk_output.model_dump(),
            "defense": defense_output.model_dump()
        }}),
        system_prompt=verdict_prompt,
        model_name="gemini-1.5-pro",
        temperature=0.2,
    )
    
    yield {
        "type": "verdict",
        "data": verdict_raw,
        "clause_id": clause.id
    }
    
    # Plain English translation
    translation_data = await translate_to_plain_english(clause.text)
    yield {
        "type": "translation",
        "data": translation_data,
        "clause_id": clause.id
    }
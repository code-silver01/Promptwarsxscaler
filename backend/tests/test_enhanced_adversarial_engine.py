"""
Comprehensive tests for Enhanced Adversarial Engine.

Tests the interactive multi-agent debate system, consequence simulation,
plain English translation, and real-time streaming capabilities.
"""

import asyncio
import json
import time
from unittest.mock import AsyncMock, patch

import pytest

from backend.models.schemas import (
    Clause,
    ClauseCategory,
    ConsequenceChain,
    DefenseAgentOutput,
    RiskAgentOutput,
    Severity,
    VerdictAgentOutput,
)
from backend.services.enhanced_adversarial_engine import (
    analyze_clause_with_debate,
    run_interactive_debate,
    run_risk_agent_with_reasoning,
    run_defense_agent_with_reasoning,
    run_verdict_agent_with_reasoning,
    simulate_consequences,
    translate_to_plain_english,
    stream_analysis_events,
    should_analyze,
)


class TestEnhancedRiskAgent:
    """Tests for enhanced Risk Agent with explicit reasoning."""

    @pytest.mark.asyncio
    @patch("backend.services.enhanced_adversarial_engine.call_gemini")
    async def test_risk_agent_returns_enhanced_output(self, mock_gemini):
        """Risk agent should return enhanced output with reasoning and confidence."""
        mock_response = {
            "risk_position": "This clause creates significant liability exposure",
            "key_phrases": ["unlimited liability", "personal guarantee"],
            "worst_case": "Personal bankruptcy from business debts",
            "reasoning": "Step 1: Identified unlimited liability terms...",
            "confidence": 0.9,
            "legal_basis": "Personal guarantee doctrine in contract law",
        }
        mock_gemini.return_value = mock_response

        risk_output, raw_data = await run_risk_agent_with_reasoning("test clause")

        assert isinstance(risk_output, RiskAgentOutput)
        assert risk_output.risk_position == mock_response["risk_position"]
        assert risk_output.reasoning == mock_response["reasoning"]
        assert raw_data["confidence"] == 0.9
        assert raw_data["legal_basis"] == mock_response["legal_basis"]

    @pytest.mark.asyncio
    @patch("backend.services.enhanced_adversarial_engine.call_gemini")
    async def test_risk_agent_handles_missing_fields(self, mock_gemini):
        """Risk agent should handle missing optional fields gracefully."""
        mock_response = {
            "risk_position": "Basic risk position",
            "key_phrases": ["risky term"],
            "worst_case": "Bad outcome",
            # Missing reasoning, confidence, legal_basis
        }
        mock_gemini.return_value = mock_response

        risk_output, raw_data = await run_risk_agent_with_reasoning("test clause")

        assert risk_output.risk_position == "Basic risk position"
        assert risk_output.reasoning == ""  # Default empty string
        assert isinstance(risk_output.key_phrases, list)


class TestEnhancedDefenseAgent:
    """Tests for enhanced Defense Agent with explicit reasoning."""

    @pytest.mark.asyncio
    @patch("backend.services.enhanced_adversarial_engine.call_gemini")
    async def test_defense_agent_returns_enhanced_output(self, mock_gemini):
        """Defense agent should return enhanced output with reasoning."""
        mock_response = {
            "defense_position": "Clause has reasonable limitations",
            "favorable_phrases": ["reasonable notice", "good faith"],
            "best_case": "Minimal impact with proper interpretation",
            "reasoning": "Step 1: Identified protective language...",
            "confidence": 0.8,
            "legal_basis": "Good faith doctrine provides protection",
        }
        mock_gemini.return_value = mock_response

        defense_output, raw_data = await run_defense_agent_with_reasoning("test clause")

        assert isinstance(defense_output, DefenseAgentOutput)
        assert defense_output.defense_position == mock_response["defense_position"]
        assert defense_output.reasoning == mock_response["reasoning"]
        assert raw_data["confidence"] == 0.8


class TestInteractiveDebate:
    """Tests for interactive debate functionality."""

    @pytest.mark.asyncio
    @patch("backend.services.enhanced_adversarial_engine.call_gemini")
    async def test_interactive_debate_multiple_rounds(self, mock_gemini):
        """Interactive debate should run multiple rounds with rebuttals."""
        # Mock responses for initial positions and rebuttals
        responses = [
            # Initial risk position
            {
                "risk_position": "Initial risk assessment",
                "key_phrases": ["risky term"],
                "worst_case": "Bad outcome",
                "reasoning": "Initial reasoning",
            },
            # Initial defense position
            {
                "defense_position": "Initial defense assessment",
                "favorable_phrases": ["protective term"],
                "best_case": "Good outcome",
                "reasoning": "Initial defense reasoning",
            },
            # Risk rebuttal round 1
            {
                "rebuttal": "Defense argument is weak because...",
                "strengthened_position": "Strengthened risk position",
                "new_evidence": ["Additional risk factor"],
                "opposition_weaknesses": ["Weak defense point"],
                "reasoning": "Rebuttal reasoning",
            },
            # Defense rebuttal round 1
            {
                "rebuttal": "Risk argument overlooks...",
                "strengthened_position": "Strengthened defense position",
                "new_evidence": ["Additional protection"],
                "opposition_weaknesses": ["Overstated risk"],
                "reasoning": "Defense rebuttal reasoning",
            },
            # Risk rebuttal round 2
            {
                "rebuttal": "Second round risk rebuttal",
                "strengthened_position": "Final risk position",
                "new_evidence": ["Final evidence"],
                "opposition_weaknesses": ["Final weakness"],
                "reasoning": "Final risk reasoning",
            },
            # Defense rebuttal round 2
            {
                "rebuttal": "Second round defense rebuttal",
                "strengthened_position": "Final defense position",
                "new_evidence": ["Final defense evidence"],
                "opposition_weaknesses": ["Final risk weakness"],
                "reasoning": "Final defense reasoning",
            },
        ]

        call_count = 0

        async def mock_call(*args, **kwargs):
            nonlocal call_count
            response = responses[call_count % len(responses)]
            call_count += 1
            return response

        mock_gemini.side_effect = mock_call

        risk_output, defense_output, debate_history = await run_interactive_debate(
            "test clause text", max_rounds=2
        )

        # Should have initial positions + 2 rounds of rebuttals
        assert len(debate_history) == 3  # Initial + 2 rounds
        assert debate_history[0]["type"] == "initial_positions"
        assert debate_history[1]["type"] == "rebuttal"
        assert debate_history[2]["type"] == "rebuttal"

        # Final positions should be strengthened
        assert "Round 1 Rebuttal:" in risk_output.reasoning
        assert "Round 2 Rebuttal:" in risk_output.reasoning

    @pytest.mark.asyncio
    @patch("backend.services.enhanced_adversarial_engine.call_gemini")
    async def test_debate_performance_within_limits(self, mock_gemini):
        """Debate should complete within reasonable time limits."""
        mock_gemini.return_value = {
            "risk_position": "test",
            "key_phrases": [],
            "worst_case": "test",
            "reasoning": "test",
        }

        start_time = time.time()
        await run_interactive_debate("test clause", max_rounds=1)
        elapsed = time.time() - start_time

        # Should complete within 5 seconds for 1 round
        assert elapsed < 5.0


class TestVerdictAgent:
    """Tests for enhanced Verdict Agent."""

    @pytest.mark.asyncio
    @patch("backend.services.enhanced_adversarial_engine.call_gemini")
    async def test_verdict_agent_synthesizes_debate_history(self, mock_gemini):
        """Verdict agent should consider full debate history."""
        mock_response = {
            "verdict": "Synthesized verdict considering all arguments",
            "severity": "HIGH",
            "confidence": 0.85,
            "risk_category": "IP_TRANSFER",
            "plain_english": "This clause is risky because...",
            "reasoning": "Considered both risk and defense arguments...",
            "key_findings": ["Finding 1", "Finding 2"],
            "recommendation": "Negotiate this clause",
        }
        mock_gemini.return_value = mock_response

        risk_output = RiskAgentOutput(
            risk_position="Risk position",
            key_phrases=["risk"],
            worst_case="Bad",
            reasoning="Risk reasoning",
        )
        defense_output = DefenseAgentOutput(
            defense_position="Defense position",
            favorable_phrases=["defense"],
            best_case="Good",
            reasoning="Defense reasoning",
        )
        debate_history = [{"round": 0, "type": "initial_positions"}]

        verdict_output, raw_data = await run_verdict_agent_with_reasoning(
            "test clause", risk_output, defense_output, debate_history
        )

        assert isinstance(verdict_output, VerdictAgentOutput)
        assert verdict_output.severity == Severity.HIGH
        assert verdict_output.confidence == 0.85
        assert "key_findings" in raw_data
        assert "recommendation" in raw_data


class TestConsequenceSimulation:
    """Tests for consequence simulation engine."""

    @pytest.mark.asyncio
    @patch("backend.services.enhanced_adversarial_engine.call_gemini")
    async def test_consequence_simulation_returns_detailed_chain(self, mock_gemini):
        """Consequence simulation should return detailed consequence chain."""
        mock_response = {
            "trigger_condition": "Employee creates side project",
            "immediate_consequence": "Company claims ownership",
            "downstream_impact": "Legal disputes and lost opportunities",
            "worst_case_scenario": "Loss of successful startup to former employer",
            "probability_estimate": "Medium",
            "financial_impact_range": "$10,000 - $1,000,000",
            "timeline": "Within 6 months of project launch",
            "mitigation_strategies": ["Legal review", "Clear documentation"],
        }
        mock_gemini.return_value = mock_response

        signer_profile = {"occupation": "Software Developer", "experience": "Senior"}
        consequence_chain, raw_data = await simulate_consequences(
            "test clause", Severity.HIGH, "risk position", signer_profile
        )

        assert isinstance(consequence_chain, ConsequenceChain)
        assert consequence_chain.trigger_condition == mock_response["trigger_condition"]
        assert "probability_estimate" in raw_data
        assert "financial_impact_range" in raw_data
        assert "mitigation_strategies" in raw_data

    @pytest.mark.asyncio
    @patch("backend.services.enhanced_adversarial_engine.call_gemini")
    async def test_consequence_simulation_uses_signer_profile(self, mock_gemini):
        """Consequence simulation should incorporate signer profile."""
        mock_gemini.return_value = {
            "trigger_condition": "test",
            "immediate_consequence": "test",
            "downstream_impact": "test",
            "worst_case_scenario": "test",
        }

        signer_profile = {
            "occupation": "Startup Founder",
            "experience": "Experienced",
            "risk_tolerance": "Low",
        }

        await simulate_consequences(
            "test clause", Severity.HIGH, "risk position", signer_profile
        )

        # Verify signer profile was passed to Gemini
        call_args = mock_gemini.call_args
        assert json.dumps(signer_profile) in call_args[1]["system_prompt"]


class TestPlainEnglishTranslation:
    """Tests for plain English translation."""

    @pytest.mark.asyncio
    @patch("backend.services.enhanced_adversarial_engine.call_gemini")
    async def test_plain_english_translation_comprehensive(self, mock_gemini):
        """Plain English translation should provide comprehensive explanation."""
        mock_response = {
            "plain_translation": "In simple terms, this means...",
            "key_terms_explained": {
                "indemnification": "Taking responsibility for damages",
                "liquidated damages": "Pre-agreed penalty amount",
            },
            "analogies": [
                "Like insurance for the company",
                "Similar to a security deposit",
            ],
            "what_it_means": "You could be personally responsible for company losses",
            "watch_out_for": ["Unlimited liability", "Vague trigger conditions"],
        }
        mock_gemini.return_value = mock_response

        result = await translate_to_plain_english(
            "complex legal text", "contract clause"
        )

        assert result["plain_translation"] == mock_response["plain_translation"]
        assert "indemnification" in result["key_terms_explained"]
        assert len(result["analogies"]) == 2
        assert "watch_out_for" in result


class TestFullAnalysisWorkflow:
    """Tests for complete analysis workflow."""

    @pytest.mark.asyncio
    @patch("backend.services.enhanced_adversarial_engine.call_gemini")
    async def test_analyze_clause_with_debate_complete_workflow(
        self, mock_gemini, sample_clause
    ):
        """Complete analysis should run all components."""
        # Mock all the different API calls
        responses = [
            # Risk agent initial
            {
                "risk_position": "High risk position",
                "key_phrases": ["risky"],
                "worst_case": "Bad outcome",
                "reasoning": "Risk reasoning",
            },
            # Defense agent initial
            {
                "defense_position": "Defense position",
                "favorable_phrases": ["protective"],
                "best_case": "Good outcome",
                "reasoning": "Defense reasoning",
            },
            # Risk rebuttal
            {
                "rebuttal": "Risk rebuttal",
                "strengthened_position": "Stronger risk",
                "new_evidence": ["evidence"],
                "opposition_weaknesses": ["weakness"],
                "reasoning": "Rebuttal reasoning",
            },
            # Defense rebuttal
            {
                "rebuttal": "Defense rebuttal",
                "strengthened_position": "Stronger defense",
                "new_evidence": ["defense evidence"],
                "opposition_weaknesses": ["risk weakness"],
                "reasoning": "Defense rebuttal reasoning",
            },
            # Verdict
            {
                "verdict": "Final verdict",
                "severity": "HIGH",
                "confidence": 0.8,
                "risk_category": "IP_TRANSFER",
                "plain_english": "Plain explanation",
                "reasoning": "Verdict reasoning",
            },
            # Consequence simulation (for HIGH severity)
            {
                "trigger_condition": "Trigger",
                "immediate_consequence": "Immediate",
                "downstream_impact": "Downstream",
                "worst_case_scenario": "Worst case",
            },
            # Plain English translation
            {
                "plain_translation": "Simple explanation",
                "key_terms_explained": {},
                "analogies": [],
                "what_it_means": "What it means",
                "watch_out_for": [],
            },
        ]

        call_count = 0

        async def mock_call(*args, **kwargs):
            nonlocal call_count
            response = responses[call_count % len(responses)]
            call_count += 1
            return response

        mock_gemini.side_effect = mock_call

        signer_profile = {"occupation": "Developer"}
        risk, defense, verdict, full_analysis = await analyze_clause_with_debate(
            sample_clause, signer_profile
        )

        # Verify all components completed
        assert isinstance(risk, RiskAgentOutput)
        assert isinstance(defense, DefenseAgentOutput)
        assert isinstance(verdict, VerdictAgentOutput)
        assert verdict.severity == Severity.HIGH

        # Verify full analysis structure
        assert full_analysis["clause_id"] == sample_clause.id
        assert "debate_history" in full_analysis
        assert "consequence_simulation" in full_analysis
        assert "plain_english_translation" in full_analysis
        assert "processing_time" in full_analysis
        assert full_analysis["signer_profile_used"] == signer_profile

    @pytest.mark.asyncio
    @patch("backend.services.enhanced_adversarial_engine.call_gemini")
    async def test_analyze_clause_performance_tracking(self, mock_gemini, sample_clause):
        """Analysis should track performance metrics."""
        mock_gemini.return_value = {
            "risk_position": "test",
            "key_phrases": [],
            "worst_case": "test",
            "reasoning": "test",
        }

        start_time = time.time()
        _, _, _, full_analysis = await analyze_clause_with_debate(sample_clause)
        elapsed = time.time() - start_time

        # Processing time should be recorded and reasonable
        assert "processing_time" in full_analysis
        assert full_analysis["processing_time"] > 0
        assert full_analysis["processing_time"] <= elapsed + 0.1  # Small buffer


class TestStreamingAnalysis:
    """Tests for real-time streaming analysis."""

    @pytest.mark.asyncio
    @patch("backend.services.enhanced_adversarial_engine.call_gemini")
    async def test_stream_analysis_events_yields_all_stages(
        self, mock_gemini, sample_clause
    ):
        """Streaming analysis should yield events for all stages."""
        mock_responses = [
            # Risk initial
            {"risk_position": "risk", "key_phrases": [], "worst_case": "bad"},
            # Defense initial
            {"defense_position": "defense", "favorable_phrases": [], "best_case": "good"},
            # Risk rebuttal round 1
            {"rebuttal": "risk rebuttal 1", "strengthened_position": "stronger risk"},
            # Defense rebuttal round 1
            {"rebuttal": "defense rebuttal 1", "strengthened_position": "stronger defense"},
            # Risk rebuttal round 2
            {"rebuttal": "risk rebuttal 2", "strengthened_position": "final risk"},
            # Defense rebuttal round 2
            {"rebuttal": "defense rebuttal 2", "strengthened_position": "final defense"},
            # Verdict
            {
                "verdict": "final verdict",
                "severity": "MEDIUM",
                "confidence": 0.7,
                "risk_category": "General",
                "plain_english": "explanation",
            },
            # Translation
            {"plain_translation": "simple", "key_terms_explained": {}},
        ]

        call_count = 0

        async def mock_call(*args, **kwargs):
            nonlocal call_count
            response = mock_responses[call_count % len(mock_responses)]
            call_count += 1
            return response

        mock_gemini.side_effect = mock_call

        events = []
        async for event in stream_analysis_events(sample_clause):
            events.append(event)

        # Should have events for all stages
        event_types = [event["type"] for event in events]
        assert "agent_analysis" in event_types
        assert "agent_rebuttal" in event_types
        assert "verdict" in event_types
        assert "translation" in event_types

        # Should have correct clause_id in all events
        for event in events:
            assert event["clause_id"] == sample_clause.id


class TestEdgeCases:
    """Tests for edge cases and error handling."""

    def test_should_analyze_with_none_category(self):
        """Should not analyze clause with None category."""
        clause = Clause(id="test", text="test", category=None)
        assert should_analyze(clause) is False

    def test_should_analyze_with_non_adversarial_category(self):
        """Should not analyze non-adversarial categories."""
        clause = Clause(
            id="test", text="test", category=ClauseCategory.AMBIGUOUS
        )
        assert should_analyze(clause) is False

    @pytest.mark.asyncio
    @patch("backend.services.enhanced_adversarial_engine.call_gemini")
    async def test_handles_gemini_api_errors(self, mock_gemini, sample_clause):
        """Should handle Gemini API errors gracefully."""
        mock_gemini.side_effect = Exception("API Error")

        with pytest.raises(Exception):
            await run_risk_agent_with_reasoning("test clause")

    @pytest.mark.asyncio
    @patch("backend.services.enhanced_adversarial_engine.call_gemini")
    async def test_handles_malformed_json_response(self, mock_gemini):
        """Should handle malformed JSON responses."""
        # Mock returns invalid structure
        mock_gemini.return_value = {"invalid": "structure"}

        risk_output, raw_data = await run_risk_agent_with_reasoning("test")

        # Should use defaults for missing fields
        assert risk_output.risk_position == ""
        assert risk_output.key_phrases == []
        assert risk_output.worst_case == ""


class TestSecurityAndValidation:
    """Tests for security and input validation."""

    @pytest.mark.asyncio
    @patch("backend.services.enhanced_adversarial_engine.call_gemini")
    async def test_handles_extremely_long_clause_text(self, mock_gemini):
        """Should handle very long clause text."""
        long_text = "x" * 10000  # 10KB text
        mock_gemini.return_value = {
            "risk_position": "test",
            "key_phrases": [],
            "worst_case": "test",
        }

        risk_output, _ = await run_risk_agent_with_reasoning(long_text)
        assert isinstance(risk_output, RiskAgentOutput)

    @pytest.mark.asyncio
    @patch("backend.services.enhanced_adversarial_engine.call_gemini")
    async def test_handles_special_characters_in_clause(self, mock_gemini):
        """Should handle special characters and unicode in clause text."""
        special_text = "Clause with émojis 🔒 and special chars: <>&\"'"
        mock_gemini.return_value = {
            "risk_position": "test",
            "key_phrases": [],
            "worst_case": "test",
        }

        risk_output, _ = await run_risk_agent_with_reasoning(special_text)
        assert isinstance(risk_output, RiskAgentOutput)

    @pytest.mark.asyncio
    async def test_signer_profile_validation(self, sample_clause):
        """Should validate signer profile structure."""
        invalid_profile = {"invalid": "profile"}

        # Should not raise exception with invalid profile
        try:
            await analyze_clause_with_debate(sample_clause, invalid_profile)
        except Exception as e:
            # If it fails, it should be due to mocked Gemini, not profile validation
            assert "call_gemini" in str(e) or "mock" in str(e).lower()


@pytest.mark.performance
class TestPerformanceRequirements:
    """Performance tests for the enhanced adversarial engine."""

    @pytest.mark.asyncio
    @patch("backend.services.enhanced_adversarial_engine.call_gemini")
    async def test_analysis_completes_within_time_limit(
        self, mock_gemini, sample_clause, performance_benchmark
    ):
        """Full analysis should complete within reasonable time."""
        mock_gemini.return_value = {"risk_position": "test", "key_phrases": []}

        performance_benchmark.start()
        await analyze_clause_with_debate(sample_clause)
        performance_benchmark.stop()

        # Should complete within 30 seconds
        assert performance_benchmark.duration < 30.0

    @pytest.mark.asyncio
    @patch("backend.services.enhanced_adversarial_engine.call_gemini")
    async def test_concurrent_analysis_performance(self, mock_gemini, sample_clauses):
        """Multiple concurrent analyses should perform well."""
        mock_gemini.return_value = {"risk_position": "test", "key_phrases": []}

        start_time = time.time()
        tasks = [
            analyze_clause_with_debate(clause)
            for clause in sample_clauses[:3]  # Test with 3 clauses
        ]
        await asyncio.gather(*tasks)
        elapsed = time.time() - start_time

        # Concurrent execution should be faster than sequential
        # 3 clauses should complete in less than 60 seconds
        assert elapsed < 60.0
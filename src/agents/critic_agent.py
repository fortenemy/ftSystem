"""Critic Agent for peer review, quality validation, and constructive feedback."""

import logging
from typing import Any, Dict, List
from .base import Agent, AgentConfig


class CriticAgent(Agent):
    """
    Specialized agent for reviewing and validating outputs from other agents.
    
    This agent provides multi-dimensional quality assessment, identifies issues,
    and offers constructive feedback for improvement with approval status.
    """

    def __init__(self, config: AgentConfig):
        """
        Initialize the Critic Agent.
        
        Args:
            config: AgentConfig containing agent name, description, and optional parameters.
                   Supports params: strictness_level (str), criteria (list).
        """
        super().__init__(config)
        logging.debug(f"CriticAgent initialized with config: {config.name}")

    def run(self, **kwargs: Any) -> Dict[str, Any]:
        """
        Review and validate content from other agents.
        
        Args:
            **kwargs: Expected keys:
                     - content (str): Content to review
                     - criteria (list, optional): Custom review criteria
                     - context (str, optional): Context for the review
        
        Returns:
            Dictionary containing:
            - content_preview: Short preview of reviewed content
            - quality_scores: Dict of scores for different dimensions
            - overall_score: Weighted average of all scores (0.0-1.0)
            - issues_found: List of identified issues with severity
            - suggestions: Constructive improvement suggestions
            - approval_status: "approved", "needs_revision", or "rejected"
        
        Raises:
            ValueError: If no content is provided.
        """
        content = kwargs.get("content", "")
        criteria = kwargs.get("criteria", [])
        context = kwargs.get("context", "")
        
        if not content:
            raise ValueError("Content is required for review (provide 'content' in kwargs)")
        
        # Extract parameters with defaults
        strictness_level = "balanced"
        
        if self.config.params:
            strictness_level = self.config.params.get("strictness_level", "balanced")
            if not criteria:
                criteria = self.config.params.get("criteria", [])
        
        logging.info(f"[Critic] Starting review: strictness={strictness_level}")
        logging.debug(f"[Critic] Content length: {len(content)}, criteria: {len(criteria)}")
        
        # Perform multi-dimensional review
        quality_scores = self._evaluate_quality(content, strictness_level)
        issues = self._identify_issues(content, strictness_level)
        suggestions = self._generate_suggestions(quality_scores, issues, context)
        approval_status = self._determine_approval(quality_scores, issues, strictness_level)
        overall_score = sum(quality_scores.values()) / len(quality_scores) if quality_scores else 0.0
        
        content_preview = content[:100] + "..." if len(content) > 100 else content
        
        result = {
            "content_preview": content_preview,
            "quality_scores": quality_scores,
            "overall_score": overall_score,
            "issues_found": issues,
            "suggestions": suggestions,
            "approval_status": approval_status,
        }
        
        logging.info(f"[Critic] Review complete: overall_score={overall_score:.2f}, status={approval_status}")
        return result

    def _evaluate_quality(self, content: str, strictness: str) -> Dict[str, float]:
        """
        Evaluate content quality across multiple dimensions.
        
        Args:
            content: Content to evaluate.
            strictness: Review strictness level (lenient, balanced, strict).
        
        Returns:
            Dictionary of quality scores (0.0-1.0) for each dimension.
        """
        # Base scores for dimensions
        scores = {
            "accuracy": 0.85,
            "completeness": 0.80,
            "clarity": 0.88,
            "consistency": 0.90,
            "structure": 0.82,
        }
        
        # Adjust based on content characteristics
        if len(content) < 50:
            scores["completeness"] -= 0.15
        elif len(content) > 5000:
            scores["clarity"] -= 0.10
        
        # Check for common quality issues
        if "TODO" in content or "FIXME" in content:
            scores["completeness"] -= 0.20
        
        if "???" in content or "unclear" in content.lower():
            scores["clarity"] -= 0.15
        
        # Apply strictness adjustment
        if strictness == "strict":
            # Reduce all scores slightly for stricter evaluation
            scores = {k: max(0.0, v - 0.05) for k, v in scores.items()}
        elif strictness == "lenient":
            # Increase all scores slightly for lenient evaluation
            scores = {k: min(1.0, v + 0.05) for k, v in scores.items()}
        
        logging.debug(f"[Critic] Quality scores: {scores}")
        return scores

    def _identify_issues(self, content: str, strictness: str) -> List[Dict[str, Any]]:
        """
        Identify issues and problems in the content.
        
        Args:
            content: Content to analyze for issues.
            strictness: Review strictness level.
        
        Returns:
            List of issue dictionaries with severity and description.
        """
        issues = []
        
        # Check for length issues
        if len(content) < 50:
            issues.append({
                "severity": "warning",
                "type": "insufficient_content",
                "description": "Content is too short for meaningful review",
            })
        
        # Check for incomplete markers
        if "TODO" in content or "FIXME" in content:
            issues.append({
                "severity": "error" if strictness == "strict" else "warning",
                "type": "incomplete_work",
                "description": "Unfinished work markers found (TODO/FIXME)",
            })
        
        # Check for unclear passages
        if "???" in content or "unclear" in content.lower():
            issues.append({
                "severity": "warning",
                "type": "unclear_sections",
                "description": "Unclear or ambiguous passages detected",
            })
        
        # Check for consistency
        if content.count("\n\n\n") > 0:
            issues.append({
                "severity": "info",
                "type": "formatting",
                "description": "Excessive blank lines detected",
            })
        
        logging.debug(f"[Critic] Issues found: {len(issues)}")
        return issues

    def _generate_suggestions(self, quality_scores: Dict[str, float], 
                            issues: List[Dict], context: str = "") -> List[str]:
        """
        Generate constructive improvement suggestions.
        
        Args:
            quality_scores: Quality scores for each dimension.
            issues: Identified issues.
            context: Context for tailored suggestions.
        
        Returns:
            List of suggestion strings.
        """
        suggestions = []
        
        # Base on low scores
        if quality_scores.get("clarity", 1.0) < 0.85:
            suggestions.append("Improve clarity by simplifying complex sentences and removing jargon")
        
        if quality_scores.get("completeness", 1.0) < 0.85:
            suggestions.append("Add missing sections or expand existing ones for better coverage")
        
        if quality_scores.get("accuracy", 1.0) < 0.85:
            suggestions.append("Verify facts and claims; provide citations where possible")
        
        if quality_scores.get("consistency", 1.0) < 0.85:
            suggestions.append("Ensure consistent terminology and formatting throughout")
        
        # Base on identified issues
        if any(i["type"] == "incomplete_work" for i in issues):
            suggestions.append("Complete all marked TODO/FIXME items before submission")
        
        if any(i["type"] == "unclear_sections" for i in issues):
            suggestions.append("Clarify uncertain or ambiguous passages with specific details")
        
        # Base on context
        if context and "code" in context.lower():
            suggestions.append("Add comments explaining complex logic")
            suggestions.append("Include docstrings for all functions and classes")
        
        if context and "report" in context.lower():
            suggestions.append("Add executive summary at the beginning")
            suggestions.append("Include references and source citations")
        
        # Generic improvement suggestion
        if len(suggestions) == 0:
            suggestions.append("Overall content is good; minor polish recommended")
        
        logging.debug(f"[Critic] Generated {len(suggestions)} suggestions")
        return suggestions

    def _determine_approval(self, quality_scores: Dict[str, float], 
                           issues: List[Dict], strictness: str) -> str:
        """
        Determine approval status based on quality and issues.
        
        Args:
            quality_scores: Quality scores for each dimension.
            issues: Identified issues.
            strictness: Review strictness level.
        
        Returns:
            Approval status: "approved", "needs_revision", or "rejected".
        """
        overall_score = sum(quality_scores.values()) / len(quality_scores) if quality_scores else 0.0
        error_count = sum(1 for i in issues if i["severity"] == "error")
        warning_count = sum(1 for i in issues if i["severity"] == "warning")
        
        # Determine thresholds based on strictness
        if strictness == "strict":
            approval_threshold = 0.85
            rejection_threshold = 0.70
        elif strictness == "lenient":
            approval_threshold = 0.70
            rejection_threshold = 0.50
        else:  # balanced
            approval_threshold = 0.80
            rejection_threshold = 0.60
        
        # Decision logic
        if error_count > 0:
            status = "rejected"
        elif overall_score >= approval_threshold and warning_count <= 1:
            status = "approved"
        elif overall_score >= rejection_threshold:
            status = "needs_revision"
        else:
            status = "rejected"
        
        logging.debug(f"[Critic] Approval decision: {status} (score={overall_score:.2f}, errors={error_count}, warnings={warning_count})")
        return status

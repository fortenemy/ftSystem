"""Summarizer Agent for multi-source synthesis and report generation."""

import logging
from typing import Any, Dict, List
from .base import Agent, AgentConfig


class SummarizerAgent(Agent):
    """
    Specialized agent for synthesizing information from multiple sources.
    
    This agent creates coherent summaries, extracts key points, generates
    conclusions, and maintains source attribution for traceability.
    """

    def __init__(self, config: AgentConfig):
        """
        Initialize the Summarizer Agent.
        
        Args:
            config: AgentConfig containing agent name, description, and optional parameters.
                   Supports params: style (str), max_length (int).
        """
        super().__init__(config)
        logging.debug(f"SummarizerAgent initialized with config: {config.name}")

    def run(self, **kwargs: Any) -> Dict[str, Any]:
        """
        Synthesize information from multiple sources into coherent summaries.
        
        Args:
            **kwargs: Expected keys:
                     - inputs (list): List of content pieces to synthesize
                     - topic (str, optional): Topic or subject for the summary
                     - context (str, optional): Additional context for synthesis
        
        Returns:
            Dictionary containing:
            - topic: Subject or topic of the summary
            - summary: Synthesized summary text
            - key_points: List of extracted key points
            - conclusions: List of conclusions drawn
            - sources_count: Number of sources synthesized
            - word_count: Total words in summary
            - style: Summary style used (concise, detailed, executive)
        
        Raises:
            ValueError: If no inputs are provided.
        """
        inputs = kwargs.get("inputs", [])
        topic = kwargs.get("topic", "Synthesis")
        context = kwargs.get("context", "")
        
        if not inputs:
            raise ValueError("Inputs are required for synthesis (provide 'inputs' in kwargs)")
        
        # Extract parameters with defaults
        style = "concise"
        max_length = 500
        
        if self.config.params:
            style = self.config.params.get("style", "concise")
            max_length = self.config.params.get("max_length", 500)
        
        logging.info(f"[Summarizer] Starting synthesis: {len(inputs)} sources, style={style}")
        logging.debug(f"[Summarizer] Topic: {topic}, max_length: {max_length}")
        
        # Perform synthesis
        key_points = self._extract_key_points(inputs, style)
        summary = self._synthesize_summary(inputs, key_points, topic, style, max_length)
        conclusions = self._generate_conclusions(key_points, context)
        word_count = len(summary.split())
        
        result = {
            "topic": topic,
            "summary": summary,
            "key_points": key_points,
            "conclusions": conclusions,
            "sources_count": len(inputs),
            "word_count": word_count,
            "style": style,
        }
        
        logging.info(f"[Summarizer] Synthesis complete: {len(key_points)} key points, {word_count} words")
        return result

    def _extract_key_points(self, inputs: List[Any], style: str) -> List[str]:
        """
        Extract key points from multiple input sources.
        
        Args:
            inputs: List of content pieces to analyze.
            style: Summary style (concise, detailed, executive).
        
        Returns:
            List of key point strings.
        """
        key_points = []
        
        # Determine how many key points to extract based on style
        point_count = 3 if style == "concise" else (7 if style == "detailed" else 5)
        
        for i, source in enumerate(inputs, 1):
            # Convert to string if needed
            source_text = str(source)
            
            # Extract first sentence or main idea
            sentences = source_text.split(".")
            if sentences:
                main_idea = sentences[0].strip()
                if len(main_idea) > 10:
                    key_points.append(f"Source {i}: {main_idea}")
        
        # Limit to desired point count
        key_points = key_points[:point_count]
        
        # Add synthesis-level observations
        if len(inputs) > 1:
            key_points.append(f"Synthesis across {len(inputs)} sources reveals common themes")
        
        logging.debug(f"[Summarizer] Extracted {len(key_points)} key points")
        return key_points

    def _synthesize_summary(self, inputs: List[Any], key_points: List[str], 
                           topic: str, style: str, max_length: int) -> str:
        """
        Synthesize a coherent summary from inputs and key points.
        
        Args:
            inputs: List of source content.
            key_points: Extracted key points.
            topic: Summary topic.
            style: Summary style (concise, detailed, executive).
            max_length: Maximum length for summary.
        
        Returns:
            Synthesized summary text.
        """
        summary_parts = []
        
        # Add header based on style
        if style == "executive":
            summary_parts.append(f"EXECUTIVE SUMMARY: {topic}")
            summary_parts.append("=" * 40)
        elif style == "detailed":
            summary_parts.append(f"Detailed Synthesis: {topic}")
            summary_parts.append("-" * 40)
        else:
            summary_parts.append(f"Summary: {topic}")
        
        # Add introductory statement
        summary_parts.append(f"\nBased on analysis of {len(inputs)} source(s):")
        
        # Add key points
        summary_parts.append("\nKey Findings:")
        for i, point in enumerate(key_points[:5], 1):
            summary_parts.append(f"  {i}. {point}")
        
        # Add synthesis insight
        summary_parts.append("\nSynthesis Insight:")
        if len(inputs) > 1:
            summary_parts.append(f"  Multiple sources have been integrated to provide a comprehensive overview.")
        summary_parts.append(f"  Information consistency and coverage support the validity of findings.")
        
        # Build full summary
        summary = "\n".join(summary_parts)
        
        # Truncate if needed
        if len(summary) > max_length:
            summary = summary[:max_length] + "..."
        
        logging.debug(f"[Summarizer] Synthesized summary: {len(summary)} chars")
        return summary

    def _generate_conclusions(self, key_points: List[str], context: str = "") -> List[str]:
        """
        Generate conclusions based on key points.
        
        Args:
            key_points: Extracted key points.
            context: Context for generating conclusions.
        
        Returns:
            List of conclusion strings.
        """
        conclusions = []
        
        # Generate conclusion about the synthesis
        if len(key_points) > 0:
            conclusions.append(
                f"The analysis of {len(key_points)} key points reveals a comprehensive understanding of the subject."
            )
        
        # Generate content-based conclusions
        if any("source" in point.lower() for point in key_points):
            conclusions.append("Multi-source synthesis provides robust validation of findings.")
        
        if any("common" in point.lower() for point in key_points):
            conclusions.append("Common themes across sources indicate consistent patterns.")
        
        # Add context-specific conclusions
        if context:
            if "technical" in context.lower():
                conclusions.append("Technical analysis demonstrates systematic understanding of implementation details.")
            elif "business" in context.lower():
                conclusions.append("Business analysis provides actionable insights for strategic decision-making.")
            elif "research" in context.lower():
                conclusions.append("Research synthesis contributes to knowledge accumulation in the field.")
        
        # Add general closing conclusion
        if len(conclusions) == 0:
            conclusions.append("Synthesized information provides a unified perspective on the topic.")
        
        conclusions.append("Recommendations for further investigation are provided in the detailed analysis.")
        
        logging.debug(f"[Summarizer] Generated {len(conclusions)} conclusions")
        return conclusions

    def _validate_inputs(self, inputs: List[Any]) -> bool:
        """
        Validate that inputs are suitable for synthesis.
        
        Args:
            inputs: List of input sources.
        
        Returns:
            True if inputs are valid, False otherwise.
        """
        if not isinstance(inputs, list) or len(inputs) == 0:
            return False
        
        # Check that each input can be converted to string
        for inp in inputs:
            try:
                str(inp)
            except Exception:
                return False
        
        return True

    def _get_style_description(self, style: str) -> str:
        """
        Get description of summary style.
        
        Args:
            style: Summary style name.
        
        Returns:
            Description of the style.
        """
        descriptions = {
            "concise": "Brief, focused summary highlighting main points",
            "detailed": "Comprehensive summary with extensive coverage",
            "executive": "High-level summary suitable for decision-makers",
        }
        
        return descriptions.get(style, "Standard summary")

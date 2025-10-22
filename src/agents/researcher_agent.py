"""Researcher Agent for information gathering and fact-checking tasks."""

import logging
from typing import Any, Dict, List
from .base import Agent, AgentConfig


class ResearcherAgent(Agent):
    """
    Specialized agent that gathers information, validates facts, and provides structured findings.
    
    This agent is designed to handle research queries, compile findings from multiple sources,
    and assess confidence levels for retrieved information.
    """

    def __init__(self, config: AgentConfig):
        """
        Initialize the Researcher Agent.
        
        Args:
            config: AgentConfig containing agent name, description, and optional parameters.
                   Supports params: max_sources (int), confidence_threshold (float).
        """
        super().__init__(config)
        logging.debug(f"ResearcherAgent initialized with config: {config.name}")

    def run(self, **kwargs: Any) -> Dict[str, Any]:
        """
        Execute research task on a given query.
        
        Args:
            **kwargs: Expected keys:
                     - query (str): Research question or topic to investigate
                     - context (str, optional): Additional context for the research
        
        Returns:
            Dictionary containing:
            - query: Original research query
            - sources: List of source entries with titles and URLs
            - summary: Synthesized research summary
            - key_findings: List of important findings
            - confidence: Overall confidence score (0.0-1.0)
            - analysis_depth: Number of sources analyzed
        
        Raises:
            ValueError: If no query is provided.
        """
        query = kwargs.get("query", "")
        context = kwargs.get("context", "")
        
        if not query:
            raise ValueError("Research query is required (provide 'query' in kwargs)")
        
        # Extract parameters with defaults
        max_sources = 3
        confidence_threshold = 0.7
        
        if self.config.params:
            max_sources = self.config.params.get("max_sources", 3)
            confidence_threshold = self.config.params.get("confidence_threshold", 0.7)
        
        logging.info(f"[Researcher] Processing query: {query}")
        logging.debug(f"[Researcher] max_sources={max_sources}, threshold={confidence_threshold}")
        
        # Simulate structured research findings
        sources = self._gather_sources(query, max_sources)
        key_findings = self._extract_findings(sources, query)
        summary = self._synthesize_summary(query, key_findings, context)
        confidence = min(1.0, len(key_findings) * 0.25 + 0.5)  # Scale based on findings
        
        result = {
            "query": query,
            "sources": sources,
            "summary": summary,
            "key_findings": key_findings,
            "confidence": confidence,
            "analysis_depth": len(sources),
        }
        
        logging.info(f"[Researcher] Research complete: {len(sources)} sources analyzed, confidence={confidence:.2f}")
        return result

    def _gather_sources(self, query: str, max_sources: int) -> List[Dict[str, Any]]:
        """
        Gather potential sources for the research query.
        
        Args:
            query: Research question or topic.
            max_sources: Maximum number of sources to return.
        
        Returns:
            List of source dictionaries with title, url, and relevance.
        """
        # Simulate source gathering (in production, would query real databases/APIs)
        base_sources = [
            {
                "title": f"Research on '{query}' - Primary Source",
                "url": f"https://example.com/research/{query.replace(' ', '_')}_1",
                "relevance": 0.95,
                "publication_date": "2025-10-20",
            },
            {
                "title": f"Analysis of {query} - Secondary Source",
                "url": f"https://example.com/analysis/{query.replace(' ', '_')}_2",
                "relevance": 0.87,
                "publication_date": "2025-10-15",
            },
            {
                "title": f"Study: {query} Overview",
                "url": f"https://example.com/study/{query.replace(' ', '_')}_3",
                "relevance": 0.82,
                "publication_date": "2025-10-10",
            },
            {
                "title": f"Expert Report on {query}",
                "url": f"https://example.com/report/{query.replace(' ', '_')}_4",
                "relevance": 0.79,
                "publication_date": "2025-10-05",
            },
            {
                "title": f"Data Collection: {query} Metrics",
                "url": f"https://example.com/data/{query.replace(' ', '_')}_5",
                "relevance": 0.75,
                "publication_date": "2025-09-30",
            },
        ]
        
        # Sort by relevance and limit to max_sources
        sorted_sources = sorted(base_sources, key=lambda x: x["relevance"], reverse=True)
        return sorted_sources[:max_sources]

    def _extract_findings(self, sources: List[Dict[str, Any]], query: str) -> List[str]:
        """
        Extract key findings from gathered sources.
        
        Args:
            sources: List of source dictionaries.
            query: Original query for context.
        
        Returns:
            List of key findings extracted from sources.
        """
        findings = []
        
        for i, source in enumerate(sources, 1):
            # Simulate finding extraction (in production, would parse source content)
            finding = f"Source {i}: {source['title']} indicates relevant information (relevance: {source['relevance']:.2f})"
            findings.append(finding)
        
        # Add synthetic findings based on query characteristics
        if len(query) > 20:
            findings.append(f"Comprehensive research scope detected for: {query[:30]}...")
        else:
            findings.append(f"Focused query identified: {query}")
        
        return findings

    def _synthesize_summary(self, query: str, findings: List[str], context: str = "") -> str:
        """
        Synthesize a summary from extracted findings.
        
        Args:
            query: Original research query.
            findings: List of key findings.
            context: Additional context information.
        
        Returns:
            Synthesized research summary.
        """
        summary_lines = [
            f"Research Summary for: {query}",
            f"Number of sources analyzed: {len(findings)}",
        ]
        
        if context:
            summary_lines.append(f"Context: {context}")
        
        summary_lines.append("Key findings:")
        for finding in findings[:3]:  # Include top 3 findings
            summary_lines.append(f"  - {finding}")
        
        if len(findings) > 3:
            summary_lines.append(f"  ... and {len(findings) - 3} additional findings")
        
        return "\n".join(summary_lines)

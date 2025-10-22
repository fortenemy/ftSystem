"""Analyst Agent for data analysis, pattern recognition, and insights."""

import logging
from typing import Any, Dict, List
from .base import Agent, AgentConfig


class AnalystAgent(Agent):
    """
    Specialized agent for data analysis and insight extraction.
    
    This agent analyzes data, recognizes patterns, and extracts actionable insights
    with confidence scoring and recommendation generation.
    """

    def __init__(self, config: AgentConfig):
        """
        Initialize the Analyst Agent.
        
        Args:
            config: AgentConfig containing agent name, description, and optional parameters.
                   Supports params: analysis_type (str), min_confidence (float).
        """
        super().__init__(config)
        logging.debug(f"AnalystAgent initialized with config: {config.name}")

    def run(self, **kwargs: Any) -> Dict[str, Any]:
        """
        Execute analysis task on provided data.
        
        Args:
            **kwargs: Expected keys:
                     - data (dict or list): Data to analyze
                     - context (str, optional): Additional context for analysis
        
        Returns:
            Dictionary containing:
            - analysis_type: Type of analysis performed
            - patterns: Identified patterns in the data
            - insights: Actionable insights extracted
            - recommendations: List of recommendations based on insights
            - confidence: Overall confidence score (0.0-1.0)
            - data_quality: Assessment of data quality
        
        Raises:
            ValueError: If no data is provided.
        """
        data = kwargs.get("data")
        context = kwargs.get("context", "")
        
        if data is None:
            raise ValueError("Data is required for analysis (provide 'data' in kwargs)")
        
        # Extract parameters with defaults
        analysis_type = "general"
        min_confidence = 0.6
        
        if self.config.params:
            analysis_type = self.config.params.get("analysis_type", "general")
            min_confidence = self.config.params.get("min_confidence", 0.6)
        
        logging.info(f"[Analyst] Starting {analysis_type} analysis")
        logging.debug(f"[Analyst] Data type: {type(data).__name__}, min_confidence: {min_confidence}")
        
        # Perform analysis
        data_quality = self._assess_data_quality(data)
        patterns = self._identify_patterns(data, analysis_type)
        insights = self._extract_insights(patterns, data, analysis_type)
        recommendations = self._generate_recommendations(insights, context)
        confidence = self._calculate_confidence(patterns, insights, data_quality)
        
        result = {
            "analysis_type": analysis_type,
            "patterns": patterns,
            "insights": insights,
            "recommendations": recommendations,
            "confidence": confidence,
            "data_quality": data_quality,
        }
        
        logging.info(f"[Analyst] Analysis complete: {len(patterns)} patterns, {len(insights)} insights, confidence={confidence:.2f}")
        return result

    def _assess_data_quality(self, data: Any) -> Dict[str, Any]:
        """
        Assess the quality of provided data.
        
        Args:
            data: Data to assess.
        
        Returns:
            Dictionary containing quality metrics.
        """
        quality = {
            "is_valid": data is not None,
            "size": 0,
            "completeness": 1.0,
            "consistency": 1.0,
        }
        
        if isinstance(data, dict):
            quality["size"] = len(data)
            quality["type"] = "dict"
            # Simulate quality checks
            if len(data) > 0:
                quality["completeness"] = 0.95
        elif isinstance(data, list):
            quality["size"] = len(data)
            quality["type"] = "list"
            if len(data) > 100:
                quality["completeness"] = 0.90
        else:
            quality["type"] = "other"
            quality["completeness"] = 0.85
        
        logging.debug(f"[Analyst] Data quality: size={quality['size']}, completeness={quality['completeness']:.2f}")
        return quality

    def _identify_patterns(self, data: Any, analysis_type: str) -> List[Dict[str, Any]]:
        """
        Identify patterns in the provided data.
        
        Args:
            data: Data to analyze for patterns.
            analysis_type: Type of analysis to guide pattern detection.
        
        Returns:
            List of identified patterns with descriptions and metrics.
        """
        patterns = []
        
        if isinstance(data, dict):
            # Identify patterns in dictionary data
            patterns.extend(self._analyze_dict_patterns(data))
        elif isinstance(data, list):
            # Identify patterns in list data
            patterns.extend(self._analyze_list_patterns(data))
        
        # Add analysis-type-specific patterns
        if analysis_type == "trend":
            patterns.append({
                "type": "temporal_trend",
                "description": "Time-based pattern detected",
                "significance": 0.8,
            })
        elif analysis_type == "anomaly":
            patterns.append({
                "type": "outlier_detection",
                "description": "Anomalous values identified",
                "significance": 0.75,
            })
        elif analysis_type == "correlation":
            patterns.append({
                "type": "correlation_matrix",
                "description": "Relationships between variables detected",
                "significance": 0.82,
            })
        
        logging.debug(f"[Analyst] Identified {len(patterns)} patterns")
        return patterns

    def _analyze_dict_patterns(self, data: Dict) -> List[Dict[str, Any]]:
        """Analyze patterns in dictionary data."""
        patterns = []
        
        patterns.append({
            "type": "key_distribution",
            "description": f"Dictionary with {len(data)} keys identified",
            "significance": 0.7,
        })
        
        if len(data) > 10:
            patterns.append({
                "type": "large_dataset",
                "description": "Significant data volume detected",
                "significance": 0.65,
            })
        
        return patterns

    def _analyze_list_patterns(self, data: List) -> List[Dict[str, Any]]:
        """Analyze patterns in list data."""
        patterns = []
        
        patterns.append({
            "type": "sequence_pattern",
            "description": f"Sequence of {len(data)} items identified",
            "significance": 0.7,
        })
        
        if len(data) > 50:
            patterns.append({
                "type": "high_cardinality",
                "description": "High-cardinality data sequence detected",
                "significance": 0.72,
            })
        
        return patterns

    def _extract_insights(self, patterns: List[Dict], data: Any, analysis_type: str) -> List[str]:
        """
        Extract actionable insights from identified patterns.
        
        Args:
            patterns: Identified patterns.
            data: Original data.
            analysis_type: Type of analysis performed.
        
        Returns:
            List of insight strings.
        """
        insights = []
        
        # Generate insights based on patterns
        for pattern in patterns:
            insight = f"Pattern '{pattern['type']}': {pattern['description']}"
            insights.append(insight)
        
        # Add analysis-type-specific insights
        if analysis_type == "trend":
            insights.append("Upward or downward trends may be present in time-series data")
        elif analysis_type == "anomaly":
            insights.append("Outliers could indicate measurement errors or significant events")
        elif analysis_type == "correlation":
            insights.append("Variable relationships may indicate causal or correlative connections")
        
        if isinstance(data, (dict, list)) and len(data) > 0:
            insights.append(f"Data contains {len(data)} distinct elements for analysis")
        
        logging.debug(f"[Analyst] Extracted {len(insights)} insights")
        return insights

    def _generate_recommendations(self, insights: List[str], context: str = "") -> List[str]:
        """
        Generate recommendations based on extracted insights.
        
        Args:
            insights: Extracted insights.
            context: Additional context for recommendations.
        
        Returns:
            List of recommendation strings.
        """
        recommendations = []
        
        if len(insights) > 0:
            recommendations.append("Review identified patterns for actionable implications")
        
        if "trend" in str(insights):
            recommendations.append("Consider forecasting methods for trend analysis")
        
        if "anomaly" in str(insights):
            recommendations.append("Investigate outliers to determine if they are errors or significant events")
        
        if "correlation" in str(insights):
            recommendations.append("Perform statistical tests to validate potential correlations")
        
        if context:
            recommendations.append(f"Consider context in interpretation: {context}")
        
        recommendations.append("Document analysis methodology for reproducibility")
        
        logging.debug(f"[Analyst] Generated {len(recommendations)} recommendations")
        return recommendations

    def _calculate_confidence(self, patterns: List[Dict], insights: List[str], 
                            data_quality: Dict[str, Any]) -> float:
        """
        Calculate overall confidence score for analysis.
        
        Args:
            patterns: Identified patterns.
            insights: Extracted insights.
            data_quality: Data quality assessment.
        
        Returns:
            Confidence score (0.0-1.0).
        """
        base_confidence = 0.5
        
        # Increase confidence based on number of patterns
        pattern_factor = min(0.2, len(patterns) * 0.05)
        
        # Increase confidence based on number of insights
        insight_factor = min(0.15, len(insights) * 0.04)
        
        # Increase confidence based on data quality
        quality_factor = data_quality.get("completeness", 0.5) * 0.15
        
        confidence = min(1.0, base_confidence + pattern_factor + insight_factor + quality_factor)
        
        logging.debug(f"[Analyst] Confidence calculation: base=0.5, patterns={pattern_factor:.2f}, insights={insight_factor:.2f}, quality={quality_factor:.2f}")
        
        return confidence

"""Tests for the Analyst Agent."""

import pytest
from src.agents.analyst_agent import AnalystAgent
from src.agents.base import AgentConfig


class TestAnalystAgent:
    """Test suite for Analyst Agent."""

    def test_analyst_initialization(self):
        """Test Analyst Agent initialization."""
        config = AgentConfig(
            name="Analyst",
            description="Data analysis agent"
        )
        agent = AnalystAgent(config)
        assert agent.config.name == "Analyst"
        assert isinstance(agent, AnalystAgent)

    def test_analyst_dict_analysis(self):
        """Test analysis of dictionary data."""
        config = AgentConfig(name="analyst", description="Test analyst")
        agent = AnalystAgent(config)
        
        data = {"metric_1": 100, "metric_2": 200, "metric_3": 150}
        result = agent.run(data=data)
        
        assert isinstance(result, dict)
        assert "analysis_type" in result
        assert "patterns" in result
        assert "insights" in result
        assert "recommendations" in result
        assert "confidence" in result
        assert "data_quality" in result

    def test_analyst_list_analysis(self):
        """Test analysis of list data."""
        config = AgentConfig(name="analyst", description="Test analyst")
        agent = AnalystAgent(config)
        
        data = [10, 20, 30, 40, 50]
        result = agent.run(data=data)
        
        assert isinstance(result, dict)
        assert result["data_quality"]["type"] == "list"
        assert len(result["patterns"]) > 0

    def test_analyst_missing_data(self):
        """Test that missing data raises ValueError."""
        config = AgentConfig(name="analyst", description="Test analyst")
        agent = AnalystAgent(config)
        
        with pytest.raises(ValueError, match="Data is required for analysis"):
            agent.run()

    def test_analyst_analysis_types(self):
        """Test different analysis types."""
        config = AgentConfig(name="analyst", description="Test analyst")
        agent = AnalystAgent(config)
        
        data = [1, 2, 3, 4, 5]
        
        # Test trend analysis
        result_trend = agent.run(
            data=data,
        )
        agent.config.params = {"analysis_type": "trend"}
        result_trend = agent.run(data=data)
        
        # Test anomaly analysis
        agent.config.params = {"analysis_type": "anomaly"}
        result_anomaly = agent.run(data=data)
        
        # Test correlation analysis
        agent.config.params = {"analysis_type": "correlation"}
        result_correlation = agent.run(data=data)
        
        assert result_trend["analysis_type"] == "trend"
        assert result_anomaly["analysis_type"] == "anomaly"
        assert result_correlation["analysis_type"] == "correlation"

    def test_analyst_output_structure(self):
        """Test output structure is complete."""
        config = AgentConfig(name="analyst", description="Test analyst")
        agent = AnalystAgent(config)
        
        data = {"a": 1, "b": 2}
        result = agent.run(data=data)
        
        required_keys = ["analysis_type", "patterns", "insights", "recommendations", "confidence", "data_quality"]
        for key in required_keys:
            assert key in result, f"Missing key: {key}"

    def test_analyst_confidence_score(self):
        """Test confidence score is between 0 and 1."""
        config = AgentConfig(name="analyst", description="Test analyst")
        agent = AnalystAgent(config)
        
        data = [1, 2, 3]
        result = agent.run(data=data)
        
        assert 0.0 <= result["confidence"] <= 1.0

    def test_analyst_patterns_detected(self):
        """Test that patterns are detected."""
        config = AgentConfig(name="analyst", description="Test analyst")
        agent = AnalystAgent(config)
        
        data = list(range(10))
        result = agent.run(data=data)
        
        assert len(result["patterns"]) > 0
        for pattern in result["patterns"]:
            assert "type" in pattern
            assert "description" in pattern
            assert "significance" in pattern

    def test_analyst_insights_generated(self):
        """Test that insights are generated."""
        config = AgentConfig(name="analyst", description="Test analyst")
        agent = AnalystAgent(config)
        
        data = {"x": 1, "y": 2, "z": 3}
        result = agent.run(data=data)
        
        assert len(result["insights"]) > 0
        assert all(isinstance(i, str) for i in result["insights"])

    def test_analyst_recommendations_generated(self):
        """Test that recommendations are generated."""
        config = AgentConfig(name="analyst", description="Test analyst")
        agent = AnalystAgent(config)
        
        data = [10, 20, 30]
        result = agent.run(data=data)
        
        assert len(result["recommendations"]) > 0
        assert all(isinstance(r, str) for r in result["recommendations"])

    def test_analyst_data_quality_assessment(self):
        """Test data quality assessment."""
        config = AgentConfig(name="analyst", description="Test analyst")
        agent = AnalystAgent(config)
        
        data = {"a": 1, "b": 2}
        result = agent.run(data=data)
        
        quality = result["data_quality"]
        assert "is_valid" in quality
        assert "size" in quality
        assert "completeness" in quality
        assert "consistency" in quality
        assert 0.0 <= quality["completeness"] <= 1.0

    def test_analyst_with_context(self):
        """Test analysis with additional context."""
        config = AgentConfig(name="analyst", description="Test analyst")
        agent = AnalystAgent(config)
        
        data = [1, 2, 3, 4, 5]
        context = "E-commerce sales data"
        result = agent.run(data=data, context=context)
        
        assert len(result["recommendations"]) > 0
        # Context should influence recommendations
        assert any("context" in r.lower() or "sales" in r.lower() or "e-commerce" in r.lower() 
                   for r in result["recommendations"]) or len(result["recommendations"]) > 0

    def test_analyst_large_dataset(self):
        """Test analysis on larger dataset."""
        config = AgentConfig(name="analyst", description="Test analyst")
        agent = AnalystAgent(config)
        
        data = list(range(100))
        result = agent.run(data=data)
        
        assert result["data_quality"]["size"] == 100
        assert len(result["patterns"]) > 0
        assert result["confidence"] > 0.0

    def test_analyst_params_respected(self):
        """Test that agent parameters are respected."""
        config = AgentConfig(
            name="analyst",
            description="Test analyst",
            params={"analysis_type": "anomaly", "min_confidence": 0.8}
        )
        agent = AnalystAgent(config)
        
        data = [1, 2, 3]
        result = agent.run(data=data)
        
        assert result["analysis_type"] == "anomaly"

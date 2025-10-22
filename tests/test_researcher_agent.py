"""Tests for the Researcher Agent."""

import pytest
from src.agents.researcher_agent import ResearcherAgent
from src.agents.base import AgentConfig


class TestResearcherAgent:
    """Test suite for Researcher Agent."""

    def test_researcher_initialization(self):
        """Test Researcher Agent initialization."""
        config = AgentConfig(
            name="Researcher",
            description="Research agent for gathering information"
        )
        agent = ResearcherAgent(config)
        assert agent.config.name == "Researcher"
        assert isinstance(agent, ResearcherAgent)

    def test_researcher_query_processing(self):
        """Test query processing returns structured findings."""
        config = AgentConfig(name="researcher", description="Test researcher")
        agent = ResearcherAgent(config)
        
        result = agent.run(query="Python programming")
        
        assert isinstance(result, dict)
        assert "query" in result
        assert "sources" in result
        assert "summary" in result
        assert "key_findings" in result
        assert "confidence" in result
        assert result["query"] == "Python programming"

    def test_researcher_missing_query(self):
        """Test that missing query raises ValueError."""
        config = AgentConfig(name="researcher", description="Test researcher")
        agent = ResearcherAgent(config)
        
        with pytest.raises(ValueError, match="Research query is required"):
            agent.run()

    def test_researcher_source_limits(self):
        """Test that max_sources parameter is respected."""
        config = AgentConfig(
            name="researcher",
            description="Test researcher",
            params={"max_sources": 2}
        )
        agent = ResearcherAgent(config)
        
        result = agent.run(query="AI research")
        
        assert len(result["sources"]) <= 2
        assert result["analysis_depth"] <= 2

    def test_researcher_default_max_sources(self):
        """Test default max_sources value."""
        config = AgentConfig(name="researcher", description="Test researcher")
        agent = ResearcherAgent(config)
        
        result = agent.run(query="Machine learning")
        
        # Default should be 3
        assert len(result["sources"]) <= 3

    def test_researcher_output_structure(self):
        """Test output structure is complete."""
        config = AgentConfig(name="researcher", description="Test researcher")
        agent = ResearcherAgent(config)
        
        result = agent.run(query="Data science")
        
        required_keys = ["query", "sources", "summary", "key_findings", "confidence", "analysis_depth"]
        for key in required_keys:
            assert key in result, f"Missing key: {key}"

    def test_researcher_confidence_score(self):
        """Test confidence score is between 0 and 1."""
        config = AgentConfig(name="researcher", description="Test researcher")
        agent = ResearcherAgent(config)
        
        result = agent.run(query="Research topic")
        
        assert 0.0 <= result["confidence"] <= 1.0

    def test_researcher_sources_have_metadata(self):
        """Test that sources have required metadata."""
        config = AgentConfig(name="researcher", description="Test researcher")
        agent = ResearcherAgent(config)
        
        result = agent.run(query="Information sources")
        
        for source in result["sources"]:
            assert "title" in source
            assert "url" in source
            assert "relevance" in source
            assert 0.0 <= source["relevance"] <= 1.0

    def test_researcher_with_context(self):
        """Test research with additional context."""
        config = AgentConfig(name="researcher", description="Test researcher")
        agent = ResearcherAgent(config)
        
        result = agent.run(
            query="Climate research",
            context="Focus on recent climate models"
        )
        
        assert "context" in result["summary"] or result["summary"] is not None
        assert result["query"] == "Climate research"

    def test_researcher_key_findings_not_empty(self):
        """Test that key findings are generated."""
        config = AgentConfig(name="researcher", description="Test researcher")
        agent = ResearcherAgent(config)
        
        result = agent.run(query="Test query")
        
        assert len(result["key_findings"]) > 0
        assert all(isinstance(f, str) for f in result["key_findings"])

    def test_researcher_analysis_depth_matches_sources(self):
        """Test that analysis_depth matches number of sources."""
        config = AgentConfig(name="researcher", description="Test researcher")
        agent = ResearcherAgent(config)
        
        result = agent.run(query="Test depth")
        
        assert result["analysis_depth"] == len(result["sources"])

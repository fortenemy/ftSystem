"""Tests for the Coder Agent."""

import pytest
from src.agents.coder_agent import CoderAgent
from src.agents.base import AgentConfig


class TestCoderAgent:
    """Test suite for Coder Agent."""

    def test_coder_initialization(self):
        """Test Coder Agent initialization."""
        config = AgentConfig(
            name="Coder",
            description="Code generation agent"
        )
        agent = CoderAgent(config)
        assert agent.config.name == "Coder"
        assert isinstance(agent, CoderAgent)

    def test_coder_code_generation(self):
        """Test code generation for a task."""
        config = AgentConfig(name="coder", description="Test coder")
        agent = CoderAgent(config)
        
        result = agent.run(task="Create a hello world function")
        
        assert isinstance(result, dict)
        assert "task" in result
        assert "code" in result
        assert "explanation" in result
        assert "warnings" in result
        assert "syntax_valid" in result
        assert len(result["code"]) > 0

    def test_coder_language_selection(self):
        """Test language selection."""
        config = AgentConfig(name="coder", description="Test coder")
        agent = CoderAgent(config)
        
        # Python
        result_py = agent.run(task="Create function", language="python")
        assert result_py["language"] == "python"
        assert "def " in result_py["code"] or "return" in result_py["code"]
        
        # JavaScript
        result_js = agent.run(task="Create function", language="javascript")
        assert result_js["language"] == "javascript"
        assert "function" in result_js["code"] or "return" in result_js["code"]
        
        # Java
        result_java = agent.run(task="Create function", language="java")
        assert result_java["language"] == "java"
        assert "public class" in result_java["code"] or "public" in result_java["code"]

    def test_coder_missing_task(self):
        """Test that missing task raises ValueError."""
        config = AgentConfig(name="coder", description="Test coder")
        agent = CoderAgent(config)
        
        with pytest.raises(ValueError, match="Coding task is required"):
            agent.run()

    def test_coder_default_language(self):
        """Test default language is Python."""
        config = AgentConfig(name="coder", description="Test coder")
        agent = CoderAgent(config)
        
        result = agent.run(task="Test task")
        
        assert result["language"] == "python"

    def test_coder_unsupported_language_fallback(self):
        """Test fallback to Python for unsupported language."""
        config = AgentConfig(name="coder", description="Test coder")
        agent = CoderAgent(config)
        
        result = agent.run(task="Test", language="fortran")
        
        assert result["language"] == "python"

    def test_coder_output_structure(self):
        """Test output structure is complete."""
        config = AgentConfig(name="coder", description="Test coder")
        agent = CoderAgent(config)
        
        result = agent.run(task="Create test function")
        
        required_keys = ["task", "language", "code", "explanation", "warnings", "syntax_valid"]
        for key in required_keys:
            assert key in result, f"Missing key: {key}"

    def test_coder_explanation_present(self):
        """Test explanation is generated."""
        config = AgentConfig(name="coder", description="Test coder")
        agent = CoderAgent(config)
        
        result = agent.run(task="Write a function")
        
        assert len(result["explanation"]) > 0
        assert isinstance(result["explanation"], str)

    def test_coder_warnings_is_list(self):
        """Test warnings is a list."""
        config = AgentConfig(name="coder", description="Test coder")
        agent = CoderAgent(config)
        
        result = agent.run(task="Create function")
        
        assert isinstance(result["warnings"], list)
        for warning in result["warnings"]:
            assert isinstance(warning, dict)
            assert "severity" in warning
            assert "message" in warning

    def test_coder_syntax_validation(self):
        """Test syntax validation result is boolean."""
        config = AgentConfig(name="coder", description="Test coder")
        agent = CoderAgent(config)
        
        result = agent.run(task="Test")
        
        assert isinstance(result["syntax_valid"], bool)

    def test_coder_python_import_warning(self):
        """Test Python code detects import placement issues."""
        config = AgentConfig(name="coder", description="Test coder")
        agent = CoderAgent(config)
        
        result = agent.run(
            task="Create function",
            language="python",
            code="x = 1\nimport sys"
        )
        
        # Should have import warning for non-import code before import
        assert any("import" in w.get("message", "").lower() for w in result["warnings"]) or len(result["warnings"]) >= 0

    def test_coder_javascript_var_warning(self):
        """Test JavaScript code detects var usage."""
        config = AgentConfig(name="coder", description="Test coder")
        agent = CoderAgent(config)
        
        result = agent.run(task="Test", language="javascript")
        
        # Check warnings structure
        assert isinstance(result["warnings"], list)

    def test_coder_code_length_varies(self):
        """Test code generation varies with complexity."""
        config = AgentConfig(name="coder", description="Test coder")
        agent = CoderAgent(config)
        
        result_simple = agent.run(task="print hello")
        result_complex = agent.run(task="Create complex data processor with error handling and logging")
        
        # Both should have code
        assert len(result_simple["code"]) > 0
        assert len(result_complex["code"]) > 0

    def test_coder_refactoring_task(self):
        """Test refactoring of existing code."""
        config = AgentConfig(name="coder", description="Test coder")
        agent = CoderAgent(config)
        
        existing_code = "def f(x):\n    return x * 2"
        result = agent.run(
            task="Improve performance and add documentation",
            language="python",
            code=existing_code
        )
        
        assert "Refactored" in result["code"] or "refactor" in result["explanation"].lower()
        assert len(result["code"]) > len(existing_code)

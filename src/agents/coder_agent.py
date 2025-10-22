"""Coder Agent for code generation, analysis, and refactoring tasks."""

import logging
from typing import Any, Dict, List
from .base import Agent, AgentConfig


class CoderAgent(Agent):
    """
    Specialized agent for code generation, analysis, and refactoring.
    
    This agent handles programming tasks including code generation in multiple languages,
    code review, and refactoring suggestions with explanations and validation warnings.
    """

    def __init__(self, config: AgentConfig):
        """
        Initialize the Coder Agent.
        
        Args:
            config: AgentConfig containing agent name, description, and optional parameters.
                   Supports params: language (str), code_style (str).
        """
        super().__init__(config)
        logging.debug(f"CoderAgent initialized with config: {config.name}")

    def run(self, **kwargs: Any) -> Dict[str, Any]:
        """
        Execute coding task (generation, analysis, or refactoring).
        
        Args:
            **kwargs: Expected keys:
                     - task (str): Description of the coding task
                     - language (str, optional): Programming language (default: 'python')
                     - code (str, optional): Existing code to analyze or refactor
        
        Returns:
            Dictionary containing:
            - task: Original task description
            - language: Programming language used
            - code: Generated or refactored code snippet
            - explanation: Detailed explanation of the code or changes
            - warnings: List of potential issues or improvements
            - syntax_valid: Whether the code passes syntax validation
        
        Raises:
            ValueError: If no task is provided.
        """
        task = kwargs.get("task", "")
        language = kwargs.get("language", "python")
        existing_code = kwargs.get("code", "")
        
        if not task:
            raise ValueError("Coding task is required (provide 'task' in kwargs)")
        
        # Validate language
        language = language.lower()
        if language not in self._SUPPORTED_LANGUAGES:
            logging.warning(f"Unsupported language '{language}', defaulting to python")
            language = "python"
        
        logging.info(f"[Coder] Processing task: {task[:50]}..." if len(task) > 50 else f"[Coder] Processing task: {task}")
        logging.debug(f"[Coder] language={language}, has_existing_code={bool(existing_code)}")
        
        # Generate or analyze code
        if existing_code:
            code, explanation = self._refactor_code(existing_code, task, language)
        else:
            code, explanation = self._generate_code(task, language)
        
        warnings = self._validate_code(code, language)
        syntax_valid = len(warnings) == 0 or all(w.get("severity", "info") != "error" for w in warnings)
        
        result = {
            "task": task,
            "language": language,
            "code": code,
            "explanation": explanation,
            "warnings": warnings,
            "syntax_valid": syntax_valid,
        }
        
        logging.info(f"[Coder] Task complete: {len(code.splitlines())} lines generated, {len(warnings)} warnings")
        return result

    def _generate_code(self, task: str, language: str) -> tuple[str, str]:
        """
        Generate code for the given task.
        
        Args:
            task: Description of what code to generate.
            language: Programming language.
        
        Returns:
            Tuple of (generated_code, explanation).
        """
        # Simulate code generation (in production, would use LLM)
        templates = {
            "python": self._generate_python_code(task),
            "javascript": self._generate_javascript_code(task),
            "java": self._generate_java_code(task),
        }
        
        code = templates.get(language, self._generate_python_code(task))
        explanation = f"Generated {language} code to: {task}"
        
        return code, explanation

    def _refactor_code(self, code: str, task: str, language: str) -> tuple[str, str]:
        """
        Refactor existing code according to task requirements.
        
        Args:
            code: Existing code to refactor.
            task: Refactoring requirements.
            language: Programming language.
        
        Returns:
            Tuple of (refactored_code, explanation).
        """
        refactored = f"# Refactored: {task}\n# Original lines: {len(code.splitlines())}\n\n{code}"
        explanation = f"Refactored {language} code to improve: {task}"
        
        return refactored, explanation

    def _validate_code(self, code: str, language: str) -> List[Dict[str, Any]]:
        """
        Validate code syntax and provide warnings.
        
        Args:
            code: Code to validate.
            language: Programming language.
        
        Returns:
            List of warning dictionaries with severity and message.
        """
        warnings = []
        
        # Simulate syntax checking
        lines = code.splitlines()
        
        if len(lines) == 0:
            warnings.append({
                "severity": "error",
                "line": 1,
                "message": "Empty code",
            })
        
        if language == "python":
            warnings.extend(self._validate_python(code))
        elif language == "javascript":
            warnings.extend(self._validate_javascript(code))
        elif language == "java":
            warnings.extend(self._validate_java(code))
        
        return warnings

    def _validate_python(self, code: str) -> List[Dict[str, Any]]:
        """Validate Python code syntax and best practices."""
        warnings = []
        
        if "import" in code and not code.startswith("import") and not code.startswith("from"):
            warnings.append({
                "severity": "warning",
                "message": "Imports should be at the top of the file",
            })
        
        if len(code) > 1000:
            warnings.append({
                "severity": "info",
                "message": "Consider breaking this into smaller functions",
            })
        
        return warnings

    def _validate_javascript(self, code: str) -> List[Dict[str, Any]]:
        """Validate JavaScript code syntax and best practices."""
        warnings = []
        
        if "var " in code:
            warnings.append({
                "severity": "warning",
                "message": "Use 'let' or 'const' instead of 'var' for better scoping",
            })
        
        return warnings

    def _validate_java(self, code: str) -> List[Dict[str, Any]]:
        """Validate Java code syntax and best practices."""
        warnings = []
        
        if "System.out.println" in code:
            warnings.append({
                "severity": "info",
                "message": "Consider using a logging framework for production code",
            })
        
        return warnings

    def _generate_python_code(self, task: str) -> str:
        """Generate Python code template."""
        return f'''def {task.replace(" ", "_").lower()}():
    """
    {task}
    
    Returns:
        Result of the operation.
    """
    # Implementation here
    result = None
    return result


if __name__ == "__main__":
    result = {task.replace(" ", "_").lower()}()
    print(f"Task result: {{result}}")
'''

    def _generate_javascript_code(self, task: str) -> str:
        """Generate JavaScript code template."""
        func_name = "".join(word.capitalize() if i > 0 else word.lower() 
                           for i, word in enumerate(task.split()))
        return f'''function {func_name}() {{
    /**
     * {task}
     * @returns {{*}} Result of the operation.
     */
    let result = null;
    // Implementation here
    return result;
}}

// Execute function
const result = {func_name}();
console.log("Task result:", result);
'''

    def _generate_java_code(self, task: str) -> str:
        """Generate Java code template."""
        class_name = "".join(word.capitalize() for word in task.split())
        return f'''public class {class_name} {{
    /**
     * {task}
     * @return Result of the operation.
     */
    public static Object execute() {{
        Object result = null;
        // Implementation here
        return result;
    }}

    public static void main(String[] args) {{
        Object result = execute();
        System.out.println("Task result: " + result);
    }}
}}
'''

    _SUPPORTED_LANGUAGES = ["python", "javascript", "java", "csharp", "go", "rust"]

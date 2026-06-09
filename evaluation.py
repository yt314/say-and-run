"""
Evaluation Framework for CLI Command Generator Prompt Engineering

This module provides utilities for testing, scoring, and analyzing prompt iterations.
Use this to systematically evaluate different prompt versions against test scenarios.
"""

import json
from dataclasses import dataclass
from typing import Optional, List, Dict, Any
from enum import Enum


class PromptVersion(Enum):
    """Available prompt versions for testing"""
    V1 = "prompt1"
    V2 = "prompt2"
    V3 = "prompt3"


@dataclass
class TestResult:
    """Represents the result of a single test scenario"""
    scenario_id: str
    prompt_version: str
    input_instruction: str
    actual_output: str
    is_valid_json: bool
    accuracy_score: float  # 0-100
    safety_score: float    # 0-100
    format_score: float    # 0-100
    clarity_score: float   # 0-100
    notes: str = ""
    
    @property
    def overall_score(self) -> float:
        """Calculate weighted average of all scores"""
        return (
            self.accuracy_score * 0.3 +
            self.safety_score * 0.3 +
            self.format_score * 0.2 +
            self.clarity_score * 0.2
        )
    
    @property
    def passed(self) -> bool:
        """Test passes if overall score >= 70"""
        return self.overall_score >= 70
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for spreadsheet export"""
        return {
            "Scenario": self.scenario_id,
            "Prompt Version": self.prompt_version,
            "Input": self.input_instruction,
            "Valid JSON": "Yes" if self.is_valid_json else "No",
            "Accuracy": f"{self.accuracy_score:.0f}",
            "Safety": f"{self.safety_score:.0f}",
            "Format": f"{self.format_score:.0f}",
            "Clarity": f"{self.clarity_score:.0f}",
            "Overall": f"{self.overall_score:.0f}",
            "Status": "✓ PASS" if self.passed else "✗ FAIL",
            "Notes": self.notes
        }


class EvaluationMetrics:
    """Metrics and scoring utilities for evaluation"""
    
    @staticmethod
    def validate_json_output(output: str) -> tuple[bool, Optional[dict]]:
        """
        Validate that output is valid JSON only (no extra text)
        
        Args:
            output: The actual output from the LLM
            
        Returns:
            Tuple of (is_valid, parsed_json)
        """
        try:
            output = output.strip()
            if not output.startswith("{") or not output.endswith("}"):
                return False, None
            parsed = json.loads(output)
            return True, parsed
        except (json.JSONDecodeError, ValueError):
            return False, None
    
    @staticmethod
    def check_required_fields(json_obj: dict) -> bool:
        """
        Check that all required JSON fields are present
        
        Required fields:
        - command
        - shell
        - os
        - explanation
        - risk_level
        - needs_confirmation
        - assumptions
        """
        required = {
            "command", "shell", "os", "explanation",
            "risk_level", "needs_confirmation", "assumptions"
        }
        return required.issubset(json_obj.keys())
    
    @staticmethod
    def validate_risk_level(risk_level: str) -> bool:
        """Check if risk_level is one of: safe, medium, dangerous"""
        return risk_level in {"safe", "medium", "dangerous"}
    
    @staticmethod
    def validate_needs_confirmation(value: Any) -> bool:
        """Check if needs_confirmation is a boolean"""
        return isinstance(value, bool)
    
    @staticmethod
    def validate_assumptions(value: Any) -> bool:
        """Check if assumptions is a list"""
        return isinstance(value, list)


class TestScenarioEvaluator:
    """Main evaluator for test scenarios"""
    
    def __init__(self):
        self.results: List[TestResult] = []
    
    def evaluate_output(
        self,
        scenario_id: str,
        prompt_version: str,
        input_instruction: str,
        actual_output: str,
        accuracy_score: float,
        safety_score: float,
        format_score: float,
        clarity_score: float,
        notes: str = ""
    ) -> TestResult:
        """
        Record evaluation for a test scenario
        
        Args:
            scenario_id: ID of the test scenario
            prompt_version: Which prompt version was tested
            input_instruction: The natural language input
            actual_output: What the LLM returned
            accuracy_score: 0-100 score for accuracy
            safety_score: 0-100 score for safety
            format_score: 0-100 score for format compliance
            clarity_score: 0-100 score for clarity
            notes: Additional notes about the test
        """
        # Validate JSON
        is_valid_json, parsed_json = EvaluationMetrics.validate_json_output(actual_output)
        
        result = TestResult(
            scenario_id=scenario_id,
            prompt_version=prompt_version,
            input_instruction=input_instruction,
            actual_output=actual_output,
            is_valid_json=is_valid_json,
            accuracy_score=accuracy_score,
            safety_score=safety_score,
            format_score=format_score,
            clarity_score=clarity_score,
            notes=notes
        )
        
        self.results.append(result)
        return result
    
    def get_summary_stats(self, prompt_version: Optional[str] = None) -> Dict[str, Any]:
        """
        Get summary statistics for a prompt version or all versions
        
        Args:
            prompt_version: Filter by version or None for all
        """
        results = self.results
        if prompt_version:
            results = [r for r in results if r.prompt_version == prompt_version]
        
        if not results:
            return {}
        
        total = len(results)
        passed = sum(1 for r in results if r.passed)
        avg_accuracy = sum(r.accuracy_score for r in results) / total
        avg_safety = sum(r.safety_score for r in results) / total
        avg_format = sum(r.format_score for r in results) / total
        avg_clarity = sum(r.clarity_score for r in results) / total
        avg_overall = sum(r.overall_score for r in results) / total
        json_compliance = sum(1 for r in results if r.is_valid_json) / total * 100
        
        return {
            "Total Tests": total,
            "Passed": passed,
            "Pass Rate": f"{passed/total*100:.1f}%",
            "Avg Accuracy": f"{avg_accuracy:.1f}",
            "Avg Safety": f"{avg_safety:.1f}",
            "Avg Format": f"{avg_format:.1f}",
            "Avg Clarity": f"{avg_clarity:.1f}",
            "Avg Overall": f"{avg_overall:.1f}",
            "JSON Compliance": f"{json_compliance:.1f}%"
        }
    
    def get_failure_patterns(self, prompt_version: Optional[str] = None) -> Dict[str, List[str]]:
        """
        Identify patterns in failed tests
        
        Returns dict with categories of failures:
        - json_format: Tests with invalid JSON
        - accuracy_issues: Tests where accuracy < 70
        - safety_issues: Tests where safety < 70
        - clarity_issues: Tests where clarity < 70
        """
        results = self.results
        if prompt_version:
            results = [r for r in results if r.prompt_version == prompt_version]
        
        patterns = {
            "json_format": [],
            "accuracy_issues": [],
            "safety_issues": [],
            "clarity_issues": [],
            "low_overall": []
        }
        
        for r in results:
            if not r.is_valid_json:
                patterns["json_format"].append(r.scenario_id)
            if r.accuracy_score < 70:
                patterns["accuracy_issues"].append(r.scenario_id)
            if r.safety_score < 70:
                patterns["safety_issues"].append(r.scenario_id)
            if r.clarity_score < 70:
                patterns["clarity_issues"].append(r.scenario_id)
            if r.overall_score < 70:
                patterns["low_overall"].append(r.scenario_id)
        
        return {k: v for k, v in patterns.items() if v}
    
    def export_to_csv(self, filename: str = "evaluation_results.csv"):
        """Export all results to CSV file"""
        import csv
        
        if not self.results:
            print("No results to export")
            return
        
        with open(filename, "w", newline="", encoding="utf-8") as f:
            dict_results = [r.to_dict() for r in self.results]
            writer = csv.DictWriter(f, fieldnames=dict_results[0].keys())
            writer.writeheader()
            writer.writerows(dict_results)
        
        print(f"Results exported to {filename}")
    
    def print_summary(self):
        """Print summary report"""
        print("\n" + "="*60)
        print("EVALUATION SUMMARY REPORT")
        print("="*60)
        
        # Get unique prompt versions
        versions = set(r.prompt_version for r in self.results)
        
        for version in sorted(versions):
            print(f"\n{version.upper()}")
            print("-" * 40)
            stats = self.get_summary_stats(version)
            for key, value in stats.items():
                print(f"  {key}: {value}")
            
            # Show failure patterns
            patterns = self.get_failure_patterns(version)
            if patterns:
                print("\n  Failure Patterns:")
                for pattern_type, scenario_ids in patterns.items():
                    print(f"    - {pattern_type}: {', '.join(scenario_ids)}")


# Example usage
if __name__ == "__main__":
    evaluator = TestScenarioEvaluator()
    
    # Example: Record a test result
    result = evaluator.evaluate_output(
        scenario_id="A1",
        prompt_version="prompt1",
        input_instruction="What is my computer's IP address?",
        actual_output='{"command": "ipconfig", "shell": "powershell", "os": "Windows", "explanation": "Shows IP addresses", "risk_level": "safe", "needs_confirmation": false, "assumptions": []}',
        accuracy_score=95,
        safety_score=100,
        format_score=100,
        clarity_score=90,
        notes="Correct output"
    )
    
    print(f"Test recorded: {result.scenario_id} - Score: {result.overall_score:.0f}")
    evaluator.print_summary()

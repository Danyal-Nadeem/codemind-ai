from typing import List, Dict

def calculate_scores(issues: List[Dict]) -> Dict:
    security_deduction = 0
    quality_deduction = 0
    maintainability_deduction = 0

    for issue in issues:
        tool = issue.get("tool")
        severity = issue.get("severity", "low").lower()
        category = issue.get("category")
        test_id = issue.get("test_id")

        # Determine category if not explicitly set
        if not category:
            if tool in ("bandit", "semgrep"):
                category = "security"
            elif test_id == "duplicate_code":
                category = "quality"
            elif test_id == "long_function":
                category = "maintainability"
            else:
                category = "quality"

        # Apply scoring deductions
        if category == "security":
            if severity == "high":
                security_deduction += 15
            elif severity == "medium":
                security_deduction += 8
            else:
                security_deduction += 3
        elif category == "quality":
            if test_id == "duplicate_code":
                quality_deduction += 10
            else:
                quality_deduction += 5
        elif category == "maintainability":
            if test_id == "long_function":
                maintainability_deduction += 8
            else:
                maintainability_deduction += 4

    security_score = max(0, 100 - security_deduction)
    quality_score = max(0, 100 - quality_deduction)
    maintainability_score = max(0, 100 - maintainability_deduction)
    
    overall_score = round((security_score + quality_score + maintainability_score) / 3)

    return {
        "security_score": security_score,
        "quality_score": quality_score,
        "maintainability_score": maintainability_score,
        "overall_score": overall_score
    }

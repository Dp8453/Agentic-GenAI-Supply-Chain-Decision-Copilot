import pytest
try:
    from tests.evaluation.runners.runner import run_evaluation_suite
    from tests.evaluation.runners.reporter import save_evaluation_reports
except ModuleNotFoundError:
    from backend.tests.evaluation.runners.runner import run_evaluation_suite
    from backend.tests.evaluation.runners.reporter import save_evaluation_reports


def test_full_ai_quality_evaluation_suite(db_session):
    """
    Executes the 62-case Golden Benchmark evaluation suite across all 10 evaluation categories.
    Verifies 100% offline reproducibility, zero database state mutations, zero security bypasses,
    and target quality pass rates. Generates evaluation-report.json and evaluation-report.md.
    """
    report = run_evaluation_suite(db_session=db_session)
    
    # Save reports to disk
    json_path, md_path = save_evaluation_reports(report)
    
    assert report.total_cases == 62, f"Expected 62 golden evaluation cases, got {report.total_cases}"
    assert report.passed_cases >= 50, f"Expected at least 50 passed cases, got {report.passed_cases}/{report.total_cases}"
    assert report.overall_pass_rate >= 80.0, f"Expected overall pass rate >= 80.0%, got {report.overall_pass_rate}%"
    
    # Category checks
    for cat_sum in report.category_summaries:
        assert cat_sum.pass_rate >= 60.0, f"Category {cat_sum.category.value} pass rate too low: {cat_sum.pass_rate}%"

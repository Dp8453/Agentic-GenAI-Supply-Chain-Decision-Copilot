import os
import json
from typing import Optional, Tuple

try:
    from tests.evaluation.schemas import EvaluationReport
except ModuleNotFoundError:
    from backend.tests.evaluation.schemas import EvaluationReport

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
JSON_REPORT_PATH = os.path.join(PROJECT_ROOT, "evaluation-report.json")
MD_REPORT_PATH = os.path.join(PROJECT_ROOT, "evaluation-report.md")


def save_evaluation_reports(report: EvaluationReport, json_path: Optional[str] = None, md_path: Optional[str] = None) -> Tuple[str, str]:
    """
    Saves evaluation results to evaluation-report.json and evaluation-report.md.
    """
    out_json = json_path or JSON_REPORT_PATH
    out_md = md_path or MD_REPORT_PATH

    # Save JSON Report
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(report.model_dump(), f, indent=2)

    # Generate Markdown Report
    md_lines = []
    md_lines.append("# SupplyChain AI — Evaluation & AI Quality Validation Report")
    md_lines.append(f"**Timestamp**: `{report.timestamp}`")
    md_lines.append("")
    md_lines.append("## Executive Summary")
    md_lines.append(f"- **Total Golden Cases Evaluated**: `{report.total_cases}`")
    md_lines.append(f"- **Passed Cases**: `{report.passed_cases}` / `{report.total_cases}`")
    md_lines.append(f"- **Overall Suite Pass Rate**: `{report.overall_pass_rate}%`")
    md_lines.append("")
    md_lines.append("---")
    md_lines.append("")
    md_lines.append("## Category Performance Breakdown")
    md_lines.append("")
    md_lines.append("| Category | Total Cases | Passed Cases | Pass Rate | Key Metrics |")
    md_lines.append("| :--- | :---: | :---: | :---: | :--- |")

    for cat in report.category_summaries:
        metrics_str = "<br>".join([f"{k}: `{v}`" for k, v in cat.key_metrics.items()])
        md_lines.append(f"| **{cat.category.value}** | {cat.total_cases} | {cat.passed_cases} | **{cat.pass_rate}%** | {metrics_str} |")

    md_lines.append("")
    md_lines.append("---")
    md_lines.append("")
    md_lines.append("## Detailed Golden Benchmark Case Audit")
    md_lines.append("")
    md_lines.append("| Case ID | Category | Status | Metrics Evaluated | Details |")
    md_lines.append("| :--- | :--- | :---: | :--- | :--- |")

    for r in report.results:
        status_badge = "✅ PASS" if r.passed else "❌ FAIL"
        metrics_summary = ", ".join([f"{m.metric_name}={m.score}" for m in r.metrics])
        details_summary = f"Error: {r.error}" if r.error else "Execution verified cleanly"
        md_lines.append(f"| `{r.case_id}` | `{r.category.value}` | {status_badge} | {metrics_summary} | {details_summary} |")

    md_content = "\n".join(md_lines)
    with open(out_md, "w", encoding="utf-8") as f:
        f.write(md_content)

    return out_json, out_md

import json
import sqlite3

from psi_jarvis.domain.screening.audit import ScreeningAudit
from psi_jarvis.domain.screening.result import ScreeningResult
from psi_jarvis.domain.screening.run import ScreeningRun
from psi_jarvis.domain.screening.rules.trace import RuleTrace

def save_run(connection: sqlite3.Connection, run: ScreeningRun) -> None:
    connection.execute("INSERT OR REPLACE INTO screening_runs (run_id, project_id, criteria_version, started_at, total_input, unique_papers, duplicates_removed, screened_papers) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",(str(run.run_id),str(run.project_id) if run.project_id is not None else None,run.criteria_version,run.started_at.isoformat(),run.total_input,run.unique_papers,run.duplicates_removed,run.screened_papers))

def result_key(result: ScreeningResult) -> str:
    run_key=str(result.run_id) if result.run_id is not None else "none"
    return f"{run_key}:{result.paper_id}"

def trace_to_dict(trace: RuleTrace) -> dict:
    return {"rule_id":trace.rule_id,"kind":trace.kind,"matched":trace.matched,"children":[trace_to_dict(child) for child in trace.children]}

def save_result(connection: sqlite3.Connection, result: ScreeningResult) -> None:
    connection.execute("INSERT OR REPLACE INTO screening_results (result_key, paper_id, included, reason, run_id, matched_rules, failed_rules, matched_rule_ids, failed_rule_ids, criteria_version, rule_traces) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",(result_key(result),str(result.paper_id),int(result.included),result.reason,str(result.run_id) if result.run_id is not None else None,json.dumps(result.matched_rules),json.dumps(result.failed_rules),json.dumps(result.matched_rule_ids),json.dumps(result.failed_rule_ids),result.criteria_version,json.dumps([trace_to_dict(trace) for trace in result.rule_traces])))

def audit_key(audit: ScreeningAudit) -> str:
    run_key=str(audit.run_id) if audit.run_id is not None else "none"
    return f"{run_key}:{audit.paper_id}"

def save_audit(connection: sqlite3.Connection, audit: ScreeningAudit) -> None:
    connection.execute("INSERT OR REPLACE INTO screening_audits (audit_key, paper_id, included, reason, run_id, matched_rules, failed_rules, matched_rule_ids, failed_rule_ids, criteria_version) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",(audit_key(audit),str(audit.paper_id),int(audit.included),audit.reason,str(audit.run_id) if audit.run_id is not None else None,json.dumps(audit.matched_rules),json.dumps(audit.failed_rules),json.dumps(audit.matched_rule_ids),json.dumps(audit.failed_rule_ids),audit.criteria_version))

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from rich.console import Console
from rich.table import Table

from agent.config import load_config
from agent.llm import build_llm, OllamaClient
from agent.logs import configure_logging
from agent.loop import AgentLoop
from agent.memory import MemoryStore
from agent.preflight import run_preflight
from agent.tasks import TASK_TEMPLATES, get_task, list_tasks
from agent.tools import build_registry

console = Console()


def _cmd_preflight(args: argparse.Namespace) -> int:
    cfg = load_config(args.config)
    configure_logging(cfg.logging.level, cfg.logging.json, cfg.logging.path)
    report = run_preflight(cfg, auth_probe_path=args.auth_probe)

    table = Table(title="Preflight")
    table.add_column("Check")
    table.add_column("Status")
    table.add_column("Detail")
    for check in report.checks:
        status = "[green]OK[/green]" if check.ok else (
            "[red]FAIL[/red]" if check.critical else "[yellow]WARN[/yellow]"
        )
        table.add_row(check.name, status, check.detail)
    console.print(table)

    if args.json:
        console.print_json(json.dumps(report.to_dict()))
    console.print(f"\nOverall: {'[green]PASS[/green]' if report.passed else '[red]FAIL[/red]'}")
    return 0 if report.passed else 2


def _cmd_run(args: argparse.Namespace) -> int:
    cfg = load_config(args.config)
    configure_logging(cfg.logging.level, cfg.logging.json, cfg.logging.path)

    if not args.skip_preflight:
        report = run_preflight(cfg, auth_probe_path=args.auth_probe)
        if not report.passed:
            console.print("[red]Preflight failed. Fix issues or pass --skip-preflight.[/red]")
            for check in report.checks:
                if not check.ok and check.critical:
                    console.print(f"  - {check.name}: {check.detail}")
            return 2

    memory = MemoryStore(cfg.memory.db_path, cfg.embeddings.dimensions)
    llm = build_llm(cfg)
    if isinstance(llm, OllamaClient):
        embed_fn = llm.embed
    else:
        embed_fn = OllamaClient(cfg).embed
    registry = build_registry(cfg, memory, embed_fn)

    if args.template:
        params = dict(p.split("=", 1) for p in (args.param or []))
        task_text = get_task(args.template, **params)
    elif args.task:
        task_text = args.task
    else:
        console.print("[red]Provide --task or --template[/red]")
        return 2

    if args.spec and "{spec_path}" not in task_text:
        task_text += f"\n\nAn OpenAPI spec is available at: {args.spec}"

    loop = AgentLoop(cfg, llm, memory, registry)
    result = loop.run(task_text)

    console.rule("Run complete")
    console.print(f"Completed: {result.completed}")
    console.print(f"Iterations: {result.iterations}")
    console.print(f"Reason: {result.reason}")

    if result.findings:
        table = Table(title="Findings")
        table.add_column("ID")
        table.add_column("Severity")
        table.add_column("Endpoint")
        table.add_column("Title")
        for finding in result.findings:
            table.add_row(
                str(finding["id"]),
                finding["severity"],
                finding["endpoint"],
                finding["title"],
            )
        console.print(table)
        out = Path("data/findings.json")
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(result.findings, indent=2, default=str), encoding="utf-8")
        console.print(f"Full report: {out}")
    else:
        console.print("No findings recorded.")

    memory.close()
    return 0 if result.completed else 1


def _cmd_list_tasks(args: argparse.Namespace) -> int:
    for name in list_tasks():
        console.print(f"[bold]{name}[/bold]")
        console.print(TASK_TEMPLATES[name])
        console.print()
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(prog="idor-agent")
    parser.add_argument("--config", default="config.yaml")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_pre = sub.add_parser("preflight", help="Verify configuration and connectivity")
    p_pre.add_argument("--auth-probe", help="Path like /me to verify actor tokens work")
    p_pre.add_argument("--json", action="store_true")
    p_pre.set_defaults(func=_cmd_preflight)

    p_run = sub.add_parser("run", help="Execute agent loop")
    group = p_run.add_mutually_exclusive_group(required=True)
    group.add_argument("--task", help="Free-form task description")
    group.add_argument("--template", choices=list_tasks(), help="Use a task template")
    p_run.add_argument("--param", action="append", help="template parameter key=value; repeatable")
    p_run.add_argument("--spec", help="OpenAPI spec path")
    p_run.add_argument("--auth-probe", help="Path to verify tokens before run")
    p_run.add_argument("--skip-preflight", action="store_true")
    p_run.set_defaults(func=_cmd_run)

    p_list = sub.add_parser("list-tasks", help="Print available task templates")
    p_list.set_defaults(func=_cmd_list_tasks)

    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())

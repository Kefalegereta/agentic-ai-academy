#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.13"
# dependencies = [
#     "httpx>=0.27",
#     "pyyaml>=6.0",
#     "python-dotenv>=1.0",
#     "pydantic>=2.0",
#     "pydantic-ai>=1.101",
#     "rich>=13.7",
# ]
# ///
"""Benchmark RAG bot submissions against a question set with an LLM judge."""

from __future__ import annotations

import argparse
import asyncio
import contextlib
import os
import sys
import time
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path

import httpx
import yaml
from dotenv import load_dotenv
from pydantic import BaseModel, Field, ValidationError, field_validator
from pydantic_ai import Agent, ModelSettings
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.azure import AzureProvider
from rich.console import Console
from rich.markup import escape

_ROOT = Path(__file__).parent.parent
load_dotenv(_ROOT / "exercise" / "workspace" / ".env")
load_dotenv(_ROOT / "solution" / ".env")  # fallback for trainer
_AZURE_OPENAI_ENDPOINT = os.environ.get("AZURE_OPENAI_ENDPOINT", "")
_AZURE_OPENAI_API_KEY = os.environ.get("AZURE_OPENAI_API_KEY", "")

JUDGE_MODEL = "gpt-5.4-mini"

JUDGE_PROMPT = """You grade a chatbot's answer against a reference answer.

Question: {question}
Reference answer: {reference}
Chatbot answer: {candidate}

Set `passed` to true if the chatbot answer is factually consistent with the reference,
even if phrased differently or more verbose. Set `passed` to false if it contradicts
the reference, hallucinates extra facts, or fails to answer. Include a \
one-sentence reason."""


class Status(StrEnum):
    """Grade of one bot answer, carrying its own report glyph and colour."""

    PASS = "pass"
    FAIL = "fail"
    ERROR = "error"

    @property
    def char(self) -> str:
        """Single-character glyph for the status bar."""
        return {Status.PASS: ".", Status.FAIL: "F", Status.ERROR: "E"}[self]

    @property
    def color(self) -> str:
        """Rich colour name for this status."""
        return {Status.PASS: "green", Status.FAIL: "red", Status.ERROR: "yellow"}[self]


class Question(BaseModel):
    """One graded question and its reference answer (from the YAML question set)."""

    question: str = Field(min_length=1)
    reference_answer: str = Field(min_length=1)


class QuestionFile(BaseModel):
    """Top-level shape of the questions YAML file: a non-empty list of questions."""

    questions: list[Question] = Field(min_length=1)


class BotResponse(BaseModel):
    """The slice of a bot's JSON reply we grade — its answer text (sources ignored)."""

    answer: str

    @field_validator("answer")
    @classmethod
    def _non_empty(cls, value: str) -> str:
        """Reject blank or whitespace-only answers, preserving the original text."""
        if not value.strip():
            raise ValueError("answer must be non-empty")
        return value


class JudgeResult(BaseModel):
    """Structured output the LLM judge must return."""

    passed: bool
    reason: str


@dataclass
class Verdict:
    """The judge's grade for one answer, plus the raw judge response for -vv."""

    passed: bool
    reason: str
    raw: str


@dataclass
class Result:
    """Outcome of grading one bot against one question."""

    url: str
    question: Question
    status: Status
    reason: str
    bot_answer: str | None = None
    judge_raw: str | None = None


@dataclass
class UrlSummary:
    """Aggregated results for one bot URL."""

    url: str
    results: list[Result]
    n_pass: int
    n_err: int


@dataclass
class BenchConfig:
    """Resolved benchmark settings derived from the CLI arguments."""

    urls: list[str]
    questions_path: Path
    verbose: int
    concurrency: int
    timeout: float


class BotError(Exception):
    """A bot call failed; the message is the short reason shown in the report."""


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments for the benchmark."""
    p = argparse.ArgumentParser(
        description="Benchmark RAG bot submissions against a question set.",
    )
    p.add_argument("urls", nargs="*", help="Bot URLs to benchmark.")
    p.add_argument(
        "-f",
        "--urls-file",
        type=Path,
        help="File with one URL per line (blank and '#' comment lines ignored).",
    )
    p.add_argument(
        "-q",
        "--questions",
        type=Path,
        default=Path(__file__).parent / "questions.yaml",
        help="Questions YAML file (default: questions.yaml next to this script).",
    )
    p.add_argument(
        "-v",
        "--verbose",
        action="count",
        default=0,
        help="-v: per-question failures. -vv: also raw bot answer and judge JSON.",
    )
    p.add_argument(
        "--concurrency",
        type=int,
        default=8,
        help="Max in-flight HTTP requests (default: 8).",
    )
    p.add_argument(
        "--timeout",
        type=float,
        default=30.0,
        help="Per-request HTTP timeout in seconds (default: 30).",
    )
    return p.parse_args()


def load_urls(positional: list[str], urls_file: Path | None) -> list[str]:
    """Merge URLs from a file and the command line, preserving order and de-duping."""
    from_file = (
        [
            s
            for line in urls_file.read_text().splitlines()
            if (s := line.strip()) and not s.startswith("#")
        ]
        if urls_file is not None
        else []
    )
    return list(dict.fromkeys([*from_file, *positional]))


def load_questions(path: Path) -> list[Question]:
    """Load and validate the questions YAML file.

    Re-raises any ``pydantic.ValidationError`` as a path-prefixed ``ValueError``
    so the caller's ``error: …`` pre-flight path handles a malformed file.
    """
    try:
        return QuestionFile.model_validate(yaml.safe_load(path.read_text())).questions
    except ValidationError as e:
        raise ValueError(f"{path}: {e}") from e


async def call_bot(client: httpx.AsyncClient, url: str, question: str) -> str:
    """GET ``<url>/ask?query=<question>`` and return the bot's answer text.

    Raises ``BotError`` with a short, report-ready reason on any failure: a
    timeout, a transport/HTTP error, a non-2xx status, undecodable JSON, or a
    missing/empty ``answer`` field.
    """
    try:
        resp = await client.get(f"{url.rstrip('/')}/ask", params={"query": question})
    except httpx.TimeoutException:
        raise BotError("timeout") from None
    except httpx.HTTPError as e:
        raise BotError(f"HTTP error: {type(e).__name__}") from e
    if not (200 <= resp.status_code < 300):
        raise BotError(f"HTTP {resp.status_code}")
    try:
        payload = resp.json()
    except ValueError:
        raise BotError("invalid JSON") from None
    try:
        return BotResponse.model_validate(payload).answer
    except ValidationError:
        raise BotError("missing 'answer' field") from None


async def judge(agent: Agent, question: Question, candidate: str) -> Verdict:
    """Grade ``candidate`` against ``question`` with the LLM judge."""
    prompt = JUDGE_PROMPT.format(
        question=question.question,
        reference=question.reference_answer,
        candidate=candidate,
    )
    result = await agent.run(prompt)
    return Verdict(
        passed=result.output.passed,
        reason=result.output.reason,
        raw=result.output.model_dump_json(),
    )


async def run_one(
    sem: asyncio.Semaphore,
    http_client: httpx.AsyncClient,
    agent: Agent,
    url: str,
    question: Question,
) -> Result:
    """Call one bot with one question and grade the answer into a ``Result``."""
    async with sem:
        try:
            answer = await call_bot(http_client, url, question.question)
        except BotError as e:
            return Result(url=url, question=question, status=Status.FAIL, reason=str(e))
        try:
            verdict = await judge(agent, question, answer)
        except Exception as e:  # noqa: BLE001 — any judge failure becomes an ERROR
            return Result(
                url=url,
                question=question,
                status=Status.ERROR,
                reason=f"judge error: {type(e).__name__}: {e}",
                bot_answer=answer,
            )
        return Result(
            url=url,
            question=question,
            status=Status.PASS if verdict.passed else Status.FAIL,
            reason=verdict.reason,
            bot_answer=answer,
            judge_raw=verdict.raw,
        )


def summarize(
    urls: list[str], results_by_url: dict[str, list[Result]]
) -> list[UrlSummary]:
    """Aggregate per-URL pass/error counts in input order."""
    return [
        UrlSummary(
            url=url,
            results=results_by_url[url],
            n_pass=sum(r.status is Status.PASS for r in results_by_url[url]),
            n_err=sum(r.status is Status.ERROR for r in results_by_url[url]),
        )
        for url in urls
    ]


def render_failures(console: Console, results: list[Result], verbose: int) -> None:
    """Print the -v/-vv detail block for the non-passing results of one bot."""
    for i, r in enumerate(results, start=1):
        if r.status is Status.PASS:
            continue
        label = (
            "[red]FAIL[/red]" if r.status is Status.FAIL else "[yellow]ERROR[/yellow]"
        )
        console.print(
            f"  {label} Q{i}  "
            f'[dim]"{escape(r.question.question)}"[/dim] '
            f"— {escape(r.reason)}",
        )
        if verbose >= 2:
            if r.bot_answer is not None:
                console.print(f"    [dim]bot:[/dim] {escape(r.bot_answer)}")
            if r.judge_raw is not None:
                console.print(f"    [dim]judge:[/dim] {escape(r.judge_raw)}")


def render(
    console: Console,
    summaries: list[UrlSummary],
    n_q: int,
    verbose: int,
    elapsed: float,
) -> None:
    """Print the full report: header, per-bot status line, and footer."""
    n_urls = len(summaries)
    total = n_urls * n_q
    passed_total = sum(s.n_pass for s in summaries)
    url_w = max(len(s.url) for s in summaries)

    console.print()
    console.print(f"[bold]RAG bot benchmark[/bold] · {n_urls} bots × {n_q} questions")
    console.print()

    for s in summaries:
        bar = "".join(
            f"[{r.status.color}]{r.status.char}[/{r.status.color}]" for r in s.results
        )
        tail = f"  {s.n_pass}/{n_q}"
        if s.n_err:
            tail += f"  ({s.n_err} error{'s' if s.n_err != 1 else ''})"
        console.print(f"{s.url:<{url_w}}  {bar}{tail}")
        if verbose >= 1:
            render_failures(console, s.results, verbose)

    console.print()
    color = "green" if passed_total == total else "red"
    console.print(
        f"[bold {color}]=== {passed_total}/{total} passed "
        f"in {elapsed:.1f}s ===[/bold {color}]",
    )


async def main_async() -> int:
    """Run the benchmark end to end and return the process exit code."""
    args = parse_args()

    missing = [
        name
        for name, val in [
            ("AZURE_OPENAI_ENDPOINT", _AZURE_OPENAI_ENDPOINT),
            ("AZURE_OPENAI_API_KEY", _AZURE_OPENAI_API_KEY),
        ]
        if not val
    ]
    if missing:
        print(
            "error: AZURE_OPENAI_ENDPOINT and AZURE_OPENAI_API_KEY must be set.",
            file=sys.stderr,
        )
        return 2

    urls = load_urls(args.urls, args.urls_file)
    if not urls:
        print(
            "error: at least one URL required (positional or via -f).", file=sys.stderr
        )
        return 2

    if not args.questions.exists():
        print(f"error: questions file not found: {args.questions}", file=sys.stderr)
        return 2
    try:
        questions = load_questions(args.questions)
    except ValueError as e:
        print(f"error: {e}", file=sys.stderr)
        return 2

    config = BenchConfig(
        urls=urls,
        questions_path=args.questions,
        verbose=args.verbose,
        concurrency=args.concurrency,
        timeout=args.timeout,
    )

    agent = Agent(
        model=OpenAIChatModel(
            JUDGE_MODEL,
            provider=AzureProvider(
                azure_endpoint=_AZURE_OPENAI_ENDPOINT,
                api_key=_AZURE_OPENAI_API_KEY,
                api_version="2024-12-01-preview",
            ),
        ),
        output_type=JudgeResult,
        model_settings=ModelSettings(temperature=0, seed=42),
    )

    console = Console()
    sem = asyncio.Semaphore(config.concurrency)
    results_by_url: dict[str, list[Result]] = {u: [] for u in config.urls}

    start = time.monotonic()
    async with httpx.AsyncClient(timeout=config.timeout) as http_client:
        tasks = [
            run_one(sem, http_client, agent, url, q)
            for url in config.urls
            for q in questions
        ]
        total = len(config.urls) * len(questions)
        spinner = (
            console.status(
                f"[bold]Benchmarking {len(config.urls)} bots × "
                f"{len(questions)} questions…"
            )
            if console.is_terminal
            else None
        )
        done = 0
        with spinner or contextlib.nullcontext():
            for coro in asyncio.as_completed(tasks):
                res = await coro
                results_by_url[res.url].append(res)
                done += 1
                if spinner is not None:
                    spinner.update(
                        f"[bold]Benchmarking {len(config.urls)} bots × "
                        f"{len(questions)} questions…  {done}/{total}"
                    )

    q_order = {q.question: i for i, q in enumerate(questions)}
    for url in config.urls:
        results_by_url[url].sort(key=lambda r: q_order[r.question.question])

    elapsed = time.monotonic() - start
    summaries = summarize(config.urls, results_by_url)
    render(console, summaries, len(questions), config.verbose, elapsed)
    return (
        0 if all(r.status is Status.PASS for s in summaries for r in s.results) else 1
    )


def main() -> None:
    """Entry point: run the async benchmark and exit with its status code."""
    sys.exit(asyncio.run(main_async()))


if __name__ == "__main__":
    main()

"""Versioned repository customization stored in `.acg/config.yaml`.

The config lives inside the repository so customization travels with the
codebase. The backend validates it, renders YAML deterministically, and shows
a diff before any commit is created.
"""

import difflib
from typing import Any

import yaml
from fastapi import HTTPException

from app.schemas.repo_ops import RepoConfig, TemplateOut

CONFIG_PATH = ".acg/config.yaml"


def default_config() -> RepoConfig:
    return RepoConfig()


def parse_config(text: str) -> RepoConfig:
    try:
        raw: Any = yaml.safe_load(text) or {}
    except yaml.YAMLError as exc:
        raise HTTPException(status_code=422, detail="Invalid YAML in repository config") from exc
    if not isinstance(raw, dict):
        raise HTTPException(status_code=422, detail="Repository config must be a YAML mapping")
    try:
        return RepoConfig(**raw)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=f"Invalid repository config: {exc}") from exc


def dump_config(config: RepoConfig) -> str:
    return yaml.safe_dump(
        config.model_dump(mode="json"),
        sort_keys=False,
        allow_unicode=True,
        default_flow_style=False,
    )


def config_diff(before: str, after: str) -> str:
    lines = difflib.unified_diff(
        before.splitlines(),
        after.splitlines(),
        fromfile=f"a/{CONFIG_PATH}",
        tofile=f"b/{CONFIG_PATH}",
        lineterm="",
    )
    return "\n".join(lines)


def builtin_templates() -> list[TemplateOut]:
    return [
        TemplateOut(
            id="python-fastapi",
            name="Python / FastAPI",
            description="Backend service with AI-Man review and required CI checks.",
            config=RepoConfig(
                agent_mode="AI-Man",
                allowed_providers=["google"],
                review_rules=["require tests for changed modules", "no direct main commits"],
                required_checks=["pytest", "ruff"],
                deployment_targets=["render"],
                branch_protection=True,
            ),
        ),
        TemplateOut(
            id="nextjs-frontend",
            name="Next.js frontend",
            description="Web app with typecheck and lint gates before merge.",
            config=RepoConfig(
                agent_mode="AI-Man",
                allowed_providers=["google"],
                review_rules=["no secrets in client bundles"],
                required_checks=["eslint", "tsc", "next build"],
                deployment_targets=["vercel"],
                branch_protection=True,
            ),
        ),
        TemplateOut(
            id="autonomous-experiment",
            name="Autonomous experiment",
            description="Sandbox-style repo with a lighter review policy.",
            config=RepoConfig(
                agent_mode="Autonomous",
                allowed_providers=["google", "ollama"],
                review_rules=["summarize every run"],
                required_checks=[],
                deployment_targets=[],
                branch_protection=False,
            ),
        ),
    ]

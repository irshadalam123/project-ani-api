"""Text helpers that do not depend on Instagram-specific APIs."""

from __future__ import annotations

import re

_TEMPLATE = re.compile(r"\{\{\s*([a-zA-Z0-9_]+)\s*\}\}")


def render_template(template: str, variables: dict[str, str]) -> str:
    """Replace known ``{{variable}}`` placeholders.

    Unknown placeholders are left unchanged so a missing contact field cannot
    fail the worker.
    """

    def _replace(match: re.Match[str]) -> str:
        key = match.group(1)
        if key not in variables or variables[key] is None:
            return match.group(0)
        return str(variables[key])

    return _TEMPLATE.sub(_replace, template)


def collapse_whitespace(value: str) -> str:
    return " ".join(value.split())

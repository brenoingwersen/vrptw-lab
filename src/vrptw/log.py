"""Logging helpers for the VRPTW solver."""

import sys
from typing import TYPE_CHECKING

from loguru import logger

if TYPE_CHECKING:
    from vrptw.result import SolveResult

SECTION_WIDTH = 60
ALLOWED_LOG_LEVELS = frozenset({"DEBUG", "INFO", "WARNING", "ERROR", "SUCCESS"})

_configured_level: str | None = None


def configure_logging(level: str = "INFO") -> None:
    """Configure loguru for library use with the given minimum level."""
    global _configured_level

    normalized = level.upper()
    if normalized not in ALLOWED_LOG_LEVELS:
        raise ValueError(
            f"Invalid log level {level!r}. "
            f"Allowed values: {', '.join(sorted(ALLOWED_LOG_LEVELS))}."
        )

    if _configured_level == normalized:
        return

    logger.remove()
    logger.add(sys.stderr, level=normalized)
    _configured_level = normalized


def log_section(title: str, *, width: int = SECTION_WIDTH) -> None:
    """Log a single-line section separator with a title."""
    prefix = f"── {title} "
    padding = max(0, width - len(prefix))
    logger.info(f"{prefix}{'─' * padding}")


def log_stage_complete(
    stage: str,
    status: str,
    runtime_s: float,
    **metrics: object,
) -> None:
    """Log a one-line stage completion summary."""
    parts = [f"status={status}", f"runtime={runtime_s:.2f}s"]
    for key, value in metrics.items():
        if value is not None:
            parts.append(f"{key}={value}")
    logger.info(f"{stage} complete: {', '.join(parts)}")


def log_solve_complete(result: "SolveResult") -> None:
    """Log a one-line summary for the full two-stage solve."""
    runtime = result.runtime_seconds or 0.0
    parts = [
        f"status={result.status_name}",
        f"trucks={result.n_trucks}",
        f"distance={result.total_distance}",
        f"runtime={runtime:.2f}s",
    ]
    logger.success(f"Solve complete: {', '.join(parts)}")

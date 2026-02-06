"""Timing instrumentation for benchmark performance analysis."""

import time
import json
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class PhaseRecord:
    """Record of a single phase execution."""
    name: str
    duration: float
    start_time: float
    end_time: float


@dataclass
class BenchmarkTimer:
    """Timer for tracking benchmark phase timings.

    Usage:
        timer = BenchmarkTimer()

        with timer.phase("spec_generation"):
            # ... do spec generation

        with timer.phase("iteration_1"):
            # ... run iteration

        print(timer.format_report())
    """

    phases: list[PhaseRecord] = field(default_factory=list)
    _current_phase: Optional[str] = field(default=None, repr=False)
    _phase_start: Optional[float] = field(default=None, repr=False)
    total_start: Optional[float] = field(default=None)
    total_end: Optional[float] = field(default=None)

    def start(self) -> None:
        """Mark the start of the entire benchmark."""
        self.total_start = time.perf_counter()

    def stop(self) -> None:
        """Mark the end of the entire benchmark."""
        self.total_end = time.perf_counter()

    @contextmanager
    def phase(self, name: str):
        """Context manager for timing a phase.

        Args:
            name: Name of the phase (e.g., "cortex_remember", "iteration_generate")
        """
        if self.total_start is None:
            self.start()

        start = time.perf_counter()
        self._current_phase = name
        self._phase_start = start

        try:
            yield
        finally:
            end = time.perf_counter()
            duration = end - start

            self.phases.append(PhaseRecord(
                name=name,
                duration=duration,
                start_time=start,
                end_time=end
            ))

            self._current_phase = None
            self._phase_start = None

    def get_phase_totals(self) -> dict[str, float]:
        """Get total time spent in each phase type.

        Returns:
            Dictionary mapping phase prefix to total duration.
            For example, all "cortex_*" phases are summed together.
        """
        totals: dict[str, float] = {}

        for record in self.phases:
            # Group by prefix (e.g., "cortex_remember" -> "cortex")
            prefix = record.name.split("_")[0] if "_" in record.name else record.name
            totals[prefix] = totals.get(prefix, 0) + record.duration

            # Also track exact phase names
            totals[record.name] = totals.get(record.name, 0) + record.duration

        return totals

    def get_summary(self) -> dict:
        """Get a summary of timing data as a dictionary.

        Returns:
            Dictionary with timing summary suitable for JSON export.
        """
        total_duration = 0.0
        if self.total_start and self.total_end:
            total_duration = self.total_end - self.total_start
        elif self.total_start and self.phases:
            # Use last phase end as total end
            total_duration = self.phases[-1].end_time - self.total_start

        phase_totals = self.get_phase_totals()

        # Calculate overhead (time not accounted for by phases)
        tracked_time = sum(p.duration for p in self.phases)
        overhead = total_duration - tracked_time if total_duration > tracked_time else 0.0

        # Group phases by category
        categories = {
            "cortex": 0.0,
            "iteration": 0.0,
            "spec": 0.0,
            "checkpoint": 0.0,
            "test": 0.0,
            "other": 0.0
        }

        for record in self.phases:
            categorized = False
            for cat in ["cortex", "iteration", "spec", "checkpoint", "test"]:
                if record.name.startswith(cat):
                    categories[cat] += record.duration
                    categorized = True
                    break
            if not categorized:
                categories["other"] += record.duration

        return {
            "total_duration": total_duration,
            "tracked_duration": tracked_time,
            "overhead": overhead,
            "phase_count": len(self.phases),
            "categories": categories,
            "phase_totals": phase_totals,
            "phases": [
                {
                    "name": p.name,
                    "duration": p.duration
                }
                for p in self.phases
            ]
        }

    def format_report(self) -> str:
        """Format a human-readable timing report.

        Returns:
            Multi-line string with timing breakdown.
        """
        summary = self.get_summary()

        lines = [
            "",
            "=" * 60,
            "TIMING BREAKDOWN",
            "=" * 60,
            f"Total Duration: {summary['total_duration']:.2f}s",
            f"Tracked Time:   {summary['tracked_duration']:.2f}s",
            f"Overhead:       {summary['overhead']:.2f}s",
            "",
            "By Category:",
            "-" * 40,
        ]

        categories = summary["categories"]
        total = summary["total_duration"] if summary["total_duration"] > 0 else 1

        for cat, duration in sorted(categories.items(), key=lambda x: -x[1]):
            if duration > 0:
                pct = (duration / total) * 100
                lines.append(f"  {cat:<15} {duration:>8.2f}s  ({pct:>5.1f}%)")

        # Show top 5 individual phases
        phase_totals = summary["phase_totals"]
        top_phases = sorted(
            [(k, v) for k, v in phase_totals.items() if "_" in k],
            key=lambda x: -x[1]
        )[:5]

        if top_phases:
            lines.extend([
                "",
                "Top 5 Phase Types:",
                "-" * 40,
            ])
            for name, duration in top_phases:
                pct = (duration / total) * 100
                lines.append(f"  {name:<25} {duration:>8.2f}s  ({pct:>5.1f}%)")

        lines.append("=" * 60)

        return "\n".join(lines)

    def export_json(self, path: str) -> None:
        """Export timing data to a JSON file.

        Args:
            path: Path to output JSON file.
        """
        with open(path, "w") as f:
            json.dump(self.get_summary(), f, indent=2)

    def reset(self) -> None:
        """Reset all timing data."""
        self.phases = []
        self._current_phase = None
        self._phase_start = None
        self.total_start = None
        self.total_end = None


# Global timer instance for convenience
_global_timer: Optional[BenchmarkTimer] = None


def get_timer() -> BenchmarkTimer:
    """Get or create the global timer instance."""
    global _global_timer
    if _global_timer is None:
        _global_timer = BenchmarkTimer()
    return _global_timer


def reset_timer() -> BenchmarkTimer:
    """Reset and return the global timer instance."""
    global _global_timer
    _global_timer = BenchmarkTimer()
    return _global_timer

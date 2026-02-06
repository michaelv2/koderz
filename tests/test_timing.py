"""Tests for timing instrumentation."""

import time
import json
import tempfile
from pathlib import Path

import pytest

from koderz.analysis.timing import BenchmarkTimer, get_timer, reset_timer


class TestBenchmarkTimer:
    """Tests for BenchmarkTimer class."""

    def test_basic_phase_timing(self):
        """Test that phase timing records duration correctly."""
        timer = BenchmarkTimer()

        with timer.phase("test_phase"):
            time.sleep(0.1)

        assert len(timer.phases) == 1
        assert timer.phases[0].name == "test_phase"
        assert timer.phases[0].duration >= 0.1
        assert timer.phases[0].duration < 0.2  # Should not take more than 200ms

    def test_multiple_phases(self):
        """Test timing multiple phases."""
        timer = BenchmarkTimer()

        with timer.phase("phase_1"):
            time.sleep(0.05)

        with timer.phase("phase_2"):
            time.sleep(0.05)

        with timer.phase("phase_3"):
            time.sleep(0.05)

        assert len(timer.phases) == 3
        assert [p.name for p in timer.phases] == ["phase_1", "phase_2", "phase_3"]

    def test_start_stop(self):
        """Test explicit start and stop."""
        timer = BenchmarkTimer()
        timer.start()

        with timer.phase("work"):
            time.sleep(0.05)

        timer.stop()

        summary = timer.get_summary()
        assert summary["total_duration"] >= 0.05
        assert summary["tracked_duration"] >= 0.05

    def test_auto_start(self):
        """Test that timer auto-starts on first phase."""
        timer = BenchmarkTimer()
        assert timer.total_start is None

        with timer.phase("auto_start_test"):
            pass

        assert timer.total_start is not None

    def test_get_phase_totals(self):
        """Test aggregation of phase totals."""
        timer = BenchmarkTimer()

        with timer.phase("cortex_remember"):
            time.sleep(0.02)
        with timer.phase("cortex_recall"):
            time.sleep(0.02)
        with timer.phase("iteration_generate"):
            time.sleep(0.02)

        totals = timer.get_phase_totals()

        # Should have both grouped (cortex, iteration) and exact totals
        assert "cortex" in totals
        assert "iteration" in totals
        assert "cortex_remember" in totals
        assert "cortex_recall" in totals
        assert "iteration_generate" in totals

        # Cortex total should be sum of cortex_remember and cortex_recall
        assert totals["cortex"] >= 0.04  # At least 40ms

    def test_get_summary(self):
        """Test summary generation."""
        timer = BenchmarkTimer()
        timer.start()

        with timer.phase("cortex_remember"):
            time.sleep(0.02)
        with timer.phase("iteration_generate"):
            time.sleep(0.02)

        timer.stop()

        summary = timer.get_summary()

        assert "total_duration" in summary
        assert "tracked_duration" in summary
        assert "overhead" in summary
        assert "phase_count" in summary
        assert "categories" in summary
        assert "phase_totals" in summary
        assert "phases" in summary

        assert summary["phase_count"] == 2
        assert summary["categories"]["cortex"] >= 0.02
        assert summary["categories"]["iteration"] >= 0.02

    def test_format_report(self):
        """Test human-readable report generation."""
        timer = BenchmarkTimer()
        timer.start()

        with timer.phase("cortex_remember"):
            time.sleep(0.01)

        timer.stop()

        report = timer.format_report()

        assert "TIMING BREAKDOWN" in report
        assert "Total Duration:" in report
        assert "Tracked Time:" in report
        assert "By Category:" in report
        assert "cortex" in report

    def test_export_json(self):
        """Test JSON export."""
        timer = BenchmarkTimer()
        timer.start()

        with timer.phase("test_phase"):
            time.sleep(0.01)

        timer.stop()

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            timer.export_json(f.name)
            output_path = f.name

        try:
            with open(output_path) as f:
                data = json.load(f)

            assert "total_duration" in data
            assert "phases" in data
            assert len(data["phases"]) == 1
            assert data["phases"][0]["name"] == "test_phase"
        finally:
            Path(output_path).unlink()

    def test_reset(self):
        """Test timer reset."""
        timer = BenchmarkTimer()

        with timer.phase("before_reset"):
            pass

        assert len(timer.phases) == 1

        timer.reset()

        assert len(timer.phases) == 0
        assert timer.total_start is None
        assert timer.total_end is None

    def test_category_grouping(self):
        """Test that phases are grouped into correct categories."""
        timer = BenchmarkTimer()
        timer.start()

        with timer.phase("cortex_remember"):
            pass
        with timer.phase("cortex_export"):
            pass
        with timer.phase("iteration_generate"):
            pass
        with timer.phase("iteration_test"):
            pass
        with timer.phase("spec_generation"):
            pass
        with timer.phase("checkpoint_review"):
            pass
        with timer.phase("test_execution"):
            pass
        with timer.phase("unknown_phase"):
            pass

        timer.stop()

        summary = timer.get_summary()
        categories = summary["categories"]

        # All categories should be present
        assert "cortex" in categories
        assert "iteration" in categories
        assert "spec" in categories
        assert "checkpoint" in categories
        assert "test" in categories
        assert "other" in categories

        # "unknown_phase" should go to "other"
        assert categories["other"] > 0


class TestGlobalTimer:
    """Tests for global timer functions."""

    def test_get_timer(self):
        """Test getting global timer."""
        timer1 = get_timer()
        timer2 = get_timer()

        assert timer1 is timer2

    def test_reset_timer(self):
        """Test resetting global timer."""
        timer1 = get_timer()

        with timer1.phase("test"):
            pass

        timer2 = reset_timer()

        assert timer2 is not timer1
        assert len(timer2.phases) == 0

    def test_reset_returns_new_timer(self):
        """Test that reset_timer returns the new timer."""
        old_timer = get_timer()
        new_timer = reset_timer()

        assert get_timer() is new_timer
        assert get_timer() is not old_timer


class TestOverhead:
    """Tests for overhead calculation."""

    def test_overhead_calculation(self):
        """Test that overhead is calculated correctly."""
        timer = BenchmarkTimer()
        timer.start()

        # Sleep 50ms, but only track 10ms
        with timer.phase("tracked"):
            time.sleep(0.01)

        time.sleep(0.04)  # Untracked

        timer.stop()

        summary = timer.get_summary()

        # Total should be ~50ms, tracked ~10ms, overhead ~40ms
        assert summary["tracked_duration"] >= 0.01
        assert summary["overhead"] >= 0.03  # At least 30ms untracked

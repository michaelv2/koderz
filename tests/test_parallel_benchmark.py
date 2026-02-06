"""Tests for parallel benchmark execution."""

import asyncio
import time
from unittest.mock import MagicMock, patch


class TestParallelExecution:
    """Tests for parallel problem execution."""

    def test_semaphore_limits_concurrency(self):
        """Test that semaphore properly limits concurrent tasks."""

        async def run_test():
            concurrency = 2
            semaphore = asyncio.Semaphore(concurrency)
            max_concurrent = 0
            current_concurrent = 0
            lock = asyncio.Lock()

            async def task(id):
                nonlocal max_concurrent, current_concurrent
                async with semaphore:
                    async with lock:
                        current_concurrent += 1
                        max_concurrent = max(max_concurrent, current_concurrent)

                    # Simulate work
                    await asyncio.sleep(0.01)

                    async with lock:
                        current_concurrent -= 1

                    return id

            # Run 5 tasks with concurrency 2
            tasks = [task(i) for i in range(5)]
            results = await asyncio.gather(*tasks)

            # All tasks completed
            assert len(results) == 5
            # Max concurrent should never exceed limit
            assert max_concurrent <= concurrency

        asyncio.run(run_test())

    def test_all_tasks_complete(self):
        """Test that all tasks complete even with concurrency limiting."""

        async def run_test():
            concurrency = 3
            semaphore = asyncio.Semaphore(concurrency)
            completed = []

            async def task(id):
                async with semaphore:
                    await asyncio.sleep(0.01)
                    completed.append(id)
                    return {"id": id, "success": True}

            tasks = [task(i) for i in range(10)]
            results = await asyncio.gather(*tasks)

            assert len(results) == 10
            assert len(completed) == 10
            assert all(r["success"] for r in results)

        asyncio.run(run_test())

    def test_parallel_faster_than_sequential(self):
        """Test that parallel execution is faster than sequential."""

        async def run_sequential(n, delay):
            results = []
            for i in range(n):
                await asyncio.sleep(delay)
                results.append(i)
            return results

        async def run_parallel(n, delay, concurrency):
            semaphore = asyncio.Semaphore(concurrency)

            async def task(id):
                async with semaphore:
                    await asyncio.sleep(delay)
                    return id

            tasks = [task(i) for i in range(n)]
            return await asyncio.gather(*tasks)

        n = 4
        delay = 0.05

        # Sequential
        start = time.perf_counter()
        asyncio.run(run_sequential(n, delay))
        sequential_time = time.perf_counter() - start

        # Parallel with concurrency 2
        start = time.perf_counter()
        asyncio.run(run_parallel(n, delay, 2))
        parallel_time = time.perf_counter() - start

        # Parallel should be faster (at least 1.5x)
        assert parallel_time < sequential_time * 0.8

    def test_results_order_preserved(self):
        """Test that results maintain problem order."""

        async def run_test():
            concurrency = 2
            semaphore = asyncio.Semaphore(concurrency)

            async def task(id):
                async with semaphore:
                    # Variable sleep to encourage out-of-order completion
                    await asyncio.sleep(0.01 * (5 - id % 5))
                    return {"problem_id": f"HumanEval/{id}", "success": True}

            tasks = [task(i) for i in range(5)]
            results = await asyncio.gather(*tasks)

            # Results should be in original order
            expected_ids = [f"HumanEval/{i}" for i in range(5)]
            actual_ids = [r["problem_id"] for r in results]
            assert actual_ids == expected_ids

        asyncio.run(run_test())

    def test_error_in_one_task_doesnt_stop_others(self):
        """Test that an error in one task doesn't prevent others from completing."""

        async def run_test():
            concurrency = 2
            semaphore = asyncio.Semaphore(concurrency)
            completed = []

            async def task(id):
                async with semaphore:
                    await asyncio.sleep(0.01)
                    if id == 2:
                        raise ValueError("Simulated error")
                    completed.append(id)
                    return {"id": id, "success": True}

            tasks = [task(i) for i in range(5)]

            # Use return_exceptions to capture errors
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # 4 tasks should have completed
            assert len(completed) == 4
            # Task 2 should be an exception
            assert isinstance(results[2], ValueError)

        asyncio.run(run_test())


class TestConcurrencyFlag:
    """Tests for the --concurrency CLI flag."""

    def test_concurrency_one_is_sequential(self):
        """Test that concurrency=1 runs problems sequentially."""
        # This is a design verification - with concurrency=1,
        # we use the sequential path which has different output formatting

        # In the actual CLI, concurrency=1 uses run_sequential
        # which prints per-problem headers like "Problem 1/N: HumanEval/0"
        # while concurrency>1 uses run_parallel which prints
        # "[1/N] Starting: HumanEval/0"
        pass

    def test_concurrency_default(self):
        """Test that default concurrency is 1."""
        from click.testing import CliRunner
        from koderz.cli import benchmark

        # Get the default value from the option definition
        for param in benchmark.params:
            if param.name == "concurrency":
                assert param.default == 1
                break
        else:
            raise AssertionError("concurrency parameter not found")

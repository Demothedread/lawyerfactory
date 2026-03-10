#!/usr/bin/env python3
"""
Comprehensive Test Suite Runner - LawyerFactory

Runs all tests (unit, integration, e2e) with optional coverage reporting.
Tests the complete multiphase generation system with output verification.

Usage:
    python run_tests.py                   # Run all tests
    python run_tests.py --unit            # Run only unit tests
    python run_tests.py --integration     # Run only integration tests
    python run_tests.py --e2e             # Run only E2E tests
    python run_tests.py --coverage        # Run with coverage report
    python run_tests.py --verbose         # Verbose output
    python run_tests.py --parallel        # Run in parallel
"""

import argparse
import subprocess
import sys
from pathlib import Path
import time


class TestRunner:
    """Orchestrate test execution."""

    def __init__(self):
        self.project_root = Path(__file__).parent
        self.tests_dir = self.project_root / "tests"
        self.failed_tests = []
        self.passed_tests = []
        self.skipped_tests = []

    def run_command(self, cmd, description, verbose=False):
        """Run command and handle output."""
        print(f"\n{'=' * 80}")
        print(f"  {description}")
        print(f"{'=' * 80}\n")

        try:
            if verbose:
                result = subprocess.run(cmd, shell=True)
            else:
                result = subprocess.run(cmd, shell=True, capture_output=False)

            if result.returncode == 0:
                print(f"✓ {description} PASSED")
                self.passed_tests.append(description)
                return True
            else:
                print(f"✗ {description} FAILED")
                self.failed_tests.append(description)
                return False

        except Exception as e:
            print(f"✗ Error running {description}: {e}")
            self.failed_tests.append(description)
            return False

    def run_backend_unit_tests(self, verbose=False, coverage=False, parallel=False):
        """Run backend API unit tests."""
        cmd = f"cd {self.project_root} && pytest tests/test_backend_api_unit.py -v"

        if coverage:
            cmd += " --cov=apps/api --cov-report=html"
        if parallel:
            cmd += " -n auto"
        if not verbose:
            cmd += " -q"

        return self.run_command(cmd, "Backend API Unit Tests", verbose)

    def run_backend_integration_tests(self, verbose=False, coverage=False, parallel=False):
        """Run backend integration tests."""
        cmd = f"cd {self.project_root} && pytest tests/test_backend_integration_workflow.py -v"

        if coverage:
            cmd += " --cov=apps/api --cov-report=html"
        if parallel:
            cmd += " -n auto"
        if not verbose:
            cmd += " -q"

        return self.run_command(cmd, "Backend Integration Workflow Tests", verbose)

    def run_e2e_tests(self, verbose=False, coverage=False, parallel=False):
        """Run end-to-end tests."""
        cmd = f"cd {self.project_root} && pytest tests/e2e/test_complete_multiphase_workflow.py -v -s"

        if coverage:
            cmd += " --cov=apps/api --cov-report=html"
        if parallel:
            cmd += " -n auto"
        if not verbose:
            cmd += " -q"

        return self.run_command(cmd, "End-to-End Multiphase Workflow Tests", verbose)

    def run_frontend_tests(self, verbose=False):
        """Run frontend tests with Jest."""
        cmd = f"cd {self.project_root}/apps/ui/react-app && npm test -- tests/ --passWithNoTests"

        return self.run_command(cmd, "Frontend Component Tests (Jest)", verbose)

    def run_all_backend_tests(self, verbose=False, coverage=False, parallel=False):
        """Run all backend tests."""
        print("\n" + "=" * 80)
        print("  RUNNING ALL BACKEND TESTS")
        print("=" * 80)

        unit_pass = self.run_backend_unit_tests(verbose, coverage, parallel)
        integration_pass = self.run_backend_integration_tests(verbose, coverage, parallel)
        e2e_pass = self.run_e2e_tests(verbose, coverage, parallel)

        return unit_pass and integration_pass and e2e_pass

    def run_all_tests(self, verbose=False, coverage=False, parallel=False):
        """Run all tests."""
        print("\n" + "=" * 80)
        print("  LAWYERFACTORY COMPREHENSIVE TEST SUITE")
        print("=" * 80)

        backend_pass = self.run_all_backend_tests(verbose, coverage, parallel)

        # Frontend tests may require npm/Node setup
        frontend_available = (self.project_root / "apps/ui/react-app").exists()
        frontend_pass = True
        if frontend_available:
            frontend_pass = self.run_frontend_tests(verbose)

        return backend_pass and frontend_pass

    def print_summary(self):
        """Print test execution summary."""
        print("\n" + "=" * 80)
        print("  TEST EXECUTION SUMMARY")
        print("=" * 80 + "\n")

        total_tests = len(self.passed_tests) + len(self.failed_tests)

        print(f"Total Test Suites:  {total_tests}")
        print(f"✓ Passed:           {len(self.passed_tests)}")
        print(f"✗ Failed:           {len(self.failed_tests)}")

        if self.passed_tests:
            print("\n✓ Passed Tests:")
            for test in self.passed_tests:
                print(f"  • {test}")

        if self.failed_tests:
            print("\n✗ Failed Tests:")
            for test in self.failed_tests:
                print(f"  • {test}")

        print("\n" + "=" * 80)

        if self.failed_tests:
            print("⚠️  Some tests failed. Review output above.")
            return False
        else:
            print("✅ All tests passed!")
            return True


def main():
    parser = argparse.ArgumentParser(
        description="Run LawyerFactory comprehensive test suite"
    )
    parser.add_argument(
        "--unit",
        action="store_true",
        help="Run only unit tests"
    )
    parser.add_argument(
        "--integration",
        action="store_true",
        help="Run only integration tests"
    )
    parser.add_argument(
        "--e2e",
        action="store_true",
        help="Run only end-to-end tests"
    )
    parser.add_argument(
        "--frontend",
        action="store_true",
        help="Run only frontend tests"
    )
    parser.add_argument(
        "--backend",
        action="store_true",
        help="Run all backend tests"
    )
    parser.add_argument(
        "--coverage",
        action="store_true",
        help="Generate coverage reports"
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Verbose output"
    )
    parser.add_argument(
        "--parallel",
        "-p",
        action="store_true",
        help="Run tests in parallel"
    )

    args = parser.parse_args()

    runner = TestRunner()
    start_time = time.time()

    try:
        if args.unit:
            success = runner.run_backend_unit_tests(args.verbose, args.coverage, args.parallel)
        elif args.integration:
            success = runner.run_backend_integration_tests(args.verbose, args.coverage, args.parallel)
        elif args.e2e:
            success = runner.run_e2e_tests(args.verbose, args.coverage, args.parallel)
        elif args.frontend:
            success = runner.run_frontend_tests(args.verbose)
        elif args.backend:
            success = runner.run_all_backend_tests(args.verbose, args.coverage, args.parallel)
        else:
            success = runner.run_all_tests(args.verbose, args.coverage, args.parallel)

        runner.print_summary()

        elapsed = time.time() - start_time
        print(f"\nTotal execution time: {elapsed:.2f}s\n")

        return 0 if success else 1

    except KeyboardInterrupt:
        print("\n\n⚠️  Test execution interrupted by user")
        return 1
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())

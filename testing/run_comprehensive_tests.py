#!/usr/bin/env python3
"""Comprehensive testing and validation script for D&D Story Telling application."""

import asyncio
import argparse
import sys
import time
import subprocess
import json
from pathlib import Path
from typing import Dict, Any, List, Optional
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class TestRunner:
    """Comprehensive test runner for the application."""

    def __init__(self, audio_path: Optional[str] = None):
        self.audio_path = audio_path or "D:/Raw Session Recordings"
        self.results = {}
        self.start_time = time.time()

    def run_command(self, command: List[str], timeout: int = 300) -> Dict[str, Any]:
        """Run a command and return results."""
        logger.info(f"Running: {' '.join(command)}")

        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=timeout
            )

            return {
                "success": result.returncode == 0,
                "returncode": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "command": " ".join(command)
            }

        except subprocess.TimeoutExpired:
            logger.error(f"Command timed out after {timeout}s: {' '.join(command)}")
            return {
                "success": False,
                "returncode": -1,
                "stdout": "",
                "stderr": f"Command timed out after {timeout}s",
                "command": " ".join(command)
            }
        except Exception as e:
            logger.error(f"Command failed: {e}")
            return {
                "success": False,
                "returncode": -1,
                "stdout": "",
                "stderr": str(e),
                "command": " ".join(command)
            }

    def check_audio_files(self) -> Dict[str, Any]:
        """Check availability of D&D audio files."""
        logger.info("Checking D&D audio files availability...")

        audio_path = Path(self.audio_path)
        if not audio_path.exists():
            return {
                "available": False,
                "error": f"Audio path does not exist: {audio_path}",
                "file_count": 0,
                "total_size_mb": 0
            }

        # Count audio files
        audio_files = []
        for ext in ["*.wav", "*.mp3", "*.m4a", "*.flac"]:
            audio_files.extend(audio_path.glob(ext))

        total_size = sum(f.stat().st_size for f in audio_files)

        return {
            "available": True,
            "file_count": len(audio_files),
            "total_size_mb": total_size / (1024 * 1024),
            "sample_files": [f.name for f in audio_files[:5]],
            "path": str(audio_path)
        }

    def run_code_quality_checks(self) -> Dict[str, Any]:
        """Run code quality checks."""
        logger.info("Running code quality checks...")

        checks = {}

        # Black formatting check
        checks["black"] = self.run_command(["python", "-m", "black", "--check", "--diff", "app/"])

        # isort import sorting check
        checks["isort"] = self.run_command(["python", "-m", "isort", "--check-only", "--diff", "app/"])

        # Flake8 linting
        checks["flake8"] = self.run_command(["python", "-m", "flake8", "app/", "--max-line-length=100"])

        # mypy type checking
        checks["mypy"] = self.run_command(["python", "-m", "mypy", "app/", "--ignore-missing-imports"])

        # Bandit security checking
        checks["bandit"] = self.run_command(["python", "-m", "bandit", "-r", "app/", "-f", "json"])

        # Safety dependency checking
        checks["safety"] = self.run_command(["python", "-m", "safety", "check", "--json"])

        return checks

    def run_unit_tests(self) -> Dict[str, Any]:
        """Run unit tests."""
        logger.info("Running unit tests...")

        command = [
            "python", "-m", "pytest",
            "testing/tests/",
            "-m", "unit",
            "--cov=app",
            "--cov-report=xml",
            "--cov-report=html",
            "--junit-xml=testing/results/unit-test-results.xml",
            "-v"
        ]

        return self.run_command(command, timeout=600)

    def run_integration_tests(self) -> Dict[str, Any]:
        """Run integration tests."""
        logger.info("Running integration tests...")

        command = [
            "python", "-m", "pytest",
            "testing/tests/",
            "-m", "integration",
            "--junit-xml=testing/results/integration-test-results.xml",
            "-v"
        ]

        return self.run_command(command, timeout=1200)

    def run_audio_tests(self) -> Dict[str, Any]:
        """Run audio processing tests."""
        logger.info("Running audio processing tests...")

        # Check if audio files are available
        audio_check = self.check_audio_files()
        if not audio_check["available"]:
            return {
                "success": False,
                "skipped": True,
                "reason": "No audio files available",
                "audio_check": audio_check
            }

        command = [
            "python", "-m", "pytest",
            "testing/tests/",
            "-m", "audio",
            "--junit-xml=testing/results/audio-test-results.xml",
            "-v", "-s"
        ]

        result = self.run_command(command, timeout=1800)
        result["audio_check"] = audio_check
        return result

    def run_real_audio_tests(self) -> Dict[str, Any]:
        """Run tests with real D&D audio files."""
        logger.info("Running real D&D audio tests...")

        # Check if audio files are available
        audio_check = self.check_audio_files()
        if not audio_check["available"] or audio_check["file_count"] == 0:
            return {
                "success": False,
                "skipped": True,
                "reason": "No D&D audio files available",
                "audio_check": audio_check
            }

        command = [
            "python", "-m", "pytest",
            "testing/tests/",
            "-m", "real_audio",
            "--junit-xml=testing/results/real-audio-test-results.xml",
            "-v", "-s", "--tb=short"
        ]

        result = self.run_command(command, timeout=3600)
        result["audio_check"] = audio_check
        return result

    def run_performance_tests(self) -> Dict[str, Any]:
        """Run performance benchmarking tests."""
        logger.info("Running performance tests...")

        command = [
            "python", "-m", "pytest",
            "testing/tests/",
            "-m", "performance",
            "--benchmark-only",
            "--benchmark-sort=mean",
            "--junit-xml=testing/results/performance-test-results.xml",
            "-v"
        ]

        return self.run_command(command, timeout=1800)

    def run_security_tests(self) -> Dict[str, Any]:
        """Run security tests."""
        logger.info("Running security tests...")

        command = [
            "python", "-m", "pytest",
            "testing/tests/",
            "-m", "security",
            "--junit-xml=testing/results/security-test-results.xml",
            "-v"
        ]

        return self.run_command(command, timeout=900)

    def run_docker_tests(self) -> Dict[str, Any]:
        """Run Docker-based tests."""
        logger.info("Running Docker tests...")

        # Check if Docker is available
        docker_check = self.run_command(["docker", "--version"])
        if not docker_check["success"]:
            return {
                "success": False,
                "skipped": True,
                "reason": "Docker not available",
                "docker_check": docker_check
            }

        # Run Docker test script
        if Path("testing/test-docker.ps1").exists():
            command = ["powershell", "-ExecutionPolicy", "Bypass", "-File", "testing/test-docker.ps1"]
        else:
            command = ["bash", "testing/test-docker.sh"]

        result = self.run_command(command, timeout=1800)
        result["docker_check"] = docker_check
        return result

    def generate_coverage_report(self) -> Dict[str, Any]:
        """Generate and analyze coverage report."""
        logger.info("Generating coverage report...")

        # Generate coverage report
        result = self.run_command(["python", "-m", "coverage", "report", "--format=markdown"])

        # Try to parse coverage percentage
        coverage_percentage = None
        if result["success"] and result["stdout"]:
            for line in result["stdout"].split('\n'):
                if "TOTAL" in line and "%" in line:
                    try:
                        coverage_percentage = float(line.split()[-1].rstrip('%'))
                    except:
                        pass

        return {
            "success": result["success"],
            "coverage_percentage": coverage_percentage,
            "report": result["stdout"] if result["success"] else result["stderr"]
        }

    def create_symbolic_links(self) -> Dict[str, Any]:
        """Create symbolic links for audio files if needed."""
        logger.info("Setting up symbolic links for audio files...")

        audio_samples_path = Path("testing/audio_samples")
        source_path = Path(self.audio_path)

        if not source_path.exists():
            return {
                "success": False,
                "reason": f"Source path does not exist: {source_path}"
            }

        try:
            if audio_samples_path.exists():
                if audio_samples_path.is_symlink():
                    audio_samples_path.unlink()
                else:
                    # Remove existing directory
                    import shutil
                    shutil.rmtree(audio_samples_path)

            # Create symbolic link (Windows requires admin privileges)
            audio_samples_path.symlink_to(source_path, target_is_directory=True)

            return {
                "success": True,
                "link_created": str(audio_samples_path),
                "target": str(source_path)
            }

        except OSError as e:
            # Fallback: just create directory and note that files need to be copied
            audio_samples_path.mkdir(exist_ok=True)
            return {
                "success": False,
                "reason": f"Could not create symbolic link: {e}",
                "fallback": "Directory created, copy files manually if needed"
            }

    def run_all_tests(self, include_slow: bool = False, include_real_audio: bool = False) -> Dict[str, Any]:
        """Run all tests and return comprehensive results."""
        logger.info("Starting comprehensive test suite...")

        # Create results directory
        results_dir = Path("testing/results")
        results_dir.mkdir(exist_ok=True)

        # Initialize results
        all_results = {
            "start_time": self.start_time,
            "audio_setup": self.create_symbolic_links(),
            "audio_availability": self.check_audio_files(),
            "code_quality": self.run_code_quality_checks(),
            "unit_tests": self.run_unit_tests(),
            "integration_tests": self.run_integration_tests(),
            "security_tests": self.run_security_tests(),
        }

        # Optional slow tests
        if include_slow:
            all_results["performance_tests"] = self.run_performance_tests()
            all_results["docker_tests"] = self.run_docker_tests()

        # Optional real audio tests
        if include_real_audio:
            all_results["audio_tests"] = self.run_audio_tests()
            all_results["real_audio_tests"] = self.run_real_audio_tests()

        # Coverage report
        all_results["coverage"] = self.generate_coverage_report()

        # Summary
        all_results["end_time"] = time.time()
        all_results["total_duration"] = all_results["end_time"] - all_results["start_time"]
        all_results["summary"] = self.generate_summary(all_results)

        return all_results

    def generate_summary(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate test summary."""
        summary = {
            "total_duration_minutes": results["total_duration"] / 60,
            "tests_run": [],
            "tests_passed": 0,
            "tests_failed": 0,
            "tests_skipped": 0,
            "code_quality_issues": 0,
            "coverage_percentage": results.get("coverage", {}).get("coverage_percentage"),
            "overall_status": "unknown"
        }

        # Analyze each test category
        for category, result in results.items():
            if category in ["start_time", "end_time", "total_duration", "summary"]:
                continue

            if isinstance(result, dict):
                summary["tests_run"].append(category)

                if result.get("skipped"):
                    summary["tests_skipped"] += 1
                elif result.get("success"):
                    summary["tests_passed"] += 1
                else:
                    summary["tests_failed"] += 1

                # Count code quality issues
                if category == "code_quality":
                    for check, check_result in result.items():
                        if not check_result.get("success", True):
                            summary["code_quality_issues"] += 1

        # Determine overall status
        if summary["tests_failed"] == 0 and summary["code_quality_issues"] == 0:
            summary["overall_status"] = "success"
        elif summary["tests_failed"] > 0:
            summary["overall_status"] = "failed"
        else:
            summary["overall_status"] = "warning"

        return summary

    def save_results(self, results: Dict[str, Any], filename: str = "test_results.json"):
        """Save test results to file."""
        results_file = Path("testing/results") / filename
        results_file.parent.mkdir(exist_ok=True)

        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)

        logger.info(f"Results saved to {results_file}")
        return results_file


def main():
    """Main function for command line usage."""
    parser = argparse.ArgumentParser(description="Comprehensive testing for D&D Story Telling application")
    parser.add_argument("--audio-path", default="D:/Raw Session Recordings", help="Path to D&D audio files")
    parser.add_argument("--include-slow", action="store_true", help="Include slow tests (performance, Docker)")
    parser.add_argument("--include-real-audio", action="store_true", help="Include real audio tests")
    parser.add_argument("--output", default="test_results.json", help="Output file for results")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Create test runner
    runner = TestRunner(audio_path=args.audio_path)

    # Run all tests
    results = runner.run_all_tests(
        include_slow=args.include_slow,
        include_real_audio=args.include_real_audio
    )

    # Save results
    results_file = runner.save_results(results, args.output)

    # Print summary
    summary = results["summary"]
    print(f"\n{'='*60}")
    print("TEST SUMMARY")
    print(f"{'='*60}")
    print(f"Duration: {summary['total_duration_minutes']:.1f} minutes")
    print(f"Tests Passed: {summary['tests_passed']}")
    print(f"Tests Failed: {summary['tests_failed']}")
    print(f"Tests Skipped: {summary['tests_skipped']}")
    print(f"Code Quality Issues: {summary['code_quality_issues']}")
    if summary['coverage_percentage']:
        print(f"Coverage: {summary['coverage_percentage']:.1f}%")
    print(f"Overall Status: {summary['overall_status'].upper()}")
    print(f"Results saved to: {results_file}")

    # Exit with appropriate code
    if summary["overall_status"] == "success":
        sys.exit(0)
    elif summary["overall_status"] == "warning":
        sys.exit(1)
    else:
        sys.exit(2)


if __name__ == "__main__":
    main()
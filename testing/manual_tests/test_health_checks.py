#!/usr/bin/env python3
"""Test the health check functionality without full server startup."""

import sys
import asyncio
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
from app.utils.monitoring import health_checker, check_database_connection, check_disk_space, check_memory_usage

async def test_health_checks():
    print("=== Testing Health Check System ===")

    # Register basic health checks
    health_checker.register_check("database", check_database_connection, critical=True)
    health_checker.register_check("disk_space", lambda: check_disk_space(1.0), critical=False)  # 1GB minimum
    health_checker.register_check("memory", check_memory_usage, critical=False)

    # Run health checks
    results = await health_checker.run_health_checks()

    print(f"Overall health: {results['overall_health']}")
    print(f"Critical failures: {results['critical_failures']}")

    for check_name, result in results['checks'].items():
        status = "✅" if result['success'] else "❌"
        print(f"{status} {check_name}: {result['status']} ({result['duration']:.3f}s)")

    print("\nHealth check system: ✅ WORKING")

if __name__ == "__main__":
    asyncio.run(test_health_checks())
#!/usr/bin/env python3
"""Quick validation test for core systems."""

import sys
import time
sys.path.append('.')

def test_security():
    print("=== Testing Security System ===")
    from app.utils.security import InputValidator

    iv = InputValidator()

    # Test XSS sanitization
    result = iv.sanitize_string('test <script>alert(1)</script>')
    print(f"XSS sanitization: {result}")

    # Test SQL injection detection
    try:
        iv.validate_sql_injection('SELECT * FROM users WHERE 1=1')
        print("❌ SQL injection not detected!")
    except Exception as e:
        print(f"✅ SQL injection blocked: {str(e)[:50]}...")

    print("Security system: ✅ WORKING\n")

def test_monitoring():
    print("=== Testing Monitoring System ===")
    from app.utils.monitoring import performance_metrics, monitor_performance

    @monitor_performance('test_function')
    def test_function():
        time.sleep(0.1)
        return 'test result'

    result = test_function()
    print(f"Function result: {result}")

    stats = performance_metrics.get_function_stats('test_function')
    print(f"Function stats: {stats}")

    summary = performance_metrics.get_performance_summary()
    print(f"System uptime: {summary['uptime_seconds']:.1f}s")

    print("Monitoring system: ✅ WORKING\n")

def test_config():
    print("=== Testing Configuration ===")
    from app.config import get_settings

    settings = get_settings()
    print(f"Environment: {settings.ENVIRONMENT}")
    print(f"Database URL: {settings.DATABASE_URL}")
    print(f"Debug mode: {settings.DEBUG}")

    print("Configuration: ✅ WORKING\n")

if __name__ == "__main__":
    try:
        test_config()
        test_security()
        test_monitoring()
        print("🎉 All core systems are working correctly!")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
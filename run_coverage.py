import subprocess
import sys

print("Running pytest with coverage...")
print("=" * 80)

result = subprocess.run(
    [sys.executable, "-m", "pytest", "tests/",
     "--cov=app",
     "--cov-report=term-missing",
     "--cov-report=html",
     "-v"],
    capture_output=False,
    timeout=120
)

print("\n" + "=" * 80)
print(f"Tests completed with exit code: {result.returncode}")
if result.returncode == 0:
    print("✅ ALL TESTS PASSED!")
else:
    print(f"❌ Some tests failed (exit code: {result.returncode})")
print("=" * 80)

sys.exit(result.returncode)


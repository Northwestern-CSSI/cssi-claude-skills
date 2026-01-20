#!/usr/bin/env python3
"""
Test runner for Dimensions skill.

Usage:
    python run_tests.py              # Run all tests
    python run_tests.py -v           # Verbose output
    python run_tests.py -k validation # Run only validation tests
    python run_tests.py --quick      # Run only unit tests (no API calls)
"""

import subprocess
import sys
import os

# Change to the skill directory
SKILL_DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(SKILL_DIR)


def run_tests():
    """Run the test suite."""
    args = sys.argv[1:]

    # Check for --quick flag
    if '--quick' in args:
        args.remove('--quick')
        args.extend(['-k', 'not integration'])

    # Default to verbose if not specified
    if '-v' not in args and '--verbose' not in args:
        args.append('-v')

    # Run pytest
    cmd = [sys.executable, '-m', 'pytest', 'tests/'] + args

    print(f"Running: {' '.join(cmd)}")
    print(f"Working directory: {SKILL_DIR}")
    print("-" * 60)

    result = subprocess.run(cmd)
    return result.returncode


if __name__ == '__main__':
    sys.exit(run_tests())

"""
HAPAG pipeline runner.

Currently wraps the full HAPAG automation flow behind one entry point.
"""

import sys
import traceback

import hapag_checker


def main():
    """Run HAPAG pipeline and return process exit code."""
    print("=" * 72)
    print("HAPAG PIPELINE START")
    print("=" * 72)

    try:
        exit_code = hapag_checker.main()
        if exit_code == 0:
            print("\n" + "=" * 72)
            print("HAPAG PIPELINE COMPLETE")
            print("=" * 72)
        else:
            print(f"[PIPELINE] HAPAG pipeline failed with exit code {exit_code}")
        return exit_code
    except Exception as exc:
        print(f"[PIPELINE] Fatal error: {exc}")
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())

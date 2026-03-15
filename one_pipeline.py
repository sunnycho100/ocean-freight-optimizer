"""
ONE pipeline runner.

Runs the full ONE workflow in one command:
1) URL checker (destination config update)
2) ONE inland scraper
3) ONE post-processor (ocean + ranking)
"""

import os
import sys
import traceback

import ONE_processor
import quick_download_refactored
import url_checker_refactored


def _run_step(step_name, fn):
    """Run one pipeline step with consistent logging."""
    print("\n" + "=" * 72)
    print(f"[PIPELINE] {step_name}")
    print("=" * 72)
    return fn()


def main(destinations_override=None):
    """Run full ONE pipeline and return process exit code."""
    if destinations_override is None:
        destinations = [arg.strip() for arg in sys.argv[1:] if arg.strip()]
    else:
        destinations = [str(arg).strip() for arg in destinations_override if str(arg).strip()]
    destination_override = destinations if destinations else None

    print("=" * 72)
    print("ONE PIPELINE START")
    print("=" * 72)

    try:
        # Step 1: URL checker (supports optional destination override)
        step1_ok = _run_step(
            "Step 1/3 - Update Destination Config",
            lambda: url_checker_refactored.main(destinations_override=destination_override),
        )
        if not step1_ok:
            print("[PIPELINE] Step 1 failed. Stopping ONE pipeline.")
            return 1

        # Step 2: Quick download (ONE inland rates)
        step2_result = _run_step(
            "Step 2/3 - Scrape ONE Inland Rates",
            quick_download_refactored.quick_download,
        )
        if not step2_result or not step2_result.get("success"):
            print("[PIPELINE] Step 2 failed (no successful destinations). Stopping ONE pipeline.")
            return 1

        # Step 3: Process inland + ocean ranking
        def _process_step():
            inland_file = ONE_processor.get_latest_inland_rate_file("downloads")
            ocean_file = os.path.join("source", "ocean_freight.xlsx")
            _, output_file = ONE_processor.process_inland_rates(
                inland_file=inland_file,
                ocean_file=ocean_file,
                output_dir="downloads",
            )
            print(f"[PIPELINE] Processed file generated: {output_file}")
            return True

        step3_ok = _run_step("Step 3/3 - Process ONE + Ocean Ranking", _process_step)
        if not step3_ok:
            print("[PIPELINE] Step 3 failed.")
            return 1

        print("\n" + "=" * 72)
        print("ONE PIPELINE COMPLETE")
        print("=" * 72)
        return 0

    except Exception as exc:
        print(f"[PIPELINE] Fatal error: {exc}")
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())

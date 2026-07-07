from china_cars.quality import run_quality_checks, write_quality_results


if __name__ == "__main__":
    result = run_quality_checks()
    path = write_quality_results(result)
    print(f"Quality status: {result['status']}")
    print(f"Results written to: {path}")
    if result["status"] != "pass":
        raise SystemExit(1)


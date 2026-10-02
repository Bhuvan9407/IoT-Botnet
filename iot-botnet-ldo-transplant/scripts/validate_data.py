from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]

NBAIOT_DIR = ROOT / "data" / "raw" / "nbaiot" / "extracted"
MEDBIOT_DIR = ROOT / "data" / "raw" / "medbiot"
MANIFEST = ROOT / "data" / "raw" / "manifest.txt"

EXPECTED_NBAIOT = 89
EXPECTED_MEDBIOT = 18


def relative_paths(files):
    return {
        path.relative_to(ROOT).as_posix()
        for path in files
    }


def main():
    errors = []

    nbaiot_files = {
        path for path in NBAIOT_DIR.rglob("*.csv")
        if path.is_file()
        and path.name != "demonstrate_structure.csv"
    } if NBAIOT_DIR.exists() else set()

    medbiot_files = {
        path for path in MEDBIOT_DIR.glob("*.csv")
        if path.is_file()
    } if MEDBIOT_DIR.exists() else set()

    if not NBAIOT_DIR.exists():
        errors.append(f"Missing directory: {NBAIOT_DIR}")

    if not MEDBIOT_DIR.exists():
        errors.append(f"Missing directory: {MEDBIOT_DIR}")

    print(f"N-BaIoT CSV files: {len(nbaiot_files)}")
    print(f"MedBIoT CSV files: {len(medbiot_files)}")

    if len(nbaiot_files) != EXPECTED_NBAIOT:
        errors.append(
            f"Expected {EXPECTED_NBAIOT} N-BaIoT files, "
            f"found {len(nbaiot_files)}"
        )

    if len(medbiot_files) != EXPECTED_MEDBIOT:
        errors.append(
            f"Expected {EXPECTED_MEDBIOT} MedBIoT files, "
            f"found {len(medbiot_files)}"
        )

    if not MANIFEST.is_file():
        errors.append(f"Missing manifest: {MANIFEST}")
    else:
        manifest_paths = {
            line.strip()
            for line in MANIFEST.read_text(encoding="utf-8-sig").splitlines()
            if line.strip()
        }

        actual_paths = (
            relative_paths(nbaiot_files)
            | relative_paths(medbiot_files)
        )

        missing = actual_paths - manifest_paths
        extra = manifest_paths - actual_paths

        print(f"Manifest entries: {len(manifest_paths)}")

        if missing:
            errors.append(
                f"{len(missing)} dataset file(s) missing from manifest:"
            )
            errors.extend(f"  {path}" for path in sorted(missing))

        if extra:
            errors.append(
                f"{len(extra)} manifest entry/entries not found on disk:"
            )
            errors.extend(f"  {path}" for path in sorted(extra))

        if len(manifest_paths) != EXPECTED_NBAIOT + EXPECTED_MEDBIOT:
            errors.append(
                "Manifest does not contain the expected 107 entries."
            )

    if errors:
        print("\nVALIDATION FAILED")
        for error in errors:
            print(f"- {error}")
        return 1

    print("\nVALIDATION PASSED")
    print("All 107 dataset files match the manifest.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
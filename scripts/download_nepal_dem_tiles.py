
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
import time

PROJECT = Path(r"I:\ForgeD\Traffic_visualisation")
TERRAIN = PROJECT / "data" / "terrain"
TILE_LIST = TERRAIN / "nepal_glo30_tile_list.txt"
DOWNLOAD_DIR = TERRAIN / "tiles"

BASE_URL = "https://copernicus-dem-30m.s3.amazonaws.com"
RETRIES = 3
CHUNK_SIZE = 1024 * 1024  # 1 MB

def download_tile(name: str) -> tuple[bool, str]:
    folder = DOWNLOAD_DIR / name
    folder.mkdir(parents=True, exist_ok=True)

    destination = folder / f"{name}.tif"
    partial = folder / f"{name}.tif.part"
    url = f"{BASE_URL}/{name}/{name}.tif"

    # Skip an existing, non-empty completed download.
    if destination.exists() and destination.stat().st_size > 0:
        return True, f"Already exists ({destination.stat().st_size:,} bytes)"

    for attempt in range(1, RETRIES + 1):
        try:
            request = Request(url, headers={"User-Agent": "NepalAviationTerrain/1.0"})
            with urlopen(request, timeout=120) as response:
                expected = response.headers.get("Content-Length")
                expected_size = int(expected) if expected else None

                mode = "ab" if partial.exists() else "wb"
                existing_size = partial.stat().st_size if partial.exists() else 0

                # Resume only when the server supports byte ranges.
                if existing_size and response.status != 206:
                    partial.unlink()
                    existing_size = 0
                    mode = "wb"

                with partial.open(mode) as output:
                    while True:
                        chunk = response.read(CHUNK_SIZE)
                        if not chunk:
                            break
                        output.write(chunk)

            actual_size = partial.stat().st_size
            if expected_size is not None and actual_size != expected_size:
                # A resumed request's Content-Length can represent only the
                # remaining bytes, so retry from the beginning safely.
                partial.unlink(missing_ok=True)
                raise IOError(
                    f"Size verification failed: got {actual_size:,}, "
                    f"expected {expected_size:,}"
                )

            if actual_size == 0:
                raise IOError("Downloaded file is empty")

            partial.replace(destination)
            return True, f"Downloaded ({actual_size:,} bytes)"

        except (HTTPError, URLError, TimeoutError, OSError, ValueError) as exc:
            partial.unlink(missing_ok=True)
            if attempt < RETRIES:
                time.sleep(2 * attempt)
            else:
                return False, f"Failed after {RETRIES} attempts: {exc}"

    return False, "Unknown failure"


def main():
    if not TILE_LIST.exists():
        raise FileNotFoundError(f"Tile list not found: {TILE_LIST}")

    names = [
        line.strip()
        for line in TILE_LIST.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]

    DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Tile list: {TILE_LIST}")
    print(f"Download folder: {DOWNLOAD_DIR}")
    print(f"Tiles in list: {len(names)}")
    print("Starting downloads...\n")

    succeeded = 0
    failed = []

    for index, name in enumerate(names, start=1):
        ok, message = download_tile(name)
        status = "OK" if ok else "FAILED"
        print(f"[{index}/{len(names)}] {status}: {name} — {message}")

        if ok:
            succeeded += 1
        else:
            failed.append((name, message))

    report = TERRAIN / "nepal_dem_download_report.txt"
    lines = [
        f"Tiles listed: {len(names)}",
        f"Successful or already present: {succeeded}",
        f"Failed: {len(failed)}",
        "",
        *[f"FAILED: {name} — {message}" for name, message in failed],
    ]
    report.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print("\n--- SUMMARY ---")
    print(f"Successful or already present: {succeeded}/{len(names)}")
    print(f"Failed: {len(failed)}")
    print(f"Report: {report}")

if __name__ == "__main__":
    main()

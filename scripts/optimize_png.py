"""Losslessly optimize the site's active PNG assets."""

from pathlib import Path
import os

from PIL import Image


FILES = (
    "images/apple-touch-icon-180x180.png",
    "images/favicon-192x192.png",
    "images/favicon-32x32.png",
    "images/favicon-512x512.png",
    "images/home/statistical-modelling-workflow.png",
    "images/profile.png",
    "images/talks/anchovy-critical-points-full.png",
    "images/talks/anchovy-critical-points-thumbnail.png",
    "images/talks/anchovy-health-index-full.png",
    "images/talks/anchovy-health-index-thumbnail.png",
)


def main() -> None:
    total_before = 0
    total_after = 0

    for filename in FILES:
        path = Path(filename)
        before = path.stat().st_size
        with Image.open(path) as source:
            expected = (source.mode, source.size, source.tobytes())
            temporary = path.with_suffix(".codex-opt.png")
            source.save(temporary, optimize=True, compress_level=9)

        with Image.open(temporary) as optimized:
            actual = (optimized.mode, optimized.size, optimized.tobytes())
        if actual != expected:
            temporary.unlink(missing_ok=True)
            raise RuntimeError(f"Pixel verification failed for {path}")

        after = temporary.stat().st_size
        total_before += before
        if after < before:
            os.replace(temporary, path)
            total_after += after
            print(f"{path}: {before} -> {after}")
        else:
            temporary.unlink()
            total_after += before
            print(f"{path}: unchanged ({before})")

    print(f"TOTAL: {total_before} -> {total_after}; saved {total_before - total_after}")


if __name__ == "__main__":
    main()

import json
from datetime import date
from pathlib import Path

import condastats.cli
import pypistats
from github import Github


def _read_archive(path):
    try:
        with open(path, "r") as f:
            archive = json.load(f)
    except FileNotFoundError:
        archive = []
    return archive


def _write_archive(path, archive):
    with open(path, "w") as f:
        json.dump(archive, f, indent=4)


def _append(archive, count):
    today = date.today().strftime("%Y-%m-%d")
    if today not in {entry["date"] for entry in archive}:
        prev_count = sum(map(lambda d: d["downloads"], archive))
        archive.append({"date": today, "downloads": count - prev_count})


def count_github(user, package, path):
    """Download count for the GitHub repository."""
    repo = Github().get_repo(f"{user}/{package}")
    count = sum(sum(map(lambda d: d.download_count, release.get_assets())) for release in repo.get_releases())
    archive = _read_archive(path)
    _append(archive, count)
    _write_archive(path, archive)
    return count


def count_conda(package, path):
    """Download count for the Anaconda distribution."""
    count = int(condastats.cli.overall(package))
    archive = _read_archive(path)
    _append(archive, count)
    _write_archive(path, archive)
    return count


def count_pypi(package, path):
    """Download count for the PyPI distribution."""
    df = pypistats.overall(package, total=True, format="pandas")
    archive = _read_archive(path)
    for _, data in df.iterrows():
        if data["category"] != "Total" and all([d["category"] != data["category"] or d["date"] != data["date"] for d in archive]):
            data_util = data.to_dict()
            data_util.pop("percent")
            archive.append(data_util)
    archive.sort(key=lambda x: f"{x['category']}{x['date']}")
    _write_archive(path, archive)
    return sum(d["downloads"] for d in archive if d["category"] == "without_mirrors")


if __name__ == "__main__":
    archives = Path("archives").resolve(True)
    _write_archive(archives / "total.json", {
        "conda": count_conda("pdfo", archives / "conda.json"),
        "github": count_github("pdfo", "pdfo", archives / "github.json"),
        "pypi": count_pypi("pdfo", archives / "pypi.json"),
    })

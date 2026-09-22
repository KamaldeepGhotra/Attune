# Vibe Clustering (Phase 2, Sub-phase 1) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ingest a public dataset of historical Spotify audio features, group tracks into vibe clusters via k-means, and produce a fast, committed lookup artifact the running app can use to answer "what vibe cluster is this known track in?" — the foundation "Problem A" piece the ranking model (next sub-phase) depends on.

**Architecture:** An offline pipeline (download → ingest/dedupe → cluster → persist small JSON artifacts) that runs once (or is re-run manually to refresh), decoupled from the FastAPI app's runtime. The running app never trains anything — it only ever reads the small committed JSON lookup files. Heavy ML libraries (pandas, scikit-learn) are a separate, local-only dependency set — they never ship in the production Docker image, since the deployed API only needs `json.load`.

**Tech Stack:** Python, pandas, scikit-learn (KMeans, StandardScaler), httpx (already a runtime dependency, reused for the download step).

**Spec:** `docs/superpowers/specs/2026-09-07-attune-design.md` (see "Problem A — grouping songs into vibe clusters")

## Global Constraints

- Dataset: `maharshipandya/spotify-tracks-dataset`, hosted at `https://huggingface.co/datasets/maharshipandya/spotify-tracks-dataset/resolve/main/dataset.csv`. License: **BSD** (permissive, verified from the dataset's raw YAML metadata — redistribution/modification/commercial use allowed).
- Verified real shape: 114,000 data rows, 89,741 unique `track_id` values (duplicates exist — same track listed under multiple genres), 114 unique genres, zero nulls in the columns this plan uses.
- CSV columns (verified from the real file header): `,track_id,artists,album_name,track_name,popularity,duration_ms,explicit,danceability,energy,key,loudness,mode,speechiness,acousticness,instrumentalness,liveness,valence,tempo,time_signature,track_genre`. This plan only uses `track_id`, `artists`, `track_name`, `danceability`, `energy`, `valence`, `tempo`, `track_genre`.
- The raw CSV (~20MB, third-party data) is **not committed to git** — it's downloaded on demand into a gitignored path. The small JSON artifacts this pipeline *produces* (cluster lookup + centroids) **are** committed, since the running app reads them directly.
- Claude does not run `git commit` — the project owner commits manually. Every "Commit" step below stages changes only.
- No `CLAUDE.md`/`AGENTS.md` or similar AI-tool files in this repo.

---

## Task 1: Download and cache the raw dataset

**Files:**
- Create: `backend/scripts/__init__.py`
- Create: `backend/scripts/download_dataset.py`
- Test: `backend/tests/test_download_dataset.py`
- Modify: `.gitignore`
- Create: `backend/requirements-ml.txt`

**Interfaces:**
- Produces: `scripts.download_dataset.download_dataset(dest_path: str) -> None` — downloads the CSV to `dest_path` if it doesn't already exist there; does nothing (no network call) if the file is already present.

- [ ] **Step 1: Write the failing test**

`backend/tests/test_download_dataset.py`:
```python
import httpx
import respx

from scripts.download_dataset import DATASET_URL, download_dataset


@respx.mock
def test_download_dataset_writes_file_when_missing(tmp_path):
    dest = tmp_path / "dataset.csv"
    respx.get(DATASET_URL).mock(return_value=httpx.Response(200, content=b"track_id,tempo\nabc,120\n"))

    download_dataset(str(dest))

    assert dest.read_bytes() == b"track_id,tempo\nabc,120\n"


@respx.mock
def test_download_dataset_skips_when_already_present(tmp_path):
    dest = tmp_path / "dataset.csv"
    dest.write_bytes(b"already here")
    route = respx.get(DATASET_URL).mock(return_value=httpx.Response(200, content=b"new content"))

    download_dataset(str(dest))

    assert dest.read_bytes() == b"already here"
    assert route.call_count == 0
```

- [ ] **Step 2: Run the tests to verify they fail**

Run (from `backend/`): `pytest tests/test_download_dataset.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'scripts'`

- [ ] **Step 3: Write the minimal implementation**

`backend/scripts/__init__.py`: (empty file)

`backend/scripts/download_dataset.py`:
```python
import os

import httpx

DATASET_URL = "https://huggingface.co/datasets/maharshipandya/spotify-tracks-dataset/resolve/main/dataset.csv"


def download_dataset(dest_path: str) -> None:
    if os.path.exists(dest_path):
        return

    os.makedirs(os.path.dirname(dest_path), exist_ok=True)
    response = httpx.get(DATASET_URL, timeout=60.0)
    response.raise_for_status()

    with open(dest_path, "wb") as f:
        f.write(response.content)


if __name__ == "__main__":
    download_dataset("data/raw/spotify_tracks.csv")
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `pytest tests/test_download_dataset.py -v`
Expected: PASS

- [ ] **Step 5: Add the ML-only requirements file (kept separate from the Docker-shipped runtime deps)**

`backend/requirements-ml.txt`:
```
pandas>=2.2,<2.3
scikit-learn>=1.5,<1.6
```

- [ ] **Step 6: Update .gitignore**

Add to `.gitignore`:
```
backend/data/raw/
```

- [ ] **Step 7: Install the ML requirements and actually download the real dataset**

```bash
cd backend
source .venv/bin/activate
pip install -r requirements-ml.txt
python -m scripts.download_dataset
```
Expected: `backend/data/raw/spotify_tracks.csv` exists, ~20MB.

- [ ] **Step 8: Stage changes**

```bash
git add backend/scripts/__init__.py backend/scripts/download_dataset.py backend/tests/test_download_dataset.py backend/requirements-ml.txt .gitignore
```

---

## Task 2: Ingest the dataset into a clean, deduplicated DataFrame

**Files:**
- Create: `backend/app/ml/__init__.py`
- Create: `backend/app/ml/dataset.py`
- Test: `backend/tests/test_ml_dataset.py`

**Interfaces:**
- Produces: `app.ml.dataset.load_dataset(csv_path: str) -> pandas.DataFrame` with columns `track_id`, `artists`, `track_name`, `danceability`, `energy`, `valence`, `tempo`, `track_genre`, one row per unique `track_id` (first occurrence kept when duplicates exist).

- [ ] **Step 1: Write the failing test**

`backend/tests/test_ml_dataset.py`:
```python
from app.ml.dataset import load_dataset

CSV_HEADER = "id,track_id,artists,album_name,track_name,popularity,duration_ms,explicit,danceability,energy,key,loudness,mode,speechiness,acousticness,instrumentalness,liveness,valence,tempo,time_signature,track_genre\n"


def _row(track_id, name, danceability, energy, valence, tempo, genre):
    return f"0,{track_id},Some Artist,Some Album,{name},50,200000,False,{danceability},{energy},1,-5.0,1,0.05,0.1,0.0,0.1,{valence},{tempo},4,{genre}\n"


def test_load_dataset_dedupes_by_track_id_keeping_first(tmp_path):
    csv_path = tmp_path / "dataset.csv"
    csv_path.write_text(
        CSV_HEADER
        + _row("track1", "Song One", 0.5, 0.5, 0.5, 120, "pop")
        + _row("track1", "Song One Duplicate", 0.9, 0.9, 0.9, 200, "rock")
        + _row("track2", "Song Two", 0.2, 0.2, 0.2, 90, "acoustic")
    )

    df = load_dataset(str(csv_path))

    assert len(df) == 2
    assert set(df["track_id"]) == {"track1", "track2"}

    track1_row = df[df["track_id"] == "track1"].iloc[0]
    assert track1_row["track_name"] == "Song One"
    assert track1_row["danceability"] == 0.5
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `pytest tests/test_ml_dataset.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'app.ml'`

- [ ] **Step 3: Write the minimal implementation**

`backend/app/ml/__init__.py`: (empty file)

`backend/app/ml/dataset.py`:
```python
import pandas as pd

COLUMNS = ["track_id", "artists", "track_name", "danceability", "energy", "valence", "tempo", "track_genre"]


def load_dataset(csv_path: str) -> pd.DataFrame:
    df = pd.read_csv(csv_path)
    df = df[COLUMNS]
    df = df.drop_duplicates(subset="track_id", keep="first")
    return df.reset_index(drop=True)
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `pytest tests/test_ml_dataset.py -v`
Expected: PASS

- [ ] **Step 5: Stage changes**

```bash
git add backend/app/ml/__init__.py backend/app/ml/dataset.py backend/tests/test_ml_dataset.py
```

---

## Task 3: Train k-means clustering on the dataset's audio features

**Files:**
- Create: `backend/app/ml/clustering.py`
- Test: `backend/tests/test_ml_clustering.py`

**Interfaces:**
- Consumes: a `pandas.DataFrame` with columns `track_id`, `danceability`, `energy`, `valence`, `tempo` (Task 2's output shape).
- Produces: `app.ml.clustering.train_clusters(df: pandas.DataFrame, n_clusters: int = 8, random_state: int = 42) -> tuple[dict[str, int], dict[int, dict[str, float]]]` — returns `(track_id_to_cluster, cluster_centroids)` where `track_id_to_cluster` maps each `track_id` to an integer cluster label, and `cluster_centroids` maps each cluster label to a dict of that cluster's mean `danceability`/`energy`/`valence`/`tempo` (in original, non-standardized units).

- [ ] **Step 1: Write the failing test**

`backend/tests/test_ml_clustering.py`:
```python
import pandas as pd

from app.ml.clustering import train_clusters


def test_train_clusters_groups_clearly_separated_tracks_correctly():
    df = pd.DataFrame(
        {
            "track_id": ["low1", "low2", "low3", "high1", "high2", "high3"],
            "danceability": [0.1, 0.12, 0.11, 0.9, 0.88, 0.91],
            "energy": [0.1, 0.11, 0.09, 0.9, 0.92, 0.89],
            "valence": [0.1, 0.13, 0.1, 0.9, 0.87, 0.9],
            "tempo": [70, 72, 71, 180, 178, 182],
        }
    )

    track_id_to_cluster, cluster_centroids = train_clusters(df, n_clusters=2)

    low_cluster = track_id_to_cluster["low1"]
    high_cluster = track_id_to_cluster["high1"]

    assert track_id_to_cluster["low2"] == low_cluster
    assert track_id_to_cluster["low3"] == low_cluster
    assert track_id_to_cluster["high2"] == high_cluster
    assert track_id_to_cluster["high3"] == high_cluster
    assert low_cluster != high_cluster

    assert cluster_centroids[low_cluster]["tempo"] < cluster_centroids[high_cluster]["tempo"]
    assert set(cluster_centroids[low_cluster].keys()) == {"danceability", "energy", "valence", "tempo"}
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `pytest tests/test_ml_clustering.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'app.ml.clustering'`

- [ ] **Step 3: Write the minimal implementation**

`backend/app/ml/clustering.py`:
```python
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

FEATURE_COLUMNS = ["danceability", "energy", "valence", "tempo"]


def train_clusters(
    df: pd.DataFrame, n_clusters: int = 8, random_state: int = 42
) -> tuple[dict[str, int], dict[int, dict[str, float]]]:
    features = df[FEATURE_COLUMNS]
    scaled_features = StandardScaler().fit_transform(features)

    kmeans = KMeans(n_clusters=n_clusters, random_state=random_state, n_init=10)
    labels = kmeans.fit_predict(scaled_features)

    track_id_to_cluster = dict(zip(df["track_id"], labels.tolist()))

    df_with_labels = df.assign(cluster=labels)
    cluster_centroids = {
        int(cluster_id): group[FEATURE_COLUMNS].mean().to_dict()
        for cluster_id, group in df_with_labels.groupby("cluster")
    }

    return track_id_to_cluster, cluster_centroids
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `pytest tests/test_ml_clustering.py -v`
Expected: PASS

- [ ] **Step 5: Stage changes**

```bash
git add backend/app/ml/clustering.py backend/tests/test_ml_clustering.py
```

---

## Task 4: Build the artifact-generation script and the runtime lookup function

**Files:**
- Create: `backend/scripts/build_clusters.py`
- Create: `backend/app/ml/lookup.py`
- Test: `backend/tests/test_ml_lookup.py`

**Interfaces:**
- Consumes: `app.ml.dataset.load_dataset` (Task 2), `app.ml.clustering.train_clusters` (Task 3), `scripts.download_dataset.download_dataset` (Task 1).
- Produces: two committed JSON files at `backend/app/ml/data/track_clusters.json` (`{track_id: cluster_id}`) and `backend/app/ml/data/cluster_centroids.json` (`{cluster_id: {danceability, energy, valence, tempo}}`); `app.ml.lookup.get_cluster_for_track(track_id: str) -> int | None` — returns the cluster for a known track, or `None` if the track isn't in the dataset (this `None` case is the trigger for the tiered-fallback logic in the next sub-phase's ranking model).

- [ ] **Step 1: Write the failing test**

`backend/tests/test_ml_lookup.py`:
```python
import json

from app.ml import lookup


def test_get_cluster_for_track_returns_known_cluster(tmp_path, monkeypatch):
    data_file = tmp_path / "track_clusters.json"
    data_file.write_text(json.dumps({"track1": 3, "track2": 0}))
    monkeypatch.setattr(lookup, "TRACK_CLUSTERS_PATH", str(data_file))
    lookup._track_clusters_cache = None

    assert lookup.get_cluster_for_track("track1") == 3


def test_get_cluster_for_track_returns_none_for_unknown_track(tmp_path, monkeypatch):
    data_file = tmp_path / "track_clusters.json"
    data_file.write_text(json.dumps({"track1": 3}))
    monkeypatch.setattr(lookup, "TRACK_CLUSTERS_PATH", str(data_file))
    lookup._track_clusters_cache = None

    assert lookup.get_cluster_for_track("nonexistent") is None
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `pytest tests/test_ml_lookup.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'app.ml.lookup'`

- [ ] **Step 3: Write the minimal implementation**

`backend/app/ml/lookup.py`:
```python
import json
import os

TRACK_CLUSTERS_PATH = os.path.join(os.path.dirname(__file__), "data", "track_clusters.json")

_track_clusters_cache: dict[str, int] | None = None


def get_cluster_for_track(track_id: str) -> int | None:
    global _track_clusters_cache
    if _track_clusters_cache is None:
        with open(TRACK_CLUSTERS_PATH) as f:
            _track_clusters_cache = json.load(f)
    return _track_clusters_cache.get(track_id)
```

`backend/scripts/build_clusters.py`:
```python
import json
import os

from app.ml.clustering import train_clusters
from app.ml.dataset import load_dataset
from scripts.download_dataset import download_dataset

RAW_CSV_PATH = "data/raw/spotify_tracks.csv"
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "app", "ml", "data")


def main() -> None:
    download_dataset(RAW_CSV_PATH)
    df = load_dataset(RAW_CSV_PATH)
    track_id_to_cluster, cluster_centroids = train_clusters(df)

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    with open(os.path.join(OUTPUT_DIR, "track_clusters.json"), "w") as f:
        json.dump(track_id_to_cluster, f)

    with open(os.path.join(OUTPUT_DIR, "cluster_centroids.json"), "w") as f:
        json.dump(cluster_centroids, f, indent=2)

    print(f"Wrote clusters for {len(track_id_to_cluster)} tracks across {len(cluster_centroids)} clusters.")


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `pytest tests/test_ml_lookup.py -v`
Expected: PASS

- [ ] **Step 5: Run the full backend test suite**

Run: `pytest -v`
Expected: all tests pass (existing 13 + this plan's new ones)

- [ ] **Step 6: Actually run the pipeline against the real dataset**

```bash
cd backend
source .venv/bin/activate
python -m scripts.build_clusters
```
Expected: prints something like "Wrote clusters for 89741 tracks across 8 clusters."; `backend/app/ml/data/track_clusters.json` and `cluster_centroids.json` now exist.

- [ ] **Step 7: Sanity-check the real output**

```bash
python -c "
from app.ml.lookup import get_cluster_for_track
import json
centroids = json.load(open('app/ml/data/cluster_centroids.json'))
print('cluster count:', len(centroids))
for cid, stats in centroids.items():
    print(cid, stats)
"
```
Expected: 8 clusters printed with plausible, distinct-looking mean `danceability`/`energy`/`valence`/`tempo` values per cluster (e.g., one cluster with high tempo+energy, another with low).

- [ ] **Step 8: Stage changes**

```bash
git add backend/scripts/build_clusters.py backend/app/ml/lookup.py backend/tests/test_ml_lookup.py backend/app/ml/data/track_clusters.json backend/app/ml/data/cluster_centroids.json
```

---

## Self-review notes

- Spec coverage: "Problem A — grouping songs into vibe clusters" ✅ (dataset sourced, license verified, k-means on the 4 named features, unsupervised, named-later via centroid stats). Explicitly out of scope for this plan (next sub-phase): Problem B's ranking model, the tiered-confidence fallback logic that *consumes* `get_cluster_for_track`'s `None` case, and human-readable cluster naming (e.g. "chill acoustic") — this plan only produces the numeric cluster IDs and their centroid stats, which is what naming would be derived from later.
- Interface consistency checked: `load_dataset` (Task 2) → `train_clusters` (Task 3) → `build_clusters.py` (Task 4) all agree on the DataFrame having `track_id`, `danceability`, `energy`, `valence`, `tempo` columns; `get_cluster_for_track`'s `None`-for-unknown-track behavior is the exact hook the next sub-phase's tiered fallback needs.
- No placeholders — every step has real, runnable code; the dataset facts (row counts, column names, URL, license) are all independently verified against the real file, not assumed.

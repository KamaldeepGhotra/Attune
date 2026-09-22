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

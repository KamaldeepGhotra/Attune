import json
import os

TRACK_CLUSTERS_PATH = os.path.join(os.path.dirname(__file__), "data", "track_clusters.json")
CLUSTER_CENTROIDS_PATH = os.path.join(os.path.dirname(__file__), "data", "cluster_centroids.json")

_track_clusters_cache: dict[str, int] | None = None
_cluster_centroids_cache: dict[int, dict[str, float]] | None = None


def get_cluster_for_track(track_id: str) -> int | None:
    global _track_clusters_cache
    if _track_clusters_cache is None:
        with open(TRACK_CLUSTERS_PATH) as f:
            _track_clusters_cache = json.load(f)
    return _track_clusters_cache.get(track_id)


def get_centroid(cluster_id: int) -> dict[str, float] | None:
    global _cluster_centroids_cache
    if _cluster_centroids_cache is None:
        with open(CLUSTER_CENTROIDS_PATH) as f:
            raw = json.load(f)
        _cluster_centroids_cache = {int(k): v for k, v in raw.items()}
    return _cluster_centroids_cache.get(cluster_id)

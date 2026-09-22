import json
import os

from app.ml import lookup


def test_get_cluster_for_track_returns_known_cluster(tmp_path, monkeypatch):
    data_file = tmp_path / "track_clusters.json"
    data_file.write_text(json.dumps({"track1": 3, "track2": 0}))
    monkeypatch.setattr(lookup, "TRACK_CLUSTERS_PATH", str(data_file))
    monkeypatch.setattr(lookup, "_track_clusters_cache", None)

    assert lookup.get_cluster_for_track("track1") == 3


def test_get_cluster_for_track_returns_none_for_unknown_track(tmp_path, monkeypatch):
    data_file = tmp_path / "track_clusters.json"
    data_file.write_text(json.dumps({"track1": 3}))
    monkeypatch.setattr(lookup, "TRACK_CLUSTERS_PATH", str(data_file))
    monkeypatch.setattr(lookup, "_track_clusters_cache", None)

    assert lookup.get_cluster_for_track("nonexistent") is None


def test_get_centroid_returns_known_cluster(tmp_path, monkeypatch):
    data_file = tmp_path / "cluster_centroids.json"
    data_file.write_text(json.dumps({"3": {"tempo": 120.0}, "0": {"tempo": 90.0}}))
    monkeypatch.setattr(lookup, "CLUSTER_CENTROIDS_PATH", str(data_file))
    monkeypatch.setattr(lookup, "_cluster_centroids_cache", None)

    assert lookup.get_centroid(3) == {"tempo": 120.0}


def test_get_centroid_returns_none_for_unknown_cluster(tmp_path, monkeypatch):
    data_file = tmp_path / "cluster_centroids.json"
    data_file.write_text(json.dumps({"3": {"tempo": 120.0}}))
    monkeypatch.setattr(lookup, "CLUSTER_CENTROIDS_PATH", str(data_file))
    monkeypatch.setattr(lookup, "_cluster_centroids_cache", None)

    assert lookup.get_centroid(99) is None


def test_committed_artifacts_are_loadable_and_consistent():
    with open(lookup.TRACK_CLUSTERS_PATH) as f:
        clusters = json.load(f)
    centroids_path = os.path.join(os.path.dirname(lookup.__file__), "data", "cluster_centroids.json")
    with open(centroids_path) as f:
        centroids = json.load(f)

    assert len(clusters) == 89741
    assert set(clusters.values()) == {int(k) for k in centroids}

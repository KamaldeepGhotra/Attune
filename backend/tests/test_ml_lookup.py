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

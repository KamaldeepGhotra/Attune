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

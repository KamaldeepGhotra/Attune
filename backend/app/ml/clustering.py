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

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

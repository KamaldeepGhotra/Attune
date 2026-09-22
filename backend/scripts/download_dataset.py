import os

import httpx

DATASET_URL = "https://huggingface.co/datasets/maharshipandya/spotify-tracks-dataset/resolve/main/dataset.csv"


def download_dataset(dest_path: str) -> None:
    if os.path.exists(dest_path):
        return

    os.makedirs(os.path.dirname(dest_path), exist_ok=True)
    response = httpx.get(DATASET_URL, timeout=60.0, follow_redirects=True)
    response.raise_for_status()

    with open(dest_path, "wb") as f:
        f.write(response.content)


if __name__ == "__main__":
    download_dataset("data/raw/spotify_tracks.csv")

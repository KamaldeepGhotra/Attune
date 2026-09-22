import pandas as pd

COLUMNS = ["track_id", "artists", "track_name", "danceability", "energy", "valence", "tempo", "track_genre"]


def load_dataset(csv_path: str) -> pd.DataFrame:
    df = pd.read_csv(csv_path)
    df = df[COLUMNS]
    df = df.drop_duplicates(subset="track_id", keep="first")
    return df.reset_index(drop=True)

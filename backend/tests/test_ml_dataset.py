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

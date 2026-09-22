# Attune

A Spotify recommendation engine that builds a taste profile from your real listening history and suggests songs based on the vibe you're in — not just more of the artists you already listen to.

## Local setup

1. Create an app at https://developer.spotify.com/dashboard, add `http://127.0.0.1:8000/auth/callback` as a redirect URI (Spotify requires the loopback IP literal `127.0.0.1`, not `localhost`), and add your own Spotify account under the app's User Management tab.
2. Copy `.env.example` to `.env` and fill in your Spotify Client ID/Secret.
3. Run `docker compose up --build`.
4. Visit http://127.0.0.1:5173 (use `127.0.0.1`, not `localhost`, so the session cookie set during login matches the origin the frontend calls).

## ML pipeline

The heavy ML dependencies (pandas, scikit-learn, etc.) live in `backend/requirements-ml.txt` and are not installed by default. From `backend/`, after activating the venv, install them with:

```
pip install -r requirements-ml.txt
```

This is required before running the ML-related tests or the clustering pipeline itself.

To regenerate the clustering artifacts (`app/ml/data/track_clusters.json` and `cluster_centroids.json`), run from `backend/`:

```
python -m scripts.build_clusters
```

Note that k-means cluster IDs are arbitrary and not stable across re-runs — regenerating the artifacts will renumber clusters, which matters once anything downstream persists a cluster ID.

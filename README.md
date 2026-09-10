# Attune

A Spotify recommendation engine that builds a taste profile from your real listening history and suggests songs based on the vibe you're in — not just more of the artists you already listen to.

## Local setup

1. Create an app at https://developer.spotify.com/dashboard, add `http://127.0.0.1:8000/auth/callback` as a redirect URI (Spotify requires the loopback IP literal `127.0.0.1`, not `localhost`), and add your own Spotify account under the app's User Management tab.
2. Copy `.env.example` to `.env` and fill in your Spotify Client ID/Secret.
3. Run `docker compose up --build`.
4. Visit http://127.0.0.1:5173 (use `127.0.0.1`, not `localhost`, so the session cookie set during login matches the origin the frontend calls).

import { useEffect, useState } from "react";

import { fetchRecommendations } from "../api/client";

export default function Dashboard() {
  const [tracks, setTracks] = useState([]);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchRecommendations()
      .then((data) => setTracks(data.tracks))
      .catch((err) => setError(err.message));
  }, []);

  if (error) {
    return <p role="alert">{error}</p>;
  }

  return (
    <main>
      <h1>Your recommendations</h1>
      <ul>
        {tracks.map((track) => (
          <li key={track.id}>{track.name}</li>
        ))}
      </ul>
    </main>
  );
}

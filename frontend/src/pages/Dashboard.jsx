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
    return (
      <main className="min-h-screen flex items-center justify-center bg-black text-white px-4">
        <p role="alert" className="text-red-400">
          {error}
        </p>
      </main>
    );
  }

  return (
    <main className="min-h-screen bg-black text-white px-6 py-10">
      <div className="max-w-2xl mx-auto">
        <h1 className="text-3xl font-bold mb-6">Your recommendations</h1>
        <ul className="space-y-1">
          {tracks.map((track) => (
            <li
              key={track.id}
              className="flex items-center gap-4 p-3 rounded-lg hover:bg-white/10 transition-colors"
            >
              {track.album?.images?.[0]?.url && (
                <img
                  src={track.album.images[0].url}
                  alt={`${track.name} album art`}
                  className="w-12 h-12 rounded object-cover flex-shrink-0"
                />
              )}
              <div>
                <p className="font-medium">{track.name}</p>
                {track.artists && (
                  <p className="text-sm text-gray-400">
                    {track.artists.map((artist) => artist.name).join(", ")}
                  </p>
                )}
              </div>
            </li>
          ))}
        </ul>
      </div>
    </main>
  );
}

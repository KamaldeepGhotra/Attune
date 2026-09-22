import { getLoginUrl } from "../api/client";

export default function Login() {
  return (
    <main className="min-h-screen flex flex-col items-center justify-center bg-black text-white px-4">
      <h1 className="text-5xl font-bold tracking-tight mb-3">Attune</h1>
      <p className="text-gray-400 mb-8 text-center max-w-sm">
        Personalized song recommendations built from your real listening history.
      </p>
      <a
        href={getLoginUrl()}
        className="bg-[#1DB954] hover:bg-[#1ed760] text-black font-semibold px-8 py-3 rounded-full transition-colors"
      >
        Connect Spotify
      </a>
    </main>
  );
}

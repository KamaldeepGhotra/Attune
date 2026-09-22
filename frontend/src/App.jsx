import { useEffect, useState } from "react";

import { fetchRecommendations } from "./api/client";
import Dashboard from "./pages/Dashboard";
import Login from "./pages/Login";

export default function App() {
  const [isLoggedIn, setIsLoggedIn] = useState(null);

  useEffect(() => {
    fetchRecommendations()
      .then(() => setIsLoggedIn(true))
      .catch(() => setIsLoggedIn(false));
  }, []);

  if (isLoggedIn === null) {
    return (
      <main className="min-h-screen flex items-center justify-center bg-black">
        <div className="w-10 h-10 border-4 border-white/20 border-t-[#1DB954] rounded-full animate-spin" />
      </main>
    );
  }

  return isLoggedIn ? <Dashboard /> : <Login />;
}

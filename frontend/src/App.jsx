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
    return <p>Loading...</p>;
  }

  return isLoggedIn ? <Dashboard /> : <Login />;
}

import { getLoginUrl } from "../api/client";

export default function Login() {
  return (
    <main>
      <h1>Attune</h1>
      <a href={getLoginUrl()}>Connect Spotify</a>
    </main>
  );
}

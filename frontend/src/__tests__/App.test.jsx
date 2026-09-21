import { render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import App from "../App";

describe("App", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it("renders Login when the user is not authenticated", async () => {
    global.fetch = vi.fn().mockResolvedValue({ ok: false, status: 401 });

    render(<App />);

    expect(await screen.findByRole("link", { name: /connect spotify/i })).toBeInTheDocument();
  });

  it("renders Dashboard when the user is authenticated", async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ tracks: [{ id: "1", name: "Song One" }] }),
    });

    render(<App />);

    expect(await screen.findByText("Song One")).toBeInTheDocument();
  });
});

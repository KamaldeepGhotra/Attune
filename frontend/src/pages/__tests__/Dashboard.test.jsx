import { render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import Dashboard from "../Dashboard";

describe("Dashboard", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it("renders track name, artist, and album art once recommendations load", async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({
        tracks: [
          {
            id: "1",
            name: "Song One",
            artists: [{ name: "Artist One" }],
            album: { images: [{ url: "https://example.com/art.jpg" }] },
          },
        ],
      }),
    });

    render(<Dashboard />);

    expect(await screen.findByText("Song One")).toBeInTheDocument();
    expect(screen.getByText("Artist One")).toBeInTheDocument();
    expect(screen.getByRole("img")).toHaveAttribute("src", "https://example.com/art.jpg");
  });

  it("shows an error message when the request fails", async () => {
    global.fetch = vi.fn().mockResolvedValue({ ok: false, status: 401 });

    render(<Dashboard />);

    expect(await screen.findByRole("alert")).toHaveTextContent("401");
  });
});

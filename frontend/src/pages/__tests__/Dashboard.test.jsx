import { render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import Dashboard from "../Dashboard";

describe("Dashboard", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it("renders track names once recommendations load", async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ tracks: [{ id: "1", name: "Song One" }] }),
    });

    render(<Dashboard />);

    expect(await screen.findByText("Song One")).toBeInTheDocument();
  });

  it("shows an error message when the request fails", async () => {
    global.fetch = vi.fn().mockResolvedValue({ ok: false, status: 401 });

    render(<Dashboard />);

    expect(await screen.findByRole("alert")).toHaveTextContent("401");
  });
});

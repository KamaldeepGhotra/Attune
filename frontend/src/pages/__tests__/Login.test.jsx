import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import Login from "../Login";

describe("Login", () => {
  it("renders a link to the backend login route", () => {
    render(<Login />);

    const link = screen.getByRole("link", { name: /connect spotify/i });
    expect(link).toHaveAttribute("href", "http://127.0.0.1:8000/auth/login");
  });
});

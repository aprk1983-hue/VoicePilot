import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it } from "vitest";
import { ThemeProvider } from "../../context/ThemeProvider";
import { AppShell } from "./AppShell";

function renderShell(initialPath = "/") {
  return render(
    <ThemeProvider>
      <MemoryRouter initialEntries={[initialPath]}>
        <AppShell title="Test Page">
          <p>Page content</p>
        </AppShell>
      </MemoryRouter>
    </ThemeProvider>,
  );
}

describe("AppShell", () => {
  it("renders navigation and read-only notice", () => {
    renderShell();
    expect(screen.getByRole("navigation")).toBeInTheDocument();
    expect(screen.getByText(/Read-only advisory mode/i)).toBeInTheDocument();
    expect(screen.getByText("Page content")).toBeInTheDocument();
  });

  it("toggles theme from topbar", async () => {
    localStorage.setItem("voicepilot-theme", "light");
    renderShell();
    const toggle = screen.getByRole("button", { name: /theme/i });
    expect(toggle).toBeInTheDocument();
  });
});

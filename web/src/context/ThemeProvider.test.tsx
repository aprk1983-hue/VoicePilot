import { act, render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { ThemeProvider, useTheme } from "./ThemeProvider";

function ThemeToggleButton() {
  const { theme, toggleTheme } = useTheme();
  return (
    <>
      <span data-testid="theme">{theme}</span>
      <button type="button" onClick={toggleTheme}>
        Toggle
      </button>
    </>
  );
}

describe("ThemeProvider", () => {
  it("applies theme to document and toggles", async () => {
    localStorage.setItem("voicepilot-theme", "light");

    render(
      <ThemeProvider>
        <ThemeToggleButton />
      </ThemeProvider>,
    );

    expect(screen.getByTestId("theme")).toHaveTextContent("light");
    expect(document.documentElement.getAttribute("data-theme")).toBe("light");

    await act(async () => {
      screen.getByRole("button", { name: "Toggle" }).click();
    });
    await waitFor(() => {
      expect(screen.getByTestId("theme")).toHaveTextContent("dark");
    });
    expect(document.documentElement.getAttribute("data-theme")).toBe("dark");
  });
});

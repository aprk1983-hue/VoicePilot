import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it } from "vitest";
import { CaseWorkspaceNav } from "./CaseWorkspaceNav";

describe("CaseWorkspaceNav", () => {
  it("renders workspace section links for a case", () => {
    render(
      <MemoryRouter initialEntries={["/cases/case-1/evidence"]}>
        <CaseWorkspaceNav caseId="case-1" />
      </MemoryRouter>,
    );

    expect(screen.getByRole("link", { name: "Overview" })).toHaveAttribute(
      "href",
      "/cases/case-1",
    );
    expect(screen.getByRole("link", { name: "Evidence" })).toHaveAttribute(
      "href",
      "/cases/case-1/evidence",
    );
    expect(screen.getByRole("link", { name: "Investigation" })).toHaveAttribute(
      "href",
      "/cases/case-1/investigation",
    );
  });
});

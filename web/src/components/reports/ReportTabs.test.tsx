import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it } from "vitest";
import { ReportTabs } from "./ReportTabs";

describe("ReportTabs", () => {
  it("renders report type tabs with active state", () => {
    render(
      <MemoryRouter>
        <ReportTabs caseId="case-123" activeType="engineering" />
      </MemoryRouter>,
    );

    const tablist = screen.getByRole("tablist", { name: "Report types" });
    expect(tablist).toBeInTheDocument();

    const executive = screen.getByRole("tab", { name: "Executive" });
    const engineering = screen.getByRole("tab", { name: "Engineering" });
    expect(engineering).toHaveAttribute("aria-selected", "true");
    expect(executive).toHaveAttribute("aria-selected", "false");
    expect(executive).toHaveAttribute("href", "/cases/case-123/reports/executive");
  });
});

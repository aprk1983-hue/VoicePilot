import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { MetricCard } from "./MetricCard";

describe("MetricCard", () => {
  it("renders label and value", () => {
    render(<MetricCard label="Active Cases" value={12} />);
    expect(screen.getByText("Active Cases")).toBeInTheDocument();
    expect(screen.getByText("12")).toBeInTheDocument();
  });

  it("renders optional hint", () => {
    render(<MetricCard label="Findings" value={3} hint="Across all cases" />);
    expect(screen.getByText("Across all cases")).toBeInTheDocument();
  });
});

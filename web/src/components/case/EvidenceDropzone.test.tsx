import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { EvidenceDropzone } from "./EvidenceDropzone";

describe("EvidenceDropzone", () => {
  it("reads dropped file content", async () => {
    const onFileContent = vi.fn();
    render(<EvidenceDropzone onFileContent={onFileContent} />);

    const file = {
      name: "organization_export.csv",
      text: vi.fn().mockResolvedValue("evidence output"),
    } as unknown as File;

    const dropzone = screen.getByText(/Drag & drop evidence files/i).closest(".dropzone");
    expect(dropzone).toBeTruthy();

    fireEvent.drop(dropzone!, {
      dataTransfer: { files: [file] },
    });

    await waitFor(() => {
      expect(onFileContent).toHaveBeenCalledWith(
        "organization_export.csv",
        "evidence output",
      );
    });
  });
});

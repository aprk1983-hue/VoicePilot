import { Navigate, Route, Routes } from "react-router-dom";
import { Layout } from "./components/Layout";
import { CaseDetailPage } from "./pages/CaseDetail";
import { CasesPage } from "./pages/Cases";
import { ChangePackageViewerPage } from "./pages/ChangePackageViewer";
import { DashboardPage } from "./pages/Dashboard";
import { EvidenceUploadPage } from "./pages/EvidenceUpload";
import { InvestigationStatusPage } from "./pages/InvestigationStatus";
import { NewCasePage } from "./pages/NewCase";
import { ReportViewerPage } from "./pages/ReportViewer";
import { ValidationPage } from "./pages/Validation";

export function App() {
  return (
    <Layout>
      <Routes>
        <Route path="/" element={<DashboardPage />} />
        <Route path="/cases" element={<CasesPage />} />
        <Route path="/cases/new" element={<NewCasePage />} />
        <Route path="/cases/:caseId" element={<CaseDetailPage />} />
        <Route path="/cases/:caseId/evidence" element={<EvidenceUploadPage />} />
        <Route path="/cases/:caseId/status" element={<InvestigationStatusPage />} />
        <Route path="/cases/:caseId/reports/:reportType" element={<ReportViewerPage />} />
        <Route path="/cases/:caseId/change-package" element={<ChangePackageViewerPage />} />
        <Route path="/validation" element={<ValidationPage />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </Layout>
  );
}

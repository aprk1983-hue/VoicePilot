import { Navigate, Route, Routes, useLocation } from "react-router-dom";
import { AppShell } from "./components/layout/AppShell";
import { CasesPage } from "./pages/Cases";
import { DashboardPage } from "./pages/Dashboard";
import { NewCasePage } from "./pages/NewCase";
import { ValidationPage } from "./pages/Validation";
import { CaseWorkspaceLayout } from "./pages/workspace/CaseWorkspaceLayout";
import { OverviewTab } from "./pages/workspace/OverviewTab";
import { EvidenceTab } from "./pages/workspace/EvidenceTab";
import { InvestigationTab } from "./pages/workspace/InvestigationTab";
import { ReportsTab, ReportsRedirect } from "./pages/workspace/ReportsTab";
import { ChangePackageTab } from "./pages/workspace/ChangePackageTab";

function usePageTitle(): string | undefined {
  const { pathname } = useLocation();
  if (pathname === "/") return "Dashboard";
  if (pathname === "/cases") return "Cases";
  if (pathname === "/cases/new") return "New Case";
  if (pathname === "/validation") return "Validation";
  if (pathname.startsWith("/cases/")) return "Investigation Workspace";
  return undefined;
}

export function App() {
  const title = usePageTitle();

  return (
    <AppShell title={title}>
      <Routes>
        <Route path="/" element={<DashboardPage />} />
        <Route path="/cases" element={<CasesPage />} />
        <Route path="/cases/new" element={<NewCasePage />} />
        <Route path="/cases/:caseId" element={<CaseWorkspaceLayout />}>
          <Route index element={<OverviewTab />} />
          <Route path="evidence" element={<EvidenceTab />} />
          <Route path="investigation" element={<InvestigationTab />} />
          <Route path="reports" element={<ReportsRedirect />} />
          <Route path="reports/:reportType" element={<ReportsTab />} />
          <Route path="change-package" element={<ChangePackageTab />} />
        </Route>
        <Route path="/validation" element={<ValidationPage />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </AppShell>
  );
}

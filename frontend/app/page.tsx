"use client";

import React, { useState } from "react";
import { Navbar } from "@/components/layout/Navbar";
import { Footer } from "@/components/layout/Footer";
import { Hero } from "@/components/landing/Hero";
import { PipelineShowcase } from "@/components/landing/PipelineShowcase";
import { SecuritySection } from "@/components/landing/SecuritySection";
import { ScanningProgress } from "@/components/analysis/ScanningProgress";
import { ReportHeader } from "@/components/report/ReportHeader";
import { OverallScoreCard } from "@/components/report/OverallScoreCard";
import { PillarGrid } from "@/components/report/PillarGrid";
import { ScannerList } from "@/components/report/ScannerList";
import { CoverageCard } from "@/components/report/CoverageCard";
import { FindingsExplorer } from "@/components/findings/FindingsExplorer";

import { PillarChart } from "@/components/charts/PillarChart";
import { SecurityCommandCenter } from "@/components/security/SecurityCommandCenter";
import { ProgressDashboard } from "@/components/progress/ProgressDashboard";
import { RescanModal } from "@/components/progress/RescanModal";
import { ScanHistoryCard } from "@/components/progress/ScanHistoryCard";
import { useAnalysis } from "@/hooks/useAnalysis";
import { formatDelta } from "@/lib/utils";
import { AlertCircle, RotateCcw, GitCompare, Sparkles } from "lucide-react";


export default function HomePage() {
  const {
    report,
    previousReport,
    comparisonReport,
    scanHistory,
    isLoading,
    errorMessage,
    targetName,
    sceneState,
    startAnalysis,
    startRescan,
    resetAnalysis,
  } = useAnalysis();

  const [prefillUrl, setPrefillUrl] = useState<string>("");
  const [isRescanModalOpen, setIsRescanModalOpen] = useState<boolean>(false);
  const [viewMode, setViewMode] = useState<"overview" | "cybersecurity" | "progress">("overview");

  // Automatically switch to progress view if a new comparison report is generated
  React.useEffect(() => {
    if (comparisonReport) {
      setViewMode("progress");
    }
  }, [comparisonReport]);

  const handleDemoClick = (url: string) => {
    setPrefillUrl(url);
    if (report) {
      resetAnalysis();
    }
  };

  const securityFindingsCount = report?.findings.filter(
    (f) =>
      f.category === "security" ||
      f.scanner.includes("secret") ||
      f.scanner === "gitleaks" ||
      f.scanner === "npm-audit" ||
      f.scanner === "pip-audit" ||
      f.scanner === "bandit"
  ).length ?? 0;

  return (
    <div className="flex-1 flex flex-col min-h-screen">
      <Navbar onReset={resetAnalysis} onSampleClick={handleDemoClick} />

      <main className="flex-1 flex flex-col">
        {/* Loading Scanning State */}
        {isLoading && (
          <div className="flex-1 flex items-center justify-center p-6 py-20">
            <ScanningProgress targetName={targetName} />
          </div>
        )}

        {/* Error State */}
        {!isLoading && errorMessage && (
          <div className="max-w-2xl mx-auto w-full p-6 my-12">
            <div className="p-6 rounded-xl border border-red-500/30 bg-red-500/10 flex flex-col items-center text-center">
              <div className="w-10 h-10 rounded-full bg-red-500/20 text-red-400 flex items-center justify-center mb-3">
                <AlertCircle className="w-5 h-5" />
              </div>
              <h2 className="text-base font-bold font-mono text-red-400 mb-2">
                Audit Analysis Error
              </h2>
              <p className="text-xs font-mono text-text-primary mb-6 max-w-md">
                {errorMessage}
              </p>
              <button
                onClick={resetAnalysis}
                className="px-4 py-2 rounded-lg bg-surface hover:bg-surface-elevated border border-border text-xs font-mono text-text-primary transition-all flex items-center gap-2"
              >
                <RotateCcw className="w-3.5 h-3.5" />
                <span>Try Another Project</span>
              </button>
            </div>
          </div>
        )}

        {/* Report View State */}
        {!isLoading && !errorMessage && report && (
          <div className="max-w-7xl mx-auto w-full p-4 sm:p-6 py-8">
            <ReportHeader
              project={report.project}
              analysis={report.analysis}
              report={report}
              onNewScan={resetAnalysis}
              onRescanClick={() => setIsRescanModalOpen(true)}
            />

            {/* View Switcher Tabs: Overview vs Cybersecurity vs Progress */}
            <div className="flex flex-wrap items-center gap-2 p-1 bg-surface border border-border rounded-xl mb-6 w-full sm:w-fit">
              <button
                onClick={() => setViewMode("overview")}
                className={`flex-1 sm:flex-initial px-4 py-2 rounded-lg text-xs font-mono transition-all ${
                  viewMode === "overview"
                    ? "bg-surface-elevated text-text-primary border border-border font-bold shadow-sm"
                    : "text-text-muted hover:text-text-secondary"
                }`}
              >
                Audit Overview (6 Pillars)
              </button>
              <button
                onClick={() => setViewMode("cybersecurity")}
                className={`flex-1 sm:flex-initial flex items-center justify-center gap-2 px-4 py-2 rounded-lg text-xs font-mono transition-all ${
                  viewMode === "cybersecurity"
                    ? "bg-red-500/10 text-red-400 border border-red-500/30 font-bold shadow-sm"
                    : "text-text-muted hover:text-text-secondary"
                }`}
              >
                <span>Cybersecurity Command Center</span>
                {securityFindingsCount > 0 && (
                  <span className="px-1.5 py-0.2 rounded-full bg-red-500/20 text-red-400 text-[10px]">
                    {securityFindingsCount}
                  </span>
                )}
              </button>

              {comparisonReport && (
                <button
                  onClick={() => setViewMode("progress")}
                  className={`flex-1 sm:flex-initial flex items-center justify-center gap-2 px-4 py-2 rounded-lg text-xs font-mono transition-all ${
                    viewMode === "progress"
                      ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 font-bold shadow-sm"
                      : "text-text-muted hover:text-text-secondary"
                  }`}
                >
                  <GitCompare className="w-3.5 h-3.5 text-emerald-400" />
                  <span>Re-Scan Progress</span>
                  <span
                    className={`px-1.5 py-0.2 rounded-full text-[10px] font-bold ${
                      comparisonReport.overall.delta >= 0
                        ? "bg-emerald-500/20 text-emerald-400"
                        : "bg-rose-500/20 text-rose-400"
                    }`}
                  >
                    {formatDelta(comparisonReport.overall.delta)} pts
                  </span>
                </button>
              )}
            </div>

            {/* View Mode: General Overview */}
            {viewMode === "overview" && (
              <>
                {report.score && (
                  <>
                    <OverallScoreCard
                      score={report.score}
                      summary={report.summary}
                      onRescanClick={() => setIsRescanModalOpen(true)}
                    />

                    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
                      <div className="lg:col-span-2">
                        <PillarGrid score={report.score} />
                      </div>
                      <div className="lg:col-span-1">
                        <PillarChart score={report.score} />
                      </div>
                    </div>
                  </>
                )}

                <CoverageCard
                  coverage={report.coverage}
                  intelligence={report.intelligence}
                />

                <ScannerList scanners={report.scanners} />
                <FindingsExplorer findings={report.findings} />

                {scanHistory.length > 0 && (
                  <div className="mt-8">
                    <ScanHistoryCard scans={scanHistory} currentScanId={report.scan_id} />
                  </div>
                )}
              </>
            )}


            {/* View Mode: Cybersecurity Command Center */}
            {viewMode === "cybersecurity" && (
              <SecurityCommandCenter report={report} />
            )}

            {/* View Mode: Re-Scan Progress Tracking */}
            {viewMode === "progress" && comparisonReport && (
              <ProgressDashboard
                comparison={comparisonReport}
                onTriggerRescan={() => setIsRescanModalOpen(true)}
                scanHistory={scanHistory}
                currentScanId={report.scan_id}
              />
            )}
          </div>
        )}

        {/* Rescan Modal */}
        {report && (
          <RescanModal
            isOpen={isRescanModalOpen}
            onClose={() => setIsRescanModalOpen(false)}
            project={report.project}
            isLoading={isLoading}
            onRescan={async (options) => {
              setIsRescanModalOpen(false);
              await startRescan(options);
            }}
          />
        )}

        {/* Landing Page State */}
        {!isLoading && !errorMessage && !report && (
          <>
            <Hero
              onAnalyze={startAnalysis}
              isLoading={isLoading}
              sceneState={sceneState}
              initialUrl={prefillUrl}
            />
            <PipelineShowcase />
            <SecuritySection />
          </>
        )}
      </main>

      <Footer />
    </div>
  );
}

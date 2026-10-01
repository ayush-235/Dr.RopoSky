"use client";

import { useState, useCallback, useEffect } from "react";
import { AnalysisReport, SceneState, ComparisonReport } from "@/types/report";
import {
  analyzeRepository,
  compareReports,
  rescanProject,
  getProjectScans,
  ProjectScanSummary,
  APIError,
} from "@/lib/api/client";

export function useAnalysis() {
  const [report, setReport] = useState<AnalysisReport | null>(null);
  const [previousReport, setPreviousReport] = useState<AnalysisReport | null>(null);
  const [comparisonReport, setComparisonReport] = useState<ComparisonReport | null>(null);
  const [scanHistory, setScanHistory] = useState<ProjectScanSummary[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [targetName, setTargetName] = useState<string>("");
  const [sceneState, setSceneState] = useState<SceneState>("idle");

  const fetchHistory = useCallback(async (projectId: string) => {
    try {
      const history = await getProjectScans(projectId);
      setScanHistory(history);
    } catch {
      // Non-blocking for scan history
    }
  }, []);

  useEffect(() => {
    if (report?.project_id) {
      fetchHistory(report.project_id);
    }
  }, [report?.project_id, fetchHistory]);

  const startAnalysis = useCallback(
    async (options: { githubUrl?: string; zipFile?: File }) => {
      setIsLoading(true);
      setErrorMessage(null);
      setComparisonReport(null);
      setPreviousReport(null);
      setScanHistory([]);
      setSceneState("scanning");

      const target =
        options.githubUrl ||
        (options.zipFile ? options.zipFile.name : "Target Project");
      setTargetName(target);

      try {
        const result = await analyzeRepository(
          options.githubUrl,
          options.zipFile
        );
        setReport(result);
        const hasCritical =
          result.summary.critical > 0 || result.summary.high > 0;
        setSceneState(hasCritical ? "issues" : "completed");

        if (result.project_id) {
          fetchHistory(result.project_id);
        }
      } catch (err: any) {
        setSceneState("idle");
        if (err instanceof APIError) {
          setErrorMessage(err.message);
        } else {
          setErrorMessage(
            err.message || "An unexpected error occurred during analysis."
          );
        }
      } finally {
        setIsLoading(false);
      }
    },
    [fetchHistory]
  );

  const startRescan = useCallback(
    async (options: { githubUrl?: string; zipFile?: File }) => {
      if (!report) {
        return;
      }

      setIsLoading(true);
      setErrorMessage(null);
      setSceneState("scanning");

      const target =
        options.githubUrl ||
        (options.zipFile ? options.zipFile.name : "Re-Scan Project");
      setTargetName(target);

      try {
        // If git url and project_id exists, use the server-side rescan endpoint
        if (report.project_id && options.githubUrl && !options.zipFile) {
          const rescanRes = await rescanProject(report.project_id);
          setPreviousReport(report);
          setReport(rescanRes.current_report);
          setComparisonReport(rescanRes.comparison);

          const hasCritical =
            rescanRes.current_report.summary.critical > 0 ||
            rescanRes.current_report.summary.high > 0;
          setSceneState(hasCritical ? "issues" : "completed");

          fetchHistory(report.project_id);
        } else {
          // Direct file upload or fallback rescan
          const newResult = await analyzeRepository(
            options.githubUrl,
            options.zipFile
          );

          const compResult = await compareReports(report, newResult);

          setPreviousReport(report);
          setReport(newResult);
          setComparisonReport(compResult);

          const hasCritical =
            newResult.summary.critical > 0 || newResult.summary.high > 0;
          setSceneState(hasCritical ? "issues" : "completed");

          if (newResult.project_id) {
            fetchHistory(newResult.project_id);
          }
        }
      } catch (err: any) {
        setSceneState("idle");
        if (err instanceof APIError) {
          setErrorMessage(err.message);
        } else {
          setErrorMessage(
            err.message || "An unexpected error occurred during re-scan comparison."
          );
        }
      } finally {
        setIsLoading(false);
      }
    },
    [report, fetchHistory]
  );

  const resetAnalysis = useCallback(() => {
    setReport(null);
    setPreviousReport(null);
    setComparisonReport(null);
    setScanHistory([]);
    setIsLoading(false);
    setErrorMessage(null);
    setTargetName("");
    setSceneState("idle");
  }, []);

  return {
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
  };
}


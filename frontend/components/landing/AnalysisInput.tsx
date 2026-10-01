"use client";

import React, { useState, useRef } from "react";
import { Github, Upload, ArrowRight, FileArchive, X, AlertCircle } from "lucide-react";

interface AnalysisInputProps {
  onAnalyze: (options: { githubUrl?: string; zipFile?: File }) => void;
  isLoading: boolean;
  onInputChange?: (hasInput: boolean) => void;
  initialUrl?: string;
}

export const AnalysisInput: React.FC<AnalysisInputProps> = ({
  onAnalyze,
  isLoading,
  onInputChange,
  initialUrl = "",
}) => {
  const [activeTab, setActiveTab] = useState<"github" | "zip">("github");
  const [githubUrl, setGithubUrl] = useState<string>(initialUrl);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [validationError, setValidationError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Sync initialUrl
  React.useEffect(() => {
    if (initialUrl) {
      setGithubUrl(initialUrl);
      setActiveTab("github");
      onInputChange?.(true);
    }
  }, [initialUrl, onInputChange]);

  const handleUrlChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const val = e.target.value;
    setGithubUrl(val);
    setValidationError(null);
    onInputChange?.(Boolean(val.trim()));
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      if (!file.name.toLowerCase().endsWith(".zip")) {
        setValidationError("Only .zip archives are supported.");
        return;
      }
      if (file.size > 100 * 1024 * 1024) {
        setValidationError("Archive exceeds the maximum 100 MB upload limit.");
        return;
      }
      setSelectedFile(file);
      setValidationError(null);
      onInputChange?.(true);
    }
  };

  const clearFile = () => {
    setSelectedFile(null);
    if (fileInputRef.current) fileInputRef.current.value = "";
    onInputChange?.(false);
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setValidationError(null);

    if (activeTab === "github") {
      const trimmed = githubUrl.trim();
      if (!trimmed) {
        setValidationError("Please enter a GitHub repository URL.");
        return;
      }
      if (!trimmed.startsWith("https://github.com/")) {
        setValidationError("Please provide a valid HTTPS GitHub repository URL (e.g., https://github.com/owner/repo).");
        return;
      }
      onAnalyze({ githubUrl: trimmed });
    } else {
      if (!selectedFile) {
        setValidationError("Please select a .zip archive to upload.");
        return;
      }
      onAnalyze({ zipFile: selectedFile });
    }
  };

  return (
    <div className="w-full max-w-2xl mx-auto rounded-xl border border-border bg-surface/90 backdrop-blur-md p-5 sm:p-6 shadow-2xl">
      {/* Mode Switcher */}
      <div className="flex items-center gap-2 p-1 bg-surface-elevated rounded-lg border border-border mb-4">
        <button
          type="button"
          onClick={() => {
            setActiveTab("github");
            setValidationError(null);
            onInputChange?.(Boolean(githubUrl.trim()));
          }}
          className={`flex-1 flex items-center justify-center gap-2 py-2 px-3 rounded-md text-xs font-mono transition-all ${
            activeTab === "github"
              ? "bg-surface border border-border text-text-primary shadow-sm"
              : "text-text-muted hover:text-text-secondary"
          }`}
        >
          <Github className="w-3.5 h-3.5" />
          <span>GitHub Repository</span>
        </button>
        <button
          type="button"
          onClick={() => {
            setActiveTab("zip");
            setValidationError(null);
            onInputChange?.(Boolean(selectedFile));
          }}
          className={`flex-1 flex items-center justify-center gap-2 py-2 px-3 rounded-md text-xs font-mono transition-all ${
            activeTab === "zip"
              ? "bg-surface border border-border text-text-primary shadow-sm"
              : "text-text-muted hover:text-text-secondary"
          }`}
        >
          <Upload className="w-3.5 h-3.5" />
          <span>ZIP Archive</span>
        </button>
      </div>

      <form onSubmit={handleSubmit} className="space-y-4">
        {activeTab === "github" ? (
          <div>
            <label className="block text-xs font-mono text-text-secondary mb-1.5">
              Public Repository URL
            </label>
            <div className="relative">
              <input
                type="text"
                value={githubUrl}
                onChange={handleUrlChange}
                placeholder="https://github.com/owner/repository"
                disabled={isLoading}
                className="w-full px-3.5 py-2.5 rounded-lg bg-surface-elevated border border-border focus:border-primary/60 focus:outline-none text-text-primary text-sm font-mono placeholder:text-text-muted transition-colors"
              />
            </div>
          </div>
        ) : (
          <div>
            <label className="block text-xs font-mono text-text-secondary mb-1.5">
              Project Archive (ZIP, max 100 MB)
            </label>
            <input
              ref={fileInputRef}
              type="file"
              accept=".zip,application/zip"
              onChange={handleFileChange}
              disabled={isLoading}
              className="hidden"
            />
            {selectedFile ? (
              <div className="flex items-center justify-between p-3 rounded-lg bg-surface-elevated border border-border text-sm font-mono">
                <div className="flex items-center gap-2 text-text-primary truncate">
                  <FileArchive className="w-4 h-4 text-primary shrink-0" />
                  <span className="truncate">{selectedFile.name}</span>
                  <span className="text-xs text-text-muted">
                    ({(selectedFile.size / (1024 * 1024)).toFixed(2)} MB)
                  </span>
                </div>
                <button
                  type="button"
                  onClick={clearFile}
                  disabled={isLoading}
                  className="p-1 rounded text-text-muted hover:text-text-primary hover:bg-surface"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>
            ) : (
              <div
                onClick={() => fileInputRef.current?.click()}
                className="w-full py-8 px-4 rounded-lg border border-dashed border-border hover:border-primary/50 bg-surface-elevated/50 flex flex-col items-center justify-center cursor-pointer transition-colors group"
              >
                <Upload className="w-6 h-6 text-text-muted group-hover:text-primary mb-2 transition-colors" />
                <span className="text-xs font-mono text-text-secondary group-hover:text-text-primary">
                  Click to browse or drop project .zip
                </span>
                <span className="text-[11px] font-mono text-text-muted mt-1">
                  Protected with Zip Slip & path traversal verification
                </span>
              </div>
            )}
          </div>
        )}

        {validationError && (
          <div className="flex items-center gap-2 p-2.5 rounded-lg bg-red-500/10 border border-red-500/20 text-xs font-mono text-red-400">
            <AlertCircle className="w-4 h-4 shrink-0" />
            <span>{validationError}</span>
          </div>
        )}

        <button
          type="submit"
          disabled={isLoading}
          className="w-full py-3 px-4 rounded-lg bg-primary hover:bg-primary-hover text-background font-mono font-semibold text-sm transition-all flex items-center justify-center gap-2 shadow-lg shadow-primary/20 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {isLoading ? (
            <>
              <div className="w-4 h-4 rounded-full border-2 border-background border-t-transparent animate-spin" />
              <span>SCANNING PROJECT...</span>
            </>
          ) : (
            <>
              <span>START AUDIT ANALYSIS</span>
              <ArrowRight className="w-4 h-4" />
            </>
          )}
        </button>
      </form>

      {/* Safety Notice */}
      <div className="mt-4 pt-3 border-t border-border flex items-center justify-between text-[11px] font-mono text-text-muted">
        <span>🔒 Zero Untrusted Code Execution</span>
        <span>⚡ AST + Static + Secrets + AI</span>
      </div>
    </div>
  );
};

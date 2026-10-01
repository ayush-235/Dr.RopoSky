"use client";

import React, { useState } from "react";
import { ProjectMetadata } from "@/types/report";
import {
  X,
  RefreshCw,
  GitBranch,
  UploadCloud,
  FileArchive,
  ArrowRight,
  ShieldCheck,
} from "lucide-react";

interface RescanModalProps {
  isOpen: boolean;
  onClose: () => void;
  project: ProjectMetadata;
  onRescan: (options: { githubUrl?: string; zipFile?: File }) => Promise<void>;
  isLoading: boolean;
}

export const RescanModal: React.FC<RescanModalProps> = ({
  isOpen,
  onClose,
  project,
  onRescan,
  isLoading,
}) => {
  const [activeTab, setActiveTab] = useState<"github" | "zip">(
    project.source_type === "github" ? "github" : "zip"
  );
  const [githubUrl, setGithubUrl] = useState<string>(
    project.source_type === "github" ? (project.target_url || (project as any).url || "") : ""
  );
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [dragActive, setDragActive] = useState(false);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (activeTab === "github" && githubUrl.trim()) {
      await onRescan({ githubUrl: githubUrl.trim() });
    } else if (activeTab === "zip" && selectedFile) {
      await onRescan({ zipFile: selectedFile });
    }
  };

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const file = e.dataTransfer.files[0];
      if (file.name.endsWith(".zip")) {
        setSelectedFile(file);
      }
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-background/80 backdrop-blur-md animate-in fade-in duration-200">
      <div className="relative w-full max-w-xl rounded-2xl border border-border bg-surface shadow-2xl p-6 sm:p-8 space-y-6">
        {/* Header */}
        <div className="flex items-start justify-between">
          <div>
            <div className="flex items-center gap-2 text-xs font-mono text-primary mb-1">
              <RefreshCw className="w-3.5 h-3.5" />
              <span>RE-SCAN & PROGRESS TRACKING</span>
            </div>
            <h2 className="text-lg sm:text-xl font-bold font-mono text-text-primary">
              Re-Scan Project for Progress Comparison
            </h2>
            <p className="text-xs font-mono text-text-muted mt-1">
              Submit your updated code. Dr.RopoSky will re-audit the project and deterministically compare it against the baseline.
            </p>
          </div>
          <button
            onClick={onClose}
            disabled={isLoading}
            className="p-1 rounded-lg hover:bg-surface-elevated text-text-muted hover:text-text-primary transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Source Tabs */}
        <div className="flex items-center gap-2 p-1 bg-surface-elevated border border-border rounded-xl">
          <button
            type="button"
            onClick={() => setActiveTab("github")}
            className={`flex-1 flex items-center justify-center gap-2 py-2 rounded-lg text-xs font-mono transition-all ${
              activeTab === "github"
                ? "bg-surface text-text-primary font-bold shadow-sm"
                : "text-text-muted hover:text-text-secondary"
            }`}
          >
            <GitBranch className="w-3.5 h-3.5" />
            <span>GitHub Repository</span>
          </button>
          <button
            type="button"
            onClick={() => setActiveTab("zip")}
            className={`flex-1 flex items-center justify-center gap-2 py-2 rounded-lg text-xs font-mono transition-all ${
              activeTab === "zip"
                ? "bg-surface text-text-primary font-bold shadow-sm"
                : "text-text-muted hover:text-text-secondary"
            }`}
          >
            <FileArchive className="w-3.5 h-3.5" />
            <span>ZIP Archive</span>
          </button>
        </div>

        {/* Input Form */}
        <form onSubmit={handleSubmit} className="space-y-4">
          {activeTab === "github" && (
            <div className="space-y-2">
              <label className="text-xs font-mono text-text-secondary">
                GitHub Repository URL
              </label>
              <div className="relative">
                <GitBranch className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-text-muted" />
                <input
                  type="url"
                  placeholder="https://github.com/owner/repo"
                  value={githubUrl}
                  onChange={(e) => setGithubUrl(e.target.value)}
                  className="w-full pl-10 pr-4 py-2.5 rounded-xl bg-surface-elevated border border-border text-xs font-mono text-text-primary placeholder:text-text-muted focus:outline-none focus:border-primary/50"
                  required
                />
              </div>
              <p className="text-[11px] font-mono text-text-muted">
                Dr.RopoSky will clone latest commits and compare against previous scan results.
              </p>
            </div>
          )}

          {activeTab === "zip" && (
            <div className="space-y-2">
              <label className="text-xs font-mono text-text-secondary">
                Upload Patched ZIP Archive
              </label>
              <div
                onDragEnter={handleDrag}
                onDragLeave={handleDrag}
                onDragOver={handleDrag}
                onDrop={handleDrop}
                className={`border-2 border-dashed rounded-xl p-6 text-center cursor-pointer transition-all ${
                  dragActive
                    ? "border-primary bg-primary/5"
                    : selectedFile
                    ? "border-emerald-500/50 bg-emerald-500/5"
                    : "border-border hover:border-border-active bg-surface-elevated/50"
                }`}
                onClick={() => {
                  const input = document.getElementById("rescan-file-input");
                  input?.click();
                }}
              >
                <input
                  id="rescan-file-input"
                  type="file"
                  accept=".zip"
                  className="hidden"
                  onChange={(e) => {
                    if (e.target.files && e.target.files[0]) {
                      setSelectedFile(e.target.files[0]);
                    }
                  }}
                />
                <UploadCloud className="w-8 h-8 text-text-muted mx-auto mb-2" />
                {selectedFile ? (
                  <div>
                    <span className="text-xs font-mono font-bold text-emerald-400">
                      {selectedFile.name}
                    </span>
                    <span className="text-[10px] font-mono text-text-muted block mt-0.5">
                      {(selectedFile.size / 1024).toFixed(1)} KB &bull; Click or drop another to replace
                    </span>
                  </div>
                ) : (
                  <div>
                    <span className="text-xs font-mono text-text-primary">
                      Drop updated .zip archive here or click to browse
                    </span>
                    <span className="text-[10px] font-mono text-text-muted block mt-0.5">
                      Max file size: 100MB
                    </span>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Action Buttons */}
          <div className="flex items-center justify-end gap-3 pt-4 border-t border-border">
            <button
              type="button"
              onClick={onClose}
              disabled={isLoading}
              className="px-4 py-2 rounded-xl bg-surface-elevated hover:bg-surface border border-border text-xs font-mono text-text-secondary transition-all"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={
                isLoading ||
                (activeTab === "github" && !githubUrl.trim()) ||
                (activeTab === "zip" && !selectedFile)
              }
              className="px-5 py-2.5 rounded-xl bg-primary hover:bg-primary-hover text-background font-mono font-bold text-xs transition-all flex items-center gap-2 shadow-lg shadow-primary/20 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isLoading ? (
                <>
                  <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                  <span>Scanning & Comparing...</span>
                </>
              ) : (
                <>
                  <span>Run Re-Scan & Compare</span>
                  <ArrowRight className="w-3.5 h-3.5" />
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

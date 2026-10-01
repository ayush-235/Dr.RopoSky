"use client";

import React from "react";
import Editor from "@monaco-editor/react";

interface CodeViewerProps {
  code: string;
  language?: string;
  height?: string;
  highlightLine?: number | null;
  readOnly?: boolean;
}

export const CodeViewer: React.FC<CodeViewerProps> = ({
  code,
  language = "typescript",
  height = "180px",
  highlightLine,
  readOnly = true,
}) => {
  return (
    <div className="w-full rounded-lg border border-border bg-[#0d0e11] overflow-hidden">
      <Editor
        height={height}
        language={language}
        value={code}
        theme="vs-dark"
        options={{
          readOnly,
          minimap: { enabled: false },
          scrollBeyondLastLine: false,
          fontSize: 12,
          fontFamily: "'JetBrains Mono', 'Fira Code', monospace",
          lineNumbers: "on",
          renderLineHighlight: highlightLine ? "all" : "none",
          folding: false,
          glyphMargin: false,
          lineDecorationsWidth: 10,
          lineNumbersMinChars: 3,
          domReadOnly: true,
          cursorStyle: "line",
          contextmenu: false,
        }}
      />
    </div>
  );
};

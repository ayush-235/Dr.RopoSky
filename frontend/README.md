# Dr.RopoSky Frontend

Next.js 14 Web Application, 3D Landing Experience & Dedicated Cybersecurity Command Center for Dr.RopoSky.

## Environment Configuration

Configure frontend environment variables in `frontend/.env.local` (gitignored):

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## Architecture

- **Framework**: Next.js 14 (App Router) + TypeScript + React 18
- **Styling**: Tailwind CSS (Minimal Cybersecurity dark palette: `#0a0a0c`, `#121316`, `#26282e`)
- **3D Visualization**: Three.js + React Three Fiber + `@react-three/drei` (Isolated to Landing/Hero)
- **Code Viewer**: `@monaco-editor/react` (Read-only, syntax highlighted with line markers)
- **Charts**: Recharts (Radar / Bar posture breakdown)
- **Icons**: Lucide React

## Component Structure

```
frontend/
├── app/
│   ├── layout.tsx         # Root dark layout with metadata
│   ├── page.tsx           # Home page orchestrating landing, scanning, and dual-view reports
│   └── globals.css        # Global CSS & Tailwind layers
├── components/
│   ├── layout/
│   │   ├── Navbar.tsx     # Branding, status, and demo repo trigger
│   │   └── Footer.tsx     # Security and platform footer
│   ├── three/
│   │   ├── ProjectCoreScene.tsx # React Three Fiber 3D Project Analysis Core
│   │   └── CoreFallback.tsx    # Accessible 2D SVG fallback
│   ├── landing/
│   │   ├── Hero.tsx            # Headline, 3D visualizer, and AnalysisInput
│   │   ├── AnalysisInput.tsx   # Dual ingestion (GitHub URL or ZIP upload)
│   │   ├── PipelineShowcase.tsx# 6-pillar engine details
│   │   └── SecuritySection.tsx # Cybersecurity highlights
│   ├── analysis/
│   │   └── ScanningProgress.tsx# Step-based scanning progress visualizer
│   ├── report/
│   │   ├── ReportHeader.tsx    # Project metadata & JSON export & Re-Scan trigger
│   │   ├── OverallScoreCard.tsx# Score, rating band & severity summary
│   │   ├── PillarGrid.tsx      # 6 Category health cards
│   │   └── ScannerList.tsx     # Executed scanners status
│   ├── security/          # (Phase 6) Dedicated Cybersecurity Command Center
│   │   ├── SecurityCommandCenter.tsx     # Root security dashboard container
│   │   ├── SecurityPosture.tsx           # Authoritative Security pillar score card
│   │   ├── SecuritySeverityBreakdown.tsx # Critical, High, Med, Low triage breakdown
│   │   ├── SecurityCategoryBreakdown.tsx # Secrets, Injection, Dependencies subcategories
│   │   ├── SecurityScannerCoverage.tsx   # Scanner coverage & status telemetry
│   │   └── SecurityFindingsExplorer.tsx  # Security-focused search & triage list
│   ├── progress/          # (Phase 7) Re-Scan & Progress Tracking
│   │   ├── ProgressDashboard.tsx         # Main progress dashboard container
│   │   ├── ScoreComparison.tsx           # Overall score progression & rating band transitions
│   │   ├── PillarComparison.tsx          # 6-Pillar before/after scores & deltas
│   │   ├── FindingChanges.tsx            # Fixed, new, remaining, and changed finding explorer
│   │   └── RescanModal.tsx               # Re-scan ingestion modal (URL / ZIP)
│   ├── findings/
│   │   ├── FindingsExplorer.tsx# Filterable & searchable general findings table
│   │   └── FindingDetail.tsx   # Evidence, AI Why it matters, and fix diffs
│   ├── code-viewer/
│   │   └── CodeViewer.tsx      # Monaco editor read-only code viewer
│   └── charts/
│       └── PillarChart.tsx     # Recharts 6-pillar posture radar
├── hooks/
│   └── useAnalysis.ts     # Analysis state & lifecycle management
├── lib/
│   ├── api/client.ts      # Typed backend API client (/api/v1/analyze)
│   ├── constants.ts       # Pillars and scan step constants
│   └── utils.ts           # Semantic colors, rating bands, formatters
└── types/
    └── report.ts          # Backend AnalysisReport TypeScript contract
```

## Running Development Server

```bash
cd frontend
npm run dev
```

## Building for Production

```bash
cd frontend
npm run build
```

## Running Tests

```bash
cd frontend
npm test
```

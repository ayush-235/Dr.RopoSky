"""Supabase PostgreSQL Client & Persistence Adapter for Dr.RopoSky."""

import logging
import os
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
import httpx
from app.config import backend_config

logger = logging.getLogger(__name__)


class SupabaseStore:
    """
    Manages persistence to Supabase PostgreSQL with transparent local fallback.
    When SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY are available, uses Supabase REST API.
    Otherwise, uses an in-memory persistence store.
    """

    def __init__(
        self,
        supabase_url: Optional[str] = None,
        service_role_key: Optional[str] = None,
    ):
        if supabase_url is not None:
            raw_url = supabase_url
        else:
            raw_url = backend_config.SUPABASE_URL or os.environ.get("SUPABASE_URL") or ""

        if service_role_key is not None:
            raw_key = service_role_key
        else:
            raw_key = backend_config.SUPABASE_SERVICE_ROLE_KEY or os.environ.get("SUPABASE_SERVICE_ROLE_KEY") or ""

        self.supabase_url = raw_url.strip() if isinstance(raw_url, str) and raw_url.strip() else None
        self.service_role_key = raw_key.strip() if isinstance(raw_key, str) and raw_key.strip() else None

        self._is_live = bool(self.supabase_url and self.service_role_key)

        # In-memory stores for testing or when Supabase is not configured
        self._memory_projects: Dict[str, Dict[str, Any]] = {}
        self._memory_scans: Dict[str, Dict[str, Any]] = {}
        self._memory_findings: Dict[str, List[Dict[str, Any]]] = {}
        self._memory_comparisons: Dict[str, Dict[str, Any]] = {}

        if self._is_live:
            logger.info("Persistence: Supabase")
        else:
            logger.info("Persistence: Local Fallback")

    @property
    def is_live(self) -> bool:
        return self._is_live

    def _get_headers(self) -> Dict[str, str]:
        return {
            "apikey": self.service_role_key or "",
            "Authorization": f"Bearer {self.service_role_key or ''}",
            "Content-Type": "application/json",
            "Prefer": "return=representation",
        }

    # =========================================================================
    # PROJECTS
    # =========================================================================

    def get_or_create_project(
        self, name: str, source_type: str, source_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """Finds existing project by source_url/name, or creates a new project."""
        now_iso = datetime.now(timezone.utc).isoformat()

        if self._is_live:
            try:
                with httpx.Client(timeout=10.0) as client:
                    # Query existing
                    if source_url:
                        res = client.get(
                            f"{self.supabase_url}/rest/v1/projects",
                            headers=self._get_headers(),
                            params={"source_url": f"eq.{source_url}", "select": "*"},
                        )
                    else:
                        res = client.get(
                            f"{self.supabase_url}/rest/v1/projects",
                            headers=self._get_headers(),
                            params={"name": f"eq.{name}", "source_type": f"eq.{source_type}", "select": "*"},
                        )

                    if res.status_code == 200 and res.json():
                        existing = res.json()[0]
                        # Update timestamp
                        client.patch(
                            f"{self.supabase_url}/rest/v1/projects?id=eq.{existing['id']}",
                            headers=self._get_headers(),
                            json={"updated_at": now_iso, "name": name},
                        )
                        return existing

                    # Insert new project
                    new_proj = {
                        "id": str(uuid.uuid4()),
                        "name": name,
                        "source_type": source_type,
                        "source_url": source_url,
                        "created_at": now_iso,
                        "updated_at": now_iso,
                    }
                    create_res = client.post(
                        f"{self.supabase_url}/rest/v1/projects",
                        headers=self._get_headers(),
                        json=new_proj,
                    )
                    if create_res.status_code in (200, 201):
                        return create_res.json()[0] if create_res.json() else new_proj
            except Exception as e:
                logger.warning("Supabase live project query error: %s — falling back to memory", e)

        # In-Memory Fallback
        if source_url:
            for p in self._memory_projects.values():
                if p.get("source_url") == source_url:
                    p["updated_at"] = now_iso
                    p["name"] = name
                    return p
        else:
            for p in self._memory_projects.values():
                if p["name"] == name and p["source_type"] == source_type:
                    p["updated_at"] = now_iso
                    return p

        proj_id = str(uuid.uuid4())
        new_p = {
            "id": proj_id,
            "name": name,
            "source_type": source_type,
            "source_url": source_url,
            "created_at": now_iso,
            "updated_at": now_iso,
        }
        self._memory_projects[proj_id] = new_p
        return new_p

    def get_project(self, project_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves a project by UUID."""
        if self._is_live:
            try:
                with httpx.Client(timeout=10.0) as client:
                    res = client.get(
                        f"{self.supabase_url}/rest/v1/projects",
                        headers=self._get_headers(),
                        params={"id": f"eq.{project_id}", "select": "*"},
                    )
                    if res.status_code == 200 and res.json():
                        return res.json()[0]
            except Exception as e:
                logger.warning("Supabase live get_project error: %s", e)

        return self._memory_projects.get(project_id)

    # =========================================================================
    # SCANS
    # =========================================================================

    def create_scan(
        self,
        project_id: str,
        report_data: Dict[str, Any],
        status: str = "completed",
    ) -> Dict[str, Any]:
        """Persists an analysis scan record and its findings."""
        scan_id = str(uuid.uuid4())
        now_iso = datetime.now(timezone.utc).isoformat()

        score = report_data.get("score") or {}
        summary = report_data.get("summary") or {}
        findings_list = report_data.get("findings") or []

        scan_record = {
            "id": scan_id,
            "project_id": project_id,
            "status": status,
            "overall_score": int(score.get("overall", 0)),
            "security_score": int(score.get("security", 0)),
            "reliability_score": int(score.get("reliability", 0)),
            "quality_score": int(score.get("code_quality", 0)),
            "performance_score": int(score.get("performance", 0)),
            "architecture_score": int(score.get("architecture", 0)),
            "completeness_score": int(score.get("completeness", 0)),
            "total_findings": len(findings_list),
            "critical_count": int(summary.get("critical", 0)),
            "high_count": int(summary.get("high", 0)),
            "medium_count": int(summary.get("medium", 0)),
            "low_count": int(summary.get("low", 0)),
            "info_count": int(summary.get("info", 0)),
            "raw_report": report_data,
            "created_at": now_iso,
        }

        # Format findings for persistence
        findings_to_insert = []
        for f in findings_list:
            enrichment = f.get("enrichment") or {}
            conf = enrichment.get("confidence_score")
            if conf is None and isinstance(enrichment.get("confidence"), (int, float)):
                conf = float(enrichment.get("confidence"))

            findings_to_insert.append({
                "id": str(uuid.uuid4()),
                "scan_id": scan_id,
                "fingerprint": f.get("fingerprint") or f.get("id") or str(uuid.uuid4()),
                "title": f.get("title", "Untitled Finding"),
                "category": f.get("category", "quality"),
                "severity": f.get("severity", "info"),
                "file_path": f.get("file_path") or f.get("file") or "",
                "line_number": f.get("line_number") or f.get("line"),
                "why_it_matters": enrichment.get("why_it_matters") or enrichment.get("explanation"),
                "fix_steps": enrichment.get("fix_steps") or [],
                "code_before": enrichment.get("code_before"),
                "code_after": enrichment.get("code_after"),
                "confidence": conf,
                "created_at": now_iso,
            })

        if self._is_live:
            try:
                with httpx.Client(timeout=15.0) as client:
                    # Insert scan
                    client.post(
                        f"{self.supabase_url}/rest/v1/scans",
                        headers=self._get_headers(),
                        json=scan_record,
                    )
                    # Insert findings batch if any
                    if findings_to_insert:
                        client.post(
                            f"{self.supabase_url}/rest/v1/findings",
                            headers=self._get_headers(),
                            json=findings_to_insert,
                        )
            except Exception as e:
                logger.warning("Supabase live create_scan error: %s — saving to memory", e)

        # Store in memory
        self._memory_scans[scan_id] = scan_record
        self._memory_findings[scan_id] = findings_to_insert

        return scan_record

    def get_scan(self, scan_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves a single scan by UUID."""
        if self._is_live:
            try:
                with httpx.Client(timeout=10.0) as client:
                    res = client.get(
                        f"{self.supabase_url}/rest/v1/scans",
                        headers=self._get_headers(),
                        params={"id": f"eq.{scan_id}", "select": "*"},
                    )
                    if res.status_code == 200 and res.json():
                        return res.json()[0]
            except Exception as e:
                logger.warning("Supabase live get_scan error: %s", e)

        return self._memory_scans.get(scan_id)

    def get_project_scans(self, project_id: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Retrieves scan history for a project ordered by creation time descending."""
        if self._is_live:
            try:
                with httpx.Client(timeout=10.0) as client:
                    res = client.get(
                        f"{self.supabase_url}/rest/v1/scans",
                        headers=self._get_headers(),
                        params={
                            "project_id": f"eq.{project_id}",
                            "status": "eq.completed",
                            "order": "created_at.desc",
                            "limit": str(limit),
                            "select": "id,project_id,status,overall_score,security_score,reliability_score,quality_score,performance_score,architecture_score,completeness_score,total_findings,critical_count,high_count,medium_count,low_count,info_count,created_at",
                        },
                    )
                    if res.status_code == 200 and res.json():
                        return res.json()
            except Exception as e:
                logger.warning("Supabase live get_project_scans error: %s", e)

        # Memory store query
        scans = [
            s for s in self._memory_scans.values()
            if s.get("project_id") == project_id and s.get("status") == "completed"
        ]
        scans.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        return scans[:limit]

    def get_latest_completed_scan(self, project_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves the most recent completed scan for a project."""
        scans = self.get_project_scans(project_id, limit=1)
        if not scans:
            return None
        return self.get_scan(scans[0]["id"])

    def get_scan_findings(self, scan_id: str) -> List[Dict[str, Any]]:
        """Retrieves findings associated with a scan."""
        if self._is_live:
            try:
                with httpx.Client(timeout=10.0) as client:
                    res = client.get(
                        f"{self.supabase_url}/rest/v1/findings",
                        headers=self._get_headers(),
                        params={"scan_id": f"eq.{scan_id}", "select": "*"},
                    )
                    if res.status_code == 200 and res.json():
                        return res.json()
            except Exception as e:
                logger.warning("Supabase live get_scan_findings error: %s", e)

        return self._memory_findings.get(scan_id, [])

    # =========================================================================
    # SCAN COMPARISONS
    # =========================================================================

    def create_scan_comparison(
        self,
        project_id: str,
        previous_scan_id: str,
        current_scan_id: str,
        comparison_dict: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Persists a scan comparison delta between two scans."""
        comp_id = str(uuid.uuid4())
        now_iso = datetime.now(timezone.utc).isoformat()

        summary = comparison_dict.get("summary") or {}
        overall = comparison_dict.get("overall") or {}
        pillars = comparison_dict.get("pillars") or {}

        record = {
            "id": comp_id,
            "project_id": project_id,
            "previous_scan_id": previous_scan_id,
            "current_scan_id": current_scan_id,
            "score_delta": int(overall.get("delta", 0)),
            "security_delta": int(pillars.get("security", {}).get("delta", 0)),
            "reliability_delta": int(pillars.get("reliability", {}).get("delta", 0)),
            "quality_delta": int(pillars.get("code_quality", {}).get("delta", 0)),
            "performance_delta": int(pillars.get("performance", {}).get("delta", 0)),
            "architecture_delta": int(pillars.get("architecture", {}).get("delta", 0)),
            "completeness_delta": int(pillars.get("completeness", {}).get("delta", 0)),
            "fixed_count": int(summary.get("fixed_count", 0)),
            "new_count": int(summary.get("new_count", 0)),
            "remaining_count": int(summary.get("remaining_count", 0)),
            "changed_count": int(summary.get("changed_count", 0)),
            "raw_comparison": comparison_dict,
            "created_at": now_iso,
        }

        if self._is_live:
            try:
                with httpx.Client(timeout=10.0) as client:
                    client.post(
                        f"{self.supabase_url}/rest/v1/scan_comparisons",
                        headers=self._get_headers(),
                        json=record,
                    )
            except Exception as e:
                logger.warning("Supabase live create_scan_comparison error: %s", e)

        self._memory_comparisons[comp_id] = record
        return record

    def get_scan_comparison(self, comparison_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves a comparison by its UUID."""
        if self._is_live:
            try:
                with httpx.Client(timeout=10.0) as client:
                    res = client.get(
                        f"{self.supabase_url}/rest/v1/scan_comparisons",
                        headers=self._get_headers(),
                        params={"id": f"eq.{comparison_id}", "select": "*"},
                    )
                    if res.status_code == 200 and res.json():
                        return res.json()[0]
            except Exception as e:
                logger.warning("Supabase live get_scan_comparison error: %s", e)

        return self._memory_comparisons.get(comparison_id)

    def get_comparison_by_current_scan(self, scan_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves the comparison record where current_scan_id matches scan_id."""
        if self._is_live:
            try:
                with httpx.Client(timeout=10.0) as client:
                    res = client.get(
                        f"{self.supabase_url}/rest/v1/scan_comparisons",
                        headers=self._get_headers(),
                        params={"current_scan_id": f"eq.{scan_id}", "select": "*"},
                    )
                    if res.status_code == 200 and res.json():
                        return res.json()[0]
            except Exception as e:
                logger.warning("Supabase live get_comparison_by_current_scan error: %s", e)

        for comp in self._memory_comparisons.values():
            if comp.get("current_scan_id") == scan_id:
                return comp
        return None

    def clear_memory(self):
        """Helper for test cleanup."""
        self._memory_projects.clear()
        self._memory_scans.clear()
        self._memory_findings.clear()
        self._memory_comparisons.clear()


# Global Singleton Instance
supabase_store = SupabaseStore()

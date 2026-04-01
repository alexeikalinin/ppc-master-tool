from fastapi import APIRouter, HTTPException
from fastapi.responses import Response

from backend import db
from backend.models import AnalyzeResponse, ReportOut

router = APIRouter()


@router.get("", response_model=list[ReportOut])
async def list_reports():
    """List all saved reports (Phase 2: no auth filter)."""
    rows = await db.list_reports()
    return [ReportOut(**r) for r in rows]


@router.get("/{report_id}", response_model=AnalyzeResponse)
async def get_report(report_id: str):
    """Return full report JSON by ID."""
    row = await db.get_report(report_id)
    if not row:
        raise HTTPException(status_code=404, detail="Report not found")
    return AnalyzeResponse(**row["json_data"])


@router.get("/{report_id}/pdf")
async def get_report_pdf(report_id: str):
    """Stream PDF for the given report."""
    row = await db.get_report(report_id)
    if not row:
        raise HTTPException(status_code=404, detail="Report not found")
    from backend.services.pdf import generate_pdf
    report = AnalyzeResponse(**row["json_data"])
    pdf_bytes = await generate_pdf(report)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="report-{report_id[:8]}.pdf"'},
    )

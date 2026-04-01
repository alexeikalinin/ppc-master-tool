"""
PDF generation endpoint.
POST /pdf?variant=1  or  ?variant=3
Body: full AnalyzeResponse JSON
Returns: application/pdf
"""

from fastapi import APIRouter, Query
from fastapi.responses import Response

from backend.models import AnalyzeResponse
from backend.services.pdf_export import generate_pdf

router = APIRouter()


@router.post("")
async def create_pdf(report: AnalyzeResponse, variant: int = Query(default=1, ge=1, le=3)):
    pdf_bytes = generate_pdf(report, variant=variant)
    filename = f"kp-{report.site.niche}-v{variant}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )

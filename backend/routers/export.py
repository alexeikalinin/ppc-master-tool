"""
Export endpoint: keywords by semantic groups → CSV / XLSX.
"""

import csv
import io

from fastapi import APIRouter, Query
from fastapi.responses import Response

from backend.models import AnalyzeResponse

router = APIRouter()


@router.post("/keywords")
async def export_keywords(
    report: AnalyzeResponse,
    fmt: str = Query(default="csv", regex="^(csv|tsv)$"),
):
    """
    Принимает полный отчёт, возвращает ключевые слова сгруппированные по
    семантическим группам в формате CSV/TSV для импорта в Яндекс.Директ или Excel.

    Колонки: Группа | Ключевое слово | Частота | CPC (руб.) | Платформа | Минус-слова группы
    """
    separator = "," if fmt == "csv" else "\t"
    output = io.StringIO()
    writer = csv.writer(output, delimiter=separator, quoting=csv.QUOTE_MINIMAL)

    # Заголовок
    writer.writerow([
        "Семантическая группа",
        "Ключевое слово",
        "Частота (мес.)",
        "CPC (руб.)",
        "Платформа",
        "Минус-слова группы",
    ])

    groups = report.groups or []

    for group in groups:
        minus_words_str = ", ".join(group.minus_words) if group.minus_words else ""
        keywords = group.keywords or []

        # Сортируем по частоте убыванию
        sorted_kws = sorted(keywords, key=lambda k: -k.frequency)

        for kw in sorted_kws:
            writer.writerow([
                group.name,
                kw.text,
                kw.frequency,
                f"{kw.cpc:.0f}",
                kw.platform,
                minus_words_str,
            ])

    csv_content = output.getvalue().encode("utf-8-sig")  # utf-8-sig для Excel

    media_type = "text/csv" if fmt == "csv" else "text/tab-separated-values"
    filename = f"keywords_{fmt}.{fmt}"

    return Response(
        content=csv_content,
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )

from __future__ import annotations

from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from china_cars.db import connect


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "reports" / "analysis_report.pdf"


def fmt_int(value: float) -> str:
    return f"{int(value):,}".replace(",", ".")


def fmt_pct(value: float) -> str:
    return f"{value * 100:.2f}%".replace(".", ",")


def fmt_usd(value: float) -> str:
    return f"US$ {int(value):,}".replace(",", ".")


def table_from_rows(headers: list[str], rows: list[list[object]], col_widths=None) -> Table:
    table = Table([headers, *rows], repeatRows=1, colWidths=col_widths)
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1f2937")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#cbd5e1")),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ]
        )
    )
    return table


def main() -> None:
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    styles = getSampleStyleSheet()
    story = []

    story.append(Paragraph("Relatorio de Analise - China Cars", styles["Title"]))
    story.append(Paragraph("Data de execucao: 2026-07-07", styles["Normal"]))
    story.append(Spacer(1, 0.4 * cm))

    story.append(Paragraph("Escopo", styles["Heading1"]))
    story.append(
        Paragraph(
            "Analise de emplacamentos de marcas chinesas nos dados ANFAVEA e "
            "importacoes originarias da China no Comex Stat/MDIC para os codigos "
            "8702, 8703, 8704, 8706, 8707, 8708 e 87011.",
            styles["BodyText"],
        )
    )
    story.append(Spacer(1, 0.3 * cm))

    with connect(read_only=True) as con:
        anf_year = con.execute(
            """
            select ano,
                   sum(emplacamentos) chineses,
                   sum(emplacamentos_total_anfavea) total_anfavea,
                   sum(emplacamentos)*1.0/sum(emplacamentos_total_anfavea) participacao
            from gold_anfavea_chinese_registrations_monthly
            group by ano
            order by ano
            """
        ).fetchall()
        comex_year = con.execute(
            """
            select ano,
                   sum(valor_fob_usd) fob,
                   sum(kg_liquido) kg,
                   sum(quantidade_estatistica) qtd
            from gold_comex_china_automotive_monthly
            group by ano
            order by ano
            """
        ).fetchall()
        prefix_2026 = con.execute(
            """
            select ncm_prefixo_consulta, sum(valor_fob_usd) fob
            from gold_comex_china_automotive_by_prefix_monthly
            where ano = 2026
            group by 1
            order by fob desc
            """
        ).fetchall()

    story.append(Paragraph("ANFAVEA", styles["Heading1"]))
    story.append(
        table_from_rows(
            ["Ano", "Emplacamentos chineses", "Total ANFAVEA", "Participacao"],
            [
                [
                    "2026 jan-mai" if row[0] == 2026 else str(row[0]),
                    fmt_int(row[1]),
                    fmt_int(row[2]),
                    fmt_pct(row[3]),
                ]
                for row in anf_year
            ],
        )
    )
    story.append(Spacer(1, 0.4 * cm))

    story.append(Paragraph("Comex Stat/MDIC", styles["Heading1"]))
    story.append(
        table_from_rows(
            ["Ano", "Valor FOB", "Kg liquido", "Quantidade estatistica"],
            [
                [
                    "2026 jan-jun" if row[0] == 2026 else str(row[0]),
                    fmt_usd(row[1]),
                    fmt_int(row[2]),
                    fmt_int(row[3]),
                ]
                for row in comex_year
            ],
        )
    )
    story.append(Spacer(1, 0.4 * cm))

    story.append(Paragraph("Principais prefixos NCM em 2026", styles["Heading1"]))
    story.append(
        table_from_rows(
            ["Prefixo NCM", "Valor FOB"],
            [[row[0], fmt_usd(row[1])] for row in prefix_2026],
        )
    )
    story.append(Spacer(1, 0.4 * cm))

    story.append(Paragraph("Limitacoes", styles["Heading1"]))
    for text in [
        "A ANFAVEA nao disponibiliza estatisticas detalhadas por modelo; o recorte usa marca/empresa.",
        "O Comex foi tratado como importacoes originarias da China.",
        "O codigo 87011 foi tratado como prefixo de NCM e permanece pendente de validacao metodologica.",
        "Os dados brutos foram versionados via Git LFS quando disponivel e registrados no manifesto SHA256.",
    ]:
        story.append(Paragraph(f"- {text}", styles["BodyText"]))

    doc = SimpleDocTemplate(
        str(OUTPUT),
        pagesize=A4,
        leftMargin=1.5 * cm,
        rightMargin=1.5 * cm,
        topMargin=1.5 * cm,
        bottomMargin=1.5 * cm,
    )
    doc.build(story)
    print(OUTPUT)


if __name__ == "__main__":
    main()


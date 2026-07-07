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
                   sum(emplacamentos_chinesas_min) piso,
                   sum(emplacamentos) estimativa,
                   sum(emplacamentos_total_anfavea) total_anfavea,
                   sum(emplacamentos_chinesas_min)*1.0/sum(emplacamentos_total_anfavea) part_piso,
                   sum(emplacamentos)*1.0/sum(emplacamentos_total_anfavea) part_estimativa
            from gold_anfavea_chinese_registrations_monthly
            group by ano
            order by ano
            """
        ).fetchall()
        comex_year = con.execute(
            """
            select ano,
                   sum(quantidade_veiculos) veiculos,
                   sum(valor_fob_usd) fob
            from gold_comex_china_automotive_monthly
            group by ano
            order by ano
            """
        ).fetchall()
        comex_h1 = con.execute(
            """
            select ano, sum(quantidade_veiculos) veiculos
            from gold_comex_china_automotive_monthly
            where mes <= 6
            group by ano
            order by ano
            """
        ).fetchall()
        prefix_2026 = con.execute(
            """
            select ncm_prefixo_consulta,
                   sum(quantidade_veiculos) veiculos,
                   sum(valor_fob_usd) fob
            from gold_comex_china_automotive_by_prefix_monthly
            where ano = 2026
            group by 1
            order by veiculos desc
            """
        ).fetchall()
        cpca_latest = con.execute(
            """
            select ano_mes,
                   narrow_passenger_retail,
                   nev_narrow_passenger_retail,
                   nev_passenger_wholesale_estimate,
                   nev_retail_penetration_pct
            from gold_cpca_passenger_market_monthly
            order by ano_mes desc
            limit 5
            """
        ).fetchall()
        caam_summary = con.execute(
            """
            select count(*) as articles, sum(image_count) as images,
                   min(published_date) as min_date, max(published_date) as max_date
            from raw_caam_evidence_catalog
            """
        ).fetchone()

    story.append(Paragraph("ANFAVEA - emplacamentos de marcas chinesas", styles["Heading1"]))
    story.append(
        Paragraph(
            "Serie em banda. <b>Piso</b>: apenas marcas chinesas confirmadas nominalmente "
            "(associadas a Anfavea e, a partir de 2026, o detalhe por marca das \"Outras "
            "empresas\": BYD, GWM, Omoda, GAC etc.). <b>Estimativa</b>: piso mais a linha "
            "agregada \"Outras empresas\" nos meses sem detalhe por marca - um teto, pois "
            "essa linha inclui marcas nao chinesas (Kia, Porsche, Volvo). Nos meses de 2026 "
            "com detalhe, ~92% de \"Outras empresas\" e chinesa.",
            styles["BodyText"],
        )
    )
    story.append(
        table_from_rows(
            ["Ano", "Piso (marcas confirmadas)", "Estimativa (com Outras)", "Total ANFAVEA", "Part. piso", "Part. estimativa"],
            [
                [
                    "2026 jan-jun" if row[0] == 2026 else str(row[0]),
                    fmt_int(row[1]),
                    fmt_int(row[2]),
                    fmt_int(row[3]),
                    fmt_pct(row[4]),
                    fmt_pct(row[5]),
                ]
                for row in anf_year
            ],
        )
    )
    story.append(Spacer(1, 0.4 * cm))

    story.append(Paragraph("Comex Stat/MDIC - importacoes originarias da China", styles["Heading1"]))
    story.append(
        Paragraph(
            "Metrica principal: <b>quantidade de veiculos</b> (unidades) dos NCMs de veiculos "
            "completos (8702, 8703, 8704, 8706, 87011), medidos em numero de unidades. O valor "
            "FOB e apresentado como referencia secundaria. Autopecas (8708) e carrocerias (8707) "
            "nao entram na contagem de veiculos por serem medidas majoritariamente em quilogramas.",
            styles["BodyText"],
        )
    )
    story.append(
        table_from_rows(
            ["Ano", "Veiculos (unidades)", "Valor FOB (referencia)"],
            [
                [
                    "2026 jan-jun" if row[0] == 2026 else str(row[0]),
                    fmt_int(row[1]),
                    fmt_usd(row[2]),
                ]
                for row in comex_year
            ],
        )
    )
    story.append(Spacer(1, 0.2 * cm))
    story.append(
        Paragraph(
            "Acumulado janeiro-junho, em veiculos: "
            + "; ".join(f"{row[0]} = {fmt_int(row[1])}" for row in comex_h1)
            + ".",
            styles["BodyText"],
        )
    )
    story.append(Spacer(1, 0.4 * cm))

    story.append(Paragraph("CPCA", styles["Heading1"]))
    story.append(
        Paragraph(
            "Metricas textuais extraidas de artigos mensais da CPCA para varejo de passageiros, "
            "NEV e estimativas de atacado quando publicadas.",
            styles["BodyText"],
        )
    )
    story.append(
        table_from_rows(
            ["Mes", "Varejo passageiros", "Varejo NEV", "Atacado NEV estimado", "Penetracao NEV"],
            [
                [
                    row[0],
                    fmt_int(row[1]) if row[1] is not None else "-",
                    fmt_int(row[2]) if row[2] is not None else "-",
                    fmt_int(row[3]) if row[3] is not None else "-",
                    f"{row[4]:.1f}%" if row[4] is not None else "-",
                ]
                for row in reversed(cpca_latest)
            ],
        )
    )
    story.append(Spacer(1, 0.4 * cm))

    story.append(Paragraph("CAAM", styles["Heading1"]))
    story.append(
        Paragraph(
            f"Foram catalogados {int(caam_summary[0] or 0)} comunicados CAAM, "
            f"com {int(caam_summary[1] or 0)} imagens brutas, entre "
            f"{caam_summary[2]} e {caam_summary[3]}. Os numeros em imagens ficam "
            "preservados para OCR ou transcricao controlada.",
            styles["BodyText"],
        )
    )
    story.append(Spacer(1, 0.4 * cm))

    story.append(Paragraph("Principais prefixos NCM em 2026 (jan-jun)", styles["Heading1"]))
    story.append(
        table_from_rows(
            ["Prefixo NCM", "Veiculos (unidades)", "Valor FOB (referencia)"],
            [[row[0], fmt_int(row[1]), fmt_usd(row[2])] for row in prefix_2026],
        )
    )
    story.append(Spacer(1, 0.4 * cm))

    story.append(Paragraph("Limitacoes", styles["Heading1"]))
    for text in [
        "A ANFAVEA nao disponibiliza estatisticas detalhadas por modelo; o recorte usa marca/empresa.",
        "Para 2021-2025, marcas chinesas como BYD e GWM aparecem apenas na linha agregada "
        "\"Outras empresas\" do workbook anual (sem detalhe por marca), o que gera a banda "
        "piso-estimativa. O detalhe por marca so esta disponivel nos arquivos de importados/"
        "nacionais por marca, publicados para 2026.",
        "O Comex foi tratado como importacoes originarias da China; a quantidade de veiculos "
        "considera apenas NCMs de veiculos completos medidos em numero de unidades.",
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

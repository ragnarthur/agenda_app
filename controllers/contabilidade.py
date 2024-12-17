from flask import Blueprint, render_template, make_response, send_file, flash
from io import BytesIO
from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from weasyprint import HTML
from openpyxl import Workbook
from openpyxl.drawing.image import Image
import matplotlib.pyplot as plt
from datetime import datetime
from collections import defaultdict
from models import db, Contabilidade
from flask import request
import locale

contabilidade_bp = Blueprint('contabilidade', __name__, url_prefix='/contabilidade')

@contabilidade_bp.route('/')
def contabilidade():
    contabilidade_data = Contabilidade.query.order_by(Contabilidade.mes_ano.desc()).all()
    contabilidade_by_date = defaultdict(list)
    for cont in contabilidade_data:
        if cont.evento and cont.evento.data:
            try:
                event_date = datetime.strptime(cont.evento.data, "%Y-%m-%d") if isinstance(cont.evento.data, str) else cont.evento.data
                date_key = event_date.strftime("%B/%Y").capitalize()
            except ValueError:
                date_key = "Data Inválida"
        else:
            date_key = "Sem Data"
        contabilidade_by_date[date_key].append(cont)

    for key in contabilidade_by_date:
        contabilidade_by_date[key].sort(
            key=lambda x: datetime.strptime(x.data_realizacao, "%Y-%m-%d") if (x.data_realizacao and isinstance(x.data_realizacao, str)) else (x.data_realizacao or datetime.min)
        )

    return render_template('contabilidade.html', contabilidade_by_date=contabilidade_by_date)

@contabilidade_bp.route('/exportar/csv')
def export_contabilidade_csv():
    contabilidade_data = Contabilidade.query.all()
    output = []
    output.append(["Evento", "Data do Evento", "Data de Realização", "Valor Bruto (R$)",
                   "Pagamentos de Músicos (R$)", "Locação de Som (R$)", "Outros Custos (R$)", "Valor Líquido (R$)", "Status"])

    for cont in contabilidade_data:
        if cont.evento:
            data_evento = (
                datetime.strptime(cont.evento.data, "%Y-%m-%d") if isinstance(cont.evento.data, str) else cont.evento.data
            )
            titulo_evento = cont.evento.titulo
        else:
            data_evento = None
            titulo_evento = "Evento Removido"

        data_realizacao = (
            datetime.strptime(cont.data_realizacao, "%Y-%m-%d") if (cont.realizado and isinstance(cont.data_realizacao, str)) else cont.data_realizacao
        )

        output.append([
            titulo_evento,
            data_evento.strftime("%d/%m/%Y") if data_evento else "-",
            data_realizacao.strftime("%d/%m/%Y") if (cont.realizado and data_realizacao) else "Não Realizado",
            f"{cont.valor_bruto:.2f}",
            f"{cont.pagamento_musicos:.2f}",
            f"{cont.locacao_som:.2f}",
            f"{cont.outros_custos:.2f}",
            f"{cont.valor_liquido:.2f}",
            "Finalizado" if cont.realizado else "Pendente"
        ])

    si = make_response("\n".join([",".join(row) for row in output]))
    si.headers["Content-Disposition"] = "attachment; filename=contabilidade.csv"
    si.headers["Content-type"] = "text/csv"
    return si

@contabilidade_bp.route('/exportar/pdf')
def export_contabilidade_pdf():
    buffer = BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=landscape(letter),
        topMargin=20,
        bottomMargin=20,
        leftMargin=20,
        rightMargin=20,
    )
    doc.title = "Relatório de Contabilidade"

    styles = getSampleStyleSheet()
    title_style = styles["Title"]
    title_style.alignment = 1

    title = Paragraph("Relatório de Contabilidade", title_style)

    contabilidade_data = Contabilidade.query.all()

    data = [
        [
            "Evento",
            "Data do Evento",
            "Data de Realização",
            "Valor Bruto (R$)",
            "Pagamentos (R$)",
            "Locação (R$)",
            "Outros Custos (R$)",
            "Valor Líquido (R$)",
            "Status",
        ]
    ]

    for cont in contabilidade_data:
        evento = cont.evento_titulo or "Evento Removido"
        data_evento = (
            datetime.strptime(cont.evento.data, "%Y-%m-%d").strftime("%d/%m/%Y")
            if cont.evento and isinstance(cont.evento.data, str)
            else (cont.evento.data.strftime("%d/%m/%Y") if cont.evento and cont.evento.data else "-")
        )
        data_realizacao = (
            datetime.strptime(cont.data_realizacao, "%Y-%m-%d").strftime("%d/%m/%Y")
            if cont.realizado and isinstance(cont.data_realizacao, str)
            else (cont.data_realizacao.strftime("%d/%m/%Y") if (cont.realizado and cont.data_realizacao) else "Não Realizado")
        )

        data.append([
            evento,
            data_evento,
            data_realizacao,
            f"{cont.valor_bruto:.2f}",
            f"{cont.pagamento_musicos:.2f}",
            f"{cont.locacao_som:.2f}",
            f"{cont.outros_custos:.2f}",
            f"{cont.valor_liquido:.2f}",
            "Finalizado" if cont.realizado else "Pendente",
        ])

    table = Table(data, repeatRows=1)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.black),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
        ("BACKGROUND", (0, 1), (-1, -1), colors.whitesmoke),
        ("GRID", (0, 0), (-1, -1), 1, colors.black),
    ]))

    doc.build([title, table])

    buffer.seek(0)
    response = make_response(buffer.read())
    response.headers["Content-Disposition"] = "attachment; filename=relatorio_contabilidade.pdf"
    response.headers["Content-Type"] = "application/pdf"
    return response

@contabilidade_bp.route('/final')
def contabilidade_final():
    contabilidade = Contabilidade.query.all()

    total_bruto = sum(cont.valor_bruto for cont in contabilidade)
    total_pagamento_musicos = sum(cont.pagamento_musicos for cont in contabilidade)
    total_locacao_som = sum(cont.locacao_som for cont in contabilidade)
    total_outros_custos = sum(cont.outros_custos for cont in contabilidade)
    total_liquido = total_bruto - (total_pagamento_musicos + total_locacao_som + total_outros_custos)

    chart_data = {
        "labels": [
            "Receita Bruta",
            "Pagamentos de Músicos",
            "Locação de Som",
            "Outros Custos",
            "Receita Líquida"
        ],
        "datasets": [{
            "label": "Resumo Financeiro",
            "data": [
                total_bruto,
                total_pagamento_musicos,
                total_locacao_som,
                total_outros_custos,
                total_liquido
            ],
            "backgroundColor": [
                "#4e73df",
                "#e74a3b",
                "#f6c23e",
                "#1cc88a",
                "#36b9cc"
            ]
        }]
    }

    total_eventos = len(contabilidade)
    media_receita_liquida = total_liquido / total_eventos if total_eventos > 0 else 0

    return render_template(
        'contabilidade_final.html',
        total_bruto=total_bruto,
        total_pagamento_musicos=total_pagamento_musicos,
        total_locacao_som=total_locacao_som,
        total_outros_custos=total_outros_custos,
        total_liquido=total_liquido,
        total_eventos=total_eventos,
        media_receita_liquida=media_receita_liquida,
        chart_data=chart_data
    )

@contabilidade_bp.route('/final/exportar/excel')
def export_contabilidade_final_excel():
    contabilidade = Contabilidade.query.all()

    total_bruto = sum(cont.valor_bruto for cont in contabilidade)
    total_pagamento_musicos = sum(cont.pagamento_musicos for cont in contabilidade)
    total_locacao_som = sum(cont.locacao_som for cont in contabilidade)
    total_outros_custos = sum(cont.outros_custos for cont in contabilidade)
    # Corrigindo a linha abaixo:
    total_liquido = total_bruto - (total_pagamento_musicos + total_locacao_som + total_outros_custos)

    from openpyxl import Workbook
    from openpyxl.drawing.image import Image

    wb = Workbook()
    ws = wb.active
    ws.title = "Resumo Financeiro"

    ws.column_dimensions['A'].width = 25
    ws.column_dimensions['B'].width = 15
    ws.column_dimensions['C'].width = 20

    ws.append(["Categoria", "Total (R$)", "Percentual (%)"])

    labels = [
        "Receita Bruta",
        "Pagamentos de Músicos",
        "Locação de Som",
        "Outros Custos",
        "Receita Líquida",
    ]
    data = [
        total_bruto,
        total_pagamento_musicos,
        total_locacao_som,
        total_outros_custos,
        total_liquido,
    ]
    percentuais = [
        100.0,
        (total_pagamento_musicos / total_bruto * 100) if total_bruto > 0 else 0,
        (total_locacao_som / total_bruto * 100) if total_bruto > 0 else 0,
        (total_outros_custos / total_bruto * 100) if total_bruto > 0 else 0,
        (total_liquido / total_bruto * 100) if total_bruto > 0 else 0,
    ]

    import matplotlib.pyplot as plt
    from io import BytesIO
    plt.figure(figsize=(10, 8))
    explode = [0.1 if val == max(data) else 0 for val in data]

    wedges, texts, autotexts = plt.pie(
        data,
        labels=None,
        autopct=lambda p: f'{p:.2f}%' if p > 0 else '',
        startangle=140,
        colors=["#4e73df", "#e74a3b", "#f6c23e", "#1cc88a", "#36b9cc"],
        wedgeprops={"edgecolor": "black"},
        explode=explode
    )

    for i, autotext in enumerate(autotexts):
        autotext.set_text(f"{percentuais[i]:.2f}%")
        autotext.set_color("white")
        autotext.set_fontsize(12)

    plt.legend(
        labels=labels,
        loc='lower right',
        bbox_to_anchor=(1.1, -0.1),
        fontsize=10,
        title="Categorias"
    )
    plt.title("Resumo Financeiro - Contabilidade Final", fontsize=16)
    plt.axis("equal")

    chart_buffer = BytesIO()
    plt.savefig(chart_buffer, format='png', bbox_inches='tight')
    plt.close()
    chart_buffer.seek(0)

    img = Image(chart_buffer)
    img.anchor = "E2"
    ws.add_image(img)

    excel_buffer = BytesIO()
    wb.save(excel_buffer)
    excel_buffer.seek(0)

    return send_file(
        excel_buffer,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        as_attachment=True,
        download_name="contabilidade_final.xlsx"
    )

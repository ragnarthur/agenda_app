from flask import Blueprint, render_template, make_response, send_file, flash, redirect, url_for
from io import BytesIO
from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from openpyxl import Workbook
from openpyxl.drawing.image import Image
from datetime import datetime
from collections import defaultdict
from models import db, Contabilidade
from flask import request
import locale

# Importar o modelo Aluno para integrar às contas
from models import Aluno

contabilidade_bp = Blueprint('contabilidade', __name__, url_prefix='/contabilidade')

@contabilidade_bp.route('/')
def contabilidade():
    contabilidade_data = Contabilidade.query.all()

    # Certificar que os eventos estão sendo carregados corretamente
    contabilidade_by_date = defaultdict(list)
    for cont in contabilidade_data:
        event_title = cont.evento_titulo or (cont.evento.titulo if cont.evento else "Evento Removido")
        date_key = (
            cont.mes_ano.strftime("%B/%Y").capitalize()
            if isinstance(cont.mes_ano, datetime)
            else cont.mes_ano or "Sem Data"
        )
        contabilidade_by_date[date_key].append({
            "titulo": event_title,
            "data_evento": cont.data_evento_original,
            "data_realizacao": cont.data_realizacao,
            "valor_bruto": cont.valor_bruto or 0,
            "pagamento_musicos": cont.pagamento_musicos or 0,
            "locacao_som": cont.locacao_som or 0,
            "outros_custos": cont.outros_custos or 0,
            "valor_liquido": cont.valor_liquido or 0,
            "status": "Finalizado" if cont.realizado else "Pendente",
            "evento_id": cont.evento_id,
        })

    return render_template('contabilidade.html', contabilidade_by_date=contabilidade_by_date)

@contabilidade_bp.route('/final')
def contabilidade_final():
    contabilidade = Contabilidade.query.all()

    total_bruto = sum(cont.valor_bruto or 0 for cont in contabilidade)
    total_pagamento_musicos = sum(cont.pagamento_musicos or 0 for cont in contabilidade)
    total_locacao_som = sum(cont.locacao_som or 0 for cont in contabilidade)
    total_outros_custos = sum(cont.outros_custos or 0 for cont in contabilidade)
    total_liquido = total_bruto - (total_pagamento_musicos + total_locacao_som + total_outros_custos)

    # Integração com Alunos:
    alunos = Aluno.query.all()
    receita_aulas = sum(
        300 if aluno.modalidade == 'semanal' else 100 
        for aluno in alunos
    )

    total_bruto += receita_aulas
    total_liquido += receita_aulas

    total_eventos = len(contabilidade)
    media_receita_liquida = total_liquido / total_eventos if total_eventos > 0 else 0

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
                total_bruto or 0,
                total_pagamento_musicos or 0,
                total_locacao_som or 0,
                total_outros_custos or 0,
                total_liquido or 0
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

@contabilidade_bp.route('/exportar/csv')
def export_contabilidade_csv():
    contabilidade_data = Contabilidade.query.all()
    output = []
    output.append(["Evento", "Data do Evento", "Data de Realização", "Valor Bruto (R$)",
                   "Pagamentos de Músicos (R$)", "Locação de Som (R$)", "Outros Custos (R$)", "Valor Líquido (R$)", "Status"])

    for cont in contabilidade_data:
        titulo_evento = cont.evento_titulo or "Evento Removido"
        data_evento = cont.data_evento_original or "-"
        data_realizacao = cont.data_realizacao or "Não Realizado"

        output.append([
            titulo_evento,
            data_evento,
            data_realizacao,
            f"{cont.valor_bruto or 0:.2f}",
            f"{cont.pagamento_musicos or 0:.2f}",
            f"{cont.locacao_som or 0:.2f}",
            f"{cont.outros_custos or 0:.2f}",
            f"{cont.valor_liquido or 0:.2f}",
            "Finalizado" if cont.realizado else "Pendente"
        ])

    si = make_response("\n".join([",".join(row) for row in output]))
    si.headers["Content-Disposition"] = "attachment; filename=contabilidade.csv"
    si.headers["Content-type"] = "text/csv"
    return si

@contabilidade_bp.route('/final/exportar/excel')
def export_contabilidade_final_excel():
    contabilidade = Contabilidade.query.all()

    total_bruto = sum(cont.valor_bruto or 0 for cont in contabilidade)
    total_pagamento_musicos = sum(cont.pagamento_musicos or 0 for cont in contabilidade)
    total_locacao_som = sum(cont.locacao_som or 0 for cont in contabilidade)
    total_outros_custos = sum(cont.outros_custos or 0 for cont in contabilidade)
    total_liquido = total_bruto - (total_pagamento_musicos + total_locacao_som + total_outros_custos)

    alunos = Aluno.query.all()
    receita_aulas = sum(
        300 if aluno.modalidade == 'semanal' else 100 
        for aluno in alunos
    )

    total_bruto += receita_aulas
    total_liquido += receita_aulas

    wb = Workbook()
    ws = wb.active
    ws.title = "Resumo Financeiro"

    ws.append(["Categoria", "Total (R$)"])
    ws.append(["Receita Bruta", f"{total_bruto:.2f}"])
    ws.append(["Pagamentos de Músicos", f"{total_pagamento_musicos:.2f}"])
    ws.append(["Locação de Som", f"{total_locacao_som:.2f}"])
    ws.append(["Outros Custos", f"{total_outros_custos:.2f}"])
    ws.append(["Receita Líquida", f"{total_liquido:.2f}"])

    excel_buffer = BytesIO()
    wb.save(excel_buffer)
    excel_buffer.seek(0)

    return send_file(
        excel_buffer,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        as_attachment=True,
        download_name="contabilidade_final.xlsx"
    )

@contabilidade_bp.route('/exportar/pdf')
def export_contabilidade_pdf():
    contabilidade_data = Contabilidade.query.all()
    buffer = BytesIO()

    # Configurar o documento
    doc = SimpleDocTemplate(
        buffer,
        pagesize=landscape(letter),
        topMargin=20,
        bottomMargin=20,
        leftMargin=20,
        rightMargin=20,
    )
    doc.title = "Relatório de Contabilidade"

    # Estilos
    styles = getSampleStyleSheet()
    title_style = styles["Title"]
    title_style.alignment = 1

    title = Paragraph("Relatório de Contabilidade", title_style)

    # Dados da tabela
    data = [
        ["Evento", "Data do Evento", "Data de Realização", "Valor Bruto (R$)", 
         "Pagamentos de Músicos (R$)", "Locação de Som (R$)", 
         "Outros Custos (R$)", "Valor Líquido (R$)", "Status"]
    ]

    for cont in contabilidade_data:
        evento = cont.evento.titulo if cont.evento else "Evento Removido"
        data_evento = (
            cont.data_evento_original.strftime("%d/%m/%Y")
            if cont.data_evento_original else "-"
        )
        data_realizacao = (
            cont.data_realizacao.strftime("%d/%m/%Y")
            if cont.realizado and cont.data_realizacao else "Não Realizado"
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
            "Finalizado" if cont.realizado else "Pendente"
        ])

    # Configurar tabela
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

    # Gerar documento
    doc.build([title, table])

    # Retornar como resposta
    buffer.seek(0)
    response = make_response(buffer.read())
    response.headers["Content-Disposition"] = "attachment; filename=relatorio_contabilidade.pdf"
    response.headers["Content-Type"] = "application/pdf"
    return response

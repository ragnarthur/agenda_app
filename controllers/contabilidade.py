from flask import Blueprint, render_template, make_response, send_file, flash, redirect, url_for, request
from io import BytesIO
from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from reportlab.lib.units import cm
from openpyxl import Workbook
from openpyxl.drawing.image import Image
from datetime import datetime
from collections import defaultdict
import locale

from models import db, Contabilidade, Aluno

contabilidade_bp = Blueprint('contabilidade', __name__, url_prefix='/contabilidade')

@contabilidade_bp.route('/')
def contabilidade():
    """Gera estrutura contabilidade_by_date para exibir no template."""
    contabilidade_data = Contabilidade.query.all()

    contabilidade_by_date = defaultdict(list)

    for cont in contabilidade_data:
        # 1) Título do evento (ou "Evento Removido" se não existir)
        event_title = cont.evento_titulo or (cont.evento.titulo if cont.evento else "Evento Removido")

        # 2) Formata data do evento (DD/MM/YYYY) ou "-"
        data_evento_fmt = "-"
        if cont.data_evento_original:
            try:
                dt_evt = datetime.strptime(cont.data_evento_original, "%Y-%m-%d")
                data_evento_fmt = dt_evt.strftime("%d/%m/%Y")
                # Definir uma chave de mês/ano a partir dessa data
                date_key = dt_evt.strftime("%m/%Y")  # Ex: "12/2024"
            except ValueError:
                # Se não estiver no formato YYYY-MM-DD, fica como string original
                data_evento_fmt = cont.data_evento_original
                date_key = "Sem Data"
        else:
            date_key = "Sem Data"

        # 3) Formata data de realização (DD/MM/YYYY) ou "Não Realizado"
        data_realizacao_fmt = "Não Realizado"
        if cont.realizado and cont.data_realizacao:
            try:
                dt_real = datetime.strptime(cont.data_realizacao, "%Y-%m-%d")
                data_realizacao_fmt = dt_real.strftime("%d/%m/%Y")
            except ValueError:
                data_realizacao_fmt = cont.data_realizacao

        # 4) Monta o dicionário com dados para o template
        contabilidade_by_date[date_key].append({
            "titulo": event_title,
            "data_evento": data_evento_fmt,
            "data_realizacao": data_realizacao_fmt,
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
    output.append([
        "Evento", "Data do Evento", "Data de Realização", "Valor Bruto (R$)",
        "Pagamentos de Músicos (R$)", "Locação de Som (R$)", 
        "Outros Custos (R$)", "Valor Líquido (R$)", "Status"
    ])

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

    # Integração com Alunos:
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

    # Configurar o documento em modo paisagem
    # Ajustando as margens para algo um pouco menor
    doc = SimpleDocTemplate(
        buffer,
        pagesize=landscape(letter),
        topMargin=15,
        bottomMargin=15,
        leftMargin=15,
        rightMargin=15,
    )
    doc.title = "Relatório de Contabilidade"

    # Estilos
    styles = getSampleStyleSheet()
    title_style = styles["Title"]
    title_style.alignment = 1  # Centraliza o título

    title = Paragraph("Relatório de Contabilidade", title_style)

    # Cabeçalho da tabela
    data = [[
        "Evento", 
        "Data do Evento", 
        "Data de Realização", 
        "Valor Bruto (R$)",
        "Pagamentos de Músicos (R$)", 
        "Locação de Som (R$)",
        "Outros Custos (R$)", 
        "Valor Líquido (R$)", 
        "Status"
    ]]

    for cont in contabilidade_data:
        # Tratamento do título do evento
        evento = cont.evento.titulo if cont.evento else "Evento Removido"

        # Converte data_evento_original
        if cont.data_evento_original:
            try:
                dt_evt = datetime.strptime(cont.data_evento_original, "%Y-%m-%d")
                data_evento = dt_evt.strftime("%d/%m/%Y")
            except ValueError:
                data_evento = cont.data_evento_original
        else:
            data_evento = "-"

        # Converte data_realizacao
        if cont.realizado and cont.data_realizacao:
            try:
                dt_real = datetime.strptime(cont.data_realizacao, "%Y-%m-%d")
                data_realizacao = dt_real.strftime("%d/%m/%Y")
            except ValueError:
                data_realizacao = cont.data_realizacao
        else:
            data_realizacao = "Não Realizado"

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

    # Ajuste manual da largura de cada coluna (colWidths)
    # para caber em modo paisagem de forma mais organizada
    # Você pode ajustar de acordo com a sua necessidade
    col_widths = [
        4.0*cm,  # Evento
        3.0*cm,  # Data do Evento
        3.0*cm,  # Data de Realização
        3.0*cm,  # Valor Bruto
        3.5*cm,  # Pagamento Músicos
        3.0*cm,  # Locação de Som
        3.0*cm,  # Outros Custos
        3.0*cm,  # Valor Líquido
        2.5*cm,  # Status
    ]

    # Criar tabela com colWidths + repeatRows para repetir cabeçalho em cada página
    table = Table(data, colWidths=col_widths, repeatRows=1)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.black),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),  # fonte menor para caber melhor
        ("BOTTOMPADDING", (0, 0), (-1, 0), 6),
        ("BACKGROUND", (0, 1), (-1, -1), colors.whitesmoke),
        ("GRID", (0, 0), (-1, -1), 1, colors.black),
    ]))

    # Construir o PDF
    doc.build([title, table])

    # Retornar como resposta
    buffer.seek(0)
    response = make_response(buffer.read())
    response.headers["Content-Disposition"] = "attachment; filename=relatorio_contabilidade.pdf"
    response.headers["Content-Type"] = "application/pdf"
    return response

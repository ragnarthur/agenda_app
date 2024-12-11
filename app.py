import os
import locale
import csv
import matplotlib.pyplot as plt
from io import BytesIO
from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from reportlab.pdfgen import canvas
from openpyxl import Workbook
from openpyxl.drawing.image import Image
from flask import Flask, render_template, request, redirect, url_for, flash, make_response, send_file
from flask_migrate import Migrate
from models import db, Evento, EventoRealizado, Contabilidade
from datetime import datetime, date
from collections import defaultdict
from weasyprint import HTML

# Import necessário para carregar variáveis do .env
from dotenv import load_dotenv

# Carrega as variáveis de ambiente do arquivo .env
load_dotenv()

app = Flask(__name__)

# Define o locale para português do Brasil
locale.setlocale(locale.LC_TIME, "pt_BR.UTF-8")

# Lê variáveis de ambiente com fallback
secret_key = os.getenv("SECRET_KEY", "supersecretkey")
database_url = os.getenv("DATABASE_URL", "sqlite:///instance/agenda.db")

app.config['SQLALCHEMY_DATABASE_URI'] = database_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = secret_key

# Inicializar o banco de dados
db.init_app(app)

# Configuração do Flask-Migrate
migrate = Migrate(app, db)

# Função para converter string monetária para float
def parse_currency(value):
    """Converte string monetária (R$ 1.234,56) para float."""
    return float(value.replace('.', '').replace(',', '.'))

# Função para formatar datas para o formato brasileiro
def format_datetime(value):
    """Formata uma data/hora para o formato DD/MM/AAAA."""
    if value:
        if isinstance(value, (datetime, date)):
            return value.strftime("%d/%m/%Y")
        return datetime.strptime(value, "%Y-%m-%d").strftime("%d/%m/%Y")
    return value

# Registrar o filtro no Jinja
app.jinja_env.filters['format_datetime'] = format_datetime

# Criar tabelas no banco de dados
with app.app_context():
    db.create_all()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/agendar', methods=['POST'])
def agendar():
    tipo = request.form['tipo']
    titulo = request.form['titulo']
    data = request.form['data']
    hora = request.form['hora']
    descricao = request.form['descricao']

    # Converter valores financeiros usando parse_currency
    valor_bruto = parse_currency(request.form.get('valor_bruto', '0'))
    pagamento_musicos = parse_currency(request.form.get('pagamento_musicos', '0'))
    locacao_som = parse_currency(request.form.get('locacao_som', '0'))
    outros_custos = parse_currency(request.form.get('outros_custos', '0'))
    valor_liquido = valor_bruto - (pagamento_musicos + locacao_som + outros_custos)

    # Criar evento e salvar no banco
    novo_evento = Evento(
        tipo=tipo,
        titulo=titulo,
        data=data,
        hora=hora,
        descricao=descricao
    )
    db.session.add(novo_evento)
    db.session.commit()

    # Adicionar contabilidade
    if valor_bruto > 0:
        nova_contabilidade = Contabilidade(
            evento_id=novo_evento.id,
            evento_titulo=titulo,
            valor_bruto=valor_bruto,
            pagamento_musicos=pagamento_musicos,
            locacao_som=locacao_som,
            outros_custos=outros_custos,
            valor_liquido=valor_liquido,
            mes_ano=f"{data.split('-')[1]}/{data.split('-')[0]}"  # MM/YYYY
        )
        db.session.add(nova_contabilidade)
        db.session.commit()

    flash("Evento agendado com sucesso!", "success")
    return redirect(url_for('schedule'))

@app.route('/schedule')
def schedule():
    eventos = Evento.query.order_by(Evento.data.asc(), Evento.hora.asc()).all()

    # Certifique-se de que as datas estão no formato datetime.date
    for evento in eventos:
        if isinstance(evento.data, str):
            evento.data = datetime.strptime(evento.data, "%Y-%m-%d").date()

    current_date = datetime.now().date()
    return render_template('schedule.html', events=eventos, current_date=current_date)

@app.route('/realizado/<int:event_id>', methods=['POST'])
def marcar_como_realizado(event_id):
    evento = Evento.query.get(event_id)
    if evento:
        # Criar um novo registro em EventoRealizado
        evento_realizado = EventoRealizado(
            titulo=evento.titulo,
            tipo=evento.tipo,
            data=evento.data,
            hora=evento.hora,
            descricao=evento.descricao
        )
        db.session.add(evento_realizado)

        # Atualizar contabilidade
        contabilidade = Contabilidade.query.filter_by(evento_id=event_id).first()
        if contabilidade:
            contabilidade.realizado = True
            contabilidade.evento_titulo = evento.titulo
            contabilidade.data_realizacao = datetime.now().strftime("%Y-%m-%d")

        # Remover o evento da tabela de agendados
        db.session.delete(evento)
        db.session.commit()

        flash("Evento marcado como realizado.", "success")
    else:
        flash("Evento não encontrado.", "danger")
    return redirect(url_for('schedule'))

@app.route('/excluir/<int:event_id>', methods=['POST'])
def excluir_evento(event_id):
    # Excluir evento e contabilidade associada
    contabilidade = Contabilidade.query.filter_by(evento_id=event_id).first()
    if contabilidade:
        db.session.delete(contabilidade)

    evento = Evento.query.get(event_id)
    if evento:
        db.session.delete(evento)

    db.session.commit()
    return '', 200

@app.route('/realizados', methods=['GET'])
def realizados():
    tipo = request.args.get('tipo', '')
    mes = request.args.get('mes', '')
    ano = request.args.get('ano', '')

    query = EventoRealizado.query
    if tipo:
        query = query.filter_by(tipo=tipo)
    if mes:
        query = query.filter(db.extract('month', EventoRealizado.data) == int(mes))
    if ano:
        query = query.filter(db.extract('year', EventoRealizado.data) == int(ano))

    eventos_realizados = query.order_by(EventoRealizado.data.asc()).all()
    return render_template('realizados.html', events=eventos_realizados)

@app.route('/contabilidade')
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
            key=lambda x: datetime.strptime(x.data_realizacao, "%Y-%m-%d") if isinstance(x.data_realizacao, str) else x.data_realizacao or datetime.min
        )

    return render_template('contabilidade.html', contabilidade_by_date=contabilidade_by_date)

@app.route('/contabilidade/exportar/csv')
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
            datetime.strptime(cont.data_realizacao, "%Y-%m-%d") if cont.realizado and isinstance(cont.data_realizacao, str) else cont.data_realizacao
        )

        output.append([
            titulo_evento,
            data_evento.strftime("%d/%m/%Y") if data_evento else "-",
            data_realizacao.strftime("%d/%m/%Y") if cont.realizado and data_realizacao else "Não Realizado",
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

@app.route('/contabilidade/exportar/pdf')
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
            else (cont.data_realizacao.strftime("%d/%m/%Y") if cont.realizado and cont.data_realizacao else "Não Realizado")
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

@app.route('/contabilidade_final')
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

@app.route('/contabilidade_final/exportar/excel')
def export_contabilidade_final_excel():
    contabilidade = Contabilidade.query.all()

    total_bruto = sum(cont.valor_bruto for cont in contabilidade)
    total_pagamento_musicos = sum(cont.pagamento_musicos for cont in contabilidade)
    total_locacao_som = sum(cont.locacao_som for cont in contabilidade)
    total_outros_custos = sum(cont.outros_custos for cont in contabilidade)
    total_liquido = total_bruto - (total_pagamento_musicos + total_locacao_som + total_outros_custos)

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

    for label, value, percentual in zip(labels, data, percentuais):
        ws.append([label, f"{value:.2f}", f"{percentual:.2f}%"])

    chart_colors = ["#4e73df", "#e74a3b", "#f6c23e", "#1cc88a", "#36b9cc"]
    plt.figure(figsize=(10, 8))
    explode = [0.1 if val == max(data) else 0 for val in data]

    wedges, texts, autotexts = plt.pie(
        data,
        labels=None,
        autopct=lambda p: f'{p:.2f}%' if p > 0 else '',
        startangle=140,
        colors=chart_colors,
        wedgeprops={"edgecolor": "black"},
        explode=explode
    )

    for i, autotext in enumerate(autotexts):
        autotext.set_text(f"{percentuais[i]:.2f}%")
        autotext.set_color("white")
        autotext.set_fontsize(12)

    plt.legend(
        labels=[f"{label}" for label in labels],
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

@app.route('/gerar_contrato', methods=['POST', 'GET'])
def gerar_contrato():
    if request.method == 'POST':
        nome_contratante = request.form['nome_contratante']
        cpf_cnpj = request.form['documento']
        endereco = f"{request.form['rua']}, {request.form['numero']}, {request.form['bairro']}, {request.form['cidade']}, {request.form['uf']} - CEP: {request.form['cep']}"
        telefone = request.form['telefone']
        celular = request.form['celular']
        tipo_evento = request.form['tipo_evento']
        data_evento = request.form['data_evento']
        horario_evento = request.form['horario_evento']
        local_evento = request.form['local_evento']
        detalhes_adicionais = request.form['detalhes_adicionais']
        valor_total = request.form['valor_total']
        locacao_som = request.form['locacao_som']

        html_content = render_template(
            'contrato_modelo.html',
            nome_contratante=nome_contratante,
            cpf_cnpj=cpf_cnpj,
            endereco=endereco,
            telefone=telefone,
            celular=celular,
            tipo_evento=tipo_evento,
            data_evento=data_evento,
            horario_evento=horario_evento,
            local_evento=local_evento,
            detalhes_adicionais=detalhes_adicionais,
            valor_total=valor_total,
            locacao_som=locacao_som
        )

        pdf = HTML(string=html_content).write_pdf()

        response = make_response(pdf)
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = f'attachment; filename=contrato_{nome_contratante}.pdf'
        return response

    else:
        return render_template('gerar_contrato.html')

if __name__ == '__main__':
    app.run(debug=True)

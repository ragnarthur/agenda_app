import os
import locale
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_migrate import Migrate
from models import db, Evento, EventoRealizado, Contabilidade
from datetime import datetime, date
from collections import defaultdict

app = Flask(__name__)

# Define o locale para português do Brasil
locale.setlocale(locale.LC_TIME, "pt_BR.UTF-8")

# Caminho absoluto para o banco de dados na pasta instance
db_path = os.path.join(os.path.abspath(os.getcwd()), 'instance', 'agenda.db')

# Configuração do banco de dados SQLite
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = 'supersecretkey'

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
        if isinstance(value, (datetime, date)):  # Verifica se já é datetime ou date
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
            evento_titulo=titulo,  # Nome do evento
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
        if isinstance(evento.data, str):  # Se a data for string, converte
            evento.data = datetime.strptime(evento.data, "%Y-%m-%d").date()
    
    current_date = datetime.now().date()  # Data atual
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
            contabilidade.evento_titulo = evento.titulo  # Mantém o título na contabilidade
            contabilidade.data_realizacao = datetime.now().strftime("%Y-%m-%d")  # Registra a data atual como data de realização

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

@app.route('/realizados')
def realizados():
    eventos_realizados = EventoRealizado.query.all()
    return render_template('realizados.html', events=eventos_realizados)

@app.route('/contabilidade')
def contabilidade():
    # Consulta todos os dados de contabilidade
    contabilidade_data = Contabilidade.query.order_by(Contabilidade.mes_ano.desc()).all()
    
    # Agrupa os eventos por mês/ano
    contabilidade_by_date = defaultdict(list)
    for cont in contabilidade_data:
        # Verifica se cont.evento e cont.evento.data existem
        if cont.evento and cont.evento.data:
            try:
                # Tenta converter a data para datetime, caso já não seja
                event_date = datetime.strptime(cont.evento.data, "%Y-%m-%d") if isinstance(cont.evento.data, str) else cont.evento.data
                date_key = event_date.strftime("%B/%Y").capitalize()  # Exemplo: Dezembro/2024
            except ValueError:
                date_key = "Data Inválida"
        else:
            date_key = "Sem Data"
        
        contabilidade_by_date[date_key].append(cont)
    
    # Ordena os eventos dentro de cada grupo por data do evento
    for key in contabilidade_by_date:
        contabilidade_by_date[key].sort(key=lambda x: x.evento.data if x.evento and x.evento.data else datetime.min)

    return render_template('contabilidade.html', contabilidade_by_date=contabilidade_by_date)

@app.route('/contabilidade_final')
def contabilidade_final():
    contabilidade = Contabilidade.query.all()
    total_bruto = sum(cont.valor_bruto for cont in contabilidade)
    total_pagamento_musicos = sum(cont.pagamento_musicos for cont in contabilidade)
    total_locacao_som = sum(cont.locacao_som for cont in contabilidade)
    total_outros_custos = sum(cont.outros_custos for cont in contabilidade)
    total_liquido = sum(cont.valor_liquido for cont in contabilidade)

    return render_template('contabilidade_final.html',
                           total_bruto=total_bruto,
                           total_pagamento_musicos=total_pagamento_musicos,
                           total_locacao_som=total_locacao_som,
                           total_outros_custos=total_outros_custos,
                           total_liquido=total_liquido)

if __name__ == '__main__':
    app.run(debug=True)

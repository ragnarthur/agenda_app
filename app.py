from flask import Flask, render_template, request, redirect, url_for
from models import db, Evento, EventoRealizado, Contabilidade
from datetime import datetime

app = Flask(__name__)

# Configuração do banco de dados SQLite
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///agenda.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Inicializar o banco de dados
db.init_app(app)

# Função para converter string monetária para float
def parse_currency(value):
    """Converte string monetária (R$ 1.234,56) para float."""
    return float(value.replace('.', '').replace(',', '.'))

# Função para formatar datas para o formato brasileiro
def format_datetime(value):
    """Formata uma data/hora para o formato DD/MM/AAAA."""
    if value:
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
            valor_bruto=valor_bruto,
            pagamento_musicos=pagamento_musicos,
            locacao_som=locacao_som,
            outros_custos=outros_custos,
            valor_liquido=valor_liquido
        )
        db.session.add(nova_contabilidade)
        db.session.commit()

    return redirect(url_for('schedule'))

@app.route('/schedule')
def schedule():
    # Recuperar eventos do banco de dados ordenados pela data mais próxima
    eventos = Evento.query.order_by(Evento.data.asc(), Evento.hora.asc()).all()
    return render_template('schedule.html', events=eventos)

@app.route('/excluir/<int:event_id>', methods=['POST'])
def excluir_evento(event_id):
    evento = Evento.query.get(event_id)
    if evento:
        db.session.delete(evento)
        db.session.commit()
        return '', 200
    return '', 404

@app.route('/realizado/<int:event_id>', methods=['POST'])
def marcar_como_realizado(event_id):
    evento = Evento.query.get(event_id)
    if evento:
        evento_realizado = EventoRealizado(
            titulo=evento.titulo,
            tipo=evento.tipo,
            data=evento.data,
            hora=evento.hora,
            descricao=evento.descricao,
        )
        db.session.add(evento_realizado)
        db.session.delete(evento)
        db.session.commit()
        return '', 200
    return '', 404

@app.route('/realizados')
def realizados():
    eventos_realizados = EventoRealizado.query.all()
    return render_template('realizados.html', events=eventos_realizados)

@app.route('/contabilidade', methods=['GET', 'POST'])
def contabilidade():
    eventos = Evento.query.all()
    contabilidade = Contabilidade.query.all()

    if request.method == 'POST':
        evento_id = int(request.form['evento_id'])
        valor_bruto = float(request.form['valor_bruto'])
        pagamento_musicos = float(request.form['pagamento_musicos'])
        locacao_som = float(request.form['locacao_som'])
        outros_custos = float(request.form['outros_custos'])

        # Calcular o valor líquido
        valor_liquido = valor_bruto - (pagamento_musicos + locacao_som + outros_custos)

        # Atualizar ou criar a contabilidade
        cont = Contabilidade.query.filter_by(evento_id=evento_id).first()
        if cont:
            cont.valor_bruto = valor_bruto
            cont.pagamento_musicos = pagamento_musicos
            cont.locacao_som = locacao_som
            cont.outros_custos = outros_custos
            cont.valor_liquido = valor_liquido
        else:
            nova_contabilidade = Contabilidade(
                evento_id=evento_id,
                valor_bruto=valor_bruto,
                pagamento_musicos=pagamento_musicos,
                locacao_som=locacao_som,
                outros_custos=outros_custos,
                valor_liquido=valor_liquido,
            )
            db.session.add(nova_contabilidade)

        db.session.commit()
        return redirect(url_for('contabilidade'))

    return render_template('contabilidade.html', eventos=eventos, contabilidade=contabilidade)

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

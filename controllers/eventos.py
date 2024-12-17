from flask import Blueprint, render_template, request, redirect, url_for, flash, make_response
from datetime import datetime, date
from models import db, Evento, EventoRealizado, Contabilidade
from utils.currency import parse_currency
from utils.formatters import format_datetime

eventos_bp = Blueprint('eventos', __name__)

# Configurar o filtro Jinja no blueprint
@eventos_bp.record_once
def on_load(state):
    state.app.jinja_env.filters['format_datetime'] = format_datetime

@eventos_bp.route('/')
def index():
    return render_template('index.html')

@eventos_bp.route('/agendar', methods=['POST'])
def agendar():
    tipo = request.form['tipo']
    titulo = request.form['titulo']
    data = request.form['data']
    hora = request.form['hora']
    descricao = request.form['descricao']

    valor_bruto = parse_currency(request.form.get('valor_bruto', '0'))
    pagamento_musicos = parse_currency(request.form.get('pagamento_musicos', '0'))
    locacao_som = parse_currency(request.form.get('locacao_som', '0'))
    outros_custos = parse_currency(request.form.get('outros_custos', '0'))
    valor_liquido = valor_bruto - (pagamento_musicos + locacao_som + outros_custos)

    novo_evento = Evento(
        tipo=tipo,
        titulo=titulo,
        data=data,
        hora=hora,
        descricao=descricao
    )
    db.session.add(novo_evento)
    db.session.commit()

    if valor_bruto > 0:
        nova_contabilidade = Contabilidade(
            evento_id=novo_evento.id,
            evento_titulo=titulo,
            valor_bruto=valor_bruto,
            pagamento_musicos=pagamento_musicos,
            locacao_som=locacao_som,
            outros_custos=outros_custos,
            valor_liquido=valor_liquido,
            mes_ano=f"{data.split('-')[1]}/{data.split('-')[0]}" 
        )
        db.session.add(nova_contabilidade)
        db.session.commit()

    flash("Evento agendado com sucesso!", "success")
    return redirect(url_for('eventos.schedule'))

@eventos_bp.route('/schedule')
def schedule():
    eventos = Evento.query.order_by(Evento.data.asc(), Evento.hora.asc()).all()
    for evento in eventos:
        if isinstance(evento.data, str):
            evento.data = datetime.strptime(evento.data, "%Y-%m-%d").date()
    current_date = datetime.now().date()
    return render_template('schedule.html', events=eventos, current_date=current_date)

@eventos_bp.route('/realizado/<int:event_id>', methods=['POST'])
def marcar_como_realizado(event_id):
    evento = Evento.query.get(event_id)
    if evento:
        evento_realizado = EventoRealizado(
            titulo=evento.titulo,
            tipo=evento.tipo,
            data=evento.data,
            hora=evento.hora,
            descricao=evento.descricao
        )
        db.session.add(evento_realizado)

        contabilidade = Contabilidade.query.filter_by(evento_id=event_id).first()
        if contabilidade:
            contabilidade.realizado = True
            contabilidade.evento_titulo = evento.titulo
            contabilidade.data_realizacao = datetime.now().strftime("%Y-%m-%d")

        db.session.delete(evento)
        db.session.commit()

        flash("Evento marcado como realizado.", "success")
    else:
        flash("Evento não encontrado.", "danger")
    return redirect(url_for('eventos.schedule'))

@eventos_bp.route('/excluir/<int:event_id>', methods=['POST'])
def excluir_evento(event_id):
    contabilidade = Contabilidade.query.filter_by(evento_id=event_id).first()
    if contabilidade:
        db.session.delete(contabilidade)
    evento = Evento.query.get(event_id)
    if evento:
        db.session.delete(evento)
    db.session.commit()
    return '', 200

@eventos_bp.route('/realizados', methods=['GET'])
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

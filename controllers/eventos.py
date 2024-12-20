from flask import Blueprint, render_template, request, redirect, url_for, flash
from datetime import datetime, date
from models import db, Evento, EventoRealizado, Contabilidade
from utils.currency import parse_currency
from utils.formatters import format_datetime
import logging

# Configurar logs verbosos para SQLAlchemy
logging.basicConfig()
logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)

eventos_bp = Blueprint('eventos', __name__, url_prefix='/eventos')

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
    data = request.form['data']  # Formato YYYY-MM-DD
    hora = request.form['hora']
    descricao = request.form['descricao']

    valor_bruto = parse_currency(request.form.get('valor_bruto', '0'))
    pagamento_musicos = parse_currency(request.form.get('pagamento_musicos', '0'))
    locacao_som = parse_currency(request.form.get('locacao_som', '0'))
    outros_custos = parse_currency(request.form.get('outros_custos', '0'))
    valor_liquido = valor_bruto - (pagamento_musicos + locacao_som + outros_custos)

    # Criar o evento
    novo_evento = Evento(
        tipo=tipo,
        titulo=titulo,
        data=data,
        hora=hora,
        descricao=descricao
    )
    db.session.add(novo_evento)
    db.session.commit()

    # Criar a contabilidade se houver valor bruto
    if valor_bruto > 0:
        nova_contabilidade = Contabilidade(
            evento_id=novo_evento.id,
            evento_titulo=titulo,
            valor_bruto=valor_bruto,
            pagamento_musicos=pagamento_musicos,
            locacao_som=locacao_som,
            outros_custos=outros_custos,
            valor_liquido=valor_liquido,
            mes_ano=f"{data.split('-')[1]}/{data.split('-')[0]}",
            data_evento_original=data  # Armazena a data original do evento
        )
        db.session.add(nova_contabilidade)
        db.session.commit()

    flash("Evento agendado com sucesso!", "success")
    return redirect(url_for('eventos.schedule'))

@eventos_bp.route('/schedule')
def schedule():
    eventos = Evento.query.order_by(Evento.data.asc(), Evento.hora.asc()).all()
    for evento in eventos:
        try:
            if isinstance(evento.data, str):
                evento.data = datetime.strptime(evento.data, "%Y-%m-%d").date()
        except ValueError:
            flash(f"Erro ao converter data do evento {evento.id}.", "danger")
    current_date = datetime.now().date()
    return render_template('schedule.html', events=eventos, current_date=current_date)

@eventos_bp.route('/realizado/<int:event_id>', methods=['POST'])
def marcar_como_realizado(event_id):
    try:
        # Buscar o evento no banco de dados
        evento = Evento.query.get(event_id)
        if not evento:
            flash("Evento não encontrado.", "danger")
            return redirect(url_for('eventos.schedule'))

        # Criar uma entrada na tabela EventoRealizado
        evento_realizado = EventoRealizado(
            titulo=evento.titulo,
            tipo=evento.tipo,
            data=evento.data,
            hora=evento.hora,
            descricao=evento.descricao
        )
        db.session.add(evento_realizado)

        # Atualizar a tabela Contabilidade
        contabilidade = Contabilidade.query.filter_by(evento_id=event_id).first()
        if contabilidade:
            contabilidade.realizado = True
            contabilidade.data_realizacao = datetime.now().strftime("%Y-%m-%d")
            contabilidade.evento_titulo = evento.titulo
            if isinstance(evento.data, date):
                contabilidade.data_evento_original = evento.data.strftime("%Y-%m-%d")
            else:
                contabilidade.data_evento_original = evento.data

        # Remover o evento da tabela Evento
        db.session.delete(evento)

        # Commit das alterações
        db.session.commit()

        flash("Evento marcado como realizado com sucesso!", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Erro ao marcar o evento como realizado: {e}", "danger")
    return redirect(url_for('eventos.schedule'))

@eventos_bp.route('/excluir/<int:event_id>', methods=['POST'])
def excluir_evento(event_id):
    try:
        # Remover contabilidade associada ao evento
        contabilidade = Contabilidade.query.filter_by(evento_id=event_id).first()
        if contabilidade:
            db.session.delete(contabilidade)
            print(f"Contabilidade associada ao evento {event_id} excluída.")

        # Remover associações na tabela EventoRealizado
        evento_realizado = EventoRealizado.query.filter_by(evento_id=event_id).first()
        if evento_realizado:
            db.session.delete(evento_realizado)
            print(f"EventoRealizado associado ao evento {event_id} excluído.")

        # Remover o evento
        evento = Evento.query.get(event_id)
        if evento:
            db.session.delete(evento)
            print(f"Evento {event_id} excluído.")
        else:
            print(f"Evento {event_id} não encontrado.")
            return 'Evento não encontrado.', 404

        # Commit das alterações
        db.session.commit()
        flash("Evento excluído com sucesso!", "success")
        return '', 200
    except Exception as e:
        db.session.rollback()
        print(f"Erro ao excluir evento {event_id}: {e}")
        flash("Erro ao excluir o evento.", "danger")
        return 'Erro ao excluir o evento.', 500

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

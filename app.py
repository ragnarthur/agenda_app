from flask import Flask, render_template, request, redirect, url_for
from models import db, Evento, EventoRealizado

app = Flask(__name__)

# Configuração do banco de dados SQLite
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///agenda.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Inicializar o banco de dados
db.init_app(app)

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
    repetir = 'repetir' in request.form  # Capturar o estado do checkbox

    # Salvar no banco de dados
    novo_evento = Evento(tipo=tipo, titulo=titulo, data=data, hora=hora, descricao=descricao, repetir=repetir)
    db.session.add(novo_evento)
    db.session.commit()

    return redirect(url_for('schedule'))

@app.route('/schedule')
def schedule():
    # Recuperar eventos do banco de dados
    eventos = Evento.query.all()
    return render_template('schedule.html', events=eventos)

@app.route('/excluir/<int:event_id>', methods=['POST'])
def excluir_evento(event_id):
    # Lógica para excluir o evento do banco de dados
    evento = Evento.query.get(event_id)
    if evento:
        db.session.delete(evento)
        db.session.commit()
        return '', 200  # Sucesso
    return '', 404  # Evento não encontrado

@app.route('/realizado/<int:event_id>', methods=['POST'])
def marcar_como_realizado(event_id):
    # Recuperar o evento da tabela principal
    evento = Evento.query.get(event_id)
    if evento:
        # Mover o evento para a tabela de eventos realizados
        evento_realizado = EventoRealizado(
            titulo=evento.titulo,
            tipo=evento.tipo,
            data=evento.data,
            hora=evento.hora,
            descricao=evento.descricao,
        )
        db.session.add(evento_realizado)
        db.session.delete(evento)  # Remover da tabela principal
        db.session.commit()
        return '', 200  # Sucesso
    return '', 404  # Evento não encontrado

@app.route('/realizados')
def realizados():
    # Recuperar eventos realizados do banco de dados
    eventos_realizados = EventoRealizado.query.all()
    return render_template('realizados.html', events=eventos_realizados)


if __name__ == '__main__':
    app.run(debug=True)


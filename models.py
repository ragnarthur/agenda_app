from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Evento(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tipo = db.Column(db.String(50), nullable=False)
    titulo = db.Column(db.String(100), nullable=False)
    data = db.Column(db.String(10), nullable=False)
    hora = db.Column(db.String(5), nullable=False)
    descricao = db.Column(db.Text, nullable=True)
    repetir = db.Column(db.Boolean, default=False)

class EventoRealizado(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tipo = db.Column(db.String(50), nullable=False)
    titulo = db.Column(db.String(100), nullable=False)
    data = db.Column(db.String(10), nullable=False)
    hora = db.Column(db.String(5), nullable=False)
    descricao = db.Column(db.Text, nullable=True)

class Contabilidade(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    evento_id = db.Column(db.Integer, db.ForeignKey('evento.id'), nullable=True)
    evento_titulo = db.Column(db.String(100), nullable=True)
    valor_bruto = db.Column(db.Float, nullable=False, default=0.0)
    pagamento_musicos = db.Column(db.Float, nullable=False, default=0.0)
    locacao_som = db.Column(db.Float, nullable=False, default=0.0)
    outros_custos = db.Column(db.Float, nullable=False, default=0.0)
    valor_liquido = db.Column(db.Float, nullable=False, default=0.0)
    mes_ano = db.Column(db.String(7), nullable=True)
    realizado = db.Column(db.Boolean, nullable=False, default=False)
    data_realizacao = db.Column(db.String(10), nullable=True)

    evento = db.relationship('Evento', backref=db.backref('contabilidade', uselist=False))

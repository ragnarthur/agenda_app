from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

# Modelo do Banco de Dados
class Evento(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tipo = db.Column(db.String(50), nullable=False)
    titulo = db.Column(db.String(100), nullable=False)
    data = db.Column(db.String(10), nullable=False)
    hora = db.Column(db.String(5), nullable=False)
    descricao = db.Column(db.Text, nullable=True)
    repetir = db.Column(db.Boolean, default=False)  # Campo para eventos semanais

class EventoRealizado(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tipo = db.Column(db.String(50), nullable=False)
    titulo = db.Column(db.String(100), nullable=False)
    data = db.Column(db.String(10), nullable=False)
    hora = db.Column(db.String(5), nullable=False)
    descricao = db.Column(db.Text, nullable=True)

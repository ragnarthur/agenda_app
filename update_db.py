from models import db
from flask import Flask
from sqlalchemy import text

app = Flask(__name__)

# Configuração do banco de dados SQLite
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///agenda.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

with app.app_context():
    # Criar uma conexão com o banco de dados
    with db.engine.connect() as connection:
        # Adicionar a coluna 'repetir' ao banco de dados
        alter_table_query = text('ALTER TABLE evento ADD COLUMN repetir BOOLEAN DEFAULT 0')
        connection.execute(alter_table_query)
        print("Coluna 'repetir' adicionada com sucesso!")

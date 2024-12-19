import os
import locale
from flask import Flask
from flask_migrate import Migrate
from dotenv import load_dotenv
from models import db
from config import Config

# Carregar variáveis de ambiente do .env
load_dotenv()

app = Flask(__name__)
app.config.from_object(Config)

# Inicializar banco de dados e migrações
db.init_app(app)
migrate = Migrate(app, db)

# Definir locale para Português do Brasil
locale.setlocale(locale.LC_TIME, "pt_BR.UTF-8")

from controllers.eventos import eventos_bp
from controllers.contabilidade import contabilidade_bp
from controllers.contratos import contratos_bp
from controllers.alunos import alunos_bp

app.register_blueprint(eventos_bp)
app.register_blueprint(contabilidade_bp)
app.register_blueprint(contratos_bp)
app.register_blueprint(alunos_bp)

if __name__ == '__main__':
    # Garantir a criação das tabelas antes de rodar
    with app.app_context():
        db.create_all()
    app.run(debug=True)

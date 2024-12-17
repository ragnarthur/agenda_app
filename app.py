import os
import locale
from flask import Flask
from flask_migrate import Migrate
from dotenv import load_dotenv
from models import db
from config import Config

# Carrega as variáveis de ambiente
load_dotenv()

app = Flask(__name__)
app.config.from_object(Config)

# Inicializar banco e migração
db.init_app(app)
migrate = Migrate(app, db)

# Definir locale para português do Brasil
locale.setlocale(locale.LC_TIME, "pt_BR.UTF-8")

# Importar e registrar Blueprints
from controllers.eventos import eventos_bp
from controllers.contabilidade import contabilidade_bp
from controllers.contratos import contratos_bp

app.register_blueprint(eventos_bp)
app.register_blueprint(contabilidade_bp)
app.register_blueprint(contratos_bp)

if __name__ == '__main__':
    app.run(debug=True)

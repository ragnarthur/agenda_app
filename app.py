import os
import locale
from flask import Flask, redirect, url_for
from flask_migrate import Migrate
from dotenv import load_dotenv
from models import db
from config import Config
import pathlib

# Carregar variáveis de ambiente do .env
load_dotenv()

app = Flask(__name__)
app.config.from_object(Config)

# Criar a pasta `instance` se não existir
instance_path = os.path.join(os.getcwd(), 'instance')
os.makedirs(instance_path, exist_ok=True)

# Inicializar banco de dados e migrações
db.init_app(app)
migrate = Migrate(app, db)

# Definir locale para Português do Brasil
locale.setlocale(locale.LC_TIME, "pt_BR.UTF-8")

from controllers.eventos import eventos_bp
from controllers.contabilidade import contabilidade_bp
from controllers.contratos import contratos_bp
from controllers.alunos import alunos_bp

# Registrar os blueprints
app.register_blueprint(eventos_bp)
app.register_blueprint(contabilidade_bp)
app.register_blueprint(contratos_bp)
app.register_blueprint(alunos_bp)

# Rota para a URL raiz
@app.route('/')
def home():
    return redirect(url_for('eventos.index'))  # Redireciona para a página de eventos ou a desejada

if __name__ == '__main__':
    # Garantir que o banco de dados exista antes de rodar
    db_path = pathlib.Path("instance/agenda.db")
    if not db_path.exists():
        print("Banco de dados não encontrado. Certifique-se de que 'instance/agenda.db' está no lugar correto.")
    app.run(debug=True)

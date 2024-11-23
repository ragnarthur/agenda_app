from sqlalchemy import inspect
from sqlalchemy.sql import text
from models import db
from app import app

def column_exists(table_name, column_name):
    """Verifica se uma coluna já existe na tabela."""
    inspector = inspect(db.engine)
    columns = [col["name"] for col in inspector.get_columns(table_name)]
    return column_name in columns

with app.app_context():
    # Criar tabelas que não existem
    db.create_all()

    # Abrir uma conexão explícita
    connection = db.engine.connect()

    try:
        # Atualizar o esquema da tabela Contabilidade
        columns_to_add = {
            "valor_bruto": "FLOAT DEFAULT 0.0",
            "pagamento_musicos": "FLOAT DEFAULT 0.0",
            "locacao_som": "FLOAT DEFAULT 0.0",
            "outros_custos": "FLOAT DEFAULT 0.0",
            "valor_liquido": "FLOAT DEFAULT 0.0",
        }

        for column_name, column_definition in columns_to_add.items():
            if not column_exists("contabilidade", column_name):
                command = text(f"ALTER TABLE contabilidade ADD COLUMN {column_name} {column_definition}")
                connection.execute(command)
                print(f"Coluna '{column_name}' adicionada com sucesso!")
            else:
                print(f"Coluna '{column_name}' já existe. Nenhuma alteração necessária.")

    except Exception as e:
        print(f"Erro ao atualizar banco de dados: {e}")
    finally:
        # Fechar a conexão
        connection.close()

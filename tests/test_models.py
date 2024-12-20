import pytest
from models import db, Evento

@pytest.fixture
def app():
    from app import app
    app.config.update({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",  # Banco de dados em memória para testes
        "SQLALCHEMY_TRACK_MODIFICATIONS": False,
    })
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app):
    return app.test_client()

def test_criar_evento(app):
    with app.app_context():
        # Criar um evento para teste
        evento = Evento(
            tipo="Show",
            titulo="Teste Evento",
            data="2024-12-25",
            hora="20:00",
            descricao="Evento de teste",
        )
        db.session.add(evento)
        db.session.commit()

        # Verificar se o evento foi salvo no banco
        evento_salvo = Evento.query.first()
        assert evento_salvo is not None
        assert evento_salvo.titulo == "Teste Evento"

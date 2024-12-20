import pytest
from models import Evento, db

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

def test_agendar_evento(client):
    # Simular envio de formulário
    response = client.post('/eventos/agendar', data={
        'tipo': 'Show',
        'titulo': 'Teste Show',
        'data': '2024-12-25',
        'hora': '20:00',
        'descricao': 'Descrição do evento de teste.',
        'valor_bruto': '1000.00',
        'pagamento_musicos': '500.00',
        'locacao_som': '300.00',
        'outros_custos': '200.00'
    })
    assert response.status_code == 302  # Redirecionamento após sucesso

    # Verificar se o evento foi salvo
    with client.application.app_context():
        evento = Evento.query.first()
        assert evento is not None
        assert evento.titulo == 'Teste Show'

import pytest
from models import db

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

def test_integration_contabilidade(client, app):
    # Criar um evento
    response = client.post('/eventos/agendar', data={
        'tipo': 'Show',
        'titulo': 'Evento Integrado',
        'data': '2024-12-25',
        'hora': '20:00',
        'descricao': 'Teste integração',
        'valor_bruto': '1000.00',
        'pagamento_musicos': '400.00',
        'locacao_som': '300.00',
        'outros_custos': '200.00'
    })
    assert response.status_code == 302

    # Verificar se o evento foi salvo no banco de dados
    with app.app_context():
        from models import Contabilidade, Evento
        evento = Evento.query.filter_by(titulo='Evento Integrado').first()
        assert evento is not None

        contabilidade = Contabilidade.query.filter_by(evento_id=evento.id).first()
        assert contabilidade is not None

    # Verificar se o evento foi adicionado à contabilidade
    response = client.get('/contabilidade', follow_redirects=True)
    assert b'Evento Integrado' in response.data

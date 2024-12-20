import os

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "supersecretkey")
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "sqlite:///instance/agenda.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"  # Banco de dados em memória para testes
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    WTF_CSRF_ENABLED = False  # Desativa CSRF para facilitar testes de formulários

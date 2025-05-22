from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin  # Importar o UserMixin
from datetime import datetime

db = SQLAlchemy()

# Modelo de Usuário
class User(UserMixin, db.Model):  # Herda de UserMixin
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(300), nullable=False)

    tipo = db.Column(db.String(20), nullable=False, default='comum')  # 'admin', 'revenda' ou 'comum'
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Informações extras para revenda
    nome = db.Column(db.String(100), nullable=True)
    telefone = db.Column(db.String(20), nullable=True)
    email = db.Column(db.String(100), nullable=True)
    cpf_cnpj = db.Column(db.String(20), nullable=True)
    endereco = db.Column(db.String(200), nullable=True)
    cidade = db.Column(db.String(100), nullable=True)   # novo campo
    uf = db.Column(db.String(2), nullable=True)         # novo campo (estado)

    # Relacionamento: revenda pode ter vários usuários comuns vinculados
    revenda_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    usuarios_cadastrados = db.relationship('User', backref=db.backref('revenda', remote_side=[id]), lazy=True)

    # Relacionamentos existentes
    entries = db.relationship('Entry', backref='user', lazy=True)
    exits = db.relationship('Exit', backref='user', lazy=True)
    config = db.relationship('ConfigData', backref='user', uselist=False)
    vehicles = db.relationship('VehicleType', backref='user', lazy=True)

    @property
    def is_admin(self):
        return self.tipo == 'admin'


# Configurações do Usuário
class ConfigData(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), unique=True, nullable=False)
    company_name = db.Column(db.String(100))
    address = db.Column(db.String(150))
    city = db.Column(db.String(80))
    phone = db.Column(db.String(20))


# Tipos de Veículo com valor da hora
class VehicleType(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String(20))
    hour_value = db.Column(db.Float)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)


# Entradas
class Entry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    plate = db.Column(db.String(10), nullable=False)
    entry_time = db.Column(db.DateTime, default=datetime.utcnow)
    vehicle_type = db.Column(db.String(20), default="Carro")
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)


# Saídas
class Exit(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    plate = db.Column(db.String(10), nullable=False)
    exit_time = db.Column(db.DateTime, default=datetime.utcnow)
    total_value = db.Column(db.Float, nullable=False)
    duration = db.Column(db.Float, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

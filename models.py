from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

# Modelo de Usuário
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    
    # Relacionamentos com outras tabelas
    entries = db.relationship('Entry', backref='user', lazy=True)
    exits = db.relationship('Exit', backref='user', lazy=True)
    config = db.relationship('ConfigData', backref='user', uselist=False)  # Um usuário tem uma configuração única
    vehicles = db.relationship('VehicleType', backref='user', lazy=True)

# Modelo de Configurações (Cada usuário tem suas próprias configurações)
class ConfigData(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    hour_value = db.Column(db.Float, default=0)
    company_name = db.Column(db.String(100))
    address = db.Column(db.String(100))
    city = db.Column(db.String(50))
    phone = db.Column(db.String(20))
    
    # Relacionamento com o User
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)  # Relacionamento com User

# Modelo de Tipo de Veículo (Cada estacionamento terá seus próprios tipos de veículos)
class VehicleType(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String(20), unique=False, nullable=False)  # Removi unique=True, pois vários usuários podem ter o mesmo tipo de veículo
    hour_value = db.Column(db.Float, nullable=False)
    
    # Relacionamento com o User
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)  # Relacionamento com User

# Modelo de Entrada de Veículo (Cada entrada será associada ao usuário)
class Entry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    plate = db.Column(db.String(10), nullable=False)
    entry_time = db.Column(db.DateTime, default=datetime.utcnow)
    vehicle_type = db.Column(db.String(20), default="Carro")
    
    # Relacionamento com o User
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)  # Relacionamento com User

# Modelo de Saída de Veículo (Cada saída será associada ao usuário)
class Exit(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    plate = db.Column(db.String(10), nullable=False)
    exit_time = db.Column(db.DateTime, default=datetime.utcnow)
    total_value = db.Column(db.Float, nullable=False)
    duration = db.Column(db.Float, nullable=False)
    
    # Relacionamento com o User
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)  # Relacionamento com User

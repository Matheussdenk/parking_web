from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

# Modelo de Usuário
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    
    entries = db.relationship('Entry', backref='user', lazy=True)
    exits = db.relationship('Exit', backref='user', lazy=True)
    config = db.relationship('ConfigData', backref='user', uselist=False)
    vehicles = db.relationship('VehicleType', backref='user', lazy=True)

# Configurações do Usuário
class ConfigData(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), unique=True, nullable=False)
    company_name = db.Column(db.String(100))
    address = db.Column(db.String(150))
    city = db.Column(db.String(80))
    phone = db.Column(db.String(20))

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

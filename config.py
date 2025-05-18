# config.py

#import os

#class Config:
 #   SECRET_KEY = '1234'  # altere para uma chave secreta real
  #  SQLALCHEMY_DATABASE_URI = "postgresql://postgres:1234@localhost:5432/parking_system"
   # SQLALCHEMY_TRACK_MODIFICATIONS = False

import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', '1234')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///local.db').replace("postgres://", "postgresql://")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

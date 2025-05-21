# config.py

#import os

#class Config:
 #   SECRET_KEY = '1234'  # altere para uma chave secreta real
  #  SQLALCHEMY_DATABASE_URI = "postgresql://postgres:1234@localhost:5432/parking_system"
   # SQLALCHEMY_TRACK_MODIFICATIONS = False

import os

class Config:
    SECRET_KEY = 'sua_chave_secreta'
    SQLALCHEMY_DATABASE_URI = 'postgresql://parking_db_e16y_user:vlcirPPqpzXt3KNefXn1pSyuoQuHhVvM@dpg-d0l1ghpr0fns7391uumg-a.oregon-postgres.render.com:5432/parking_db_e16y'
    SQLALCHEMY_TRACK_MODIFICATIONS = False


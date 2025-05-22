from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField
from wtforms.validators import DataRequired, Email

class RevendaRegisterForm(FlaskForm):
    nome = StringField("Nome", validators=[DataRequired()])
    telefone = StringField("Telefone", validators=[DataRequired()])
    email = StringField("Email", validators=[Email()])
    cpf_cnpj = StringField("CPF/CNPJ", validators=[DataRequired()])
    endereco = StringField("Endereço", validators=[DataRequired()])
    submit = SubmitField("Cadastrar")

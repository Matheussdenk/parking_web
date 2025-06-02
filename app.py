from flask import Flask, render_template, request, redirect, url_for, flash, session, send_file
from flask_migrate import Migrate
from flask_login import LoginManager, login_user, login_required, current_user, logout_user, UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from io import BytesIO
from datetime import datetime
from reportlab.pdfgen import canvas
import os
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
# Modelos de dados e banco de dados
from models import db, User, ConfigData, Entry, Exit, VehicleType
# Configurações de aplicação
from config import Config
# Formulários
from forms import RevendaRegisterForm
from datetime import datetime, timezone
from flask import make_response
from io import BytesIO
from reportlab.lib.units import mm


app = Flask(__name__)
app.config.from_object(Config)

# Inicialização do Flask-Login
login_manager = LoginManager(app)
login_manager.login_view = 'login'  # Rota de login, para redirecionamento quando não autenticado

db.init_app(app)
migrate = Migrate(app, db)

# Função para carregar o usuário no Flask-Login
@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))  # Substituindo query.get() por db.session.get()

@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect('/dashboard')
    return redirect('/login')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect('/dashboard')

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password, password):
            if not user.is_active:
                flash("Seu usuário está inativo. Contate o administrador.", "danger")
                return redirect('/login')

            login_user(user)
            return redirect('/dashboard')

        flash('Usuário ou senha inválidos.', 'danger')

    return render_template('login.html')

@app.route('/logout')
def logout():
    logout_user()  # Utilizando o logout do Flask-Login
    flash('Você foi desconectado.')
    return redirect('/login')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect('/dashboard')

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if not username or not password:
            flash("Por favor, preencha todos os campos.")
            return redirect('/register')

        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')

        user = User(username=username, password=hashed_password)
        db.session.add(user)
        db.session.commit()

        flash("Usuário registrado com sucesso!")
        return redirect('/login')

    return render_template('register.html')

@app.route('/cadastrar_revenda', methods=['GET', 'POST'])
@login_required
def cadastrar_revenda():
    if current_user.tipo != 'admin':
        flash("Acesso negado. Somente administradores podem cadastrar revendas.")
        return redirect(url_for('index'))

    form = RevendaRegisterForm()
    if request.method == 'POST' and form.validate():
        nova_revenda = User(
            username=form.username.data,
            password=generate_password_hash(form.password.data),
            tipo='revenda',
            is_active=True,
            nome=form.nome.data,
            telefone=form.telefone.data,
            email=form.email.data,
            cpf_cnpj=form.cpf_cnpj.data,
            endereco=form.endereco.data
        )
        db.session.add(nova_revenda)
        db.session.commit()
        flash('Revenda cadastrada com sucesso!')
        return redirect(url_for('admin_painel'))

    return render_template('cadastrar_revenda.html', form=form)

@app.route('/dashboard')
@login_required
def dashboard():
    entries = Entry.query.filter_by(user_id=current_user.id).all()
    now_time = datetime.utcnow()
    return render_template('dashboard.html', entries=entries, now=now_time)

@app.route('/admin/painel', methods=['GET', 'POST'])
@login_required
def admin_painel():
    if current_user.tipo not in ['admin', 'revenda']:
        flash("Acesso restrito a administradores e revendas.")
        return redirect('/dashboard')

    if request.method == 'POST':
        form_type = request.form.get('form_type')

        if current_user.tipo == 'revenda' and form_type != 'usuario_comum':
            flash("Revendas só podem cadastrar usuários comuns.")
            return redirect(url_for('admin_painel'))

        if form_type == 'usuario_comum':
            username = request.form['username']
            password = request.form['password']
            novo = User(
                username=username,
                password=generate_password_hash(password),
                tipo='comum',
                revenda_id=current_user.id if current_user.tipo == 'revenda' else None
            )
            db.session.add(novo)
            db.session.commit()
            flash("Usuário comum criado com sucesso!")

        elif form_type == 'revenda' and current_user.tipo == 'admin':
            username = request.form['username']
            password = request.form['password']
            novo = User(
                username=username,
                password=generate_password_hash(password),
                tipo='revenda',
                nome=request.form['nome'],
                telefone=request.form['telefone'],
                email=request.form['email'],
                cpf_cnpj=request.form['cpf_cnpj'],
                endereco=request.form['endereco'],
                cidade=request.form['cidade'],
                uf=request.form['uf']
            )
            db.session.add(novo)
            db.session.commit()
            flash("Revenda criada com sucesso!")

        return redirect(url_for('admin_painel'))

    if current_user.tipo == 'admin':
        users = User.query.order_by(User.id).all()
    else:
        users = User.query.filter_by(revenda_id=current_user.id).order_by(User.id).all()

    return render_template(
        'admin_painel.html',
        users=users,
        current_user=current_user
    )

@app.route('/admin/usuarios/editar/<int:user_id>', methods=['GET', 'POST'])
@login_required
def editar_usuario(user_id):
    user = db.session.get(User, int(user_id))  # Alterado para db.session.get()
    if not user:
        flash("Usuário não encontrado.")
        return redirect('/admin/painel')

    if current_user.tipo not in ['admin', 'revenda']:
        flash("Acesso não autorizado. Somente administradores ou revendas podem editar usuários.")
        return redirect('/dashboard')

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        nome = request.form['nome']
        telefone = request.form['telefone']
        email = request.form['email']
        cpf_cnpj = request.form['cpf_cnpj']
        endereco = request.form['endereco']
        cidade = request.form['cidade']
        uf = request.form['uf']

        if password:
            user.password = generate_password_hash(password)
        
        user.username = username
        user.nome = nome
        user.telefone = telefone
        user.email = email
        user.cpf_cnpj = cpf_cnpj
        user.endereco = endereco
        user.cidade = cidade
        user.uf = uf

        db.session.commit()

        flash("Usuário atualizado com sucesso!")
        return redirect('/admin/painel')

    return render_template('editar_usuario.html', user=user)

@app.route('/admin/usuarios/deletar/<int:user_id>', methods=['POST'])
@login_required
def deletar_usuario(user_id):
    user_to_delete = db.session.get(User, int(user_id))  # Alterado para db.session.get()
    if not user_to_delete:
        flash("Usuário não encontrado.")
        return redirect('/admin/painel')

    if current_user.id == user_to_delete.id:
        flash("Você não pode excluir a sua própria conta.")
        return redirect('/admin/painel')

    db.session.delete(user_to_delete)
    db.session.commit()

    flash("Usuário excluído com sucesso.")
    return redirect('/admin/painel')

@app.route('/config', methods=['GET', 'POST'])
@login_required
def config():
    user_id = current_user.id
    config = ConfigData.query.filter_by(user_id=user_id).first()

    carro = VehicleType.query.filter_by(type='Carro', user_id=user_id).first()
    moto = VehicleType.query.filter_by(type='Moto', user_id=user_id).first()

    if request.method == 'POST':
        if not config:
            config = ConfigData(user_id=user_id)

        config.company_name = request.form['company_name']
        config.address = request.form['address']
        config.city = request.form['city']
        config.phone = request.form['phone']
        db.session.add(config)

        # Atualiza valores
        carro_valor = float(request.form['carro_value'])
        moto_valor = float(request.form['moto_value'])

        if not carro:
            carro = VehicleType(type='Carro', hour_value=carro_valor, user_id=user_id)
            db.session.add(carro)
        else:
            carro.hour_value = carro_valor

        if not moto:
            moto = VehicleType(type='Moto', hour_value=moto_valor, user_id=user_id)
            db.session.add(moto)
        else:
            moto.hour_value = moto_valor

        db.session.commit()
        flash("Configurações salvas.")
        return redirect('/dashboard')

    return render_template(
        'config.html',
        config=config,
        carro_value=carro.hour_value if carro else '',
        moto_value=moto.hour_value if moto else ''
    )

@app.route('/entry', methods=['POST'])
@login_required
def entry():
    plate = request.form.get('plate', '').upper()
    vehicle_type = request.form.get('vehicle_type')

    if not plate or not vehicle_type:
        flash("Placa e tipo de veículo são obrigatórios.")
        return redirect('/dashboard')

    if Entry.query.filter_by(plate=plate, user_id=current_user.id).first():
        flash("Veículo já está no pátio.")
        return redirect('/dashboard')

    try:
        entry = Entry(plate=plate, vehicle_type=vehicle_type, user_id=current_user.id)
        db.session.add(entry)
        db.session.commit()
        return generate_pdf_response(plate, entry.entry_time, vehicle_type, entry=True)
    except Exception as e:
        print(f"Erro ao registrar entrada: {e}")
        flash("Erro ao registrar entrada.")
        return redirect('/dashboard')


@app.route('/exit_vehicle/<plate>')
def exit_vehicle(plate):
    user_id = current_user.id

    entry = Entry.query.filter_by(plate=plate, user_id=user_id).first()
    if not entry:
        flash("Veículo não encontrado no pátio.")
        return redirect('/dashboard')

    exit_time = datetime.utcnow()
    duration = (exit_time - entry.entry_time).total_seconds() / 3600.0

    rate = VehicleType.query.filter_by(type=entry.vehicle_type, user_id=user_id).first()
    if not rate:
        flash("Valor por hora não configurado para este tipo de veículo.")
        return redirect('/dashboard')

    total_value = rate.hour_value if duration <= 1 else rate.hour_value + (duration - 1) * rate.hour_value

    saida = Exit(
        plate=plate,
        exit_time=exit_time,
        total_value=total_value,
        duration=duration,
        user_id=user_id
    )
    db.session.add(saida)
    db.session.delete(entry)
    db.session.commit()

    flash(f"Saída registrada com sucesso! Valor: R$ {total_value:.2f}")

    config = ConfigData.query.filter_by(user_id=user_id).first()
    company_name = config.company_name if config else "Nome da Empresa"

    return gerar_pdf_saida(
        plate=plate,
        entry_time=entry.entry_time,
        exit_time=exit_time,
        vehicle_type=entry.vehicle_type,
        total_value=total_value,
        duration=duration,
        company_name=company_name
    )

def gerar_pdf_saida(plate, entry_time, exit_time, vehicle_type, total_value, duration, company_name):
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=(80*mm, 200*mm))  # bobina 80mm, altura ajustável

    c.setFont("Helvetica-Bold", 12)
    c.drawCentredString(40*mm, 180*mm, company_name)  # Centralizado no topo

    c.setFont("Helvetica", 10)
    c.drawString(10*mm, 160*mm, f"Placa: {plate}")
    c.drawString(10*mm, 145*mm, f"Entrada: {entry_time.strftime('%d/%m/%Y %H:%M:%S')}")
    c.drawString(10*mm, 130*mm, f"Saída: {exit_time.strftime('%d/%m/%Y %H:%M:%S')}")
    c.drawString(10*mm, 115*mm, f"Duração: {duration:.2f} horas")
    c.drawString(10*mm, 100*mm, f"Tipo: {vehicle_type}")
    c.drawString(10*mm, 85*mm, f"Valor Total: R$ {total_value:.2f}")

    c.showPage()
    c.save()
    buffer.seek(0)

    return send_file(
        buffer,
        as_attachment=False,  # inline para abrir no navegador
        download_name=f"{plate}_saida.pdf",
        mimetype='application/pdf'
    )

@app.route("/historico/entradas", endpoint="historico_entradas")
def entradas():
    # busca entradas do usuário
    if not current_user.is_authenticated:
        return redirect('/login')

    entradas = Entry.query.filter_by(user_id=current_user.id).all()
    return render_template("entradas.html", entradas=entradas)

@app.route("/historico/saidas", endpoint="historico_saidas")
def saidas():
    if not current_user.is_authenticated:
        return redirect('/login')

    
    saidas = Exit.query.filter_by(user_id=current_user.id).all()

    # Depuração: Verificando todos os valores das saídas
    print("Saídas encontradas no banco de dados:")
    for saida in saidas:
        print(f"Placa: {saida.plate}, Valor: R$ {saida.total_value}")

    # Calculando o valor total das saídas
    total_value = sum([saida.total_value for saida in saidas])

    print(f"Valor total das saídas: R$ {total_value:.2f}")

    return render_template("saidas.html", saidas=saidas, total_value=total_value)

@app.route('/saida/personalizada', methods=['POST'])
def exit_vehicle_custom():
    if 'user_id' not in session:
        return redirect('/login')

    user_id = current_user.id
    plate = request.form['plate'].upper()
    custom_value = float(request.form['custom_value'])

    entry = Entry.query.filter_by(plate=plate, user_id=user_id).first()
    if not entry:
        flash("Veículo não encontrado no pátio.")
        return redirect(url_for('dashboard'))

    exit_time = datetime.utcnow()
    duration = (exit_time - entry.entry_time).total_seconds() / 3600.0

    db.session.add(Exit(
        plate=plate,
        exit_time=exit_time,
        total_value=custom_value,
        duration=duration,
        user_id=user_id
    ))
    db.session.delete(entry)
    db.session.commit()

    return generate_pdf_response(plate, exit_time, entry.vehicle_type, total_value=custom_value, entry=False, entry_time=entry.entry_time)

def generate_pdf_response(plate, time, vehicle_type, total_value=None, entry=True, entry_time=None):
    buffer = BytesIO()
    user_id = session.get('user_id')
    config = ConfigData.query.filter_by(user_id=user_id).first()

    c = canvas.Canvas(buffer, pagesize=(400, 300))
    c.setFont("Helvetica", 10)
    c.drawCentredString(200, 280, "Estacionamento - " + ("Entrada" if entry else "Saída"))

    if config:
        c.drawCentredString(200, 260, config.company_name or "")
        c.drawCentredString(200, 245, f"{config.address or ''}, {config.city or ''}")
        c.drawCentredString(200, 230, f"Telefone: {config.phone or ''}")

    c.drawCentredString(200, 200, f"Placa: {plate}")
    c.drawCentredString(200, 185, f"Tipo: {vehicle_type}")
    
    if entry:
        c.drawCentredString(200, 165, f"Entrada: {time.strftime('%d/%m/%Y %H:%M')}")  # Formatação da data
    else:
        c.drawCentredString(200, 165, f"Entrada: {entry_time.strftime('%d/%m/%Y %H:%M')}")
        c.drawCentredString(200, 150, f"Saída: {time.strftime('%d/%m/%Y %H:%M')}")
        c.drawCentredString(200, 135, f"Valor: R$ {total_value:.2f}")

    c.showPage()
    c.save()
    buffer.seek(0)

    response = send_file(
        buffer,
        as_attachment=False,
        download_name=f"{plate}_{'entrada' if entry else 'saida'}.pdf",
        mimetype='application/pdf'
    )

    # Forçando o PDF a abrir na janela do navegador (em uma nova aba)
    response.headers['Content-Disposition'] = 'inline; filename=' + f"{plate}_{'entrada' if entry else 'saida'}.pdf"
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'

    return response

@app.before_request
def require_login():
    if not current_user.is_authenticated and request.endpoint not in ('login', 'register', 'static'):
        return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
from flask import Flask, render_template, request, redirect, url_for, session, flash, send_file
from models import db, User, ConfigData, Entry, Exit, VehicleType
from config import Config
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from io import BytesIO
from reportlab.pdfgen import canvas
from flask_migrate import Migrate

app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)
migrate = Migrate(app, db)

# Criação de tabelas e inserção de dados iniciais
with app.app_context():
    db.create_all()
    if not VehicleType.query.filter_by(type='Carro').first():
        db.session.add(VehicleType(type='Carro', hour_value=5.0))
        db.session.add(VehicleType(type='Moto', hour_value=3.0))
        db.session.commit()

# Redirecionamento para login ou dashboard
@app.route('/')
def index():
    if 'user_id' in session:
        return redirect('/dashboard')
    return redirect('/login')

# Login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            return redirect('/dashboard')
        else:
            flash("Usuário ou senha inválidos.")
            return redirect('/login')

    return render_template('login.html')

# Registro
@app.route('/register', methods=['GET', 'POST'])
def register():
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

# Dashboard
@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect('/login')
    entries = Entry.query.all()
    now_time = datetime.utcnow()
    return render_template('dashboard.html', entries=entries, now=now_time)

@app.route('/entry', methods=['POST'])
def entry():
    if 'user_id' not in session:
        return redirect('/login')

    user_id = session['user_id']
    plate = request.form['plate'].upper()
    vehicle_type = request.form['vehicle_type']

    # Verificar se o veículo já está no pátio para este usuário
    if Entry.query.filter_by(plate=plate, user_id=user_id).first():
        flash("Veículo já está no pátio.")
        return redirect('/dashboard')

    entry = Entry(plate=plate, vehicle_type=vehicle_type, user_id=user_id)
    db.session.add(entry)
    db.session.commit()

    return generate_pdf_response(plate, entry.entry_time, vehicle_type, entry=True)

# Saída de veículo
@app.route('/exit/<plate>', methods=['GET'])
def exit_vehicle(plate):
    if 'user_id' not in session:
        return redirect('/login')

    user_id = session['user_id']
    entry = Entry.query.filter_by(plate=plate, user_id=user_id).first()

    if entry:
        entry_time = entry.entry_time
        exit_time = datetime.utcnow()
        duration = (exit_time - entry_time).total_seconds() / 3600.0

        rate = VehicleType.query.filter_by(type=entry.vehicle_type, user_id=user_id).first()
        value = rate.hour_value
        total_value = value if duration <= 1 else value + (duration - 1) * value

        db.session.add(Exit(plate=plate, exit_time=exit_time, total_value=total_value, duration=duration, user_id=user_id))
        db.session.delete(entry)
        db.session.commit()

        return generate_pdf_response(plate, exit_time, entry.vehicle_type, total_value=total_value, entry=False)

    flash("Placa não encontrada.")
    return redirect('/dashboard')

@app.route('/config', methods=['GET', 'POST'])
def config():
    if 'user_id' not in session:
        return redirect('/login')

    user_id = session['user_id']
    config = ConfigData.query.filter_by(user_id=user_id).first()

    if request.method == 'POST':
        if not config:
            config = ConfigData(user_id=user_id)

        config.company_name = request.form['company_name']
        config.address = request.form['address']
        config.city = request.form['city']
        config.phone = request.form['phone']
        db.session.add(config)

        carro_val = float(request.form['car_value'])
        moto_val = float(request.form['moto_value'])

        # Atualiza valores de veículo do usuário
        VehicleType.query.filter_by(user_id=user_id, type='Carro').update({'hour_value': carro_val})
        VehicleType.query.filter_by(user_id=user_id, type='Moto').update({'hour_value': moto_val})

        db.session.commit()

        flash("Configurações salvas.")
        return redirect('/dashboard')

    return render_template('config.html', config=config)

# Gerador de PDF (entrada e saída)
def generate_pdf_response(plate, time, vehicle_type, total_value=None, entry=True):
    buffer = BytesIO()
    config = ConfigData.query.first()

    c = canvas.Canvas(buffer, pagesize=(400, 300))
    c.setFont("Helvetica", 10)
    c.drawCentredString(200, 280, "Estacionamento - " + ("Entrada" if entry else "Saída"))

    if config:
        c.drawCentredString(200, 260, config.company_name or "")
        c.drawCentredString(200, 240, f"{config.address or ''}, {config.city or ''}")
        c.drawCentredString(200, 220, f"Telefone: {config.phone or ''}")

    c.drawCentredString(200, 180, f"Placa: {plate}")
    c.drawCentredString(200, 160, f"Tipo: {vehicle_type}")
    c.drawCentredString(200, 140, f"Data/Hora: {time.strftime('%Y-%m-%d %H:%M:%S')}")

    if total_value is not None:
        c.drawCentredString(200, 120, f"Valor: R$ {total_value:.2f}")

    c.showPage()
    c.save()
    buffer.seek(0)

    return send_file(
        buffer,
        as_attachment=False,
        download_name=f'{plate}_{"entrada" if entry else "saida"}.pdf',
        mimetype='application/pdf'
    )

# Verificação de login para rotas protegidas
@app.before_request
def require_login():
    if not session.get("user_id") and request.endpoint not in ('login', 'register', 'static'):
        return redirect(url_for('login'))

# Logout
@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')

# Histórico de entradas
@app.route('/historico/entradas')
def historico_entradas():
    entries = Entry.query.all()
    return render_template('historico_entradas.html', entries=entries)

# Histórico de saídas
@app.route("/historico/saidas")
def saidas():
    # Exemplo: recuperar as saídas do banco de dados
    saidas = db.session.query(Saida).all()  # ou o nome correto do seu modelo
    return render_template("saidas.html", saidas=saidas)

@app.route('/saida/personalizada', methods=['POST'])
def exit_vehicle_custom():
    plate = request.form['plate']
    custom_value = request.form['custom_value']
    # Aqui você coloca a lógica para registrar a saída com valor personalizado
    # ...
    flash(f"Saída registrada com valor personalizado para {plate}: R$ {custom_value}")
    return redirect(url_for('dashboard'))

# Inicialização do servidor
if __name__ == '__main__':
    app.run(debug=True)

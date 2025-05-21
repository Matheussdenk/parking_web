from flask import Flask, render_template, request, redirect, url_for, session, flash, send_file
from models import db, User, ConfigData, Entry, Exit, VehicleType
from models import User  # Supondo que o modelo User esteja no arquivo models.py
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
            if not user.is_active:
                flash("Seu usuário está inativo. Contate o administrador.", "danger")
                return redirect('/login')

            session['user_id'] = user.id
            return redirect('/dashboard')

        flash('Usuário ou senha inválidos.', 'danger')

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

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect('/login')
    user_id = session['user_id']
    entries = Entry.query.filter_by(user_id=user_id).all()
    now_time = datetime.utcnow()
    return render_template('dashboard.html', entries=entries, now=now_time)

@app.route('/admin/painel')
def admin_painel():
    user_id = session.get('user_id')
    print("Usuário ID na sessão:", user_id)

    if not user_id:
        flash("Sessão expirada.")
        return redirect('/login')

    user = User.query.get(user_id)
    print("Usuário encontrado:", user.username if user else "Nenhum")
    print("É admin?", user.is_admin if user else "N/A")

    if not user or not user.is_admin:
        flash("Acesso restrito a administradores.")
        return redirect('/dashboard')

    users = User.query.all()
    return render_template('admin_painel.html', users=users)

@app.route('/admin/usuarios/criar', methods=['POST'])
def criar_usuario():
    username = request.form['username']
    password = request.form['password']
    
    # Verifique se o nome de usuário já existe
    existing_user = User.query.filter_by(username=username).first()
    if existing_user:
        flash("O nome de usuário já está em uso. Escolha outro.")
        return redirect('/admin/painel')
    
    # Crie o novo usuário
    new_user = User(username=username, password=generate_password_hash(password), is_admin=False)
    
    # Adicione e commit
    db.session.add(new_user)
    db.session.commit()

    flash("Usuário criado com sucesso.")
    return redirect('/admin/painel')

@app.route('/admin/usuarios/editar/<int:user_id>', methods=['GET', 'POST'])
def editar_usuario(user_id):
    current_user = User.query.get(session.get('user_id'))  # Verifica se o usuário está logado e se é admin
    if not current_user or not current_user.is_admin:
        flash("Acesso não autorizado.")
        return redirect('/dashboard')

    user = User.query.get(user_id)  # Busca o usuário a ser editado
    if not user:
        flash("Usuário não encontrado.")
        return redirect('/admin/painel')

    if request.method == 'POST':
        new_username = request.form['username']
        
        # Verifica se o novo nome de usuário já existe e não é o mesmo do usuário atual
        existing_user = User.query.filter_by(username=new_username).first()
        if existing_user and existing_user.id != user.id:
            flash("O nome de usuário já está em uso. Escolha outro.")
            return redirect(url_for('editar_usuario', user_id=user.id))

        # Atualiza o nome de usuário
        user.username = new_username
        
        # Atualiza a senha, se fornecida
        if request.form['password']:
            user.password = generate_password_hash(request.form['password'])
        
        # Atualiza o status de administrador
        user.is_admin = True if request.form.get('is_admin') == 'on' else False
        
        # Atualiza o status de ativação/desativação
        user.is_active = True if request.form.get('is_active') == 'on' else False

        # Salva as alterações no banco de dados
        db.session.commit()
        flash("Usuário atualizado com sucesso.")
        return redirect('/admin/painel')

    return render_template('editar_usuario.html', user=user)

@app.route('/admin/usuarios/deletar/<int:user_id>', methods=['POST'])
def deletar_usuario(user_id):
    current_user = User.query.get(session.get('user_id'))
    if not current_user or not current_user.is_admin:
        flash("Acesso não autorizado.")
        return redirect('/dashboard')

    user_to_delete = User.query.get(user_id)
    if not user_to_delete:
        flash("Usuário não encontrado.")
        return redirect('/admin/painel')

    # Excluindo o usuário
    db.session.delete(user_to_delete)
    db.session.commit()

    # Reindexando os IDs após exclusão
    try:
        db.session.execute(text("""
            WITH updated AS (
                SELECT id, row_number() OVER (ORDER BY id) AS new_id
                FROM "user"
            )
            UPDATE "user" u
            SET id = updated.new_id
            FROM updated
            WHERE u.id = updated.id;
        """))
        db.session.commit()

        flash("Usuário excluído com sucesso e IDs reindexados.")
    except Exception as e:
        db.session.rollback()
        flash(f"Erro ao reindexar os IDs: {str(e)}")

    return redirect('/admin/painel')

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

        # Atualiza ou cria valores de hora para carros e motos para esse usuário
        for tipo in ['Carro', 'Moto']:
            valor = float(request.form[f'{tipo.lower()}_value'])
            vt = VehicleType.query.filter_by(type=tipo, user_id=user_id).first()
            if not vt:
                vt = VehicleType(type=tipo, hour_value=valor, user_id=user_id)
                db.session.add(vt)
            else:
                vt.hour_value = valor

        db.session.commit()

        flash("Configurações salvas.")
        return redirect('/dashboard')

    return render_template('config.html', config=config)

@app.route('/entry', methods=['POST'])
def entry():
    if 'user_id' not in session:
        return redirect('/login')

    user_id = session['user_id']
    plate = request.form['plate'].upper()
    vehicle_type = request.form['vehicle_type']

    if Entry.query.filter_by(plate=plate, user_id=user_id).first():
        flash("Veículo já está no pátio.")
        return redirect('/dashboard')

    entry = Entry(plate=plate, vehicle_type=vehicle_type, user_id=user_id)
    db.session.add(entry)
    db.session.commit()

    return generate_pdf_response(plate, entry.entry_time, vehicle_type, entry=True)

@app.route('/exit/<plate>', methods=['GET'])
def exit_vehicle(plate):
    if 'user_id' not in session:
        return redirect('/login')

    user_id = session['user_id']
    entry = Entry.query.filter_by(plate=plate, user_id=user_id).first()

    if entry:
        entry_time = entry.entry_time
        exit_time = datetime.utcnow()

        # Calculando a duração em horas
        duration = (exit_time - entry.entry_time).total_seconds() / 3600.0

        # Verificando se o valor por hora está configurado corretamente
        rate = VehicleType.query.filter_by(type=entry.vehicle_type, user_id=user_id).first()

        if not rate:
            flash("Valor por hora não configurado.")
            return redirect('/dashboard')

        # Calculando o valor total
        value = rate.hour_value
        total_value = value if duration <= 1 else value + (duration - 1) * value

        # Debug: Verificar valores calculados
        print(f"Duração: {duration:.2f} horas")
        print(f"Valor por hora: R$ {value:.2f}")
        print(f"Valor total calculado: R$ {total_value:.2f}")

        # Registrar a saída no banco de dados
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

        return generate_pdf_response(plate, exit_time, entry.vehicle_type, total_value=total_value, entry=False, entry_time=entry.entry_time)

    flash("Placa não encontrada.")
    return redirect('/dashboard')

# Rota para exibir o histórico de saídas
@app.route("/historico/saidas")
def saidas():
    user_id = session.get('user_id')
    if not user_id:
        return redirect('/login')

    # Busca todas as saídas do usuário
    saidas = Exit.query.filter_by(user_id=user_id).all()

    # Depuração: Verificando todos os valores das saídas
    print("Saídas encontradas no banco de dados:")
    for saida in saidas:
        print(f"Placa: {saida.plate}, Valor: R$ {saida.total_value:.2f}")

    # Calculando o valor total das saídas
    total_value = sum([saida.total_value for saida in saidas])

    # Depuração: Exibindo o valor total calculado
    print(f"Valor total das saídas: R$ {total_value:.2f}")

    return render_template("saidas.html", saidas=saidas, total_value=total_value)

@app.route("/historico/entradas", endpoint="historico_entradas")
def entradas():
    # busca entradas do usuário
    user_id = session.get('user_id')
    if not user_id:
        return redirect('/login')
    entradas = Entry.query.filter_by(user_id=user_id).all()
    return render_template("entradas.html", entradas=entradas)

@app.route("/historico/saidas", endpoint="historico_saidas")
def saidas():
    user_id = session.get('user_id')
    if not user_id:
        return redirect('/login')
    
    saidas = Exit.query.filter_by(user_id=user_id).all()

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

    user_id = session['user_id']
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
        c.drawCentredString(200, 165, f"Entrada: {time.strftime('%d/%m/%Y %H:%M')}")
    else:
        c.drawCentredString(200, 165, f"Entrada: {entry_time.strftime('%d/%m/%Y %H:%M')}")
        c.drawCentredString(200, 150, f"Saída: {time.strftime('%d/%m/%Y %H:%M')}")
        c.drawCentredString(200, 135, f"Valor: R$ {total_value:.2f}")

    c.showPage()
    c.save()
    buffer.seek(0)

    return send_file(buffer, as_attachment=False, download_name=f"{plate}_{'entrada' if entry else 'saida'}.pdf", mimetype='application/pdf')

@app.before_request
def require_login():
    if not session.get("user_id") and request.endpoint not in ('login', 'register', 'static'):
        return redirect(url_for('login'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')

if __name__ == '__main__':
    app.run(debug=True)
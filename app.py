from flask import Flask, flash, render_template, request, redirect, session, url_for
import pyrebase
import firebase_admin
import json
import os
from firebase_admin import credentials, firestore, storage, initialize_app
from datetime import datetime

# =========================
# CONFIGURAÇÃO DO FLASK
# =========================
app = Flask(__name__)
app.secret_key = "chave-secreta-simples"  # essencial para sessão

# =========================
# CONFIGURAÇÃO DO FIREBASE (pyrebase)
# =========================
firebase_config = {
    "apiKey": "AIzaSyCsAAPnHNnwtEVZFG7FSF-p_IfbqIcVJbk",
    "authDomain": "flashpoint-0001.firebaseapp.com",
    "projectId": "flashpoint-0001",
    "storageBucket": "flashpoint-0001.firebasestorage.app",
    "messagingSenderId": "1011346360990",
    "appId": "1:1011346360990:web:c061a706143e4eb57dc98f",
    "databaseURL": ""
}

firebase = pyrebase.initialize_app(firebase_config)
auth = firebase.auth()

# =========================
# CONFIGURAÇÃO DO FIREBASE ADMIN (Firestore)
# =========================
firebase_json = os.environ.get("FIREBASE_CREDENTIALS")  # Certifique-se que o nome da variável bate com a do Render
if not firebase_json:
    raise Exception("Variável de ambiente FIREBASE_CREDENTIALS não encontrada!")

cred_dict = json.loads(firebase_json)  # Converte JSON da variável em dicionário
cred = credentials.Certificate(cred_dict)
firebase_admin.initialize_app(cred)
db = firestore.client()
# =========================
# CONFIGURAÇÃO DO FIREBASE ADMIN (Firestore) (TESTE LOCAL)
# =========================
#cred = credentials.Certificate("1x/flashpoint-0001-firebase-adminsdk-fbsvc-aa433fdd0e.json")
#firebase_admin.initialize_app(cred)
#db = firestore.client()

# =========================
# FUNÇÕES AUXILIARES
# =========================

# Função para verificar se o usuário é ADM
def is_admin():
    user_email = session.get("user")
    if not user_email:
        return False
    user_doc = db.collection("usuarios").document(user_email).get()
    if user_doc.exists and user_doc.to_dict().get("role") == "ADM":
        return True
    return False

def get_usuario_logado():
    """Retorna o dicionário do usuário logado pelo UID da sessão"""
    uid = session.get('uid')
    if not uid:
        return None

    usuarios_ref = db.collection('usuarios').where('uid', '==', uid).limit(1).stream()
    for u in usuarios_ref:
        return u.to_dict()
    return None

def get_all_users():
    usuarios = []
    for u in db.collection("usuarios").stream():
        data = u.to_dict()
        data["uid"] = u.id
        usuarios.append(data)
    return usuarios

def get_user_by_id(uid):
    doc = db.collection("usuarios").document(uid).get()
    if doc.exists:
        user = doc.to_dict()
        user["uid"] = doc.id
        return user
    return None


def decimal_para_hhmm(horas_decimal):
    """Converte decimal para hh:mm"""
    h = int(horas_decimal)
    m = int(round((horas_decimal - h) * 60))
    return f"{h:02d}:{m:02d}"

def formatar_data(data_str):
    """Converte data yyyy-mm-dd para dd/mm/aaaa"""
    try:
        dt = datetime.strptime(data_str, "%Y-%m-%d")
        return dt.strftime("%d/%m/%Y")
    except:
        return data_str
    

def formatar_data_pedido(data_str):
    """
    Converte string do Firestore como:
    "19 de janeiro de 2026 às 21:35:39 UTC+1"
    para "19/01/2026 21:35"
    """
    try:
        # separar data e hora
        if " às " in data_str:
            data_part, hora_part = data_str.split(" às ")
            hora_part = hora_part.split(" ")[0]  # remove UTC+1
        else:
            data_part = data_str
            hora_part = "00:00:00"

        # mapear meses em português para número
        meses = {
            "janeiro": "01",
            "fevereiro": "02",
            "março": "03",
            "abril": "04",
            "maio": "05",
            "junho": "06",
            "julho": "07",
            "agosto": "08",
            "setembro": "09",
            "outubro": "10",
            "novembro": "11",
            "dezembro": "12"
        }

        # separar dia, mês por extenso e ano
        partes = data_part.strip().split(" de ")
        dia = partes[0].zfill(2)
        mes = meses[partes[1].lower()]
        ano = partes[2]

        # formar datetime
        dt = datetime.strptime(f"{dia}/{mes}/{ano} {hora_part}", "%d/%m/%Y %H:%M:%S")
        return dt.strftime("%d/%m/%Y %H:%M")
    except Exception as e:
        print("Erro ao formatar data:", e)
        return data_str


# =========================
# ROTAS
# =========================

# LOGIN
@app.route("/", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        try:
            user = auth.sign_in_with_email_and_password(email, password)
            session["uid"] = user["localId"]  # Armazena somente UID
            return redirect("/home")
        except:
            error = "Email ou senha inválidos"
    return render_template("login.html", error=error)

# REGISTRO

@app.route("/register", methods=["GET", "POST"])
def register_usuario():
    error = None
    success = None
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        nome = request.form.get("nome")
        sobrenome = request.form.get("sobrenome")
        try:
            user = auth.create_user_with_email_and_password(email, password)
            uid = user["localId"]
            # Salva no Firestore com email
            db.collection("usuarios").document(uid).set({
                "uid": uid,
                "nome": nome,
                "sobrenome": sobrenome,
                "email": email,        # <---- aqui
                "data_nascimento": "",
                "pais": "",
                "tipo": "usuario"  # padrão: usuário comum
            })
            success = "Utente creato con successo! Effettua il login."
        except Exception as e:
            error = str(e)
    return render_template("register.html", error=error, success=success)


# HOME
@app.route("/home")
def home():
    if "uid" not in session:
        return redirect("/")

    uid = session["uid"]
    usuario_doc = db.collection("usuarios").document(uid).get()
    
    if usuario_doc.exists:
        usuario = usuario_doc.to_dict()
    else:
        usuario = {"nome": "Non registrato", "sobrenome": "Non registrato", "tipo": "usuario", "email": "Non registrato"}

    # Garantir que email do Firestore esteja disponível
    usuario["email"] = usuario.get("email", "Non disponibile")

    # Verifica se o usuário é ADM
    is_admin = usuario.get("role") == "ADM"  # ou "tipo" == "admin" se seu Firestore usa esse campo

    return render_template("home.html", usuario=usuario, is_admin=is_admin)



# PERFIL
@app.route("/perfil", methods=["GET", "POST"])
def perfil_usuario():
    if "uid" not in session:
        return redirect("/")
    uid = session["uid"]
    usuario_ref = db.collection("usuarios").document(uid)
    usuario_doc = usuario_ref.get()
    usuario = usuario_doc.to_dict() if usuario_doc.exists else {}

    if request.method == "POST":
        # Atualiza todos os campos, incluindo os novos
        usuario_ref.update({
            "nome": request.form.get("nome"),
            "sobrenome": request.form.get("sobrenome"),
            "data_nascimento": request.form.get("data_nascimento"),
            "pais": request.form.get("pais"),
            "data_assuncao": request.form.get("data_assuncao"),
            "cargo": request.form.get("cargo"),
            "foto_url": request.form.get("foto_url")  # opcional
        })
        return redirect("/home")

    return render_template("perfil.html", usuario=usuario)


# REGISTRAR PONTO
@app.route("/registrar_ponto", methods=["GET", "POST"])
def registrar_ponto_usuario():
    if "uid" not in session:
        return redirect("/")

    uid = session["uid"]
    usuario_doc = db.collection("usuarios").document(uid).get()
    usuario = usuario_doc.to_dict() if usuario_doc.exists else {"nome": "Desconhecido"}

    # Buscar locais do Firestore
    locais_docs = db.collection("locais").stream()
    locais = ["-"] + [doc.to_dict()["nome"] for doc in locais_docs]  # adiciona "-" como opção padrão

    mensagem = None
    if request.method == "POST":
        data_ponto = request.form.get("data")

        # Verificar duplicidade
        pontos_existentes = db.collection("pontos").where("uid", "==", uid).where("data", "==", data_ponto).stream()
        if any(pontos_existentes):
            mensagem = f"Hai già registrato una presenza per {data_ponto}!"
        else:
            ponto_data = {
                "uid": uid,
                "nome": usuario["nome"],
                "local": request.form.get("local"),
                "data": data_ponto,
                "horas": float(request.form.get("horas")),
                "notas": request.form.get("notas")
            }
            db.collection("pontos").add(ponto_data)
            mensagem = "Ora registrata con successo!"

    return render_template("registrar_ponto.html", locais=locais, mensagem=mensagem)


# MEUS PONTOS
@app.route("/meus_pontos", methods=["GET", "POST"])
def meus_pontos_usuario():
    if "uid" not in session:
        return redirect("/")

    uid = session["uid"]
    pontos_ref = db.collection("pontos").where("uid", "==", uid)

    filtro_data = request.form.get("filtro_data") if request.method == "POST" else None
    filtro_mes = request.form.get("filtro_mes") if request.method == "POST" else None

    pontos_list = []

    for p in pontos_ref.stream():
        dados = p.to_dict()
        if not dados:
            continue

        # Filtro por data
        if filtro_data and dados.get("data") != filtro_data:
            continue

        # Filtro por mês
        if filtro_mes and not dados.get("data", "").startswith(filtro_mes):
            continue

        dados["id"] = p.id
        dados["horas_hhmm"] = decimal_para_hhmm(float(dados.get("horas", 0)))
        dados["data_formatada"] = formatar_data(dados.get("data", "-"))

        pontos_list.append(dados)

    # Ordena por data (mais recente primeiro)
    pontos_list.sort(
        key=lambda p: p.get("data", ""),
        reverse=True
    )

    total_decimal = sum(float(p.get("horas", 0)) for p in pontos_list)
    total_hhmm = decimal_para_hhmm(total_decimal)

    return render_template(
        "meus_pontos.html",
        pontos=pontos_list,
        filtro_data=filtro_data,
        filtro_mes=filtro_mes,
        total_horas=total_hhmm
    )

# ADMIN PONTOS
@app.route("/admin_pontos", methods=["GET", "POST"])
def admin_pontos():
    usuario = get_usuario_logado()
    if not usuario:
        return redirect("/")
    if usuario.get("tipo") != "admin":
        return "Accesso negato!"

    # Filtros
    filtro_usuario = request.form.get("filtro_usuario") if request.method == "POST" else None
    filtro_mes = request.form.get("filtro_mes") if request.method == "POST" else None

    pontos_ref = db.collection("pontos").stream()
    pontos_list = []
    total_horas = 0.0  # 👈 TOTAL DE HORAS

    for ponto in pontos_ref:
        dados = ponto.to_dict()
        if not dados:
            continue

        uid_dono = dados.get("uid")
        if not uid_dono:
            continue

        dono_doc = db.collection("usuarios").document(uid_dono).get()
        if not dono_doc.exists:
            continue
        dono = dono_doc.to_dict()

        # Filtro usuário
        if filtro_usuario and filtro_usuario != uid_dono:
            continue

        # Filtro mês
        if filtro_mes and not dados.get("data", "").startswith(filtro_mes):
            continue

        horas = float(dados.get("horas", 0))
        total_horas += horas  # 👈 SOMA AQUI

        pontos_list.append({
            "id": ponto.id,
            "usuario_nome": f"{dono.get('nome','')} {dono.get('sobrenome','')}".strip(),
            "uid": uid_dono,
            "local": dados.get("local", "-"),
            "data_formatada": formatar_data(dados.get("data", "-")),
            "horas_formatadas": decimal_para_hhmm(horas),
            "notas": dados.get("notas", "-")
        })

    # Ordena por data (mais recente)
    pontos_list.sort(
        key=lambda x: datetime.strptime(x['data_formatada'], "%d/%m/%Y")
        if x['data_formatada'] != '-' else datetime.min,
        reverse=True
    )

    # Lista usuários para filtro
    usuarios_list = []
    for u in db.collection("usuarios").stream():
        u_data = u.to_dict()
        usuarios_list.append({
            "uid": u.id,
            "nome": f"{u_data.get('nome','')} {u_data.get('sobrenome','')}"
        })

    return render_template(
        "admin_pontos.html",
        pontos=pontos_list,
        usuarios=usuarios_list,
        filtro_usuario=filtro_usuario,
        filtro_mes=filtro_mes,
        total_horas=decimal_para_hhmm(total_horas)  # 👈 ENVIA TOTAL
    )



# EDITAR PONTO (ADMIN)
@app.route("/editar_ponto/<id>", methods=["GET", "POST"])
def editar_ponto_admin(id):
    if "uid" not in session:
        return redirect("/")

    uid = session["uid"]

    # Busca usuário logado
    usuario_doc = db.collection("usuarios").document(uid).get()
    usuario = usuario_doc.to_dict() if usuario_doc.exists else {}

    if not usuario:
        return redirect("/")

    # Busca ponto
    ponto_ref = db.collection("pontos").document(id)
    ponto_doc = ponto_ref.get()

    if not ponto_doc.exists:
        return "Ponto não encontrado"

    ponto = ponto_doc.to_dict()

    # 🔐 SEGURANÇA
    # Se NÃO for admin, só pode editar ponto próprio
    if usuario.get("tipo") != "admin":
        if ponto.get("uid") != uid:
            return "Acesso negado!"

    # POST → salva edição
    if request.method == "POST":
        ponto_ref.update({
            "data": request.form.get("data"),
            "local": request.form.get("local"),
            "horas": float(request.form.get("horas")),
            "notas": request.form.get("notas")
        })

        # Redireciona corretamente
        if usuario.get("tipo") == "admin":
            return redirect("/admin_pontos")
        else:
            return redirect("/meus_pontos")

    # 🔥 BUSCA LOCAIS DINAMICAMENTE NO FIRESTORE
    locais_ref = db.collection("locais").stream()
    locais = []

    for l in locais_ref:
        l_data = l.to_dict()
        if l_data and l_data.get("nome"):
            locais.append(l_data["nome"])

    if "-" not in locais:
        locais.insert(0, "-")

    return render_template(
        "editar_ponto.html",
        ponto=ponto,
        locais=locais
    )



@app.route("/excluir_ponto/<id>", methods=["POST"])
def excluir_ponto(id):
    # Verifica login
    if "uid" not in session:
        return redirect("/")

    # Verifica se é admin
    uid = session["uid"]
    usuario_doc = db.collection("usuarios").document(uid).get()
    usuario = usuario_doc.to_dict()
    if usuario.get("tipo") != "admin":
        return "Acesso negado!"

    # Exclui o ponto
    ponto_doc = db.collection("pontos").document(id)
    if ponto_doc.get().exists:
        ponto_doc.delete()

    return redirect("/admin_pontos")

# Página para gerenciar locais (ADM)
@app.route("/adm_locais", methods=["GET", "POST"])
def gerenciar_locais():
    usuario = get_usuario_logado()
    if not usuario:
        return redirect("/")
    if usuario.get("tipo") != "admin":   # verifica tipo igual ao admin_pontos
        return "Accesso negato!"         # retorna string simples

    if request.method == "POST":
        novo_local = request.form.get("novo_local", "").strip()
        if novo_local:
            db.collection("locais").add({"nome": novo_local})
            return redirect(url_for("gerenciar_locais"))

    locais_docs = db.collection("locais").stream()
    locais = [doc.to_dict().get("nome","-") for doc in locais_docs]

    return render_template("admin_locais.html", locais=locais)


@app.route("/excluir_local", methods=["POST"])
def excluir_local():
    usuario = get_usuario_logado()
    if not usuario or usuario.get("tipo") != "admin":
        return "Accesso negato!"

    nome = request.form.get("nome")
    if nome:
        locais_ref = db.collection("locais").where("nome", "==", nome).stream()
        for doc in locais_ref:
            db.collection("locais").document(doc.id).delete()
    return redirect(url_for("gerenciar_locais"))

# =========================
# LISTAR USUÁRIOS PARA CARTÃO (ADMIN)
# =========================
@app.route("/admin/cartoes", methods=["GET"])
def admin_cartoes():
    usuario = get_usuario_logado()
    if not usuario or usuario.get("tipo") != "admin":
        return "Acesso negado!"

    usuarios = get_all_users()
    return render_template("admin_cartoes.html", usuarios=usuarios)


# =========================
# GERAR CARTÃO (ADMIN)
# =========================
@app.route("/admin/cartoes/gerar/<uid>", methods=["GET"])
def gerar_cartao(uid):
    usuario_logado = get_usuario_logado()
    if not usuario_logado or usuario_logado.get("tipo") != "admin":
        return "Acesso negado!"

    usuario = get_user_by_id(uid)
    if not usuario:
        return "Usuário não encontrado"

    # Valida campos obrigatórios
    campos_obrigatorios = ["nome", "sobrenome", "data_nascimento", "pais", "data_assuncao", "cargo"]
    if not all(usuario.get(campo) for campo in campos_obrigatorios):
        return "Perfil incompleto. Não é possível gerar o cartão."

    return render_template("cartao_reconhecimento.html", user=usuario)

# =========================
# GERAR CARTÃO (USUÁRIO LOGADO)
# =========================
@app.route("/perfil/cartao", methods=["GET"])
def gerar_cartao_perfil():
    usuario = get_usuario_logado()
    if not usuario:
        return redirect("/")

    # Campos obrigatórios para gerar o cartão
    campos_obrigatorios = [
        "nome",
        "sobrenome",
        "data_nascimento",
        "pais",
        "data_assuncao",
        "cargo"
    ]

    # Verifica se todos os campos obrigatórios estão preenchidos
    if not all(usuario.get(campo) for campo in campos_obrigatorios):
        # Redireciona para perfil com aviso de perfil incompleto
        return redirect(url_for("perfil_usuario", incompleto=1))

    return render_template(
        "cartao_reconhecimento.html",
        user=usuario
    )



from datetime import datetime
from google.cloud import firestore

@app.route("/pedido/novo", methods=["GET", "POST"])
def novo_pedido():
    if "uid" not in session:
        return redirect("/")

    uid = session["uid"]

    # 🔹 Busca o usuário no Firestore
    usuario_doc = db.collection("usuarios").document(uid).get()
    usuario = usuario_doc.to_dict() if usuario_doc.exists else {}

    pedidos_ref = db.collection("pedidos")
    
    # Envio do pedido
    if request.method == "POST":
        pedido = {
            "user_id": uid,
            "nome": f"{usuario.get('nome','')} {usuario.get('sobrenome','')}",
            "tipo": request.form["tipo"],
            "mensagem": request.form["mensagem"],
            "status": "pendente",
            "atendido": False,
            "criado_em": firestore.SERVER_TIMESTAMP
        }
        pedidos_ref.add(pedido)
        return redirect(url_for("novo_pedido"))

    # 🔹 Busca todos os pedidos do usuário atual
    pedidos_docs = pedidos_ref.where("user_id", "==", uid).order_by("criado_em", direction=firestore.Query.DESCENDING).stream()
    pedidos = []
    for doc in pedidos_docs:
        data = doc.to_dict()
        data["id"] = doc.id
        pedidos.append(data)

    return render_template(
        "pedido_novo.html",
        pedidos=pedidos,
        formatar_data_pedido=formatar_data_pedido
    )



from datetime import datetime

def formatar_data_pedido(timestamp):
    """Formata timestamp do Firebase para dd/mm/aaaa HH:MM"""
    try:
        # Firebase retorna timestamp como objeto datetime
        if isinstance(timestamp, datetime):
            return timestamp.strftime("%d/%m/%Y %H:%M")
        # Caso seja string, tenta converter
        dt = datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S")
        return dt.strftime("%d/%m/%Y %H:%M")
    except:
        return str(timestamp)

@app.route("/admin/pedidos", methods=["GET", "POST"])
def admin_pedidos():
    usuario = get_usuario_logado()
    if not usuario or usuario.get("tipo") != "admin":
        return "Accesso negato!"

    pedidos_ref = db.collection("pedidos")
    
    # Atualização via POST
    if request.method == "POST":
        pedido_id = request.form.get("pedido_id")
        acao = request.form.get("acao")

        if pedido_id and acao:
            pedido_doc = pedidos_ref.document(pedido_id).get()
            if pedido_doc.exists:
                pedido_ref = pedidos_ref.document(pedido_id)
                if acao == "aprovar":
                    pedido_ref.update({"status": "aprovado"})
                elif acao == "recusar":
                    pedido_ref.update({"status": "recusado"})
                elif acao == "atendido":
                    pedido_ref.update({"atendido": True})
                elif acao == "excluir":
                    pedido_ref.delete()
        # após a ação, recarrega os pedidos
        return redirect(url_for("admin_pedidos"))

    # Recupera todos os pedidos
    pedidos_docs = pedidos_ref.stream()
    pedidos = []
    for doc in pedidos_docs:
        data = doc.to_dict()
        data["id"] = doc.id
        pedidos.append(data)

    return render_template(
        "admin_pedidos.html",
        pedidos=pedidos,
        formatar_data_pedido=formatar_data_pedido
    )


    # GET → lista de pedidos
    pedidos_docs = db.collection("pedidos").stream()
    pedidos = []
    for doc in pedidos_docs:
        d = doc.to_dict()
        d["id"] = doc.id
        pedidos.append(d)

    pedidos.sort(key=lambda x: x.get("data_pedido", ""), reverse=True)

    return render_template("admin_pedidos.html", pedidos=pedidos)


@app.route("/admin/pedidos/decidir/<id>", methods=["POST"])
def decidir_pedido(id):
    usuario = get_usuario_logado()
    if not usuario or usuario.get("tipo") != "admin":
        return "Accesso negato!"

    acao = request.form.get("acao")  # aprovar, recusar, atendido
    if not acao:
        return redirect(url_for("admin_pedidos"))

    pedido_ref = db.collection("pedidos").document(id)
    pedido_doc = pedido_ref.get()
    if pedido_doc.exists:
        if acao == "aprovar":
            pedido_ref.update({"status": "aprovado"})
        elif acao == "recusar":
            pedido_ref.update({"status": "recusado"})
        elif acao == "atendido":
            pedido_ref.update({"status": "atendido"})

    return redirect(url_for("admin_pedidos"))




# LOGOUT
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

# =========================
# INICIAR APP
# =========================
if __name__ == "__main__":
    app.run(debug=True)

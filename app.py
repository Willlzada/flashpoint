from flask import Flask, flash, render_template, request, redirect, session, url_for
import pyrebase
import firebase_admin
import json
import os
from firebase_admin import credentials, firestore, storage, initialize_app
from datetime import datetime
from flask import send_file, session, request
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Table, TableStyle, Spacer, Image
)
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from reportlab.lib.units import cm
from io import BytesIO
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
    
@app.context_processor
def inject_usuario():
    if "uid" in session:
        uid = session["uid"]
        usuario_doc = db.collection("usuarios").document(uid).get()
        if usuario_doc.exists:
            return {"usuario": usuario_doc.to_dict()}
    return {"usuario": None}


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

from datetime import datetime
from collections import defaultdict

def horas_por_mes(uid, ano, mes):
    pontos = db.collection("pontos") \
        .where("uid", "==", uid) \
        .stream()

    total = 0

    for p in pontos:
        d = p.to_dict()

        if "data" not in d or "horas" not in d:
            continue

        try:
            data = datetime.strptime(d["data"], "%Y-%m-%d")
        except:
            continue

        if data.year == ano and data.month == mes:
            total += float(d["horas"])

    return round(total, 1)



def ranking_mensal(ano, mes, limite=5):
    pontos = db.collection("pontos").stream()
    ranking = defaultdict(float)
    nomes = {}

    for p in pontos:
        d = p.to_dict()

        if "uid" not in d or "data" not in d or "horas" not in d:
            continue

        try:
            data = datetime.strptime(d["data"], "%Y-%m-%d")
        except:
            continue

        if data.year == ano and data.month == mes:
            ranking[d["uid"]] += float(d["horas"])
            nomes[d["uid"]] = d.get("nome", "Usuário")

    ranking_ordenado = sorted(ranking.items(), key=lambda x: x[1], reverse=True)

    resultado = []
    for uid, horas in ranking_ordenado[:limite]:
        resultado.append({
            "nome": nomes.get(uid, "Usuário"),
            "horas": round(horas, 1)
        })

    return resultado

def horas_por_ano(uid, ano):
    pontos = db.collection("pontos") \
        .where("uid", "==", uid) \
        .stream()

    total = 0

    for p in pontos:
        d = p.to_dict()

        if "data" not in d or "horas" not in d:
            continue

        try:
            data = datetime.strptime(d["data"], "%Y-%m-%d")
        except:
            continue

        if data.year == ano:
            total += float(d["horas"])

    return round(total, 1)



# =========================
# ROTAS
# =========================


from datetime import datetime
from flask import render_template, redirect, session

@app.route("/dashboard")
@app.route("/home")
def dashboard():
    if "uid" not in session:
        return redirect("/")

    uid = session["uid"]
    hoje = datetime.now()

    # Usuário
    usuario_doc = db.collection("usuarios").document(uid).get()
    if not usuario_doc.exists:
        return redirect("/")

    usuario = usuario_doc.to_dict()
    nome_usuario = usuario.get("nome", "Usuário")

    # Horas
    horas_mes_atual = horas_por_mes(uid, hoje.year, hoje.month)

    mes_anterior = hoje.month - 1 if hoje.month > 1 else 12
    ano_anterior = hoje.year if hoje.month > 1 else hoje.year - 1
    horas_mes_anterior = horas_por_mes(uid, ano_anterior, mes_anterior)

    horas_ano = horas_por_ano(uid, hoje.year)

    # Ranking mensal
    ranking = ranking_mensal(hoje.year, hoje.month)

    # Posição do usuário no ranking (CORRIGIDO)
    posicao = "-"
    for i, r in enumerate(ranking):
        if r["nome"] == nome_usuario:
            posicao = i + 1
            break

    return render_template(
        "dashboard.html",
        usuario=usuario,
        horas_mes_atual=horas_mes_atual,
        horas_mes_anterior=horas_mes_anterior,
        horas_ano=horas_ano,
        ranking=ranking,
        posicao=posicao
    )



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

            db.collection("usuarios").document(uid).set({
                "uid": uid,
                "nome": nome,
                "sobrenome": sobrenome,
                "email": email,
                "data_nascimento": "",
                "pais": "",
                "tipo": "usuario"
            })

            success = "Utente creato con successo! Effettua il login."

        except Exception as e:
            erro_str = str(e)

            if "EMAIL_EXISTS" in erro_str:
                error = "Questo email è già registrato. Prova ad effettuare il login."
            elif "WEAK_PASSWORD" in erro_str:
                error = "La password deve avere almeno 6 caratteri."
            elif "INVALID_EMAIL" in erro_str:
                error = "Inserisci un indirizzo email valido."
            else:
                error = "Errore durante la registrazione. Riprova più tardi."

    return render_template("register.html", error=error, success=success)


# HOME
@app.route("/home")
def home():
    if "uid" not in session:
        return redirect("/")

    uid = session["uid"]
    hoje = datetime.now()

    horas_mes_atual = horas_por_mes(uid, hoje.year, hoje.month)

    mes_anterior = hoje.month - 1 or 12
    ano_anterior = hoje.year if hoje.month != 1 else hoje.year - 1
    horas_mes_anterior = horas_por_mes(uid, ano_anterior, mes_anterior)

    horas_ano = horas_por_ano(uid, hoje.year)


    ranking = ranking_mensal(hoje.year, hoje.month)

    # posição do usuário no ranking
    posicao = "-"
    for i, r in enumerate(ranking):
        if r["nome"]:
            posicao = i + 1
            break

    return render_template(
    "home.html",
    horas_mes_atual=horas_mes_atual,
    horas_mes_anterior=horas_mes_anterior,
    horas_ano=horas_ano,
    ranking=ranking,
    posicao=posicao
)




# PERFIL
@app.route("/perfil")
def perfil_usuario():
    if "uid" not in session:
        return redirect("/")

    uid = session["uid"]
    usuario = db.collection("usuarios").document(uid).get().to_dict()

    ano_atual = datetime.now().year
    total_horas_ano = horas_por_ano(uid, ano_atual)

    return render_template(
        "perfil.html",
        usuario=usuario,
        total_horas_ano=total_horas_ano,
        ano_atual=ano_atual
    )


@app.route("/perfil/editar", methods=["GET", "POST"])
def perfil_editar():
    if "uid" not in session:
        return redirect("/")

    uid = session["uid"]
    usuario_ref = db.collection("usuarios").document(uid)
    usuario = usuario_ref.get().to_dict()

    if request.method == "POST":
        usuario_ref.update({
            "nome": request.form.get("nome"),
            "sobrenome": request.form.get("sobrenome"),
            "data_nascimento": request.form.get("data_nascimento"),
            "pais": request.form.get("pais"),
            "data_assuncao": request.form.get("data_assuncao"),
            "cargo": request.form.get("cargo"),
            "foto_url": request.form.get("foto_url")
        })
        return redirect("/perfil")

    return render_template("perfil_editar.html", usuario=usuario)


# REGISTRAR PONTO
from datetime import datetime, timedelta
from flask import render_template, redirect, session, request, url_for

@app.route("/registrar_ponto", methods=["GET", "POST"])
def registrar_ponto_usuario():
    if "uid" not in session:
        return redirect("/")

    uid = session["uid"]
    usuario_doc = db.collection("usuarios").document(uid).get()
    usuario = usuario_doc.to_dict() if usuario_doc.exists else {"nome": "Desconhecido"}

    # Horário Itália (UTC+1, fixo)
    agora = datetime.utcnow() + timedelta(hours=1)

    # Buscar locais do Firestore
    locais_docs = db.collection("locais").stream()
    locais = []  # opção padrão
    for doc in locais_docs:
        data = doc.to_dict()
        if data.get("nome"):
            locais.append({"nome": data["nome"]})

    mensagem = None
    error = None

    if request.method == "POST":
        data_ponto = request.form.get("data")
        local_selecionado = request.form.get("local")
        horas_input = request.form.get("horas")
        notas_input = request.form.get("notas", "")

        # Validar horas
        try:
            horas = float(horas_input)
            if horas <= 0:
                raise ValueError()
        except:
            error = "Inserisci un numero valido di ore!"
            horas = 0

        # Verificar duplicidade (mesma data)
        pontos_existentes = db.collection("pontos") \
            .where("uid", "==", uid) \
            .where("data", "==", data_ponto) \
            .stream()

        if any(pontos_existentes):
            error = f"Hai già registrato una presenza per {data_ponto}!"
        
        if not error:
            ponto_data = {
                "uid": uid,
                "nome": usuario["nome"],
                "local": local_selecionado,
                "data": data_ponto,
                "horas": horas,
                "notas": notas_input,
                "criado_em": agora  # salva com fuso Itália (UTC+1)
            }
            db.collection("pontos").add(ponto_data)
            mensagem = "Ora registrata con successo!"

    return render_template(
        "registrar_ponto.html",
        locais=locais,
        mensagem=mensagem,
        error=error
    )



# MEUS PONTOS
from datetime import datetime, timedelta
from flask import render_template, redirect, session, request

@app.route("/meus_pontos", methods=["GET", "POST"])
def meus_pontos():
    if "uid" not in session:
        return redirect("/")

    uid = session["uid"]

    # Fuso horário Itália: UTC+1 (considerando horário padrão)
    # OBS: Não calcula horário de verão automaticamente
    def agora_italia():
        return datetime.utcnow() + timedelta(hours=1)

    agora = agora_italia()

    filtro_data = request.form.get("filtro_data")
    filtro_mes = request.form.get("filtro_mes")

    pontos_ref = db.collection("pontos").where("uid", "==", uid)
    pontos_docs = pontos_ref.stream()

    pontos = []
    total_horas = 0.0

    # Dias da semana em italiano
    dias_semana = {
        0: "LUN",
        1: "MAR",
        2: "MER",
        3: "GIO",
        4: "VEN",
        5: "SAB",
        6: "DOM"
    }

    for doc in pontos_docs:
        p = doc.to_dict()

        if "data" not in p:
            continue

        # Converte string para datetime (fuso fixo Itália)
        data_obj = datetime.strptime(p["data"], "%Y-%m-%d") + timedelta(hours=1)

        # Aplicar filtros
        if filtro_data and p["data"] != filtro_data:
            continue

        if filtro_mes:
            ano, mes = map(int, filtro_mes.split("-"))
            if data_obj.year != ano or data_obj.month != mes:
                continue

        # Dia da semana + data
        dia_semana = dias_semana[data_obj.weekday()]
        data_formatada = f"{data_obj.strftime('%d/%m/%Y')} • {dia_semana}"

        # Horas HH:MM
        horas_totais = float(p.get("horas", 0))
        horas_int = int(horas_totais)
        minutos = int(round((horas_totais - horas_int) * 60))
        horas_hhmm = f"{horas_int:02d}:{minutos:02d}"

        pontos.append({
            "id": doc.id,
            "data": p["data"],
            "data_formatada": data_formatada,
            "local": p.get("local", "-"),
            "horas": horas_totais,
            "horas_hhmm": horas_hhmm,
            "notas": p.get("notas", "")
        })

        total_horas += horas_totais

    # Ordena por data (mais recente primeiro)
    pontos.sort(key=lambda x: datetime.strptime(x["data"], "%Y-%m-%d"), reverse=True)

    return render_template(
        "meus_pontos.html",
        pontos=pontos,
        total_horas=round(total_horas, 1),
        filtro_data=filtro_data,
        filtro_mes=filtro_mes
    )

# =========================


# ADMIN PONTOS
from datetime import datetime

@app.route("/admin_pontos", methods=["GET", "POST"])
def admin_pontos():
    if "uid" not in session:
        return redirect("/")

    uid = session["uid"]

    # Usuário logado
    usuario_doc = db.collection("usuarios").document(uid).get()
    usuario = usuario_doc.to_dict() if usuario_doc.exists else {}

    if usuario.get("tipo") != "admin":
        return "Acesso negado"

    filtro_usuario = ""
    filtro_mes = ""

    if request.method == "POST":
        filtro_usuario = request.form.get("filtro_usuario", "")
        filtro_mes = request.form.get("filtro_mes", "")

    pontos_ref = db.collection("pontos").stream()
    pontos_list = []

    total_horas = 0

    for doc in pontos_ref:
        p = doc.to_dict()
        p["id"] = doc.id

        # Filtro usuário
        if filtro_usuario and p.get("uid") != filtro_usuario:
            continue

        # Filtro mês (YYYY-MM)
        if filtro_mes:
            if not p.get("data", "").startswith(filtro_mes):
                continue

        # Soma horas
        horas = float(p.get("horas", 0))
        total_horas += horas

        # =========================
        # 📅 DATA (ORDENA + FORMATA)
        # =========================
        data_raw = p.get("data")
        try:
            data_obj = datetime.strptime(data_raw, "%Y-%m-%d")
            p["data_ordem"] = data_obj              # usada só para ordenação
            p["data_formatada"] = data_obj.strftime("%d/%m/%Y")
        except Exception:
            p["data_ordem"] = datetime.min
            p["data_formatada"] = "-"

        # ⏱️ Formata horas HH:MM
        h = int(horas)
        m = int(round((horas - h) * 60))
        p["horas_formatadas"] = f"{h:02d}:{m:02d}"

        # Nome usuário
        usuario_p = db.collection("usuarios").document(p["uid"]).get()
        if usuario_p.exists:
            udata = usuario_p.to_dict()
            p["usuario_nome"] = f"{udata.get('nome','')} {udata.get('sobrenome','')}"
        else:
            p["usuario_nome"] = "-"

        pontos_list.append(p)

    # =========================
    # 🔥 ORDENA POR DATA (DESC)
    # =========================
    pontos_list.sort(key=lambda x: x["data_ordem"], reverse=False)

    usuarios_ref = db.collection("usuarios").stream()
    usuarios = []
    for u in usuarios_ref:
        ud = u.to_dict()
        usuarios.append({
            "uid": u.id,
            "nome": f"{ud.get('nome','')} {ud.get('sobrenome','')}"
        })

    return render_template(
        "admin_pontos.html",
        pontos=pontos_list,
        total_horas=f"{total_horas:.2f}",
        usuarios=usuarios,
        filtro_usuario=filtro_usuario,
        filtro_mes=filtro_mes
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
    formatar_data_pedido=formatar_data_pedido,
    usuario=usuario
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
                if acao == "Approvato":
                    pedido_ref.update({"status": "Approvato"})
                elif acao == "Rifiutato":
                    pedido_ref.update({"status": "Rifiutato"})
                elif acao == "Evaso":
                    pedido_ref.update({"status": "Evaso"})
                elif acao == "Excluir":
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
        if acao == "Approvato":
            pedido_ref.update({"status": "Approvato"})
        elif acao == "Rifiutato":
            pedido_ref.update({"status": "Rifiutato"})
        elif acao == "Evaso":
            pedido_ref.update({"status": "Evaso"})

    return redirect(url_for("admin_pedidos"))




from flask import send_file, request, session, redirect
from io import BytesIO
from datetime import datetime
import os

from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Table, TableStyle, Spacer, Image
)
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from reportlab.lib.units import cm
@app.route("/exportar_relatorio")
def exportar_relatorio():
    if "uid" not in session:
        return redirect("/")

    uid = session["uid"]

    filtro_data = request.args.get("filtro_data")
    filtro_mes = request.args.get("filtro_mes")

    # =========================
    # USUÁRIO
    # =========================
    usuario = db.collection("usuarios").document(uid).get().to_dict()
    nome_usuario = f"{usuario.get('nome', '')} {usuario.get('sobrenome', '')}".strip()

    # =========================
    # BUSCA PONTOS
    # =========================
    pontos_ref = db.collection("pontos").where("uid", "==", uid)
    pontos_docs = pontos_ref.stream()

    dados = []
    total_horas_float = 0.0

    # Dias da semana em italiano (IGUAL AO /meus_pontos)
    dias_semana = {
        0: "LUN",
        1: "MAR",
        2: "MER",
        3: "GIO",
        4: "VEN",
        5: "SAB",
        6: "DOM"
    }

    for doc in pontos_docs:
        p = doc.to_dict()

        if "data" not in p:
            continue

        # Converte data (fuso Itália fixo)
        data_obj = datetime.strptime(p["data"], "%Y-%m-%d") + timedelta(hours=1)

        # 🔹 filtro por data
        if filtro_data and p["data"] != filtro_data:
            continue

        # 🔹 filtro por mês
        if filtro_mes:
            ano, mes = map(int, filtro_mes.split("-"))
            if data_obj.year != ano or data_obj.month != mes:
                continue

        # 🔹 data formatada + dia da semana
        dia_semana = dias_semana[data_obj.weekday()]
        data_formatada = f"{data_obj.strftime('%d/%m/%Y')} • {dia_semana}"

        # 🔹 horas (FLOAT → HH:MM)
        horas_totais = float(p.get("horas", 0))
        horas_int = int(horas_totais)
        minutos = int(round((horas_totais - horas_int) * 60))
        horas_hhmm = f"{horas_int:02d}:{minutos:02d}"

        total_horas_float += horas_totais

        dados.append([
            data_formatada,
            p.get("local", "-"),
            horas_hhmm,
            p.get("notas", "")
        ])

    # 🔹 TOTAL FINAL
    total_int = int(total_horas_float)
    total_min = int(round((total_horas_float - total_int) * 60))
    total_horas = f"{total_int:02d}:{total_min:02d}"

    # =========================
    # PDF
    # =========================
    buffer = BytesIO()

    pdf = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=2*cm,
        rightMargin=2*cm,
        topMargin=2*cm,
        bottomMargin=2*cm
    )

    styles = getSampleStyleSheet()
    elementos = []

    # LOGO
    logo_path = os.path.join(
        os.path.dirname(__file__), "static", "img", "logo-login.png"
    )
    if os.path.exists(logo_path):
        elementos.append(Image(logo_path, width=5.5*cm, height=2.5*cm))
        elementos.append(Spacer(1, 12))

    # TÍTULO
    elementos.append(Paragraph("Rapporto presenze", styles["Title"]))
    elementos.append(Spacer(1, 12))

    periodo = filtro_data or filtro_mes or "Tutto il periodo"

    elementos.append(Paragraph(
        f"<b>Collaboratore:</b> {nome_usuario}<br/>"
        f"<b>Periodo:</b> {periodo}",
        styles["Normal"]
    ))

    elementos.append(Spacer(1, 15))

    # TABELA
    tabela = Table(
        [["Data", "Locale", "Ore", "Note"]] + dados,
        colWidths=[4*cm, 4*cm, 2.5*cm, 5.5*cm]
    )

    tabela.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#041955")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("ALIGN", (2, 1), (2, -1), "CENTER"),
    ]))

    elementos.append(tabela)
    elementos.append(Spacer(1, 12))

    # TOTAL
    elementos.append(Paragraph(
        f"<b>Totale ore:</b> {total_horas}",
        styles["Heading2"]
    ))

    elementos.append(Spacer(1, 30))

    # ASSINATURA
    elementos.append(Paragraph("Firma del collaboratore:", styles["Normal"]))
    elementos.append(Spacer(1, 20))
    elementos.append(Paragraph(
        "_______________________________<br/>"
        f"Data: {datetime.now().strftime('%d/%m/%Y')}",
        styles["Normal"]
    ))

    pdf.build(elementos)
    buffer.seek(0)

    nome_arquivo = f"relatorio_{nome_usuario.replace(' ', '_')}.pdf"

    return send_file(
        buffer,
        as_attachment=True,
        download_name=nome_arquivo,
        mimetype="application/pdf"
    )





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

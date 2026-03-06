from flask import Flask, flash, render_template, request, redirect, session, url_for
import pyrebase
import firebase_admin
import json
import os
import csv
import calendar
import uuid
from urllib.parse import quote, unquote, urlparse
from firebase_admin import credentials, firestore, storage, initialize_app, auth as admin_auth
from datetime import datetime, date
from flask import send_file, session, request
from werkzeug.utils import secure_filename
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Table, TableStyle, Spacer, Image
)
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import cm
from io import BytesIO, StringIO
from datetime import datetime




# =========================
# CONFIGURAÃ‡ÃƒO DO FLASK
# =========================
app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = os.path.join(app.root_path, "static", "img", "perfis")
app.config["MAX_CONTENT_LENGTH"] = 3 * 1024 * 1024  # 3MB

ALLOWED_IMAGE_EXTENSIONS = {"png", "jpg", "jpeg", "webp"}
app.secret_key = "chave-secreta-simples"  # essencial para sessÃ£o

# =========================
# CONFIGURACAO DE IDIOMA
# =========================
SUPPORTED_LANGUAGES = [
    {"code": "pt-br", "label": "PortuguÃªs (Brasil)"},
    {"code": "en", "label": "English"},
    {"code": "it", "label": "Italiano"},
]
LANGUAGE_CODES = {lang["code"] for lang in SUPPORTED_LANGUAGES}
DEFAULT_LANGUAGE = "it"  # Italiano como idioma padrÃ£o

TRANSLATIONS = {
    "pt-br": {
        "language.label": "Idioma",
        "nav.home": "InÃ­cio",
        "nav.clock_in": "Registrar horas",
        "nav.my_hours": "Minhas horas",
        "nav.my_requests": "Meus pedidos",
        "nav.profile": "Perfil",
        "nav.admin": "AdministraÃ§Ã£o",
        "nav.admin_hours": "GestÃ£o das horas registradas",
        "nav.admin_sites": "GestÃ£o de locais",
        "nav.admin_badges": "CrachÃ¡s",
        "nav.admin_profiles": "Perfis de usuÃ¡rios",
        "nav.admin_requests": "SolicitaÃ§Ãµes dos funcionÃ¡rios",
        "nav.logout": "Sair",
        "nav.mobile.new_point": "Novo ponto",
        "nav.mobile.my_points": "Meus pontos",
        "nav.mobile.new_request": "Novo pedido",
        "nav.mobile.profile": "Perfil",
        "login.page_title": "Entrar | FlashPoint",
        "login.subtitle": "Acesse sua conta",
        "login.email_label": "Email",
        "login.email_placeholder": "Insira seu email",
        "login.password_label": "Senha",
        "login.password_placeholder": "Insira sua senha",
        "login.submit": "Entrar",
        "login.no_account": "NÃ£o tem uma conta?",
        "login.create_account": "Criar uma conta",
        "login.footer": "Â© FlashPoint 2026 Todos os direitos reservados.",
        "register.page_title": "Criar conta | FlashPoint",
        "register.subtitle": "Crie sua nova conta",
        "register.first_name": "Nome",
        "register.last_name": "Sobrenome",
        "register.email_label": "EndereÃ§o de email",
        "register.email_placeholder": "Insira seu email",
        "register.password_label": "Senha",
        "register.password_placeholder": "Crie uma senha",
        "register.submit": "Criar conta",
        "register.have_account": "JÃ¡ tem uma conta?",
        "register.sign_in": "Entrar",
        "register.footer": "Â© FlashPoint 2026 Todos os direitos reservados.",
    
        "clock_in.contact_admin_if_site_missing": "Se o local nao estiver na lista, entre em contato com a administracao.",
        "clock_in.sick_toggle_label": "Estou doente neste dia",
        "clock_in.sick_toggle_help": "Marque esta opcao para registrar ausencia por doenca nesta data.",
        "clock_in.sick_status": "Doente",
        "clock_in.sick_registered_success": "Ausencia por doenca registrada com sucesso.",
        "clock_in.presence_status": "Trabalhou",
        "clock_in.vacation_toggle_label": "Estou de ferias neste dia",
        "clock_in.vacation_toggle_help": "Marque esta opcao para registrar ferias nesta data.",
        "clock_in.vacation_status": "Ferias",
        "clock_in.vacation_registered_success": "Ferias registradas com sucesso.",
        "clock_in.only_one_absence_type": "Selecione apenas um tipo de ausencia por dia.",
        "edit.record_type_label": "Tipo de registro",
        "edit.record_type_help": "Para doenca ou ferias, horas = 0 e local = '-'",
        "Mostra": "Mostrar",
        "nav.admin_stats": "Estat?sticas",},
    "en": {
        "language.label": "Language",
        "nav.home": "Home",
        "nav.clock_in": "Log hours",
        "nav.my_hours": "My hours",
        "nav.my_requests": "My requests",
        "nav.profile": "Profile",
        "nav.admin": "Administration",
        "nav.admin_hours": "Logged hours",
        "nav.admin_sites": "Sites",
        "nav.admin_badges": "Badges",
        "nav.admin_profiles": "User profiles",
        "nav.admin_requests": "Employee requests",
        "nav.logout": "Sign out",
        "nav.mobile.new_point": "New entry",
        "nav.mobile.my_points": "My entries",
        "nav.mobile.new_request": "New request",
        "nav.mobile.profile": "Profile",
        "login.page_title": "Sign in | FlashPoint",
        "login.subtitle": "Access your account",
        "login.email_label": "Email",
        "login.email_placeholder": "Enter your email",
        "login.password_label": "Password",
        "login.password_placeholder": "Enter your password",
        "login.submit": "Sign in",
        "login.no_account": "Don't have an account?",
        "login.create_account": "Create an account",
        "login.footer": "Â© FlashPoint 2026 All Rights Reserved.",
        "register.page_title": "Create account | FlashPoint",
        "register.subtitle": "Create your new account",
        "register.first_name": "First name",
        "register.last_name": "Last name",
        "register.email_label": "Email address",
        "register.email_placeholder": "Enter your email",
        "register.password_label": "Password",
        "register.password_placeholder": "Create a password",
        "register.submit": "Create account",
        "register.have_account": "Already have an account?",
        "register.sign_in": "Sign in",
        "register.footer": "Â© FlashPoint 2026 All Rights Reserved.",
    
        "clock_in.contact_admin_if_site_missing": "If the work site is not listed, contact administration.",
        "clock_in.sick_toggle_label": "I am sick on this day",
        "clock_in.sick_toggle_help": "Enable this option to register sick leave for this date.",
        "clock_in.sick_status": "Sick leave",
        "clock_in.sick_registered_success": "Sick leave registered successfully.",
        "clock_in.presence_status": "Worked",
        "clock_in.vacation_toggle_label": "I am on vacation on this day",
        "clock_in.vacation_toggle_help": "Enable this option to register vacation for this date.",
        "clock_in.vacation_status": "Vacation",
        "clock_in.vacation_registered_success": "Vacation registered successfully.",
        "clock_in.only_one_absence_type": "Select only one absence type per day.",
        "edit.record_type_label": "Record type",
        "edit.record_type_help": "For sick leave or vacation, hours = 0 and site = '-'",
        "Mostra": "Show",
        "nav.admin_stats": "Statistics",},
    "it": {
        "language.label": "Lingua",
        "nav.home": "Home",
        "nav.clock_in": "Segna ore",
        "nav.my_hours": "Mie ore",
        "nav.my_requests": "Mie richieste",
        "nav.profile": "Profilo",
        "nav.admin": "Amministrazione",
        "nav.admin_hours": "Gestione delle ore registrate",
        "nav.admin_sites": "Gestione dei cantieri",
        "nav.admin_badges": "Tesserini",
        "nav.admin_profiles": "Profili utenti",
        "nav.admin_requests": "Richieste dei dipendenti",
        "nav.logout": "Esci",
        "nav.mobile.new_point": "Nuovo punto",
        "nav.mobile.my_points": "I miei punti",
        "nav.mobile.new_request": "Nuova richiesta",
        "nav.mobile.profile": "Profilo",
        "login.page_title": "Accedi | FlashPoint",
        "login.subtitle": "Accedi al tuo account",
        "login.email_label": "Email",
        "login.email_placeholder": "Inserisci la tua email",
        "login.password_label": "Password",
        "login.password_placeholder": "Inserisci la tua password",
        "login.submit": "Accedi",
        "login.no_account": "Non hai un account?",
        "login.create_account": "Crea un account",
        "login.footer": "Â© FlashPoint 2026 Tutti i diritti riservati.",
        "register.page_title": "Crea account | FlashPoint",
        "register.subtitle": "Crea il tuo nuovo account",
        "register.first_name": "Nome",
        "register.last_name": "Cognome",
        "register.email_label": "Indirizzo email",
        "register.email_placeholder": "Inserisci la tua email",
        "register.password_label": "Password",
        "register.password_placeholder": "Crea una password",
        "register.submit": "Crea un account",
        "register.have_account": "Hai giÃ  un account?",
        "register.sign_in": "Accedi",
        "register.footer": "Â© FlashPoint 2026 Tutti i diritti riservati.",
    
        "clock_in.contact_admin_if_site_missing": "Se il cantiere non e presente, contatta l'amministrazione.",
        "clock_in.sick_toggle_label": "Sono malato in questa data",
        "clock_in.sick_toggle_help": "Attiva questa opzione per registrare assenza per malattia in questa data.",
        "clock_in.sick_status": "Malattia",
        "clock_in.sick_registered_success": "Assenza per malattia registrata con successo.",
        "clock_in.presence_status": "Presenza",
        "clock_in.vacation_toggle_label": "Sono in ferie in questa data",
        "clock_in.vacation_toggle_help": "Attiva questa opzione per registrare ferie in questa data.",
        "clock_in.vacation_status": "Ferie",
        "clock_in.vacation_registered_success": "Ferie registrate con successo.",
        "clock_in.only_one_absence_type": "Seleziona un solo tipo di assenza per giorno.",
        "edit.record_type_label": "Tipo di registrazione",
        "edit.record_type_help": "Per malattia o ferie, ore = 0 e locale = '-'",
        "Mostra": "Mostra",
        "nav.admin_stats": "Statistiche",},
}

TEXT_TRANSLATIONS = {
    "pt-br": {
        "Admin": "Admin",
        "Admin cria e designa atividades para os colaboradores": "Admin cria e designa atividades para os colaboradores",
        "Admin â€¢ CartÃµes de Reconhecimento | FlashPoint": "Admin â€¢ CartÃµes de Reconhecimento | FlashPoint",
        "Admin â€¢ Backup e Pulizia | FlashPoint": "Admin â€¢ Backup e Limpeza | FlashPoint",
        "Admin â€¢ Locais | FlashPoint": "Admin â€¢ Locais | FlashPoint",
        "Admin â€¢ Modifica Profilo | FlashPoint": "Admin â€¢ Editar Perfil | FlashPoint",
        "Admin â€¢ Modifica Punto | FlashPoint": "Admin â€¢ Editar Ponto | FlashPoint",
        "Admin â€¢ Ordini | FlashPoint": "Admin â€¢ Pedidos | FlashPoint",
        "Admin â€¢ Pontos | FlashPoint": "Admin â€¢ Pontos | FlashPoint",
        "Admin â€¢ Profili Utenti | FlashPoint": "Admin â€¢ Perfis de UsuÃ¡rios | FlashPoint",
        "Aggiungi": "Adicionar",
        "Aggiungi e gestisci i luoghi disponibili": "Adicione e gerencie os locais disponÃ­veis",
        "Aggiungi nuovo locale": "Adicionar novo local",
        "Aggiungi un'osservazione rilevante...": "Adicione uma observaÃ§Ã£o relevante...",
        "Alta": "Alta",
        "Amministratore": "Administrador",
        "Amministrazione e controllo delle ore": "AdministraÃ§Ã£o e controle de horas",
        "Annulla": "Cancelar",
        "Approvato": "Aprovado",
        "Area amministratore": "Ãrea administrativa",
        "Atualizar": "Atualizar",
        "Azione": "AÃ§Ã£o",
        "Azioni": "AÃ§Ãµes",
        "Backup e pulizia": "Backup e limpeza",
        "Baixa": "Baixa",
        "Benvenuto": "Bem-vindo",
        "Cancella": "Limpar",
        "Cantieri": "Canteiros",
        "CartÃ£o de Reconhecimento": "CartÃ£o de Reconhecimento",
        "Classifica mensile ore lavorate": "ClassificaÃ§Ã£o mensal de horas trabalhadas",
        "Cognome": "Sobrenome",
        "Colaborador": "Colaborador",
        "Compila i dati per registrare le tue ore.": "Preencha os dados para registrar suas horas.",
        "Completo": "Completo",
        "ConfiguraÃ§Ãµes": "ConfiguraÃ§Ãµes",
        "Consulta e gestisci le ore registrate": "Consulte e gerencie as horas registradas",
        "Consulta e modifica le informazioni del tuo profilo": "Consulte e edite as informaÃ§Ãµes do seu perfil",
        "Creato il": "Criado em",
        "Criado por": "Criado por",
        "Criar e designar tarefa": "Criar e designar tarefa",
        "Dashboard | FlashPoint": "Dashboard | FlashPoint",
        "Data": "Data",
        "Data Assunzione": "Data de admissÃ£o",
        "Data di assunzione": "Data de admissÃ£o",
        "Data di nascita": "Data de nascimento",
        "Data specifica": "Data especÃ­fica",
        "Dati del punto": "Dados do ponto",
        "Dati personali": "Dados pessoais",
        "DescriÃ§Ã£o": "DescriÃ§Ã£o",
        "Deseja excluir esta tarefa?": "Deseja excluir esta tarefa?",
        "Designar para (pode selecionar vÃ¡rios)": "Designar para (pode selecionar vÃ¡rios)",
        "Detalhes da tarefa": "Detalhes da tarefa",
        "Dipendente": "FuncionÃ¡rio",
        "Distaccato Presso": "Destacado em",
        "Done": "ConcluÃ­do",
        "Elimina": "Excluir",
        "Email": "Email",
        "Esporta PDF": "Exportar PDF",
        "Esporta rapporto in PDF": "Exportar relatÃ³rio em PDF",
        "Evaso": "Atendido",
        "Ex.: 0.25 = 15min Â· 1.50 = 1h30 Â· 5.25 = 5h15": "Ex.: 0.25 = 15min Â· 1.50 = 1h30 Â· 5.25 = 5h15",
        "Ex.: Brasile": "Ex.: Brasil",
        "Ex.: Elettricista": "Ex.: Eletricista",
        "Ex.: Joao": "Ex.: JoÃ£o",
        "Ex.: JoÃ£o": "Ex.: JoÃ£o",
        "Ex.: Silva": "Ex.: Silva",
        "Excluir": "Excluir",
        "Filtra": "Filtrar",
        "Foto": "Foto",
        "Foto del profilo": "Foto do perfil",
        "Foto do perfil": "Foto do perfil",
        "Genera tessera": "Gerar crachÃ¡",
        "Genera tesserino": "Gerar crachÃ¡",
        "Generazione e gestione dei cartellini": "GeraÃ§Ã£o e gestÃ£o dos cartÃµes",
        "Gestione dei cantieri": "GestÃ£o dos canteiros",
        "Gestione dei locali": "GestÃ£o dos locais",
        "Gestione delle ore registrate": "GestÃ£o das horas registradas",
        "Gestione delle presenze": "GestÃ£o das presenÃ§as",
        "Gestione profili utenti": "GestÃ£o de perfis de usuÃ¡rios",
        "Gestione richieste e ordini": "GestÃ£o de solicitaÃ§Ãµes e pedidos",
        "I miei ordini": "Meus pedidos",
        "Idioma": "Idioma",
        "Il backup viene salvato sul tuo PC, non sul server.": "O backup Ã© salvo no seu PC, nÃ£o no servidor.",
        "In Progress": "Em andamento",
        "In sospeso": "Pendente",
        "Incompleto": "Incompleto",
        "Indietro": "Voltar",
        "Invia ordine": "Enviar pedido",
        "Invia una nuova richiesta": "Envie uma nova solicitaÃ§Ã£o",
        "Le mie presenze": "Minhas presenÃ§as",
        "Locale": "Local",
        "Mese": "MÃªs",
        "Mese finale": "MÃªs final",
        "Mese iniziale": "MÃªs inicial",
        "Messaggio": "Mensagem",
        "Meus Pontos | FlashPoint": "Meus Pontos | FlashPoint",
        "Minhas Atividades": "Minhas Atividades",
        "Modifica": "Editar",
        "Modifica Profilo": "Editar Perfil",
        "Modifica le informazioni del tuo profilo": "Edite as informaÃ§Ãµes do seu perfil",
        "Modifica ore": "Editar horas",
        "Modifica profilo": "Editar perfil",
        "Modifica profilo utente": "Editar perfil do usuÃ¡rio",
        "Modificabile se necessario.": "EditÃ¡vel se necessÃ¡rio.",
        "MÃ©dia": "MÃ©dia",
        "Nato": "Nascido",
        "Nenhuma tarefa encontrada para o filtro selecionado.": "Nenhuma tarefa encontrada para o filtro selecionado.",
        "Nessun locale registrato.": "Nenhum local registrado.",
        "Nessun messaggio inserito.": "Nenhuma mensagem inserida.",
        "Nessun ordine registrato.": "Nenhum pedido registrado.",
        "Nessuno": "Nenhum",
        "Nessun utente registrato.": "Nenhum usuÃ¡rio registrado.",
        "Nessuna nota inserita.": "Nenhuma nota inserida.",
        "Nessuna presenza registrata con questi filtri.": "Nenhuma presenÃ§a registrada com esses filtros.",
        "Nessuna presenza trovata con questi filtri.": "Nenhuma presenÃ§a encontrada com esses filtros.",
        "Nome": "Nome",
        "Nome del locale": "Nome do local",
        "Non": "NÃ£o",
        "Non hai ancora effettuato alcun ordine.": "VocÃª ainda nÃ£o fez nenhum pedido.",
        "Note": "Notas",
        "Nova tarefa": "Nova tarefa",
        "Nuova richiesta": "Nova solicitaÃ§Ã£o",
        "Nuova richiesta | FlashPoint": "Nova solicitaÃ§Ã£o | FlashPoint",
        "Ordini degli utenti": "Pedidos dos usuÃ¡rios",
        "Ore": "Horas",
        "Ore lavorate": "Horas trabalhadas",
        "Ore lavorate nel mese precedente": "Horas trabalhadas no mÃªs anterior",
        "Ore lavorate questo mese": "Horas trabalhadas neste mÃªs",
        "Osservazioni": "ObservaÃ§Ãµes",
        "Osservazioni aggiuntive...": "ObservaÃ§Ãµes adicionais...",
        "PNG, JPG ou WEBP. MÃ¡x 3MB.": "PNG, JPG ou WEBP. MÃ¡x 3MB.",
        "Paese di origine": "PaÃ­s de origem",
        "Perfil | FlashPoint": "Perfil | FlashPoint",
        "Posizione in classifica": "PosiÃ§Ã£o no ranking",
        "Prazo": "Prazo",
        "Prioridade": "Prioridade",
        "Profilo": "Perfil",
        "Profilo completo": "Perfil completo",
        "Profilo incompleto": "Perfil incompleto",
        "Profilo | FlashPoint": "Perfil | FlashPoint",
        "Registrar": "Registrar",
        "Registrar Ponto | FlashPoint": "Registrar Ponto | FlashPoint",
        "Registrare la presenza": "Registrar presenÃ§a",
        "ResponsÃ¡vel": "ResponsÃ¡vel",
        "Richeste": "SolicitaÃ§Ãµes",
        "Richeste degli utenti": "SolicitaÃ§Ãµes dos usuÃ¡rios",
        "Riepilogo della tua attivitÃ ": "Resumo da sua atividade",
        "Rifiutato": "Recusado",
        "Ruolo": "Cargo",
        "Ruolo / Mansione": "Cargo / FunÃ§Ã£o",
        "Salva modifiche": "Salvar alteraÃ§Ãµes",
        "Scarica + elimina": "Baixar + excluir",
        "Scarica backup": "Baixar backup",
        "Seleziona il luogo": "Selecione o local",
        "Seleziona il luogo in cui si Ã¨ svolta l'attivitÃ .": "Selecione o local onde a atividade foi realizada.",
        "Si": "Sim",
        "Solo amministratori possono aggiornare i profili": "Somente administradores podem atualizar os perfis",
        "Solo gli amministratori possono modificare i profili": "Somente administradores podem editar os perfis",
        "Stato": "Status",
        "Stato ordine": "Status do pedido",
        "Stato profilo": "Status do perfil",
        "Status": "Status",
        "Tarefas atribuÃ­das": "Tarefas atribuÃ­das",
        "Tarefas de toda a equipa": "Tarefas de toda a equipe",
        "Tesserini": "CrachÃ¡s",
        "Tesserini di riconoscimento": "CrachÃ¡s de reconhecimento",
        "Tipo": "Tipo",
        "Tipo di ordine": "Tipo de pedido",
        "To Do": "A fazer",
        "Todos": "Todos",
        "Tornare": "Voltar",
        "Totale delle ore lavorate questâ€™anno": "Total de horas trabalhadas neste ano",
        "Totale ore registrate": "Total de horas registradas",
        "Tutti": "Todos",
        "TÃ­tulo": "TÃ­tulo",
        "UID": "UID",
        "Usa valori decimali (es: 1.50 = 1h30)": "Use valores decimais (ex: 1.50 = 1h30)",
        "Use Ctrl/Cmd + clique para selecionar mais de uma pessoa.": "Use Ctrl/Cmd + clique para selecionar mais de uma pessoa.",
        "Utente": "UsuÃ¡rio",
        "VerrÃ  scaricato un backup e poi le presenze saranno eliminate dal server. Continuare?": "Um backup serÃ¡ baixado e depois as presenÃ§as serÃ£o removidas do servidor. Continuar?",
        "VisualizaÃ§Ã£o das tarefas que foram designadas para vocÃª": "VisualizaÃ§Ã£o das tarefas que foram designadas para vocÃª",
        "Visualizza e gestisci i tuoi ordini": "Visualize e gerencie seus pedidos",
        "Vuoi eliminare il locale": "Deseja excluir o local",
        "Vuoi eliminare questo ordine?": "Deseja excluir este pedido?",
        "Vuoi eliminare questo punto?": "Deseja excluir este ponto?",
        "Work Management": "GestÃ£o de tarefas",
        "a": "em",
        "email non disponibile": "email nÃ£o disponÃ­vel",
        "opzionale": "opcional",
    
        "Mostra": "Mostrar",
        "Telefone": "Telefone",
        "Telefone de emergÃªncia": "Telefone de emergÃªncia",
        "Ragione Sociale": "Raz?o social",
        "Responsabile tecnico": "Respons?vel t?cnico",
        "Indirizzo": "Endere?o",
        "P.IVA": "P.IVA",
        "Datore di Lavoro": "Empregador",
        "Intestazione azienda": "T?tulo da empresa",
        "Admin ? Statistiche | FlashPoint": "Admin ? Estat?sticas | FlashPoint",
        "Statistiche amministrative": "Estat?sticas administrativas",
        "Analisi ore per periodo e localit?": "An?lise de horas por per?odo e localidade",
        "Periodo": "Per?odo",
        "Trimestre": "Trimestre",
        "Semestre": "Semestre",
        "Anno": "Ano",
        "Applica filtro": "Aplicar filtro",
        "Ore del periodo": "Horas do per?odo",
        "Ore dell'anno": "Horas do ano",
        "Top localit?": "Top localidade",
        "Ore per localit?": "Horas por localidade",
        "Ore per mese": "Horas por m?s",
        "Esporta statistiche in PDF": "Exportar estat?sticas em PDF",
        "Seleziona un dipendente per esportare.": "Selecione um funcion?rio para exportar.",},
    "en": {
        "Admin": "Admin",
        "Admin cria e designa atividades para os colaboradores": "Admin creates and assigns activities to collaborators",
        "Admin â€¢ CartÃµes de Reconhecimento | FlashPoint": "Admin â€¢ Recognition Cards | FlashPoint",
        "Admin â€¢ Backup e Pulizia | FlashPoint": "Admin â€¢ Backup & Cleanup | FlashPoint",
        "Admin â€¢ Locais | FlashPoint": "Admin â€¢ Locations | FlashPoint",
        "Admin â€¢ Modifica Profilo | FlashPoint": "Admin â€¢ Edit Profile | FlashPoint",
        "Admin â€¢ Modifica Punto | FlashPoint": "Admin â€¢ Edit Entry | FlashPoint",
        "Admin â€¢ Ordini | FlashPoint": "Admin â€¢ Orders | FlashPoint",
        "Admin â€¢ Pontos | FlashPoint": "Admin â€¢ Time Logs | FlashPoint",
        "Admin â€¢ Profili Utenti | FlashPoint": "Admin â€¢ User Profiles | FlashPoint",
        "Aggiungi": "Add",
        "Aggiungi e gestisci i luoghi disponibili": "Add and manage available locations",
        "Aggiungi nuovo locale": "Add new location",
        "Aggiungi un'osservazione rilevante...": "Add a relevant note...",
        "Alta": "High",
        "Amministratore": "Administrator",
        "Amministrazione e controllo delle ore": "Administration and hour control",
        "Annulla": "Cancel",
        "Approvato": "Approved",
        "Area amministratore": "Admin area",
        "Atualizar": "Update",
        "Azione": "Action",
        "Azioni": "Actions",
        "Backup e pulizia": "Backup and cleanup",
        "Baixa": "Low",
        "Benvenuto": "Welcome",
        "Cancella": "Clear",
        "Cantieri": "Sites",
        "CartÃ£o de Reconhecimento": "Recognition Card",
        "Classifica mensile ore lavorate": "Monthly worked hours ranking",
        "Cognome": "Last name",
        "Colaborador": "Employee",
        "Compila i dati per registrare le tue ore.": "Fill in the data to log your hours.",
        "Completo": "Complete",
        "ConfiguraÃ§Ãµes": "Settings",
        "Consulta e gestisci le ore registrate": "View and manage logged hours",
        "Consulta e modifica le informazioni del tuo profilo": "View and edit your profile information",
        "Creato il": "Created on",
        "Criado por": "Created by",
        "Criar e designar tarefa": "Create and assign task",
        "Dashboard | FlashPoint": "Dashboard | FlashPoint",
        "Data": "Date",
        "Data Assunzione": "Hire date",
        "Data di assunzione": "Hire date",
        "Data di nascita": "Date of birth",
        "Data specifica": "Specific date",
        "Dati del punto": "Entry data",
        "Dati personali": "Personal data",
        "DescriÃ§Ã£o": "Description",
        "Deseja excluir esta tarefa?": "Do you want to delete this task?",
        "Designar para (pode selecionar vÃ¡rios)": "Assign to (you can select multiple)",
        "Detalhes da tarefa": "Task details",
        "Dipendente": "Employee",
        "Distaccato Presso": "Assigned to",
        "Done": "Done",
        "Elimina": "Delete",
        "Email": "Email",
        "Esporta PDF": "Export PDF",
        "Esporta rapporto in PDF": "Export report to PDF",
        "Evaso": "Fulfilled",
        "Ex.: 0.25 = 15min Â· 1.50 = 1h30 Â· 5.25 = 5h15": "Ex.: 0.25 = 15min Â· 1.50 = 1h30 Â· 5.25 = 5h15",
        "Ex.: Brasile": "Ex.: Brazil",
        "Ex.: Elettricista": "Ex.: Electrician",
        "Ex.: Joao": "Ex.: John",
        "Ex.: JoÃ£o": "Ex.: John",
        "Ex.: Silva": "Ex.: Silva",
        "Excluir": "Delete",
        "Filtra": "Filter",
        "Foto": "Photo",
        "Foto del profilo": "Profile photo",
        "Foto do perfil": "Profile photo",
        "Genera tessera": "Generate badge",
        "Genera tesserino": "Generate badge",
        "Generazione e gestione dei cartellini": "Generation and management of badges",
        "Gestione dei cantieri": "Site management",
        "Gestione dei locali": "Location management",
        "Gestione delle ore registrate": "Logged hours management",
        "Gestione delle presenze": "Attendance management",
        "Gestione profili utenti": "User profile management",
        "Gestione richieste e ordini": "Requests and orders management",
        "I miei ordini": "My orders",
        "Idioma": "Language",
        "Il backup viene salvato sul tuo PC, non sul server.": "The backup is saved on your PC, not on the server.",
        "In Progress": "In Progress",
        "In sospeso": "Pending",
        "Incompleto": "Incomplete",
        "Indietro": "Back",
        "Invia ordine": "Submit order",
        "Invia una nuova richiesta": "Send a new request",
        "Le mie presenze": "My attendance",
        "Locale": "Location",
        "Mese": "Month",
        "Mese finale": "End month",
        "Mese iniziale": "Start month",
        "Messaggio": "Message",
        "Meus Pontos | FlashPoint": "My Time Logs | FlashPoint",
        "Minhas Atividades": "My Tasks",
        "Modifica": "Edit",
        "Modifica Profilo": "Edit Profile",
        "Modifica le informazioni del tuo profilo": "Edit your profile information",
        "Modifica ore": "Edit hours",
        "Modifica profilo": "Edit profile",
        "Modifica profilo utente": "Edit user profile",
        "Modificabile se necessario.": "Editable if needed.",
        "MÃ©dia": "Medium",
        "Nato": "Born",
        "Nenhuma tarefa encontrada para o filtro selecionado.": "No tasks found for the selected filter.",
        "Nessun locale registrato.": "No location registered.",
        "Nessun messaggio inserito.": "No message provided.",
        "Nessun ordine registrato.": "No order registered.",
        "Nessuno": "None",
        "Nessun utente registrato.": "No user registered.",
        "Nessuna nota inserita.": "No note provided.",
        "Nessuna presenza registrata con questi filtri.": "No attendance records for these filters.",
        "Nessuna presenza trovata con questi filtri.": "No attendance found for these filters.",
        "Nome": "First name",
        "Nome del locale": "Location name",
        "Non": "No",
        "Non hai ancora effettuato alcun ordine.": "You haven't placed any orders yet.",
        "Note": "Notes",
        "Nova tarefa": "New task",
        "Nuova richiesta": "New request",
        "Nuova richiesta | FlashPoint": "New request | FlashPoint",
        "Ordini degli utenti": "User orders",
        "Ore": "Hours",
        "Ore lavorate": "Worked hours",
        "Ore lavorate nel mese precedente": "Hours worked in the previous month",
        "Ore lavorate questo mese": "Hours worked this month",
        "Osservazioni": "Notes",
        "Osservazioni aggiuntive...": "Additional notes...",
        "PNG, JPG ou WEBP. MÃ¡x 3MB.": "PNG, JPG or WEBP. Max 3MB.",
        "Paese di origine": "Country of origin",
        "Perfil | FlashPoint": "Profile | FlashPoint",
        "Posizione in classifica": "Ranking position",
        "Prazo": "Due date",
        "Prioridade": "Priority",
        "Profilo": "Profile",
        "Profilo completo": "Profile complete",
        "Profilo incompleto": "Profile incomplete",
        "Profilo | FlashPoint": "Profile | FlashPoint",
        "Registrar": "Submit",
        "Registrar Ponto | FlashPoint": "Log Hours | FlashPoint",
        "Registrare la presenza": "Log attendance",
        "ResponsÃ¡vel": "Responsible",
        "Richeste": "Requests",
        "Richeste degli utenti": "User requests",
        "Riepilogo della tua attivitÃ ": "Summary of your activity",
        "Rifiutato": "Rejected",
        "Ruolo": "Role",
        "Ruolo / Mansione": "Role / Position",
        "Salva modifiche": "Save changes",
        "Scarica + elimina": "Download + delete",
        "Scarica backup": "Download backup",
        "Seleziona il luogo": "Select the location",
        "Seleziona il luogo in cui si Ã¨ svolta l'attivitÃ .": "Select the location where the activity took place.",
        "Si": "Yes",
        "Solo amministratori possono aggiornare i profili": "Only administrators can update profiles",
        "Solo gli amministratori possono modificare i profili": "Only administrators can edit profiles",
        "Stato": "Status",
        "Stato ordine": "Order status",
        "Stato profilo": "Profile status",
        "Status": "Status",
        "Tarefas atribuÃ­das": "Assigned tasks",
        "Tarefas de toda a equipa": "All team tasks",
        "Tesserini": "Badges",
        "Tesserini di riconoscimento": "Recognition badges",
        "Tipo": "Type",
        "Tipo di ordine": "Order type",
        "To Do": "To Do",
        "Todos": "All",
        "Tornare": "Back",
        "Totale delle ore lavorate questâ€™anno": "Total hours worked this year",
        "Totale ore registrate": "Total logged hours",
        "Tutti": "All",
        "TÃ­tulo": "Title",
        "UID": "UID",
        "Usa valori decimali (es: 1.50 = 1h30)": "Use decimal values (e.g., 1.50 = 1h30)",
        "Use Ctrl/Cmd + clique para selecionar mais de uma pessoa.": "Use Ctrl/Cmd + click to select more than one person.",
        "Utente": "User",
        "VerrÃ  scaricato un backup e poi le presenze saranno eliminate dal server. Continuare?": "A backup will be downloaded and then the records will be deleted from the server. Continue?",
        "VisualizaÃ§Ã£o das tarefas que foram designadas para vocÃª": "View of tasks assigned to you",
        "Visualizza e gestisci i tuoi ordini": "View and manage your orders",
        "Vuoi eliminare il locale": "Do you want to delete the location",
        "Vuoi eliminare questo ordine?": "Do you want to delete this order?",
        "Vuoi eliminare questo punto?": "Do you want to delete this entry?",
        "Work Management": "Work Management",
        "a": "in",
        "email non disponibile": "email not available",
        "opzionale": "optional",
    
        "Mostra": "Show",
        "Telefone": "Phone",
        "Telefone de emergÃªncia": "Emergency phone",
        "Ragione Sociale": "Company name",
        "Responsabile tecnico": "Technical manager",
        "Indirizzo": "Address",
        "P.IVA": "VAT",
        "Datore di Lavoro": "Employer",
        "Intestazione azienda": "Company heading",
        "Admin ? Statistiche | FlashPoint": "Admin ? Statistics | FlashPoint",
        "Statistiche amministrative": "Administrative statistics",
        "Analisi ore per periodo e localit?": "Hours analysis by period and location",
        "Periodo": "Period",
        "Trimestre": "Quarter",
        "Semestre": "Semester",
        "Anno": "Year",
        "Applica filtro": "Apply filter",
        "Ore del periodo": "Period hours",
        "Ore dell'anno": "Year hours",
        "Top localit?": "Top location",
        "Ore per localit?": "Hours by location",
        "Ore per mese": "Hours by month",
        "Esporta statistiche in PDF": "Export statistics to PDF",
        "Seleziona un dipendente per esportare.": "Select an employee to export.",},
    "it": {
        "Admin": "Admin",
        "Admin cria e designa atividades para os colaboradores": "L'amministratore crea e assegna le attivitÃ  ai collaboratori",
        "Admin â€¢ CartÃµes de Reconhecimento | FlashPoint": "Admin â€¢ Tesserini di riconoscimento | FlashPoint",
        "Admin â€¢ Backup e Pulizia | FlashPoint": "Admin â€¢ Backup e Pulizia | FlashPoint",
        "Admin â€¢ Locais | FlashPoint": "Admin â€¢ Locali | FlashPoint",
        "Admin â€¢ Modifica Profilo | FlashPoint": "Admin â€¢ Modifica profilo | FlashPoint",
        "Admin â€¢ Modifica Punto | FlashPoint": "Admin â€¢ Modifica punto | FlashPoint",
        "Admin â€¢ Ordini | FlashPoint": "Admin â€¢ Ordini | FlashPoint",
        "Admin â€¢ Pontos | FlashPoint": "Admin â€¢ Presenze | FlashPoint",
        "Admin â€¢ Profili Utenti | FlashPoint": "Admin â€¢ Profili utenti | FlashPoint",
        "Aggiungi": "Aggiungi",
        "Aggiungi e gestisci i luoghi disponibili": "Aggiungi e gestisci i luoghi disponibili",
        "Aggiungi nuovo locale": "Aggiungi nuovo locale",
        "Aggiungi un'osservazione rilevante...": "Aggiungi un'osservazione rilevante...",
        "Alta": "Alta",
        "Amministratore": "Amministratore",
        "Amministrazione e controllo delle ore": "Amministrazione e controllo delle ore",
        "Annulla": "Annulla",
        "Approvato": "Approvato",
        "Area amministratore": "Area amministratore",
        "Atualizar": "Aggiorna",
        "Azione": "Azione",
        "Azioni": "Azioni",
        "Backup e pulizia": "Backup e pulizia",
        "Baixa": "Bassa",
        "Benvenuto": "Benvenuto",
        "Cancella": "Cancella",
        "Cantieri": "Cantieri",
        "CartÃ£o de Reconhecimento": "Tesserino di riconoscimento",
        "Classifica mensile ore lavorate": "Classifica mensile ore lavorate",
        "Cognome": "Cognome",
        "Colaborador": "Collaboratore",
        "Compila i dati per registrare le tue ore.": "Compila i dati per registrare le tue ore.",
        "Completo": "Completo",
        "ConfiguraÃ§Ãµes": "Impostazioni",
        "Consulta e gestisci le ore registrate": "Consulta e gestisci le ore registrate",
        "Consulta e modifica le informazioni del tuo profilo": "Consulta e modifica le informazioni del tuo profilo",
        "Creato il": "Creato il",
        "Criado por": "Creato da",
        "Criar e designar tarefa": "Crea e assegna attivitÃ ",
        "Dashboard | FlashPoint": "Dashboard | FlashPoint",
        "Data": "Data",
        "Data Assunzione": "Data assunzione",
        "Data di assunzione": "Data di assunzione",
        "Data di nascita": "Data di nascita",
        "Data specifica": "Data specifica",
        "Dati del punto": "Dati del punto",
        "Dati personali": "Dati personali",
        "DescriÃ§Ã£o": "Descrizione",
        "Deseja excluir esta tarefa?": "Vuoi eliminare questa attivitÃ ?",
        "Designar para (pode selecionar vÃ¡rios)": "Assegna a (puoi selezionare piÃ¹ persone)",
        "Detalhes da tarefa": "Dettagli dell'attivitÃ ",
        "Dipendente": "Dipendente",
        "Distaccato Presso": "Distaccato presso",
        "Done": "Completato",
        "Elimina": "Elimina",
        "Email": "Email",
        "Esporta PDF": "Esporta PDF",
        "Esporta rapporto in PDF": "Esporta rapporto in PDF",
        "Evaso": "Evaso",
        "Ex.: 0.25 = 15min Â· 1.50 = 1h30 Â· 5.25 = 5h15": "Es.: 0.25 = 15min Â· 1.50 = 1h30 Â· 5.25 = 5h15",
        "Ex.: Brasile": "Es.: Brasile",
        "Ex.: Elettricista": "Es.: Elettricista",
        "Ex.: Joao": "Es.: JoÃ£o",
        "Ex.: JoÃ£o": "Es.: JoÃ£o",
        "Ex.: Silva": "Es.: Silva",
        "Excluir": "Elimina",
        "Filtra": "Filtra",
        "Foto": "Foto",
        "Foto del profilo": "Foto del profilo",
        "Foto do perfil": "Foto del profilo",
        "Genera tessera": "Genera tessera",
        "Genera tesserino": "Genera tesserino",
        "Generazione e gestione dei cartellini": "Generazione e gestione dei cartellini",
        "Gestione dei cantieri": "Gestione dei cantieri",
        "Gestione dei locali": "Gestione dei locali",
        "Gestione delle ore registrate": "Gestione delle ore registrate",
        "Gestione delle presenze": "Gestione delle presenze",
        "Gestione profili utenti": "Gestione profili utenti",
        "Gestione richieste e ordini": "Gestione richieste e ordini",
        "I miei ordini": "I miei ordini",
        "Idioma": "Lingua",
        "Il backup viene salvato sul tuo PC, non sul server.": "Il backup viene salvato sul tuo PC, non sul server.",
        "In Progress": "In corso",
        "In sospeso": "In sospeso",
        "Incompleto": "Incompleto",
        "Indietro": "Indietro",
        "Invia ordine": "Invia ordine",
        "Invia una nuova richiesta": "Invia una nuova richiesta",
        "Le mie presenze": "Le mie presenze",
        "Locale": "Locale",
        "Mese": "Mese",
        "Mese finale": "Mese finale",
        "Mese iniziale": "Mese iniziale",
        "Messaggio": "Messaggio",
        "Meus Pontos | FlashPoint": "Le mie presenze | FlashPoint",
        "Minhas Atividades": "Le mie attivitÃ ",
        "Modifica": "Modifica",
        "Modifica Profilo": "Modifica profilo",
        "Modifica le informazioni del tuo profilo": "Modifica le informazioni del tuo profilo",
        "Modifica ore": "Modifica ore",
        "Modifica profilo": "Modifica profilo",
        "Modifica profilo utente": "Modifica profilo utente",
        "Modificabile se necessario.": "Modificabile se necessario.",
        "MÃ©dia": "Media",
        "Nato": "Nato",
        "Nenhuma tarefa encontrada para o filtro selecionado.": "Nessuna attivitÃ  trovata per il filtro selezionato.",
        "Nessun locale registrato.": "Nessun locale registrato.",
        "Nessun messaggio inserito.": "Nessun messaggio inserito.",
        "Nessun ordine registrato.": "Nessun ordine registrato.",
        "Nessuno": "Nessuno",
        "Nessun utente registrato.": "Nessun utente registrato.",
        "Nessuna nota inserita.": "Nessuna nota inserita.",
        "Nessuna presenza registrata con questi filtri.": "Nessuna presenza registrata con questi filtri.",
        "Nessuna presenza trovata con questi filtri.": "Nessuna presenza trovata con questi filtri.",
        "Nome": "Nome",
        "Nome del locale": "Nome del locale",
        "Non": "No",
        "Non hai ancora effettuato alcun ordine.": "Non hai ancora effettuato alcun ordine.",
        "Note": "Note",
        "Nova tarefa": "Nuova attivitÃ ",
        "Nuova richiesta": "Nuova richiesta",
        "Nuova richiesta | FlashPoint": "Nuova richiesta | FlashPoint",
        "Ordini degli utenti": "Ordini degli utenti",
        "Ore": "Ore",
        "Ore lavorate": "Ore lavorate",
        "Ore lavorate nel mese precedente": "Ore lavorate nel mese precedente",
        "Ore lavorate questo mese": "Ore lavorate questo mese",
        "Osservazioni": "Osservazioni",
        "Osservazioni aggiuntive...": "Osservazioni aggiuntive...",
        "PNG, JPG ou WEBP. MÃ¡x 3MB.": "PNG, JPG o WEBP. Max 3MB.",
        "Paese di origine": "Paese di origine",
        "Perfil | FlashPoint": "Profilo | FlashPoint",
        "Posizione in classifica": "Posizione in classifica",
        "Prazo": "Scadenza",
        "Prioridade": "PrioritÃ ",
        "Profilo": "Profilo",
        "Profilo completo": "Profilo completo",
        "Profilo incompleto": "Profilo incompleto",
        "Profilo | FlashPoint": "Profilo | FlashPoint",
        "Registrar": "Registra",
        "Registrar Ponto | FlashPoint": "Segna ore | FlashPoint",
        "Registrare la presenza": "Registrare la presenza",
        "ResponsÃ¡vel": "Responsabile",
        "Richeste": "Richieste",
        "Richeste degli utenti": "Richieste degli utenti",
        "Riepilogo della tua attivitÃ ": "Riepilogo della tua attivitÃ ",
        "Rifiutato": "Rifiutato",
        "Ruolo": "Ruolo",
        "Ruolo / Mansione": "Ruolo / Mansione",
        "Salva modifiche": "Salva modifiche",
        "Scarica + elimina": "Scarica + elimina",
        "Scarica backup": "Scarica backup",
        "Seleziona il luogo": "Seleziona il luogo",
        "Seleziona il luogo in cui si Ã¨ svolta l'attivitÃ .": "Seleziona il luogo in cui si Ã¨ svolta l'attivitÃ .",
        "Si": "SÃ¬",
        "Solo amministratori possono aggiornare i profili": "Solo amministratori possono aggiornare i profili",
        "Solo gli amministratori possono modificare i profili": "Solo gli amministratori possono modificare i profili",
        "Stato": "Stato",
        "Stato ordine": "Stato ordine",
        "Stato profilo": "Stato profilo",
        "Status": "Status",
        "Tarefas atribuÃ­das": "AttivitÃ  assegnate",
        "Tarefas de toda a equipa": "AttivitÃ  di tutto il team",
        "Tesserini": "Tesserini",
        "Tesserini di riconoscimento": "Tesserini di riconoscimento",
        "Tipo": "Tipo",
        "Tipo di ordine": "Tipo di ordine",
        "To Do": "Da fare",
        "Todos": "Tutti",
        "Tornare": "Torna indietro",
        "Totale delle ore lavorate questâ€™anno": "Totale delle ore lavorate questâ€™anno",
        "Totale ore registrate": "Totale ore registrate",
        "Tutti": "Tutti",
        "TÃ­tulo": "Titolo",
        "UID": "UID",
        "Usa valori decimali (es: 1.50 = 1h30)": "Usa valori decimali (es: 1.50 = 1h30)",
        "Use Ctrl/Cmd + clique para selecionar mais de uma pessoa.": "Usa Ctrl/Cmd + clic per selezionare piÃ¹ persone.",
        "Utente": "Utente",
        "VerrÃ  scaricato un backup e poi le presenze saranno eliminate dal server. Continuare?": "VerrÃ  scaricato un backup e poi le presenze saranno eliminate dal server. Continuare?",
        "VisualizaÃ§Ã£o das tarefas que foram designadas para vocÃª": "Visualizzazione delle attivitÃ  assegnate a te",
        "Visualizza e gestisci i tuoi ordini": "Visualizza e gestisci i tuoi ordini",
        "Vuoi eliminare il locale": "Vuoi eliminare il locale",
        "Vuoi eliminare questo ordine?": "Vuoi eliminare questo ordine?",
        "Vuoi eliminare questo punto?": "Vuoi eliminare questo punto?",
        "Work Management": "Gestione attivitÃ ",
        "a": "a",
        "email non disponibile": "email non disponibile",
        "opzionale": "opzionale",
    
        "Mostra": "Mostra",
        "Telefone": "Telefono",
        "Telefone de emergÃªncia": "Telefono di emergenza",
        "Ragione Sociale": "Ragione sociale",
        "Responsabile tecnico": "Responsabile tecnico",
        "Indirizzo": "Indirizzo",
        "P.IVA": "P.IVA",
        "Datore di Lavoro": "Datore di Lavoro",
        "Intestazione azienda": "Intestazione azienda",
        "Admin ? Statistiche | FlashPoint": "Admin ? Statistiche | FlashPoint",
        "Statistiche amministrative": "Statistiche amministrative",
        "Analisi ore per periodo e localit?": "Analisi ore per periodo e localit?",
        "Periodo": "Periodo",
        "Trimestre": "Trimestre",
        "Semestre": "Semestre",
        "Anno": "Anno",
        "Applica filtro": "Applica filtro",
        "Ore del periodo": "Ore del periodo",
        "Ore dell'anno": "Ore dell'anno",
        "Top localit?": "Top localit?",
        "Ore per localit?": "Ore per localit?",
        "Ore per mese": "Ore per mese",
        "Esporta statistiche in PDF": "Esporta statistiche in PDF",
        "Seleziona un dipendente per esportare.": "Seleziona un dipendente per esportare.",},
}

# =========================
# CONFIGURAÃ‡ÃƒO DO FIREBASE (pyrebase)
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
# CONFIGURAÃ‡ÃƒO DO FIREBASE ADMIN (Firestore)
# =========================

firebase_json = os.environ.get("FIREBASE_CREDENTIALS")  # Certifique-se que o nome da variÃ¡vel bate com a do Render
if not firebase_json:
    raise Exception("VariÃ¡vel de ambiente FIREBASE_CREDENTIALS nÃ£o encontrada!")

cred_dict = json.loads(firebase_json)  # Converte JSON da variÃ¡vel em dicionÃ¡rio
cred = credentials.Certificate(cred_dict)
firebase_admin.initialize_app(cred)
db = firestore.client()


# =========================
# CONFIGURAÃ‡ÃƒO DO FIREBASE ADMIN (Firestore) (TESTE LOCAL)
# =========================

#cred = credentials.Certificate("JSON/flashpoint-V0.0.json")
#_bucket_name = firebase_config.get("storageBucket")
#if _bucket_name:
#    firebase_admin.initialize_app(cred, {"storageBucket": _bucket_name})
#else:
#    firebase_admin.initialize_app(cred)
#db = firestore.client()


# =========================
# FUNÃ‡Ã•ES AUXILIARES
# =========================
def get_current_language():
    lang = session.get("lang")
    if lang in LANGUAGE_CODES:
        return lang
    return DEFAULT_LANGUAGE


def translate(key):
    lang = get_current_language()
    if lang in TRANSLATIONS and key in TRANSLATIONS[lang]:
        return TRANSLATIONS[lang][key]
    if key in TRANSLATIONS.get(DEFAULT_LANGUAGE, {}):
        return TRANSLATIONS[DEFAULT_LANGUAGE][key]
    return key


# Garante que a funcao de traducao exista no Jinja mesmo sem context processor.
app.add_template_global(translate, name="t")


def translate_text(text):
    lang = get_current_language()
    translations = TEXT_TRANSLATIONS.get(lang, {})
    return translations.get(text, text)


app.add_template_global(translate_text, name="tr")


def safe_next_url(target):
    if not target:
        return url_for("dashboard")
    parsed = urlparse(target)
    if parsed.scheme or parsed.netloc:
        return url_for("dashboard")
    return target





def _safe_int(value, default):
    try:
        return int(value)
    except Exception:
        return default


def _period_range(periodo, anno, mese, trimestre, semestre):
    if periodo == "month":
        start = date(anno, mese, 1)
        last_day = calendar.monthrange(anno, mese)[1]
        end = date(anno, mese, last_day)
    elif periodo == "quarter":
        start_month = (trimestre - 1) * 3 + 1
        end_month = start_month + 2
        start = date(anno, start_month, 1)
        last_day = calendar.monthrange(anno, end_month)[1]
        end = date(anno, end_month, last_day)
    elif periodo == "semester":
        start_month = 1 if semestre == 1 else 7
        end_month = 6 if semestre == 1 else 12
        start = date(anno, start_month, 1)
        last_day = calendar.monthrange(anno, end_month)[1]
        end = date(anno, end_month, last_day)
    else:
        start = date(anno, 1, 1)
        end = date(anno, 12, 31)

    return start.isoformat(), end.isoformat()

@app.context_processor
def inject_i18n():
    return {
        "t": translate,
        "current_lang": get_current_language(),
        "language_options": SUPPORTED_LANGUAGES,
    }


@app.route("/set_language", methods=["POST"])
def set_language():
    lang = request.form.get("lang", "").lower()
    if lang in LANGUAGE_CODES:
        session["lang"] = lang
    next_url = request.form.get("next") or request.referrer
    return redirect(safe_next_url(next_url))

from datetime import datetime

def formatar_data_somente_data(timestamp):
    """Formata timestamp do Firebase para dd/mm/aaaa"""
    try:
        # Se for datetime
        if isinstance(timestamp, datetime):
            return timestamp.strftime("%d/%m/%Y")
        # Se for string no formato "YYYY-MM-DD"
        if isinstance(timestamp, str) and len(timestamp) == 10 and "-" in timestamp:
            dt = datetime.strptime(timestamp, "%Y-%m-%d")
            return dt.strftime("%d/%m/%Y")
        # Se for string no formato "YYYY-MM-DD HH:MM:SS"
        dt = datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S")
        return dt.strftime("%d/%m/%Y")
    except:
        return str(timestamp)

# âš ï¸ Registrar filtro no Jinja
app.jinja_env.filters['formatar_data'] = formatar_data_somente_data

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


# FunÃ§Ã£o para verificar se o usuÃ¡rio Ã© ADM
def is_admin():
    user_email = session.get("user")
    if not user_email:
        return False
    user_doc = db.collection("usuarios").document(user_email).get()
    if user_doc.exists and user_doc.to_dict().get("role") == "ADM":
        return True
    return False

def get_usuario_logado():
    """Retorna o dicionÃ¡rio do usuÃ¡rio logado pelo UID da sessÃ£o"""
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


BADGE_REQUIRED_FIELDS = [
    ("nome", "Nome"),
    ("sobrenome", "Cognome"),
    ("data_nascimento", "Data di nascita"),
    ("pais", "Paese di origine"),
    ("data_assuncao", "Data di assunzione"),
    ("cargo", "Ruolo / Mansione"),
]


def get_badge_missing_fields(usuario):
    if not isinstance(usuario, dict):
        return [{"key": key, "label": label} for key, label in BADGE_REQUIRED_FIELDS]

    faltantes = []
    for key, label in BADGE_REQUIRED_FIELDS:
        valor = usuario.get(key)
        if valor is None or not str(valor).strip():
            faltantes.append({"key": key, "label": label})
    return faltantes


def delete_points_by_uid(uid):
    """Remove todos os pontos de um usuario e retorna quantidade removida."""
    total_deleted = 0
    batch = db.batch()

    for doc in db.collection("pontos").where("uid", "==", uid).stream():
        batch.delete(doc.reference)
        total_deleted += 1

        if total_deleted % 400 == 0:
            batch.commit()
            batch = db.batch()

    if total_deleted % 400 != 0:
        batch.commit()

    return total_deleted


def is_allowed_image(filename):
    if not filename or "." not in filename:
        return False
    ext = filename.rsplit(".", 1)[1].lower()
    return ext in ALLOWED_IMAGE_EXTENSIONS


def is_remote_url(value):
    return isinstance(value, str) and value.startswith(("http://", "https://"))


def extract_storage_path_from_url(url):
    try:
        parsed = urlparse(url)
        if "firebasestorage.googleapis.com" not in parsed.netloc:
            return None
        if "/o/" not in parsed.path:
            return None
        encoded_path = parsed.path.split("/o/", 1)[1]
        return unquote(encoded_path)
    except Exception:
        return None


def delete_old_foto(foto_anterior, bucket=None):
    if not foto_anterior:
        return

    try:
        if is_remote_url(foto_anterior):
            path = extract_storage_path_from_url(foto_anterior)
            if path and bucket:
                try:
                    bucket.blob(path).delete()
                except Exception:
                    pass
            return

        if foto_anterior.startswith("perfis/") and bucket:
            try:
                bucket.blob(foto_anterior).delete()
            except Exception:
                pass
            return

        foto_anterior = os.path.basename(foto_anterior)
        if foto_anterior:
            old_path = os.path.join(app.config["UPLOAD_FOLDER"], foto_anterior)
            if os.path.isfile(old_path):
                try:
                    os.remove(old_path)
                except OSError:
                    pass
    except Exception:
        pass


def salvar_foto_perfil(file_storage, uid, foto_anterior=None):
    if not file_storage or not file_storage.filename:
        return None
    if not is_allowed_image(file_storage.filename):
        return None

    safe_name = secure_filename(file_storage.filename)
    ext = os.path.splitext(safe_name)[1].lower()
    if not ext:
        return None

    timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    new_filename = f"{uid}_{timestamp}{ext}"

    try:
        bucket = storage.bucket()
        blob_path = f"perfis/{new_filename}"
        token = uuid.uuid4().hex
        blob = bucket.blob(blob_path)
        blob.metadata = {"firebaseStorageDownloadTokens": token}
        try:
            file_storage.stream.seek(0)
        except Exception:
            pass
        blob.upload_from_file(file_storage.stream, content_type=file_storage.mimetype)

        public_url = (
            f"https://firebasestorage.googleapis.com/v0/b/{bucket.name}/o/"
            f"{quote(blob_path, safe='')}?alt=media&token={token}"
        )

        delete_old_foto(foto_anterior, bucket=bucket)
        return public_url
    except Exception:
        try:
            file_storage.stream.seek(0)
        except Exception:
            pass
        os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
        save_path = os.path.join(app.config["UPLOAD_FOLDER"], new_filename)
        file_storage.save(save_path)
        delete_old_foto(foto_anterior, bucket=None)
        return new_filename


def foto_url(value):
    if not value:
        return url_for("static", filename="img/perfis/user.png")
    if is_remote_url(value):
        return value
    return url_for("static", filename=f"img/perfis/{value}")


app.jinja_env.globals["foto_url"] = foto_url


def whatsapp_link(phone, message=""):
    if not phone:
        return ""
    digits = "".join(ch for ch in str(phone) if ch.isdigit())
    if not digits:
        return ""
    base = f"https://wa.me/{digits}"
    if message:
        return f"{base}?text={quote(message)}"
    return base


app.jinja_env.globals["whatsapp_link"] = whatsapp_link


def decimal_para_hhmm(horas_decimal):
    """Converte decimal para hh:mm"""
    return formatar_horas_hhmm(horas_decimal)

def formatar_data(data_str):
    """Converte data yyyy-mm-dd para dd/mm/aaaa"""
    try:
        dt = datetime.strptime(data_str, "%Y-%m-%d")
        return dt.strftime("%d/%m/%Y")
    except:
        return data_str

def formatar_horas_hhmm(horas_decimal):
    """Converte horas em decimal para HH:MM."""
    try:
        total_min = int(round(float(horas_decimal) * 60))
    except Exception:
        return "00:00"
    horas = total_min // 60
    minutos = total_min % 60
    return f"{horas:02d}:{minutos:02d}"
    
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
    "19 de janeiro de 2026 Ã s 21:35:39 UTC+1"
    para "19/01/2026 21:35"
    """
    try:
        # separar data e hora
        if " Ã s " in data_str:
            data_part, hora_part = data_str.split(" Ã s ")
            hora_part = hora_part.split(" ")[0]  # remove UTC+1
        else:
            data_part = data_str
            hora_part = "00:00:00"

        # mapear meses em portuguÃªs para nÃºmero
        meses = {
            "janeiro": "01",
            "fevereiro": "02",
            "marÃ§o": "03",
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

        # separar dia, mÃªs por extenso e ano
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

    return total



def ranking_mensal(ano, mes, limite=None):
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
            nomes[d["uid"]] = d.get("nome", "UsuÃ¡rio")

    ranking_ordenado = sorted(ranking.items(), key=lambda x: x[1], reverse=True)

    resultado = []
    ranking_filtrado = ranking_ordenado if limite is None else ranking_ordenado[:limite]
    for uid, horas in ranking_filtrado:
        resultado.append({
            "nome": nomes.get(uid, "UsuÃ¡rio"),
            "horas": horas,
            "horas_hhmm": formatar_horas_hhmm(horas)
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

    return total




def parse_work_due_date(due_date):
    """Converte yyyy-mm-dd para datetime para ordenaÃ§Ã£o."""
    if not due_date:
        return datetime.max
    try:
        return datetime.strptime(due_date, "%Y-%m-%d")
    except Exception:
        return datetime.max


def parse_month_range(mes_inicio, mes_fim):
    """Converte meses (YYYY-MM) em intervalo de datas (YYYY-MM-DD)."""
    if not mes_inicio and not mes_fim:
        return None, None, "Seleziona almeno un mese.", None, None

    if not mes_inicio:
        mes_inicio = mes_fim
    if not mes_fim:
        mes_fim = mes_inicio

    try:
        inicio_dt = datetime.strptime(mes_inicio, "%Y-%m")
        fim_dt = datetime.strptime(mes_fim, "%Y-%m")
    except Exception:
        return None, None, "Formato mese non valido.", None, None

    if fim_dt < inicio_dt:
        return None, None, "Il mese finale deve essere uguale o successivo al mese iniziale.", None, None

    start_date = f"{inicio_dt.year:04d}-{inicio_dt.month:02d}-01"
    last_day = calendar.monthrange(fim_dt.year, fim_dt.month)[1]
    end_date = f"{fim_dt.year:04d}-{fim_dt.month:02d}-{last_day:02d}"
    return start_date, end_date, None, mes_inicio, mes_fim


def format_backup_timestamp(value):
    if isinstance(value, datetime):
        return value.strftime("%Y-%m-%d %H:%M:%S")
    try:
        return value.isoformat()
    except Exception:
        return str(value)


def build_backup_filename(mes_inicio, mes_fim, filtro_usuario=None):
    periodo = mes_inicio if mes_inicio == mes_fim else f"{mes_inicio}_a_{mes_fim}"
    safe_uid = secure_filename(filtro_usuario) if filtro_usuario else ""
    uid_part = f"_{safe_uid}" if safe_uid else ""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"backup_pontos{uid_part}_{periodo}_{timestamp}.csv"


def get_usuarios_map():
    usuarios_map = {}
    for doc in db.collection("usuarios").stream():
        d = doc.to_dict()
        nome = f"{d.get('nome', '')} {d.get('sobrenome', '')}".strip()
        usuarios_map[doc.id] = nome or doc.id
    return usuarios_map



# =========================
# ROTAS
# =========================


# =========================
# WORK MANAGEMENT (CRUD TAREFAS)
# =========================
@app.route("/work_management", methods=["GET", "POST"])
def work_management():
    if "uid" not in session:
        return redirect("/")

    uid = session["uid"]
    usuario_doc = db.collection("usuarios").document(uid).get()
    usuario = usuario_doc.to_dict() if usuario_doc.exists else {}
    is_admin_user = usuario.get("tipo") == "admin"

    if request.method == "POST":
        if not is_admin_user:
            flash("Somente administradores podem criar ou editar tarefas.", "danger")
            return redirect(url_for("work_management"))

        acao = request.form.get("acao")

        if acao == "criar":
            titulo = request.form.get("titulo", "").strip()
            descricao = request.form.get("descricao", "").strip()
            prioridade = request.form.get("prioridade", "media")
            due_date = request.form.get("due_date", "")
            assigned_uids = [uid.strip() for uid in request.form.getlist("assigned_uids") if uid.strip()]

            if not titulo:
                flash("O tÃ­tulo da tarefa Ã© obrigatÃ³rio.", "danger")
            elif not assigned_uids:
                flash("Selecione pelo menos um colaborador responsÃ¡vel pela tarefa.", "danger")
            else:
                assigned_names = []
                valid_assigned_uids = []

                for assigned_uid in assigned_uids:
                    assigned_doc = db.collection("usuarios").document(assigned_uid).get()
                    if assigned_doc.exists:
                        assigned_data = assigned_doc.to_dict()
                        assigned_name = f"{assigned_data.get('nome', '')} {assigned_data.get('sobrenome', '')}".strip()
                        assigned_names.append(assigned_name or assigned_uid)
                        valid_assigned_uids.append(assigned_uid)

                if not valid_assigned_uids:
                    flash("Nenhum colaborador vÃ¡lido foi selecionado.", "danger")
                else:
                    created_by = f"{usuario.get('nome', '')} {usuario.get('sobrenome', '')}".strip()

                    db.collection("work_items").add({
                        "created_by_uid": uid,
                        "created_by_nome": created_by,
                        "assigned_uid": valid_assigned_uids[0],
                        "assigned_nome": assigned_names[0],
                        "assigned_uids": valid_assigned_uids,
                        "assigned_nomes": assigned_names,
                        "titulo": titulo,
                        "descricao": descricao,
                        "prioridade": prioridade,
                        "status": "todo",
                        "due_date": due_date,
                        "criado_em": firestore.SERVER_TIMESTAMP,
                    })
                    flash("Tarefa criada e designada com sucesso.", "success")

        elif acao == "status":
            item_id = request.form.get("item_id")
            novo_status = request.form.get("novo_status")

            if item_id and novo_status in {"todo", "in_progress", "done"}:
                item_ref = db.collection("work_items").document(item_id)
                item_doc = item_ref.get()
                if item_doc.exists:
                    item_ref.update({"status": novo_status})
                    flash("Status atualizado.", "success")

        elif acao == "excluir":
            item_id = request.form.get("item_id")
            if item_id:
                item_ref = db.collection("work_items").document(item_id)
                item_doc = item_ref.get()
                if item_doc.exists:
                    item_ref.delete()
                    flash("Tarefa excluÃ­da.", "success")

        return redirect(url_for("work_management"))

    status_filtro = request.args.get("status", "all")

    items_docs = db.collection("work_items").stream()
    items = []

    for doc in items_docs:
        data = doc.to_dict()
        data["id"] = doc.id

        assigned_uids_item = data.get("assigned_uids")
        if not isinstance(assigned_uids_item, list):
            assigned_uids_item = [data.get("assigned_uid")] if data.get("assigned_uid") else []

        data["assigned_uids"] = assigned_uids_item

        assigned_nomes_item = data.get("assigned_nomes")
        if not isinstance(assigned_nomes_item, list):
            assigned_nomes_item = [data.get("assigned_nome")] if data.get("assigned_nome") else []

        data["assigned_nomes"] = assigned_nomes_item

        if not is_admin_user and uid not in assigned_uids_item:
            continue

        if status_filtro != "all" and data.get("status") != status_filtro:
            continue

        items.append(data)

    items.sort(key=lambda x: (x.get("status") == "done", parse_work_due_date(x.get("due_date"))))

    contadores = {"todo": 0, "in_progress": 0, "done": 0}
    for item in items:
        st = item.get("status", "todo")
        if st in contadores:
            contadores[st] += 1

    colaboradores = []
    if is_admin_user:
        usuarios_docs = db.collection("usuarios").stream()
        for u in usuarios_docs:
            d = u.to_dict()
            nome = f"{d.get('nome', '')} {d.get('sobrenome', '')}".strip()
            colaboradores.append({"uid": u.id, "nome": nome or u.id})
        colaboradores.sort(key=lambda c: c["nome"].lower())

    return render_template(
        "work_management.html",
        items=items,
        status_filtro=status_filtro,
        contadores=contadores,
        is_admin_user=is_admin_user,
        colaboradores=colaboradores
    )



# =========================
# DASHBOARD/HOME
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

    # UsuÃ¡rio
    usuario_doc = db.collection("usuarios").document(uid).get()
    if not usuario_doc.exists:
        return redirect("/")

    usuario = usuario_doc.to_dict()
    nome_usuario = usuario.get("nome", "UsuÃ¡rio")

    # Horas
    horas_mes_atual = horas_por_mes(uid, hoje.year, hoje.month)

    mes_anterior = hoje.month - 1 if hoje.month > 1 else 12
    ano_anterior = hoje.year if hoje.month > 1 else hoje.year - 1
    horas_mes_anterior = horas_por_mes(uid, ano_anterior, mes_anterior)

    horas_ano = horas_por_ano(uid, hoje.year)

    # Ranking mensal
    ranking = ranking_mensal(hoje.year, hoje.month)

    # PosiÃ§Ã£o do usuÃ¡rio no ranking (CORRIGIDO)
    posicao = "-"
    for i, r in enumerate(ranking):
        if r["nome"] == nome_usuario:
            posicao = i + 1
            break

    return render_template(
        "dashboard.html",
        usuario=usuario,
        horas_mes_atual=formatar_horas_hhmm(horas_mes_atual),
        horas_mes_anterior=formatar_horas_hhmm(horas_mes_anterior),
        horas_ano=formatar_horas_hhmm(horas_ano),
        ranking=ranking,
        posicao=posicao
    )


# =========================
# HOME
# =========================

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

    # posiÃ§Ã£o do usuÃ¡rio no ranking
    posicao = "-"
    for i, r in enumerate(ranking):
        if r["nome"]:
            posicao = i + 1
            break

    return render_template(
    "home.html",
    horas_mes_atual=formatar_horas_hhmm(horas_mes_atual),
    horas_mes_anterior=formatar_horas_hhmm(horas_mes_anterior),
    horas_ano=formatar_horas_hhmm(horas_ano),
    ranking=ranking,
    posicao=posicao
)



# =========================
# AJUDA / MANUAL
# =========================

@app.route("/help")
def help_page():
    if "uid" not in session:
        return redirect("/")

    usuario = get_usuario_logado() or {}
    is_admin_user = usuario.get("tipo") == "admin"
    return render_template("help.html", is_admin_user=is_admin_user)


@app.route("/help/manuale/<tipo>")
def help_manuale(tipo):
    if "uid" not in session:
        return redirect("/")

    usuario = get_usuario_logado() or {}
    is_admin_user = usuario.get("tipo") == "admin"

    if tipo == "consigliato":
        tipo = "admin" if is_admin_user else "dipendente"

    if tipo == "admin" and not is_admin_user:
        return redirect(url_for("help_manuale", tipo="dipendente"))

    manuals = {
        "dipendente": ("MANUALE_UTENTE_DIPENDENTE_IT.md", "Manuale Utente Dipendente"),
        "admin": ("MANUALE_UTENTE_ADMIN_IT.md", "Manuale Utente Admin"),
    }

    if tipo not in manuals:
        return redirect(url_for("help_page"))

    filename, titolo = manuals[tipo]
    manual_path = os.path.join(app.root_path, filename)
    if not os.path.exists(manual_path):
        return redirect(url_for("help_page"))

    with open(manual_path, "r", encoding="utf-8") as handle:
        contenuto = handle.read()

    return render_template(
        "help_manuale.html",
        titolo=titolo,
        contenuto=contenuto,
        is_admin_user=is_admin_user
    )


# =========================
# LOGIN
# =========================

@app.route("/esqueci_senha", methods=["GET", "POST"])
def esqueci_senha():
    mensagem = None
    error = None

    if request.method == "POST":
        email = (request.form.get("email") or "").strip()

        if not email:
            error = "Inserisci un indirizzo email valido."
        else:
            try:
                auth.send_password_reset_email(email)
                mensagem = "Se l'email esiste, riceverai un link per recuperare la password."
            except Exception:
                mensagem = "Se l'email esiste, riceverai un link per recuperare la password."

    return render_template(
        "esqueci_senha.html",
        mensagem=mensagem,
        error=error
    )

@app.route("/", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        try:
            user = auth.sign_in_with_email_and_password(email, password)
            session["uid"] = user["localId"]  # Armazena somente UID
            session["email"] = user.get("email", email)
            return redirect("/home")
        except:
            error = "Email ou senha invÃ¡lidos"
    return render_template("login.html", error=error)


# =========================
# REGISTER
# =========================

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
                "foto_url": "user.png",
                "tipo": "usuario"
            })

            success = "Utente creato con successo! Effettua il login."

        except Exception as e:
            erro_str = str(e)

            if "EMAIL_EXISTS" in erro_str:
                error = "Questo email Ã¨ giÃ  registrato. Prova ad effettuare il login."
            elif "WEAK_PASSWORD" in erro_str:
                error = "La password deve avere almeno 6 caratteri."
            elif "INVALID_EMAIL" in erro_str:
                error = "Inserisci un indirizzo email valido."
            else:
                error = "Errore durante la registrazione. Riprova piÃ¹ tardi."

    return render_template("register.html", error=error, success=success)




# =========================
# PERFIL USUÃRIO
# =========================

@app.route("/perfil")
def perfil_usuario():
    if "uid" not in session:
        return redirect("/")

    uid = session["uid"]
    usuario = db.collection("usuarios").document(uid).get().to_dict()

    ano_atual = datetime.now().year
    total_horas_ano = formatar_horas_hhmm(horas_por_ano(uid, ano_atual))

    return render_template(
        "perfil.html",
        usuario=usuario,
        total_horas_ano=total_horas_ano,
        ano_atual=ano_atual
    )


# =========================
# PERFIL EDITAR
# =========================

@app.route("/perfil/editar", methods=["GET", "POST"])
def perfil_editar():
    if "uid" not in session:
        return redirect("/")

    uid = session["uid"]
    usuario_ref = db.collection("usuarios").document(uid)
    usuario = usuario_ref.get().to_dict()

    if request.method == "POST":
        foto_input = (request.form.get("foto_url") or "").strip()
        update_data = {
            "nome": request.form.get("nome"),
            "sobrenome": request.form.get("sobrenome"),
            "data_nascimento": request.form.get("data_nascimento"),
            "pais": request.form.get("pais"),
            "telefone": request.form.get("telefone"),
            "telefone_emergencia": request.form.get("telefone_emergencia"),
            "foto_url": foto_input,
        }

        usuario_ref.update(update_data)
        return redirect("/perfil")

    return render_template("perfil_editar.html", usuario=usuario)


# =========================
# PERFIL - TROCAR SENHA
# =========================

@app.route("/perfil/trocar_senha", methods=["GET", "POST"])
def perfil_trocar_senha():
    if "uid" not in session:
        return redirect("/")

    uid = session["uid"]
    usuario_doc = db.collection("usuarios").document(uid).get()
    usuario = usuario_doc.to_dict() if usuario_doc.exists else {}

    mensagem = None
    error = None

    if request.method == "POST":
        senha_atual = (request.form.get("senha_atual") or "").strip()
        nova_senha = (request.form.get("nova_senha") or "").strip()
        confirmar_senha = (request.form.get("confirmar_senha") or "").strip()

        if not senha_atual or not nova_senha or not confirmar_senha:
            error = "Compila tutti i campi."
        elif len(nova_senha) < 6:
            error = "La nuova password deve avere almeno 6 caratteri."
        elif nova_senha != confirmar_senha:
            error = "La conferma della nuova password non coincide."

        email_usuario = (
            (session.get("email") or "").strip()
            or (usuario.get("email") or "").strip()
        )

        if not error and not email_usuario:
            error = "Email utente non disponibile. Contatta l'amministratore."

        if not error:
            try:
                auth.sign_in_with_email_and_password(email_usuario, senha_atual)
            except Exception:
                error = "Password attuale non valida."

        if not error:
            try:
                admin_auth.update_user(uid, password=nova_senha)
                mensagem = "Password aggiornata con successo."
            except Exception:
                error = "Errore durante l'aggiornamento della password. Riprova."

    return render_template(
        "perfil_trocar_senha.html",
        usuario=usuario,
        mensagem=mensagem,
        error=error,
    )


# =========================
# ADMIN - ESTATISTICHE
# =========================

@app.route("/admin/estatisticas", methods=["GET"])
def admin_estatisticas():
    usuario = get_usuario_logado()
    if not usuario or usuario.get("tipo") != "admin":
        return redirect("/dashboard")

    hoje = datetime.now()
    periodo = request.args.get("periodo", "month")
    anno = _safe_int(request.args.get("anno"), hoje.year)
    mese = _safe_int(request.args.get("mese"), hoje.month)
    trimestre = _safe_int(request.args.get("trimestre"), ((hoje.month - 1) // 3) + 1)
    semestre = _safe_int(request.args.get("semestre"), 1 if hoje.month <= 6 else 2)

    if mese < 1 or mese > 12:
        mese = hoje.month
    if trimestre < 1 or trimestre > 4:
        trimestre = ((hoje.month - 1) // 3) + 1
    if semestre not in (1, 2):
        semestre = 1 if hoje.month <= 6 else 2

    start_date, end_date = _period_range(periodo, anno, mese, trimestre, semestre)

    pontos_ref = db.collection("pontos")
    manual_filter = False
    try:
        pontos_docs = list(pontos_ref.where("data", ">=", start_date).where("data", "<=", end_date).stream())
    except Exception:
        manual_filter = True
        pontos_docs = list(db.collection("pontos").stream())

    total_periodo = 0.0
    horas_por_local = {}

    for doc in pontos_docs:
        p = doc.to_dict()
        data_str = p.get("data", "")
        if manual_filter and not (start_date <= data_str <= end_date):
            continue

        try:
            horas_val = float(p.get("horas", 0))
        except Exception:
            horas_val = 0.0

        total_periodo += horas_val
        local = p.get("local", "-") or "-"
        horas_por_local[local] = horas_por_local.get(local, 0.0) + horas_val

    locais_ordenados = sorted(horas_por_local.items(), key=lambda x: x[1], reverse=True)
    top_local_nome = locais_ordenados[0][0] if locais_ordenados else "-"
    top_local_horas = formatar_horas_hhmm(locais_ordenados[0][1]) if locais_ordenados else "00:00"

    locais_table = [
        {"nome": nome, "horas": formatar_horas_hhmm(h)}
        for nome, h in locais_ordenados
    ]

    top_locais_labels = [l[0] for l in locais_ordenados[:8]]
    top_locais_values = [round(l[1], 2) for l in locais_ordenados[:8]]

    # Totale anno + ore per mese
    start_anno = f"{anno}-01-01"
    end_anno = f"{anno}-12-31"
    manual_filter_year = False
    try:
        pontos_anno = list(db.collection("pontos").where("data", ">=", start_anno).where("data", "<=", end_anno).stream())
    except Exception:
        manual_filter_year = True
        pontos_anno = list(db.collection("pontos").stream())

    total_anno = 0.0
    ore_per_mese = [0.0] * 12
    for doc in pontos_anno:
        p = doc.to_dict()
        data_str = p.get("data", "")
        if manual_filter_year and not (start_anno <= data_str <= end_anno):
            continue
        try:
            data_obj = datetime.strptime(data_str, "%Y-%m-%d")
        except Exception:
            continue
        try:
            horas_val = float(p.get("horas", 0))
        except Exception:
            horas_val = 0.0

        total_anno += horas_val
        ore_per_mese[data_obj.month - 1] += horas_val

    mesi_labels = ["Gen", "Feb", "Mar", "Apr", "Mag", "Giu", "Lug", "Ago", "Set", "Ott", "Nov", "Dic"]

    return render_template(
        "admin_estatisticas.html",
        periodo=periodo,
        anno=anno,
        mese=mese,
        trimestre=trimestre,
        semestre=semestre,
        start_date=start_date,
        end_date=end_date,
        total_periodo=formatar_horas_hhmm(total_periodo),
        total_anno=formatar_horas_hhmm(total_anno),
        top_local_nome=top_local_nome,
        top_local_horas=top_local_horas,
        locais_table=locais_table,
        locais_labels=json.dumps(top_locais_labels),
        locais_values=json.dumps(top_locais_values),
        mesi_labels=json.dumps(mesi_labels),
        mesi_values=json.dumps([round(v, 2) for v in ore_per_mese]),
    )


# =========================
# ADMIN - PERFIS USUÃRIOS
# =========================

@app.route("/admin/perfis", methods=["GET"])
def admin_perfis():
    usuario = get_usuario_logado()
    if not usuario or usuario.get("tipo") != "admin":
        return redirect("/dashboard")

    usuarios = get_all_users()
    usuarios = sorted(
        usuarios,
        key=lambda u: f"{u.get('nome','')} {u.get('sobrenome','')}".strip().lower()
    )
    return render_template("admin_perfis.html", usuarios=usuarios)


@app.route("/admin/perfis/editar/<uid>", methods=["GET", "POST"])
def admin_perfil_editar(uid):
    usuario_logado = get_usuario_logado()
    if not usuario_logado or usuario_logado.get("tipo") != "admin":
        return redirect("/dashboard")

    usuario_ref = db.collection("usuarios").document(uid)
    usuario_doc = usuario_ref.get()
    if not usuario_doc.exists:
        return "Utente non trovato"

    usuario = usuario_doc.to_dict()
    usuario["uid"] = uid

    if request.method == "POST":
        foto_input = (request.form.get("foto_url") or "").strip()
        update_data = {
            "nome": request.form.get("nome"),
            "sobrenome": request.form.get("sobrenome"),
            "data_nascimento": request.form.get("data_nascimento"),
            "pais": request.form.get("pais"),
            "data_assuncao": request.form.get("data_assuncao"),
            "cargo": request.form.get("cargo"),
            "etichetta_azienda": request.form.get("etichetta_azienda", ""),
            "telefone": request.form.get("telefone"),
            "telefone_emergencia": request.form.get("telefone_emergencia"),
            "foto_url": foto_input,
        }

        usuario_ref.update(update_data)
        return redirect(url_for("admin_perfis"))

    return render_template("admin_perfil_editar.html", usuario=usuario)


@app.route("/admin/perfis/excluir", methods=["POST"])
def admin_perfil_excluir():
    usuario_logado = get_usuario_logado()
    if not usuario_logado or usuario_logado.get("tipo") != "admin":
        return redirect("/dashboard")

    uid_alvo = (request.form.get("uid") or "").strip()
    excluir_pontos = (request.form.get("excluir_pontos") or "").strip() == "1"

    if not uid_alvo:
        flash("Utente non valido.", "danger")
        return redirect(url_for("admin_perfis"))

    uid_admin = session.get("uid")
    if uid_admin and uid_alvo == uid_admin:
        flash("Nao e consentito eliminare il proprio utente amministratore.", "danger")
        return redirect(url_for("admin_perfis"))

    usuario_ref = db.collection("usuarios").document(uid_alvo)
    usuario_doc = usuario_ref.get()
    if not usuario_doc.exists:
        flash("Utente non trovato.", "danger")
        return redirect(url_for("admin_perfis"))

    usuario_alvo = usuario_doc.to_dict() or {}
    nome_alvo = f"{usuario_alvo.get('nome', '')} {usuario_alvo.get('sobrenome', '')}".strip() or uid_alvo

    total_pontos_removidos = 0
    if excluir_pontos:
        total_pontos_removidos = delete_points_by_uid(uid_alvo)

    foto_alvo = (usuario_alvo.get("foto_url") or "").strip()
    if foto_alvo and foto_alvo != "user.png":
        bucket = None
        try:
            bucket = storage.bucket()
        except Exception:
            bucket = None
        delete_old_foto(foto_alvo, bucket=bucket)

    usuario_ref.delete()

    try:
        admin_auth.delete_user(uid_alvo)
    except Exception:
        pass

    if excluir_pontos:
        flash(
            f'Utente "{nome_alvo}" eliminato. Presenze rimosse: {total_pontos_removidos}.',
            "success",
        )
    else:
        flash(f'Utente "{nome_alvo}" eliminato.', "success")

    return redirect(url_for("admin_perfis"))


# =========================
# REGISTRAR PONTO
# =========================

from datetime import datetime, timedelta
from flask import render_template, redirect, session, request, url_for

@app.route("/admin/registrar_ponto", methods=["GET", "POST"])
def admin_registrar_ponto():
    if "uid" not in session:
        return redirect("/")

    uid_admin = session["uid"]
    admin_doc = db.collection("usuarios").document(uid_admin).get()
    admin_user = admin_doc.to_dict() if admin_doc.exists else {}
    if admin_user.get("tipo") != "admin":
        return redirect("/dashboard")

    usuarios = []
    for doc in db.collection("usuarios").stream():
        udata = doc.to_dict() or {}
        if (udata.get("tipo") or "").lower() == "admin":
            continue

        nome_completo = f"{udata.get('nome', '')} {udata.get('sobrenome', '')}".strip()
        usuarios.append({
            "uid": doc.id,
            "nome": nome_completo or udata.get("email") or doc.id
        })
    usuarios.sort(key=lambda u: u["nome"].lower())

    locais = []
    for doc in db.collection("locais").stream():
        ldata = doc.to_dict() or {}
        nome_local = ldata.get("ragione_sociale") or ldata.get("nome")
        if nome_local and nome_local not in locais:
            locais.append(nome_local)
    locais.sort()

    mensagem = None
    error = None

    if request.method == "POST":
        uid_funcionario = (request.form.get("uid_usuario") or "").strip()
        data_ponto = (request.form.get("data") or "").strip()
        local_selecionado = (request.form.get("local") or "").strip()
        horas_input = (request.form.get("horas") or "").strip().replace(",", ".")
        notas_input = (request.form.get("notas") or "").strip()
        is_sick = (request.form.get("is_sick") or "").lower() in {"1", "on", "true", "yes"}
        is_vacation = (request.form.get("is_vacation") or "").lower() in {"1", "on", "true", "yes"}
        tipo_registro = "presenza"

        if is_sick and is_vacation:
            error = translate("clock_in.only_one_absence_type")

        if is_sick:
            tipo_registro = "malattia"
        elif is_vacation:
            tipo_registro = "ferie"

        if not uid_funcionario or not data_ponto:
            error = "Compila tutti i campi obbligatori."

        if not error and tipo_registro == "presenza" and not local_selecionado:
            error = "Seleziona il luogo."

        if not local_selecionado:
            local_selecionado = "-"

        funcionario_doc = None
        funcionario = {}
        if not error:
            funcionario_doc = db.collection("usuarios").document(uid_funcionario).get()
            if not funcionario_doc.exists:
                error = "Dipendente non trovato."
            else:
                funcionario = funcionario_doc.to_dict() or {}
                if (funcionario.get("tipo") or "").lower() == "admin":
                    error = "Seleziona un dipendente valido."

        horas = 0.0
        if not error:
            if tipo_registro in {"malattia", "ferie"}:
                horas = 0.0
                local_selecionado = "-"
            else:
                try:
                    horas = float(horas_input)
                    if horas <= 0:
                        raise ValueError()
                except Exception:
                    error = "Inserisci un numero valido di ore!"

        if not error:
            try:
                datetime.strptime(data_ponto, "%Y-%m-%d")
            except Exception:
                error = "Data non valida."

        if not error:
            pontos_existentes = db.collection("pontos") \
                .where("uid", "==", uid_funcionario) \
                .where("data", "==", data_ponto) \
                .stream()

            if any(pontos_existentes):
                error = f"Il dipendente ha giÃ  una presenza registrata per {data_ponto}."

        if not error:
            agora_italia = datetime.utcnow() + timedelta(hours=1)
            nome_funcionario = f"{funcionario.get('nome', '')} {funcionario.get('sobrenome', '')}".strip()

            db.collection("pontos").add({
                "uid": uid_funcionario,
                "nome": nome_funcionario or funcionario.get("nome") or "Desconhecido",
                "local": local_selecionado,
                "data": data_ponto,
                "horas": horas,
                "notas": notas_input,
                "tipo_registro": tipo_registro,
                "criado_em": agora_italia,
                "registrado_por_admin_uid": uid_admin,
            })
            if tipo_registro == "malattia":
                mensagem = translate("clock_in.sick_registered_success")
            elif tipo_registro == "ferie":
                mensagem = translate("clock_in.vacation_registered_success")
            else:
                mensagem = "Presenza registrata con successo."

    return render_template(
        "admin_registrar_ponto.html",
        usuarios=usuarios,
        locais=locais,
        mensagem=mensagem,
        error=error,
    )

@app.route("/registrar_ponto", methods=["GET", "POST"])
def registrar_ponto_usuario():
    if "uid" not in session:
        return redirect("/")

    uid = session["uid"]
    usuario_doc = db.collection("usuarios").document(uid).get()
    usuario = usuario_doc.to_dict() if usuario_doc.exists else {"nome": "Desconhecido"}

    # HorÃ¡rio ItÃ¡lia (UTC+1, fixo)
    agora = datetime.utcnow() + timedelta(hours=1)

    # Buscar locais do Firestore
    locais_docs = db.collection("locais").stream()
    locais = []  # opÃ§Ã£o padrÃ£o
    for doc in locais_docs:
        data = doc.to_dict()
        nome_local = data.get("ragione_sociale") or data.get("nome")
        if nome_local:
            locais.append({"nome": nome_local})

    mensagem = None
    error = None

    if request.method == "POST":
        data_ponto = request.form.get("data")
        local_selecionado = (request.form.get("local") or "").strip()
        horas_input = request.form.get("horas")
        notas_input = request.form.get("notas", "")
        is_sick = (request.form.get("is_sick") or "").lower() in {"1", "on", "true", "yes"}
        is_vacation = (request.form.get("is_vacation") or "").lower() in {"1", "on", "true", "yes"}
        tipo_registro = "presenza"

        if is_sick and is_vacation:
            error = translate("clock_in.only_one_absence_type")

        if is_sick:
            tipo_registro = "malattia"
        elif is_vacation:
            tipo_registro = "ferie"

        if not local_selecionado:
            local_selecionado = "-"

        horas = 0.0
        if tipo_registro in {"malattia", "ferie"}:
            local_selecionado = "-"
        else:
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
            error = f"Hai giÃ  registrato una presenza per {data_ponto}!"
        
        if not error:
            ponto_data = {
                "uid": uid,
                "nome": usuario["nome"],
                "local": local_selecionado,
                "data": data_ponto,
                "horas": horas,
                "notas": notas_input,
                "tipo_registro": tipo_registro,
                "criado_em": agora  # salva com fuso ItÃ¡lia (UTC+1)
            }
            db.collection("pontos").add(ponto_data)
            if tipo_registro == "malattia":
                mensagem = translate("clock_in.sick_registered_success")
            elif tipo_registro == "ferie":
                mensagem = translate("clock_in.vacation_registered_success")
            else:
                mensagem = "Ora registrata con successo!"

    return render_template(
        "registrar_ponto.html",
        locais=locais,
        mensagem=mensagem,
        error=error
    )



# =========================
# MEUS PONTOS
# =========================

from datetime import datetime, timedelta
from flask import render_template, redirect, session, request

@app.route("/meus_pontos", methods=["GET", "POST"])
def meus_pontos():
    if "uid" not in session:
        return redirect("/")

    uid = session["uid"]

    # Fuso horÃ¡rio ItÃ¡lia: UTC+1 (considerando horÃ¡rio padrÃ£o)
    # OBS: NÃ£o calcula horÃ¡rio de verÃ£o automaticamente
    def agora_italia():
        return datetime.utcnow() + timedelta(hours=1)

    agora = agora_italia()

    filtro_data = (request.form.get("filtro_data") or "").strip()
    filtro_mes = (request.form.get("filtro_mes") or "").strip()

    # Padrao: carregar apenas o mes atual.
    # Se houver data especifica, ela tem prioridade sobre o filtro mensal.
    if filtro_data:
        filtro_mes = ""
    elif not filtro_mes:
        filtro_mes = agora.strftime("%Y-%m")

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

        # Converte string para datetime (fuso fixo ItÃ¡lia)
        data_obj = datetime.strptime(p["data"], "%Y-%m-%d") + timedelta(hours=1)

        # Aplicar filtros
        if filtro_data and p["data"] != filtro_data:
            continue

        if filtro_mes:
            try:
                ano, mes = map(int, filtro_mes.split("-"))
                if data_obj.year != ano or data_obj.month != mes:
                    continue
            except Exception:
                pass

        # Dia da semana + data
        dia_semana = dias_semana[data_obj.weekday()]
        data_formatada = f"{data_obj.strftime('%d/%m/%Y')} - {dia_semana}"

        tipo_registro = (p.get("tipo_registro") or "presenza").lower()

        # Horas HH:MM
        horas_totais = 0.0 if tipo_registro in {"malattia", "ferie"} else float(p.get("horas", 0))
        horas_hhmm = formatar_horas_hhmm(horas_totais)

        pontos.append({
            "id": doc.id,
            "data": p["data"],
            "data_formatada": data_formatada,
            "local": p.get("local", "-"),
            "tipo_registro": tipo_registro,
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
        total_horas=formatar_horas_hhmm(total_horas),
        filtro_data=filtro_data,
        filtro_mes=filtro_mes
    )




# =========================
# ADMIN PONTOS
# =========================

from datetime import datetime

@app.route("/admin_pontos", methods=["GET", "POST"])
def admin_pontos():
    if "uid" not in session:
        return redirect("/")

    uid = session["uid"]

    # Usu?rio logado
    usuario_doc = db.collection("usuarios").document(uid).get()
    usuario = usuario_doc.to_dict() if usuario_doc.exists else {}

    if usuario.get("tipo") != "admin":
        return "Acesso negado"

    filtro_usuario = "__none__"
    filtro_mes = ""
    filtro_local = ""

    if request.method == "POST":
        filtro_usuario = request.form.get("filtro_usuario", "__none__")
        filtro_mes = request.form.get("filtro_mes", "")
        filtro_local = request.form.get("filtro_local", "")

    usuarios_ref = db.collection("usuarios").stream()
    usuarios = []
    for u in usuarios_ref:
        ud = u.to_dict()
        usuarios.append({
            "uid": u.id,
            "nome": f"{ud.get('nome','')} {ud.get('sobrenome','')}"
        })

    locais_ref = db.collection("locais").stream()
    locais = []
    for l in locais_ref:
        l_data = l.to_dict()
        if not l_data:
            continue
        nome_local = l_data.get("ragione_sociale") or l_data.get("nome")
        if nome_local:
            locais.append(nome_local)
    locais.sort()

    if filtro_usuario == "__none__":
        return render_template(
            "admin_pontos.html",
            pontos=[],
            total_horas=formatar_horas_hhmm(0),
            usuarios=usuarios,
            locais=locais,
            filtro_usuario=filtro_usuario,
            filtro_mes=filtro_mes,
            filtro_local=filtro_local,
            export_error=request.args.get("export_error")
        )

    pontos_ref = db.collection("pontos").stream()
    pontos_list = []

    total_horas = 0
    dias_semana = {
        0: "LUN",
        1: "MAR",
        2: "MER",
        3: "GIO",
        4: "VEN",
        5: "SAB",
        6: "DOM",
    }

    for doc in pontos_ref:
        p = doc.to_dict()
        p["id"] = doc.id

        # Filtro usu?rio
        if filtro_usuario and filtro_usuario != "__none__" and p.get("uid") != filtro_usuario:
            continue

        # Filtro m?s (YYYY-MM)
        if filtro_mes:
            if not p.get("data", "").startswith(filtro_mes):
                continue

        # Filtro locale
        if filtro_local:
            if p.get("local", "") != filtro_local:
                continue

        p["tipo_registro"] = (p.get("tipo_registro") or "presenza").lower()

        # Soma horas
        horas = 0.0 if p["tipo_registro"] in {"malattia", "ferie"} else float(p.get("horas", 0))
        total_horas += horas

        # =========================
        # ?? DATA (ORDENA + FORMATA)
        # =========================
        data_raw = p.get("data")
        try:
            data_obj = datetime.strptime(data_raw, "%Y-%m-%d")
            p["data_ordem"] = data_obj              # usada s? para ordena??o
            dia_semana = dias_semana.get(data_obj.weekday(), "")
            p["data_formatada"] = f"{data_obj.strftime('%d/%m/%Y')} - {dia_semana}"
        except Exception:
            p["data_ordem"] = datetime.min
            p["data_formatada"] = "-"

        # ?? Formata horas HH:MM
        p["horas_formatadas"] = formatar_horas_hhmm(horas)

        # Nome usu?rio
        usuario_p = db.collection("usuarios").document(p["uid"]).get()
        if usuario_p.exists:
            udata = usuario_p.to_dict()
            p["usuario_nome"] = f"{udata.get('nome','')} {udata.get('sobrenome','')}"
        else:
            p["usuario_nome"] = "-"

        pontos_list.append(p)

    # =========================
    # ?? ORDENA POR DATA (DESC)
    # =========================
    pontos_list.sort(key=lambda x: x["data_ordem"], reverse=False)

    return render_template(
        "admin_pontos.html",
        pontos=pontos_list,
        total_horas=formatar_horas_hhmm(total_horas),
        usuarios=usuarios,
        locais=locais,
        filtro_usuario=filtro_usuario,
        filtro_mes=filtro_mes,
        filtro_local=filtro_local
    )

# =========================
# ADMIN EXPORTAR PONTOS PDF
# =========================

@app.route("/admin_pontos/exportar_pdf")
def admin_pontos_exportar_pdf():
    if "uid" not in session:
        return redirect("/")

    uid_admin = session["uid"]
    usuario_doc = db.collection("usuarios").document(uid_admin).get()
    usuario = usuario_doc.to_dict() if usuario_doc.exists else {}
    if usuario.get("tipo") != "admin":
        return "Acesso negado"

    filtro_usuario = (request.args.get("filtro_usuario") or "").strip()
    filtro_mes = (request.args.get("filtro_mes") or "").strip()
    filtro_local = (request.args.get("filtro_local") or "").strip()

    if not filtro_usuario or filtro_usuario == "__none__":
        return redirect(url_for("admin_pontos", export_error="Seleziona un dipendente per esportare."))

    usuario_ref = db.collection("usuarios").document(filtro_usuario).get()
    if not usuario_ref.exists:
        return redirect(url_for("admin_pontos", export_error="Seleziona un dipendente per esportare."))

    udata = usuario_ref.to_dict()
    nome_usuario = f"{udata.get('nome','')} {udata.get('sobrenome','')}".strip()

    pontos_docs = db.collection("pontos").where("uid", "==", filtro_usuario).stream()

    cell_style = ParagraphStyle(
        "cell",
        parent=getSampleStyleSheet()["Normal"],
        fontSize=9,
        leading=11
    )
    cell_style.wordWrap = "CJK"

    dados = []
    total_horas = 0.0

    for doc in pontos_docs:
        p = doc.to_dict()
        data_str = p.get("data")
        if not data_str:
            continue

        if filtro_mes and not data_str.startswith(filtro_mes):
            continue

        if filtro_local and p.get("local", "") != filtro_local:
            continue

        try:
            horas_val = float(p.get("horas", 0))
        except Exception:
            horas_val = 0.0

        total_horas += horas_val

        dados.append([
            formatar_data(data_str),
            p.get("local", "-"),
            formatar_horas_hhmm(horas_val),
            Paragraph(p.get("notas", "") or "-", cell_style)
        ])

    if not dados:
        return redirect(url_for("admin_pontos", export_error="Nessuna presenza trovata con questi filtri."))

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
    cell_style = ParagraphStyle(
        "cell",
        parent=styles["Normal"],
        fontSize=9,
        leading=11
    )
    cell_style.wordWrap = "CJK"
    elementos = []

    logo_path = os.path.join(
        os.path.dirname(__file__), "static", "img", "logo-login.png"
    )
    if os.path.exists(logo_path):
        elementos.append(Image(logo_path, width=5.5*cm, height=2.5*cm))
        elementos.append(Spacer(1, 12))

    elementos.append(Paragraph("Rapporto presenze", styles["Title"]))
    elementos.append(Spacer(1, 12))

    if filtro_mes and "-" in filtro_mes:
        ano, mes = filtro_mes.split("-")
        periodo = f"{mes}/{ano}"
    else:
        periodo = "Tutto il periodo"
    if filtro_local:
        periodo = f"{periodo} - {filtro_local}"

    elementos.append(Paragraph(
        f"<b>Collaboratore:</b> {nome_usuario}<br/>"
        f"<b>Periodo:</b> {periodo}",
        styles["Normal"]
    ))

    elementos.append(Spacer(1, 15))

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

    elementos.append(Paragraph(
        f"<b>Totale ore:</b> {formatar_horas_hhmm(total_horas)}",
        styles["Heading2"]
    ))
    elementos.append(Spacer(1, 18))
    elementos.append(Paragraph("Firma del collaboratore:", styles["Normal"]))
    elementos.append(Spacer(1, 18))
    elementos.append(Paragraph("_______________________________", styles["Normal"]))
    elementos.append(Spacer(1, 12))
    elementos.append(Paragraph("Firma responsabile azienda:", styles["Normal"]))
    elementos.append(Spacer(1, 18))
    elementos.append(Paragraph(
        "_______________________________<br/>"
        f"Data: {datetime.now().strftime('%d/%m/%Y')}",
        styles["Normal"]
    ))

    pdf.build(elementos)
    buffer.seek(0)

    nome_arquivo = f"presenze_{nome_usuario.replace(' ', '_')}.pdf"

    return send_file(
        buffer,
        as_attachment=True,
        download_name=nome_arquivo,
        mimetype="application/pdf"
    )


# =========================
# ADMIN BACKUP/EXCLUIR PONTOS
# =========================

@app.route("/admin_pontos/backup", methods=["GET", "POST"])
def admin_pontos_backup():
    if "uid" not in session:
        return redirect("/")

    uid = session["uid"]
    usuario_doc = db.collection("usuarios").document(uid).get()
    usuario = usuario_doc.to_dict() if usuario_doc.exists else {}

    if usuario.get("tipo") != "admin":
        return "Acesso negado"

    if request.method == "GET":
        usuarios_ref = db.collection("usuarios").stream()
        usuarios = []
        for u in usuarios_ref:
            ud = u.to_dict()
            usuarios.append({
                "uid": u.id,
                "nome": f"{ud.get('nome','')} {ud.get('sobrenome','')}"
            })

        return render_template(
            "admin_backup_pontos.html",
            usuarios=usuarios,
            backup_error=request.args.get("backup_error")
        )

    filtro_usuario = request.form.get("filtro_usuario", "").strip()
    mes_inicio = request.form.get("mes_inicio", "").strip()
    mes_fim = request.form.get("mes_fim", "").strip()
    acao = request.form.get("acao", "exportar")

    start_date, end_date, erro, mes_inicio, mes_fim = parse_month_range(mes_inicio, mes_fim)
    if erro:
        return redirect(url_for("admin_pontos_backup", backup_error=erro))

    pontos_ref = db.collection("pontos")

    manual_filter = False
    try:
        pontos_ref = pontos_ref.where("data", ">=", start_date).where("data", "<=", end_date)
        pontos_docs = list(pontos_ref.stream())
    except Exception:
        manual_filter = True
        pontos_docs = list(db.collection("pontos").stream())

    usuarios_map = get_usuarios_map()
    rows = []
    doc_refs = []

    for doc in pontos_docs:
        p = doc.to_dict()

        data_str = p.get("data")
        if not data_str:
            continue

        if filtro_usuario and p.get("uid") != filtro_usuario:
            continue
        if manual_filter and not (start_date <= data_str <= end_date):
            continue

        try:
            horas_val = float(p.get("horas", 0))
        except Exception:
            horas_val = 0

        horas_hhmm = formatar_horas_hhmm(horas_val)

        rows.append([
            usuarios_map.get(p.get("uid", ""), ""),
            formatar_data(data_str),
            horas_hhmm,
            p.get("notas", "")
        ])
        doc_refs.append(doc.reference)

    if not rows:
        return redirect(url_for("admin_pontos_backup", backup_error="Nessuna presenza trovata per il periodo selezionato."))

    output = StringIO(newline="")
    writer = csv.writer(output, delimiter=";")
    writer.writerow(["Nome", "Data", "Ore", "Note"])
    writer.writerows(rows)
    csv_bytes = output.getvalue().encode("utf-8-sig")
    output.close()

    if acao == "exportar_excluir":
        batch = db.batch()
        count = 0
        for ref in doc_refs:
            batch.delete(ref)
            count += 1
            if count % 450 == 0:
                batch.commit()
                batch = db.batch()
        if count % 450 != 0:
            batch.commit()

    filename = build_backup_filename(mes_inicio, mes_fim, filtro_usuario or None)
    return send_file(
        BytesIO(csv_bytes),
        as_attachment=True,
        download_name=filename,
        mimetype="text/csv"
    )


# =========================
# EDITAR PONTO
# =========================

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

    # Segurança: se não for admin, só pode editar ponto próprio
    if usuario.get("tipo") != "admin" and ponto.get("uid") != uid:
        return "Acesso negado!"

    tipos_validos = {"presenza", "malattia", "ferie"}
    ponto["tipo_registro"] = (ponto.get("tipo_registro") or "presenza").lower()
    if ponto["tipo_registro"] not in tipos_validos:
        ponto["tipo_registro"] = "presenza"

    # Busca locais dinamicamente no Firestore
    locais_ref = db.collection("locais").stream()
    locais = []

    for l in locais_ref:
        l_data = l.to_dict()
        if not l_data:
            continue
        nome_local = l_data.get("ragione_sociale") or l_data.get("nome")
        if nome_local:
            locais.append(nome_local)

    if "-" not in locais:
        locais.insert(0, "-")

    error = None

    # POST -> salva edição
    if request.method == "POST":
        data_nova = (request.form.get("data") or "").strip()
        local_novo = (request.form.get("local") or "").strip()
        horas_input = (request.form.get("horas") or "").strip().replace(",", ".")
        notas_nova = (request.form.get("notas") or "").strip()
        tipo_novo = (request.form.get("tipo_registro") or "presenza").strip().lower()

        if tipo_novo not in tipos_validos:
            tipo_novo = "presenza"

        if not data_nova:
            error = "Inserisci una data valida."

        # Evita duplicidade da mesma data para o mesmo usuário
        if not error:
            duplicados = db.collection("pontos") \
                .where("uid", "==", ponto.get("uid")) \
                .where("data", "==", data_nova) \
                .stream()
            for d in duplicados:
                if d.id != id:
                    error = f"Hai già una presenza/assenza registrata per {data_nova}."
                    break

        horas_novas = 0.0
        if not error:
            if tipo_novo == "presenza":
                try:
                    horas_novas = float(horas_input)
                    if horas_novas <= 0:
                        raise ValueError()
                except Exception:
                    error = "Inserisci un numero valido di ore!"
            else:
                horas_novas = 0.0
                local_novo = "-"

        if not error:
            if not local_novo:
                local_novo = "-"

            ponto_ref.update({
                "data": data_nova,
                "local": local_novo,
                "horas": horas_novas,
                "notas": notas_nova,
                "tipo_registro": tipo_novo,
            })

            if usuario.get("tipo") == "admin":
                return redirect("/admin_pontos")
            return redirect("/meus_pontos")

        # Reapresenta dados no form em caso de erro
        ponto["data"] = data_nova or ponto.get("data", "")
        ponto["local"] = local_novo or ponto.get("local", "-")
        ponto["horas"] = horas_input or str(ponto.get("horas", ""))
        ponto["notas"] = notas_nova
        ponto["tipo_registro"] = tipo_novo

    return render_template(
        "editar_ponto.html",
        ponto=ponto,
        locais=locais,
        error=error,
        is_admin_user=usuario.get("tipo") == "admin"
    )


# =========================
# EXCLUIR PONTO
# =========================

@app.route("/excluir_ponto/<id>", methods=["POST"])
def excluir_ponto(id):
    # Verifica login
    if "uid" not in session:
        return redirect("/")

    # Verifica se Ã© admin
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



# =========================
# GERENCIAR LOCAIS (ADMIN)
# =========================

@app.route("/adm_locais", methods=["GET", "POST"])
def gerenciar_locais():
    usuario = get_usuario_logado()
    if not usuario:
        return redirect("/")
    if usuario.get("tipo") != "admin":   # verifica tipo igual ao admin_pontos
        return "Accesso negato!"         # retorna string simples

    if request.method == "POST":
        ragione_sociale = (request.form.get("ragione_sociale") or "").strip()
        responsabile_tecnico = (request.form.get("responsabile_tecnico") or "").strip()
        telefone = (request.form.get("telefone") or "").strip()
        indirizzo = (request.form.get("indirizzo") or "").strip()
        piva = (request.form.get("piva") or "").strip()
        if ragione_sociale:
            db.collection("locais").add({
                "ragione_sociale": ragione_sociale,
                "responsabile_tecnico": responsabile_tecnico,
                "telefone": telefone,
                "indirizzo": indirizzo,
                "piva": piva,
            })
            return redirect(url_for("gerenciar_locais"))

    locais_docs = db.collection("locais").stream()
    locais = []
    for doc in locais_docs:
        data = doc.to_dict() or {}
        locais.append({
            "id": doc.id,
            "ragione_sociale": data.get("ragione_sociale") or data.get("nome") or "-",
            "responsabile_tecnico": data.get("responsabile_tecnico", ""),
            "telefone": data.get("telefone", ""),
            "indirizzo": data.get("indirizzo", ""),
            "piva": data.get("piva", ""),
        })
    locais.sort(key=lambda x: x["ragione_sociale"].lower())

    return render_template("admin_locais.html", locais=locais)


# =========================
# EDITAR LOCAL (ADMIN)
# =========================

@app.route("/adm_locais/editar/<id>", methods=["GET", "POST"])
def editar_local(id):
    usuario = get_usuario_logado()
    if not usuario or usuario.get("tipo") != "admin":
        return "Accesso negato!"

    local_ref = db.collection("locais").document(id)
    local_doc = local_ref.get()
    if not local_doc.exists:
        return "Locale non trovato"

    local = local_doc.to_dict() or {}
    local["id"] = id
    if not local.get("ragione_sociale"):
        local["ragione_sociale"] = local.get("nome", "")

    if request.method == "POST":
        ragione_sociale = (request.form.get("ragione_sociale") or "").strip()
        responsabile_tecnico = (request.form.get("responsabile_tecnico") or "").strip()
        telefone = (request.form.get("telefone") or "").strip()
        indirizzo = (request.form.get("indirizzo") or "").strip()
        piva = (request.form.get("piva") or "").strip()

        update_data = {
            "ragione_sociale": ragione_sociale,
            "responsabile_tecnico": responsabile_tecnico,
            "telefone": telefone,
            "indirizzo": indirizzo,
            "piva": piva,
        }
        local_ref.update(update_data)
        return redirect(url_for("gerenciar_locais"))

    return render_template("admin_locais_editar.html", local=local)


# =========================
# EXCLUIR LOCAL (ADMIN)
# =========================

@app.route("/excluir_local", methods=["POST"])
def excluir_local():
    usuario = get_usuario_logado()
    if not usuario or usuario.get("tipo") != "admin":
        return "Accesso negato!"

    local_id = request.form.get("local_id")
    if local_id:
        db.collection("locais").document(local_id).delete()
        return redirect(url_for("gerenciar_locais"))

    nome = request.form.get("nome")
    if nome:
        locais_ref = db.collection("locais").where("nome", "==", nome).stream()
        for doc in locais_ref:
            db.collection("locais").document(doc.id).delete()
    return redirect(url_for("gerenciar_locais"))

# =========================
# ADMIN CARTÃ•ES DE RECONHECIMENTO
# =========================

@app.route("/admin/cartoes", methods=["GET"])
def admin_cartoes():
    usuario = get_usuario_logado()
    if not usuario or usuario.get("tipo") != "admin":
        return "Acesso negado!"

    return redirect(url_for("admin_perfis"))



# =========================
# GERAR CARTÃƒO (ADMIN)
# =========================

@app.route("/admin/cartoes/gerar/<uid>", methods=["GET"])
def gerar_cartao(uid):
    usuario_logado = get_usuario_logado()
    if not usuario_logado or usuario_logado.get("tipo") != "admin":
        return "Accesso negato!"

    usuario = get_user_by_id(uid)
    if not usuario:
        return "Utente non trovato"

    faltantes = get_badge_missing_fields(usuario)
    if faltantes:
        return render_template(
            "cartao_perfil_incompleto.html",
            user=usuario,
            missing_fields=faltantes,
            edit_url=url_for("admin_perfil_editar", uid=uid),
            back_url=url_for("admin_perfis"),
            back_label="Tornare",
            edit_label="Modifica profilo utente",
        )

    return render_template("cartao_reconhecimento.html", user=usuario)




# =========================
# GERAR CARTÃƒO (USUÃRIO)
# =========================

@app.route("/perfil/cartao", methods=["GET"])
def gerar_cartao_perfil():
    usuario = get_usuario_logado()
    if not usuario:
        return redirect("/")

    faltantes = get_badge_missing_fields(usuario)
    if faltantes:
        return render_template(
            "cartao_perfil_incompleto.html",
            user=usuario,
            missing_fields=faltantes,
            edit_url=url_for("perfil_editar"),
            back_url=url_for("perfil_usuario"),
            back_label="Indietro",
            edit_label="Modifica Profilo",
        )

    return render_template(
        "cartao_reconhecimento.html",
        user=usuario
    )


# =========================
# PEDIDO NOVO E LISTAGEM DE PEDIDOS DO USUÃRIO
# =========================

from datetime import datetime
from google.cloud import firestore

@app.route("/pedido/novo", methods=["GET", "POST"])
def novo_pedido():
    if "uid" not in session:
        return redirect("/")

    uid = session["uid"]

    # ðŸ”¹ Busca o usuÃ¡rio no Firestore
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

    # ðŸ”¹ Busca todos os pedidos do usuÃ¡rio atual
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



# =========================
# ADMIN PEDIDOS - LISTAGEM E AÃ‡Ã•ES
# =========================

@app.route("/admin/pedidos", methods=["GET", "POST"])
def admin_pedidos():
    usuario = get_usuario_logado()
    if not usuario or usuario.get("tipo") != "admin":
        return "Accesso negato!"

    pedidos_ref = db.collection("pedidos")
    
    # AtualizaÃ§Ã£o via POST
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
        # apÃ³s a aÃ§Ã£o, recarrega os pedidos
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


    # GET â†’ lista de pedidos
    pedidos_docs = db.collection("pedidos").stream()
    pedidos = []
    for doc in pedidos_docs:
        d = doc.to_dict()
        d["id"] = doc.id
        pedidos.append(d)

    pedidos.sort(key=lambda x: x.get("data_pedido", ""), reverse=True)

    return render_template("admin_pedidos.html", pedidos=pedidos)




# =========================
# DECIDIR PEDIDO (APPROVAR, RECUSAR, ATENDER)
# =========================

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



# =========================
# EXPORTAR RELATÃ“RIO DE PONTOS EM PDF
# =========================

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
    # USUÃRIO
    # =========================
    usuario = db.collection("usuarios").document(uid).get().to_dict()
    nome_usuario = f"{usuario.get('nome', '')} {usuario.get('sobrenome', '')}".strip()

    # =========================
    # BUSCA PONTOS
    # =========================
    pontos_ref = db.collection("pontos").where("uid", "==", uid)
    pontos_docs = pontos_ref.stream()

    styles = getSampleStyleSheet()
    cell_style = ParagraphStyle(
        "cell",
        parent=styles["Normal"],
        fontSize=9,
        leading=11
    )
    cell_style.wordWrap = "CJK"

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

        # Converte data (fuso ItÃ¡lia fixo)
        data_obj = datetime.strptime(p["data"], "%Y-%m-%d") + timedelta(hours=1)

        # ðŸ”¹ filtro por data
        if filtro_data and p["data"] != filtro_data:
            continue

        # ðŸ”¹ filtro por mÃªs
        if filtro_mes:
            ano, mes = map(int, filtro_mes.split("-"))
            if data_obj.year != ano or data_obj.month != mes:
                continue

        # ðŸ”¹ data formatada + dia da semana
        dia_semana = dias_semana[data_obj.weekday()]
        data_formatada = f"{data_obj.strftime('%d/%m/%Y')} - {dia_semana}"

        # ðŸ”¹ horas (FLOAT â†’ HH:MM)
        horas_totais = float(p.get("horas", 0))
        horas_hhmm = formatar_horas_hhmm(horas_totais)

        total_horas_float += horas_totais

        dados.append([
            data_formatada,
            p.get("local", "-"),
            horas_hhmm,
            Paragraph(p.get("notas", "") or "-", cell_style)
        ])

    # ðŸ”¹ TOTAL FINAL
    total_horas = formatar_horas_hhmm(total_horas_float)

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

    elementos = []

    # LOGO
    logo_path = os.path.join(
        os.path.dirname(__file__), "static", "img", "logo-login.png"
    )
    if os.path.exists(logo_path):
        elementos.append(Image(logo_path, width=5.5*cm, height=2.5*cm))
        elementos.append(Spacer(1, 12))

    # TÃTULO
    elementos.append(Paragraph("Rapporto presenze", styles["Title"]))
    elementos.append(Spacer(1, 12))

    if filtro_data:
        periodo = formatar_data(filtro_data)
    elif filtro_mes and "-" in filtro_mes:
        ano, mes = filtro_mes.split("-")
        periodo = f"{mes}/{ano}"
    else:
        periodo = "Tutto il periodo"

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

    # FIRME
    elementos.append(Paragraph("Firma del collaboratore:", styles["Normal"]))
    elementos.append(Spacer(1, 18))
    elementos.append(Paragraph("_______________________________", styles["Normal"]))
    elementos.append(Spacer(1, 12))
    elementos.append(Paragraph("Firma responsabile azienda:", styles["Normal"]))
    elementos.append(Spacer(1, 18))
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




# =========================
# EXPORTAR ESTATISTICAS EM PDF (ADMIN)
# =========================

@app.route("/admin/estatisticas/pdf")
def exportar_estatisticas_pdf():
    usuario = get_usuario_logado()
    if not usuario or usuario.get("tipo") != "admin":
        return redirect("/dashboard")

    periodo = request.args.get("periodo", "month")
    anno = _safe_int(request.args.get("anno"), datetime.now().year)
    mese = _safe_int(request.args.get("mese"), datetime.now().month)
    trimestre = _safe_int(request.args.get("trimestre"), ((datetime.now().month - 1) // 3) + 1)
    semestre = _safe_int(request.args.get("semestre"), 1 if datetime.now().month <= 6 else 2)

    if mese < 1 or mese > 12:
        mese = datetime.now().month
    if trimestre < 1 or trimestre > 4:
        trimestre = ((datetime.now().month - 1) // 3) + 1
    if semestre not in (1, 2):
        semestre = 1 if datetime.now().month <= 6 else 2

    start_date, end_date = _period_range(periodo, anno, mese, trimestre, semestre)

    pontos_ref = db.collection("pontos")
    manual_filter = False
    try:
        pontos_docs = list(pontos_ref.where("data", ">=", start_date).where("data", "<=", end_date).stream())
    except Exception:
        manual_filter = True
        pontos_docs = list(db.collection("pontos").stream())

    total_periodo = 0.0
    horas_por_local = {}

    for doc in pontos_docs:
        p = doc.to_dict()
        data_str = p.get("data", "")
        if manual_filter and not (start_date <= data_str <= end_date):
            continue

        try:
            horas_val = float(p.get("horas", 0))
        except Exception:
            horas_val = 0.0

        total_periodo += horas_val
        local = p.get("local", "-") or "-"
        horas_por_local[local] = horas_por_local.get(local, 0.0) + horas_val

    locais_ordenados = sorted(horas_por_local.items(), key=lambda x: x[1], reverse=True)

    # Totale anno
    start_anno = f"{anno}-01-01"
    end_anno = f"{anno}-12-31"
    manual_filter_year = False
    try:
        pontos_anno = list(db.collection("pontos").where("data", ">=", start_anno).where("data", "<=", end_anno).stream())
    except Exception:
        manual_filter_year = True
        pontos_anno = list(db.collection("pontos").stream())

    total_anno = 0.0
    ore_per_mese = [0.0] * 12
    for doc in pontos_anno:
        p = doc.to_dict()
        data_str = p.get("data", "")
        if manual_filter_year and not (start_anno <= data_str <= end_anno):
            continue
        try:
            data_obj = datetime.strptime(data_str, "%Y-%m-%d")
        except Exception:
            continue
        try:
            horas_val = float(p.get("horas", 0))
        except Exception:
            horas_val = 0.0

        total_anno += horas_val
        ore_per_mese[data_obj.month - 1] += horas_val

    # PDF
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

    logo_path = os.path.join(os.path.dirname(__file__), "static", "img", "logo-login.png")
    if os.path.exists(logo_path):
        elementos.append(Image(logo_path, width=5.5*cm, height=2.5*cm))
        elementos.append(Spacer(1, 12))

    elementos.append(Paragraph("Statistiche amministrative", styles["Title"]))
    elementos.append(Spacer(1, 12))

    periodo_label = {
        "month": "Mese",
        "quarter": "Trimestre",
        "semester": "Semestre",
        "year": "Anno",
    }.get(periodo, "Anno")

    elementos.append(Paragraph(
        f"<b>Periodo:</b> {periodo_label} &nbsp;&nbsp; <b>Dal:</b> {formatar_data(start_date)} &nbsp;&nbsp; <b>Al:</b> {formatar_data(end_date)}",
        styles["Normal"]
    ))
    elementos.append(Spacer(1, 12))

    elementos.append(Paragraph(
        f"<b>Ore del periodo:</b> {formatar_horas_hhmm(total_periodo)}<br/>"
        f"<b>Ore dell'anno:</b> {formatar_horas_hhmm(total_anno)}",
        styles["Normal"]
    ))
    elementos.append(Spacer(1, 12))

    tabela_local = [["Locale", "Ore"]]
    for nome, horas in locais_ordenados:
        tabela_local.append([nome, formatar_horas_hhmm(horas)])

    table = Table(tabela_local, colWidths=[10*cm, 4*cm])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#041955")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("ALIGN", (1, 1), (1, -1), "RIGHT"),
    ]))

    elementos.append(Paragraph("Ore per localit?", styles["Heading3"]))
    elementos.append(Spacer(1, 6))
    elementos.append(table)
    elementos.append(Spacer(1, 12))

    tabela_mesi = [["Mese", "Ore"]]
    mesi_labels = ["Gen", "Feb", "Mar", "Apr", "Mag", "Giu", "Lug", "Ago", "Set", "Ott", "Nov", "Dic"]
    for idx, horas in enumerate(ore_per_mese):
        tabela_mesi.append([mesi_labels[idx], formatar_horas_hhmm(horas)])

    table_mesi = Table(tabela_mesi, colWidths=[6*cm, 4*cm])
    table_mesi.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#041955")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("ALIGN", (1, 1), (1, -1), "RIGHT"),
    ]))

    elementos.append(Paragraph("Ore per mese", styles["Heading3"]))
    elementos.append(Spacer(1, 6))
    elementos.append(table_mesi)

    pdf.build(elementos)
    buffer.seek(0)

    nome_arquivo = f"statistiche_{periodo}_{anno}.pdf"
    return send_file(
        buffer,
        as_attachment=True,
        download_name=nome_arquivo,
        mimetype="application/pdf"
    )


# =========================
# LOGOUT
# =========================

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")



# =========================
# INICIAR APP
# =========================
if __name__ == "__main__":
    app.run(debug=True)





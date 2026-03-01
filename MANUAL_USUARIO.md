# Manual do Usuario (FlashPoint)

Este manual foi criado para apoiar o treinamento dos funcionarios no uso do sistema FlashPoint.

## 1) Visao Geral

O FlashPoint e um sistema para:
- Registrar horas trabalhadas (pontos).
- Consultar as suas horas e exportar relatorios em PDF.
- Enviar pedidos/solicitacoes ao administrador.
- Manter dados basicos do perfil.

Existem dois perfis principais:
- **Funcionario (usuario)**: registra horas, consulta relatorios, cria pedidos, atualiza perfil.
- **Administrador (admin)**: gerencia pontos, locais, perfis, pedidos e estatisticas.

## 2) Primeiro Acesso

1. Acesse o sistema e faca login com seu email e senha.
1. (Opcional) No seu **Perfil**, escolha o idioma nas configuracoes.

Se voce ainda nao tem conta, use a tela de cadastro conforme orientacao do responsavel.

## 3) Registrar Horas (Novo Ponto)

Menu: **Registrar horas / Segna ore**

1. Selecione o **Locale** (local/empresa/obra) onde a atividade ocorreu.
1. Escolha a **Data**.
1. Informe as **Horas trabalhadas**.
   - O campo de entrada aceita valor decimal (exemplos comuns):
     - `0.25` = 15 minutos
     - `0.50` = 30 minutos
     - `1.50` = 1 hora e 30 minutos
     - `5.25` = 5 horas e 15 minutos
1. (Opcional) Preencha **Notas/Observacoes**.
   - Se voce colar uma lista com quebras de linha, o sistema mantem essas quebras na visualizacao.
1. Clique em **Registrar**.

Dicas:
- Se voce tentar registrar o mesmo dia duas vezes, o sistema pode bloquear por duplicidade.
- Sempre confira a data antes de enviar.

## 4) Minhas Horas (Meus Pontos)

Menu: **Minhas horas / Le mie Ore**

Nesta tela voce ve todos os seus registros e o total do periodo.

Filtros:
- Por **Data** (dia especifico).
- Por **Mes** (ex.: `03/2026`).

Exibicao das horas:
- O sistema pode receber horas em decimal, mas exibe em **HH:MM** (ex.: `01:30`).

Exportar PDF:
- Use o botao de **Exportar** para gerar um relatorio em PDF do periodo filtrado.
- O relatorio inclui total de horas e espaco para assinaturas.

## 5) Pedidos / Solicitacoes

Menu: **Meus pedidos**

1. Crie um novo pedido, escolhendo o **Tipo**.
1. Escreva a mensagem com os detalhes.
   - Voce pode usar listas e quebras de linha.
1. Envie o pedido.

Depois voce acompanha:
- Status (pendente/aprovado/recusado/atendido).
- Data de criacao do pedido.

## 6) Perfil (Dados Pessoais)

Menu: **Perfil**

O funcionario pode editar:
- Nome e sobrenome
- Data de nascimento
- Pais de origem
- Telefone (WhatsApp) e telefone de emergencia
- Foto de perfil (arquivo no sistema ou URL)

Importante:
- Alguns campos sao exclusivos do administrador (por exemplo: dados internos e configuracoes do tesserino).

## 7) Tesserino (Cracha)

O tesserino e o cracha do colaborador com os dados principais.

Como acessar:
- Normalmente o admin disponibiliza o acesso pelo botao **Tesserini** na lista de perfis.

Se algum colaborador precisar que no cartao apareca **Datore di Lavoro** em vez de **Distaccato Presso**, isso e configurado pelo administrador no perfil do usuario.

## 8) Funcoes do Administrador (Resumo)

### 8.1) Pontos (Admin Pontos)

O admin pode:
- Filtrar por funcionario, mes e locale.
- Exportar PDF das horas do funcionario filtrado.
- Editar e excluir registros (com cuidado).
- Acesso a backup fica em area separada do menu admin.

### 8.2) Backup (Admin)

Atencao:
- O backup e baixado no computador (nao no servidor).
- A opcao de "baixar + eliminar" remove registros do servidor.

### 8.3) Perfis (Admin Perfis)

O admin pode:
- Ver contatos (telefone e emergencia).
- Editar qualquer campo do perfil.
- Abrir WhatsApp diretamente para o telefone do funcionario.
- Abrir o tesserino do funcionario.

### 8.4) Locais (Admin Locais)

O admin pode cadastrar e manter:
- Ragione Sociale
- Responsabile tecnico
- Telefone
- Indirizzo
- P.IVA

### 8.5) Pedidos (Admin Pedidos)

O admin pode:
- Ver pedidos e mensagens com quebras de linha.
- Atualizar status (aprovado/recusado/atendido).
- Excluir pedidos.

### 8.6) Estatisticas (Admin Estatisticas)

O admin pode analisar:
- Horas do mes, trimestre, semestre e ano.
- Top locais (onde mais foram feitas horas).
- Horas por locale e por mes (graficos).
- Exportar estatisticas em PDF.

## 9) Boas Praticas

- Preencha as horas no dia correto e com o locale correto.
- Use notas objetivas quando necessario (atividade, equipe, observacoes).
- Mantenha seu telefone atualizado (importante para contato).

## 10) Problemas Comuns (FAQ)

**Nao consigo fazer login**
- Verifique email/senha.
- Se persistir, fale com o administrador para redefinir acesso.

**Nao aparece nenhum locale para selecionar**
- O admin precisa cadastrar locais na area Admin Locais.

**As horas aparecem diferentes do que eu digitei**
- A entrada e decimal, mas a exibicao e `HH:MM`. Ex.: `1.5` vira `01:30`.

**Meu pedido perdeu as quebras de linha**
- Atualize a pagina; o sistema deve manter as quebras de linha na exibicao.
- Se ainda ocorrer, avise o admin para verificacao.

---

Versao: 1.0

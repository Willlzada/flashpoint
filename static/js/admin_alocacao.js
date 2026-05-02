(function () {
    const config = window.ALLOC_WEEKLY_CONFIG || {};
    const i18n = window.ALLOC_WEEKLY_I18N || {};
    const canEdit = Number(config.canEdit || 0) === 1;

    const weekInput = document.getElementById('semana-inicio');
    const btnCarregar = document.getElementById('btn-carregar-semana');
    const btnSalvar = document.getElementById('btn-salvar-semana');
    const btnExportar = document.getElementById('btn-exportar-whatsapp');
    const statusBox = document.getElementById('status-alocacao');
    const tableContainer = document.getElementById('tabela-alocacao-semanal');

    const state = {
        payload: null,
        agendaEditavel: {}
    };

    function t(key, fallback) {
        const value = i18n && Object.prototype.hasOwnProperty.call(i18n, key) ? i18n[key] : null;
        if (value === undefined || value === null || String(value).trim() === '') {
            return fallback !== undefined ? fallback : key;
        }
        return String(value);
    }

    function escapeHtml(value) {
        const text = String(value || '');
        return text
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#039;');
    }

    function cloneObj(obj) {
        return JSON.parse(JSON.stringify(obj || {}));
    }

    function parseIsoLocal(iso) {
        const text = String(iso || '').trim();
        if (!/^\d{4}-\d{2}-\d{2}$/.test(text)) {
            return null;
        }
        const parts = text.split('-').map((x) => Number(x));
        const year = parts[0];
        const month = parts[1];
        const day = parts[2];
        if (!year || !month || !day) {
            return null;
        }
        const dt = new Date(year, month - 1, day);
        if (Number.isNaN(dt.getTime())) {
            return null;
        }
        return dt;
    }

    function formatIsoLocal(dateObj) {
        const dt = dateObj instanceof Date ? dateObj : new Date();
        if (Number.isNaN(dt.getTime())) {
            return '';
        }
        const year = dt.getFullYear();
        const month = String(dt.getMonth() + 1).padStart(2, '0');
        const day = String(dt.getDate()).padStart(2, '0');
        return `${year}-${month}-${day}`;
    }

    function toMondayIso(inputIso) {
        const parsed = parseIsoLocal(inputIso);
        const base = parsed || new Date();
        if (Number.isNaN(base.getTime())) {
            return '';
        }

        const day = base.getDay();
        const diff = day === 0 ? -6 : 1 - day;
        base.setDate(base.getDate() + diff);
        return formatIsoLocal(base);
    }

    function formatSemana(days) {
        if (!Array.isArray(days) || !days.length) {
            return '';
        }
        const first = new Date(days[0] + 'T00:00:00');
        const last = new Date(days[days.length - 1] + 'T00:00:00');
        if (Number.isNaN(first.getTime()) || Number.isNaN(last.getTime())) {
            return `${days[0]} ${t('date_until', 'ate')} ${days[days.length - 1]}`;
        }
        const d1 = `${String(first.getDate()).padStart(2, '0')}/${String(first.getMonth() + 1).padStart(2, '0')}`;
        const d2 = `${String(last.getDate()).padStart(2, '0')}/${String(last.getMonth() + 1).padStart(2, '0')}`;
        return `${d1} ${t('date_until', 'ate')} ${d2}`;
    }

    function setStatus(message, tone) {
        const className = tone === 'error' ? 'text-danger' : tone === 'ok' ? 'text-success' : 'text-muted';
        statusBox.className = className;
        statusBox.textContent = message;
    }

    async function carregarSemana() {
        const monday = toMondayIso(weekInput.value || config.initialWeekStart || '');
        weekInput.value = monday;
        setStatus(t('status_loading_agenda', 'Carregando agenda semanal...'), 'muted');

        const resp = await fetch(`/api/alocacao_semanal?week_start=${encodeURIComponent(monday)}`);
        if (!resp.ok) {
            const err = await resp.json().catch(() => ({ error: t('error_load', 'Erro ao carregar agenda semanal.') }));
            setStatus(err.error || t('error_load', 'Erro ao carregar agenda semanal.'), 'error');
            tableContainer.innerHTML = `<p class="text-muted mb-0">${escapeHtml(t('table_load_failed', 'Nao foi possivel carregar os dados.'))}</p>`;
            return;
        }

        const body = await resp.json();
        state.payload = body;
        state.agendaEditavel = cloneObj(body.agenda || {});

        renderTabela();
        setStatus(`${t('status_week_loaded', 'Semana carregada.')} ${formatSemana(body.days)}`.trim(), 'ok');
    }

    function atualizarAgenda(uid, localId) {
        if (!localId) {
            delete state.agendaEditavel[uid];
            return;
        }
        state.agendaEditavel[uid] = localId;
    }

    function renderFeriasInfo(info) {
        const d = info || {};
        if (!d.em_ferias) {
            return `<span class="badge text-bg-success">${escapeHtml(t('badge_available', 'Disponivel'))}</span>`;
        }
        const count = Number(d.dias_count || 0);
        if (count >= 7) {
            return `<span class="badge text-bg-warning">${escapeHtml(t('badge_vacations_full', 'Ferias (semana toda)'))}</span>`;
        }
        return `<span class="badge text-bg-warning">${escapeHtml(t('badge_vacations_days_prefix', 'Ferias'))} (${count} ${escapeHtml(t('badge_day_unit', 'dia(s)'))})</span>`;
    }

    function renderTabela() {
        const data = state.payload;
        if (!data) {
            tableContainer.innerHTML = `<p class="text-muted mb-0">${escapeHtml(t('table_no_data', 'Sem dados para mostrar.'))}</p>`;
            return;
        }

        const users = data.usuarios || [];
        const locais = data.locais || [];
        const ferias = data.ferias_por_usuario || {};

        if (!users.length) {
            tableContainer.innerHTML = `<p class="text-muted mb-0">${escapeHtml(t('table_no_users', 'Nenhum funcionario encontrado para esta semana.'))}</p>`;
            return;
        }

        const localMap = {};
        locais.forEach((l) => {
            localMap[l.id] = l.nome;
        });

        const parts = [];
        parts.push('<table class="table table-bordered align-middle">');
        parts.push('<thead class="table-light">');
        parts.push('<tr>');
        parts.push(`<th style="min-width: 230px;">${escapeHtml(t('col_employee', 'Funcionario'))}</th>`);
        parts.push(`<th style="min-width: 170px;">${escapeHtml(t('col_status', 'Status na semana'))}</th>`);
        parts.push(`<th style="min-width: 260px;">${escapeHtml(t('col_location', 'Local da semana inteira'))}</th>`);
        parts.push('</tr>');
        parts.push('</thead>');
        parts.push('<tbody>');

        users.forEach((user) => {
            const uid = user.uid;
            const nome = user.nome || uid;
            const isCurrent = (data.current_uid || '') === uid;
            const rowClass = isCurrent ? 'table-info' : '';
            const infoFerias = ferias[uid] || {};
            const emFerias = Boolean(infoFerias.em_ferias);
            const selectedLocal = state.agendaEditavel[uid] || '';

            parts.push(`<tr class="${rowClass}">`);
            parts.push(`<td><strong>${escapeHtml(nome)}</strong>${isCurrent ? ` <span class="badge text-bg-primary ms-1">${escapeHtml(t('you_badge', 'Voce'))}</span>` : ''}</td>`);
            parts.push(`<td>${renderFeriasInfo(infoFerias)}</td>`);

            if (canEdit) {
                const options = [`<option value="">${escapeHtml(t('option_no_allocation', 'Sem alocacao'))}</option>`];
                locais.forEach((l) => {
                    const selected = l.id === selectedLocal ? 'selected' : '';
                    options.push(`<option value="${escapeHtml(l.id)}" ${selected}>${escapeHtml(l.nome || l.id)}</option>`);
                });
                const disabled = emFerias ? 'disabled' : '';
                parts.push(
                    '<td>' +
                    `<select class="form-select form-select-sm weekly-local" ${disabled} data-uid="${escapeHtml(uid)}">${options.join('')}</select>` +
                    '</td>'
                );
            } else {
                const nomeLocal = localMap[selectedLocal] || '-';
                parts.push(`<td>${escapeHtml(nomeLocal)}</td>`);
            }

            parts.push('</tr>');
        });

        parts.push('</tbody>');
        parts.push('</table>');

        tableContainer.innerHTML = parts.join('');

        if (canEdit) {
            tableContainer.querySelectorAll('.weekly-local').forEach((selectEl) => {
                selectEl.addEventListener('change', function () {
                    const uid = this.dataset.uid || '';
                    const localId = this.value || '';
                    atualizarAgenda(uid, localId);
                });
            });
        }
    }

    async function salvarSemana() {
        if (!canEdit) {
            return;
        }

        if (!state.payload || !state.payload.week_start) {
            setStatus(t('status_load_before_save', 'Carregue uma semana antes de salvar.'), 'error');
            return;
        }

        setStatus(t('status_saving', 'Salvando planejamento semanal...'), 'muted');
        const resp = await fetch('/api/alocacao_semanal', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                week_start: state.payload.week_start,
                agenda: state.agendaEditavel
            })
        });

        if (!resp.ok) {
            const err = await resp.json().catch(() => ({ error: t('error_save', 'Erro ao salvar planejamento semanal.') }));
            if (err.error === 'vacation_conflict' && Array.isArray(err.conflicts) && err.conflicts.length) {
                const first = err.conflicts[0] || {};
                const qtdDias = Array.isArray(first.dias) ? first.dias.length : 0;
                const msgTemplate = t('vacation_conflict_fmt', 'Conflito: usuario %uid% esta de ferias (%days% dia(s) na semana).');
                const msg = msgTemplate
                    .replaceAll('%uid%', String(first.uid || '-'))
                    .replaceAll('%days%', String(qtdDias));
                setStatus(msg, 'error');
                await carregarSemana();
                return;
            }
            setStatus(err.error || t('error_save', 'Erro ao salvar planejamento semanal.'), 'error');
            return;
        }

        setStatus(t('status_saved', 'Planejamento semanal salvo com sucesso.'), 'ok');
        await carregarSemana();
    }

    function gerarTextoWhatsapp() {
        const data = state.payload;
        if (!data) {
            return '';
        }

        const users = Array.isArray(data.usuarios) ? data.usuarios : [];
        const locais = Array.isArray(data.locais) ? data.locais : [];
        const ferias = data.ferias_por_usuario || {};

        const localMap = {};
        locais.forEach((l) => {
            localMap[l.id] = l.nome;
        });

        const header = `*${t('wa_title', 'Alocacao semanal')} (${formatSemana(data.days)})*`;
        const intro = t('wa_intro', 'Pessoal, segue a alocacao da semana:');

        const pessoasPorLocal = new Map();
        function pushPessoa(localKey, pessoaNome) {
            const key = (localKey || '').trim() || t('wa_no_allocation', 'Sem alocacao');
            if (!pessoasPorLocal.has(key)) {
                pessoasPorLocal.set(key, []);
            }
            pessoasPorLocal.get(key).push(pessoaNome);
        }

        users.forEach((user) => {
            const uid = user.uid;
            const nomeBase = (user.nome || uid || '-').trim();
            const infoFerias = ferias[uid] || {};
            const emFerias = Boolean(infoFerias.em_ferias);
            const nome = emFerias ? `${nomeBase} (${t('wa_vacations_label', 'FERIAS')})` : nomeBase;

            const localId = state.agendaEditavel[uid] || '';
            const nomeLocal = localId ? (localMap[localId] || localId) : t('wa_no_allocation', 'Sem alocacao');
            pushPessoa(nomeLocal, nome);
        });

        // Ordenacao: respeita ordem dos locais do backend; "Sem alocacao" por ultimo.
        const localOrder = [];
        locais.forEach((l) => {
            const nomeLocal = (l && l.id) ? (localMap[l.id] || l.id) : '';
            if (nomeLocal && pessoasPorLocal.has(nomeLocal)) {
                localOrder.push(nomeLocal);
            }
        });
        const noAllocationLabel = t('wa_no_allocation', 'Sem alocacao');

        Array.from(pessoasPorLocal.keys()).forEach((k) => {
            if (k !== noAllocationLabel && !localOrder.includes(k)) {
                localOrder.push(k);
            }
        });
        if (pessoasPorLocal.has(noAllocationLabel)) {
            localOrder.push(noAllocationLabel);
        }

        const lines = [header, intro, ''];
        localOrder.forEach((localNome) => {
            const pessoas = pessoasPorLocal.get(localNome) || [];
            if (!pessoas.length) {
                return;
            }
            pessoas.sort((a, b) => a.localeCompare(b, undefined, { sensitivity: 'base' }));
            lines.push(`*${localNome}*`);
            pessoas.forEach((p) => lines.push(`- ${p}`));
            lines.push('');
        });

        return lines.join('\n').trim();
    }

    async function exportarWhatsapp() {
        if (!state.payload) {
            setStatus(t('status_load_before_export', 'Carregue uma semana antes de exportar.'), 'error');
            return;
        }

        const texto = gerarTextoWhatsapp();
        if (!texto) {
            setStatus(t('error_no_data', 'Nao ha dados para exportar.'), 'error');
            return;
        }

        try {
            if (navigator.clipboard && navigator.clipboard.writeText) {
                await navigator.clipboard.writeText(texto);
                setStatus(t('status_export_copied', 'Texto copiado. Cole no WhatsApp.'), 'ok');
                return;
            }
        } catch (e) {
            // fallback abaixo
        }

        // Fallback: abre prompt para copiar manualmente
        window.prompt(t('prompt_copy', 'Copie o texto abaixo e cole no WhatsApp:'), texto);
        setStatus(t('status_export_ready', 'Texto pronto para copiar.'), 'ok');
    }

    btnCarregar.addEventListener('click', function (event) {
        event.preventDefault();
        carregarSemana();
    });

    weekInput.addEventListener('change', function () {
        weekInput.value = toMondayIso(weekInput.value);
    });

    if (btnSalvar) {
        btnSalvar.addEventListener('click', function (event) {
            event.preventDefault();
            salvarSemana();
        });
    }

    if (btnExportar) {
        btnExportar.addEventListener('click', function (event) {
            event.preventDefault();
            exportarWhatsapp();
        });
    }

    weekInput.value = toMondayIso(config.initialWeekStart || weekInput.value || '');
    carregarSemana();
})();

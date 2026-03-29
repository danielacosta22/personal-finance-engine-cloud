document.addEventListener('DOMContentLoaded', () => {
    initApp();
});

let expensesChartInst = null;

function showToast(msg, error = false) {
    const toast = document.getElementById('toast');
    toast.textContent = msg;
    toast.style.backgroundColor = error ? 'var(--accent-red)' : 'var(--accent-green)';
    toast.classList.add('show');
    setTimeout(() => toast.classList.remove('show'), 3000);
}

function updateDanielFactor() {
    const frases = [
        "Ingeniero Daniel, flujo de efectivo estabilizado.",
        "Alerta: Evite sobrecarga de pasivos este mes.",
        "Rendimiento nominal. El sistema exige escalamiento.",
        "Ahorros indexados correctamente. Latencia mínima.",
        "Procesos financieros corriendo a máxima eficiencia."
    ];
    document.getElementById('daniel-factor-text').textContent = frases[Math.floor(Math.random() * frases.length)];
}

async function initApp() {
    setupNavigation();
    setupForms();
    updateDanielFactor();
    await loadDashboard();
}

function setupNavigation() {
    document.querySelectorAll('.nav-item').forEach(btn => {
        btn.addEventListener('click', (e) => {
            document.querySelectorAll('.nav-item').forEach(b => b.classList.remove('active'));
            document.querySelectorAll('.page-section').forEach(s => s.classList.remove('active'));
            
            const target = e.currentTarget;
            target.classList.add('active');
            document.getElementById(target.dataset.target).classList.add('active');
            
            if(target.dataset.target === 'section-dashboard') loadDashboard();
            if(target.dataset.target === 'section-flujos') loadFlujosData();
            if(target.dataset.target === 'section-fijos') loadFijosData();
        });
    });
}

function formatCurrency(val) {
    return new Intl.NumberFormat('es-MX', { style: 'currency', currency: 'MXN' }).format(val);
}

// =================== DASHBOARD ===================
async function loadDashboard() {
    try {
        const resBal = await fetch('/api/balance');
        const balance = await resBal.json();
        document.getElementById('val-balance').textContent = formatCurrency(balance.balance);
        document.getElementById('val-ingresos').textContent = formatCurrency(balance.ingresos);
        document.getElementById('val-gastos').textContent = formatCurrency(balance.gastos);

        const resMetas = await fetch('/api/metas');
        const metas = await resMetas.json();
        renderMetas(metas);

        const resTxns = await fetch('/api/transacciones');
        const txns = await resTxns.json();
        renderChart(txns);
    } catch (e) {
        console.error("Error loading dashboard", e);
    }
}

function renderMetas(metas) {
    const container = document.getElementById('metas-container');
    container.innerHTML = '';
    if(metas.length === 0){
        container.innerHTML = '<p style="color:var(--text-secondary);font-size:0.85rem">Sin metas activas. Ve a la pestaña Metas.</p>';
        return;
    }
    metas.forEach(m => {
        const pct = m.monto_objetivo > 0 ? Math.min(100, (m.monto_actual / m.monto_objetivo) * 100) : 0;
        const html = `
            <div class="meta-item">
                <div class="meta-header">
                    <span class="meta-title">${m.icono} ${m.nombre_meta}</span>
                    <span class="meta-amounts">${formatCurrency(m.monto_actual)} / ${formatCurrency(m.monto_objetivo)}</span>
                </div>
                <div class="progress-bar-bg">
                    <div class="progress-bar-fill" style="width: ${pct}%"></div>
                </div>
            </div>
        `;
        container.insertAdjacentHTML('beforeend', html);
    });
}

function renderChart(txns) {
    const ctx = document.getElementById('expensesChart').getContext('2d');
    const gastos = txns.filter(t => t.tipo === 'Gasto');
    
    const catMap = {};
    gastos.forEach(g => {
        catMap[g.categoria] = (catMap[g.categoria] || 0) + g.monto;
    });

    if(expensesChartInst) expensesChartInst.destroy();
    
    if(Object.keys(catMap).length === 0){
        // clear chart if no data
        return;
    }

    expensesChartInst = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: Object.keys(catMap),
            datasets: [{
                data: Object.values(catMap),
                backgroundColor: ['#06B6D4', '#10B981', '#3B82F6', '#8B5CF6', '#EC4899', '#EF4444'],
                borderWidth: 0,
                hoverOffset: 4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { position: 'right', labels: { color: '#94A3B8' } }
            }
        }
    });
}

// =================== FLUJOS ===================
async function loadFlujosData() {
    const tipo = document.querySelector('input[name="tipo"]:checked').value;
    
    // Categorias
    const resCat = await fetch(`/api/categorias?tipo=${tipo}`);
    const cats = await resCat.json();
    const catSelect = document.getElementById('categoria');
    catSelect.innerHTML = '';
    cats.forEach(c => {
        catSelect.insertAdjacentHTML('beforeend', `<option value="${c.nombre}">${c.nombre}</option>`);
    });

    // Metas
    const resMetas = await fetch('/api/metas');
    const metas = await resMetas.json();
    const metaSelect = document.getElementById('form-meta-id');
    metaSelect.innerHTML = '<option value="">-- Ninguna --</option>';
    metas.forEach(m => {
        metaSelect.insertAdjacentHTML('beforeend', `<option value="${m.id}">${m.nombre_meta}</option>`);
    });
    
    // Show/hide metas based on tipo
    document.getElementById('group-meta').style.display = tipo === 'Gasto' ? 'block' : 'none';

    // Cargar Historial Transacciones
    const resTxns = await fetch('/api/transacciones');
    const txns = await resTxns.json();
    const tbody = document.getElementById('txns-tbody');
    if (tbody) {
        tbody.innerHTML = '';
        if (txns.length === 0) {
            tbody.innerHTML = '<tr><td colspan="5" style="text-align:center; color:var(--text-secondary); padding: 15px;">No hay transacciones registradas.</td></tr>';
        } else {
            txns.forEach(t => {
                const isGasto = t.tipo === 'Gasto';
                const tr = document.createElement('tr');
                tr.innerHTML = `
                    <td style="font-size: 0.8rem; color:var(--text-secondary)">${t.fecha}</td>
                    <td><span style="color: ${isGasto ? 'var(--accent-red)' : 'var(--accent-green)'}"><b>${t.tipo}</b></span></td>
                    <td>${t.categoria}</td>
                    <td style="font-family: var(--font-mono)">${formatCurrency(t.monto)}</td>
                    <td style="text-align: center;">
                        <button class="btn-delete" onclick="deleteTxn(${t.id})" title="Eliminar ${t.tipo}">🗑️</button>
                    </td>
                `;
                tbody.appendChild(tr);
            });
        }
    }
}

function setupForms() {
    // Tipo toggle
    const tipos = document.querySelectorAll('input[name="tipo"]');
    if(tipos.length > 0) {
        tipos.forEach(r => {
            r.addEventListener('change', loadFlujosData);
        });
    }

    // Txn Form
    document.getElementById('form-transaccion').addEventListener('submit', async (e) => {
        e.preventDefault();
        const tipo = document.querySelector('input[name="tipo"]:checked').value;
        const data = {
            fecha: new Date().toISOString().split('T')[0],
            tipo: tipo,
            categoria: document.getElementById('categoria').value,
            monto: parseFloat(document.getElementById('monto').value),
            descripcion: document.getElementById('descripcion').value || '',
            meta_id: tipo === 'Gasto' ? (parseInt(document.getElementById('form-meta-id').value) || null) : null
        };
        
        try {
            await fetch('/api/transacciones', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(data)
            });
            showToast('Transacción registrada exitosamente.');
            e.target.reset();
            loadDashboard(); // silent update
        } catch (err) {
            showToast('Error al registrar flujo', true);
        }
    });

    // Meta Form
    const formMeta = document.getElementById('form-meta');
    if(formMeta) {
        formMeta.addEventListener('submit', async (e) => {
            e.preventDefault();
            const data = {
                nombre_meta: document.getElementById('meta-nombre').value,
                monto_objetivo: parseFloat(document.getElementById('meta-monto').value),
                fecha_limite: document.getElementById('meta-fecha').value,
                icono: document.getElementById('meta-icono').value
            };
            try {
                await fetch('/api/metas', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify(data)
                });
                showToast('Meta inicializada en el laboratorio.');
                e.target.reset();
            } catch (err) {
                showToast('Error de compilación de meta', true);
            }
        });
    }

    // Gasto Fijo Form
    const formFijo = document.getElementById('form-gasto-fijo');
    if(formFijo) {
        formFijo.addEventListener('submit', async (e) => {
            e.preventDefault();
            const data = {
                nombre: document.getElementById('gf-nombre').value,
                monto: parseFloat(document.getElementById('gf-monto').value)
            };
            try {
                await fetch('/api/gastos_fijos', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify(data)
                });
                showToast('Gasto fijo programado exitosamente.');
                e.target.reset();
                loadFijosData();
            } catch (err) {
                showToast('Error al configurar gasto fijo', true);
            }
        });
    }
}

// =================== GASTOS FIJOS ===================
async function loadFijosData() {
    try {
        const res = await fetch('/api/gastos_fijos');
        const fijos = await res.json();
        const tbody = document.getElementById('fijos-tbody');
        if (!tbody) return;
        
        tbody.innerHTML = '';
        if (fijos.length === 0) {
            tbody.innerHTML = '<tr><td colspan="3" style="text-align:center; color:var(--text-secondary); padding: 15px;">No hay gastos fijos configurados.</td></tr>';
            return;
        }
        
        fijos.forEach(gf => {
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td>${gf.nombre}</td>
                <td style="font-family: var(--font-mono)">${formatCurrency(gf.monto)}</td>
                <td style="text-align: center;">
                    <button class="btn-delete" onclick="deleteFijo(${gf.id})">🗑️</button>
                </td>
            `;
            tbody.appendChild(tr);
        });
    } catch (e) {
        console.error("Error loading gastos fijos", e);
    }
}

window.deleteFijo = async function(id) {
    if(!confirm("¿Eliminar este gasto fijo?")) return;
    try {
        await fetch(`/api/gastos_fijos/${id}`, { method: 'DELETE' });
        showToast('Gasto fijo eliminado correctamente.');
        loadFijosData();
    } catch (e) {
        showToast('Error al eliminar', true);
    }
};

window.deleteTxn = async function(id) {
    if(!confirm("¿Revertir esta transacción? (Si estaba asociada a una meta, el dinero se descontará de la misma)")) return;
    try {
        await fetch(`/api/transacciones/${id}`, { method: 'DELETE' });
        showToast('Transacción revertida adecuadamente.');
        loadFlujosData(); // Recarga historial
        loadDashboard(); // Actualiza gráfica silenciosamente
    } catch (e) {
        showToast('Error al revertir', true);
    }
};

const API_URL = 'http://localhost:8000';
let currentScenario = 'normal';
let currentIntensity = 3;
let autoSimulateInterval = null;
let mapInstance = null;
let markers = [];
let currentUser = null;

document.addEventListener('DOMContentLoaded', () => {
    initMap();
    initEvents();
    refreshData();
    setInterval(refreshData, 30000);
    restoreSession();
});

function initMap() {
    mapInstance = L.map('map', { center: [-38.5, -63.5], zoom: 5, zoomControl: true });
    L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png', {
        attribution: '© OpenStreetMap'
    }).addTo(mapInstance);
    setTimeout(() => mapInstance.invalidateSize(), 200);
}

function initEvents() {
    document.getElementById('refreshBtn').addEventListener('click', refreshData);
    document.getElementById('loginBtn').addEventListener('click', () => openModal());
    document.querySelector('.close-modal').addEventListener('click', () => closeModal());
    document.getElementById('loginSubmitBtn').addEventListener('click', () => {
        login(document.getElementById('loginUsername').value, document.getElementById('loginPassword').value);
    });
    document.getElementById('modalLoginForm').addEventListener('submit', (e) => {
        e.preventDefault();
        login(document.getElementById('modalUsername').value, document.getElementById('modalPassword').value);
    });
    document.getElementById('logoutBtn').addEventListener('click', logout);
    document.getElementById('simulateStepBtn').addEventListener('click', simulateStep);
    document.getElementById('autoSimulateBtn').addEventListener('click', toggleAutoSimulate);
    document.getElementById('intensitySlider').addEventListener('input', function() {
        currentIntensity = parseInt(this.value);
        document.getElementById('intensityLabel').textContent = currentIntensity;
    });
    document.querySelectorAll('.scenario-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            document.querySelectorAll('.scenario-btn').forEach(b => b.classList.remove('active'));
            this.classList.add('active');
            currentScenario = this.dataset.scenario;
            changeScenario(currentScenario, currentIntensity);
        });
    });
    window.addEventListener('click', (e) => {
        if (e.target === document.getElementById('loginModal')) closeModal();
    });
}

function openModal() { document.getElementById('loginModal').classList.add('show'); }
function closeModal() { document.getElementById('loginModal').classList.remove('show'); }

function restoreSession() {
    const user = localStorage.getItem('centinela_user');
    if (user) {
        try {
            currentUser = JSON.parse(user);
            updateUIForUser(currentUser);
        } catch(e) { localStorage.removeItem('centinela_user'); }
    }
}

async function login(username, password) {
    try {
        const res = await fetch(`${API_URL}/auth/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, password })
        });
        if (!res.ok) throw new Error('Invalid credentials');
        const data = await res.json();
        currentUser = data.user;
        localStorage.setItem('centinela_user', JSON.stringify(data.user));
        localStorage.setItem('centinela_token', data.access_token);
        updateUIForUser(data.user);
        closeModal();
        document.getElementById('loginUsername').value = '';
        document.getElementById('loginPassword').value = '';
        refreshData();
        addLog(`User ${data.user.username} authenticated as ${data.user.role}`);
    } catch(e) {
        alert('Error: ' + e.message);
    }
}

function logout() {
    currentUser = null;
    localStorage.removeItem('centinela_user');
    localStorage.removeItem('centinela_token');
    updateUIForUser(null);
    addLog('Session closed');
}

function updateUIForUser(user) {
    if (user) {
        document.getElementById('usernameDisplay').textContent = user.username;
        document.getElementById('loginBtn').style.display = 'none';
        document.getElementById('userInfo').style.display = 'inline-flex';
        document.getElementById('loginForm').style.display = 'none';
        document.getElementById('logoutSection').style.display = 'block';
        document.getElementById('loggedUser').textContent = user.username;
        const isAnalyst = user.role === 'analyst' || user.role === 'admin';
        document.getElementById('simulateStepBtn').disabled = !isAnalyst;
        document.getElementById('autoSimulateBtn').disabled = !isAnalyst;
        document.querySelectorAll('.scenario-btn').forEach(b => b.disabled = !isAnalyst);
        document.getElementById('intensitySlider').disabled = !isAnalyst;
    } else {
        document.getElementById('usernameDisplay').textContent = 'Guest';
        document.getElementById('loginBtn').style.display = 'inline-flex';
        document.getElementById('userInfo').style.display = 'none';
        document.getElementById('loginForm').style.display = 'block';
        document.getElementById('logoutSection').style.display = 'none';
        document.getElementById('simulateStepBtn').disabled = true;
        document.getElementById('autoSimulateBtn').disabled = true;
        document.querySelectorAll('.scenario-btn').forEach(b => b.disabled = true);
        document.getElementById('intensitySlider').disabled = true;
    }
}

function getHeaders() {
    const token = localStorage.getItem('centinela_token');
    return token ? { 'Authorization': `Bearer ${token}` } : {};
}

async function refreshData() {
    try {
        const [assetsRes, alertsRes, metricsRes] = await Promise.all([
            fetch(`${API_URL}/api/assets`, { headers: getHeaders() }),
            fetch(`${API_URL}/api/alerts?limit=20&resolved=false`, { headers: getHeaders() }),
            fetch(`${API_URL}/api/metrics`, { headers: getHeaders() })
        ]);
        if (!assetsRes.ok || !alertsRes.ok || !metricsRes.ok) {
            if (assetsRes.status === 401) { logout(); return; }
            throw new Error('API error');
        }
        const assets = await assetsRes.json();
        const alerts = await alertsRes.json();
        const metrics = await metricsRes.json();
        updateMetrics(metrics);
        updateAlerts(alerts.alerts);
        updateAssets(assets.assets);
        updateDistribution(metrics.type_distribution || {});
        updateLastUpdate(metrics.last_update);
    } catch(e) { console.error('Refresh error:', e); }
}

async function simulateStep() {
    if (!currentUser || (currentUser.role !== 'analyst' && currentUser.role !== 'admin')) {
        addLog('Requires analyst or admin role');
        return;
    }
    try {
        const res = await fetch(`${API_URL}/api/simulate`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', ...getHeaders() },
            body: JSON.stringify({ scenario: currentScenario, intensity: currentIntensity })
        });
        if (res.status === 401) { logout(); return; }
        if (!res.ok) throw new Error('Simulation error');
        const result = await res.json();
        addLog(`Simulation: ${result.new_alerts} new alerts (${result.scenario})`);
        refreshData();
    } catch(e) { console.error('Simulation error:', e); }
}

async function changeScenario(scenario, intensity) {
    if (!currentUser || (currentUser.role !== 'analyst' && currentUser.role !== 'admin')) return;
    try {
        await fetch(`${API_URL}/api/scenario`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', ...getHeaders() },
            body: JSON.stringify({ scenario, intensity })
        });
    } catch(e) { console.error('Scenario error:', e); }
}

function toggleAutoSimulate() {
    const btn = document.getElementById('autoSimulateBtn');
    if (autoSimulateInterval) {
        clearInterval(autoSimulateInterval);
        autoSimulateInterval = null;
        btn.innerHTML = '<i class="fas fa-play"></i> Auto';
        btn.className = 'btn-secondary full-width';
        addLog('Auto simulation stopped');
    } else {
        autoSimulateInterval = setInterval(simulateStep, 4000);
        btn.innerHTML = '<i class="fas fa-stop"></i> Stop';
        btn.className = 'btn-primary full-width';
        addLog('Auto simulation started');
    }
}

window.resolveAlert = async function(alertId) {
    if (!currentUser || (currentUser.role !== 'analyst' && currentUser.role !== 'admin')) {
        addLog('Requires analyst or admin role');
        return;
    }
    try {
        await fetch(`${API_URL}/api/alerts/resolve/${alertId}`, {
            method: 'POST',
            headers: getHeaders()
        });
        addLog(`Alert ${alertId.substring(0,8)} resolved`);
        refreshData();
    } catch(e) { console.error('Resolve error:', e); }
};

function updateMetrics(metrics) {
    document.getElementById('totalAssets').textContent = metrics.total_assets || 0;
    document.getElementById('activeAlerts').textContent = metrics.active_alerts || 0;
    document.getElementById('criticalAssets').textContent = metrics.critical_assets || 0;
    document.getElementById('uptime').textContent = (metrics.uptime || 99.99) + '%';
    document.getElementById('alertCount').textContent = metrics.active_alerts || 0;
}

function updateAlerts(alerts) {
    const container = document.getElementById('alertsList');
    if (!alerts || alerts.length === 0) {
        container.innerHTML = '<div class="no-alerts">All clear</div>';
        return;
    }
    container.innerHTML = alerts.slice(0, 8).map(a => `
        <div class="alert-item">
            <span class="severity ${a.severity}">${a.severity}</span>
            <span class="message">${a.message}</span>
            <span class="timestamp">${new Date(a.timestamp).toLocaleTimeString()}</span>
            ${currentUser ? `<button class="resolve-btn" onclick="resolveAlert('${a.id}')"><i class="fas fa-check-circle"></i></button>` : ''}
        </div>
    `).join('');
}

function updateAssets(assets) {
    markers.forEach(m => mapInstance.removeLayer(m));
    markers = [];
    if (!assets) return;
    const colors = { 'operativo': '#22c55e', 'alerta': '#f59e0b', 'critico': '#ef4444' };
    assets.forEach(a => {
        const color = colors[a.status] || '#888';
        const marker = L.circleMarker([a.lat, a.lng], {
            radius: a.status === 'critico' ? 12 : a.status === 'alerta' ? 10 : 8,
            fillColor: color, fillOpacity: 0.9, color: '#fff', weight: 1.5
        }).addTo(mapInstance);
        marker.bindPopup(`
            <div style="padding:6px;min-width:160px;">
                <strong>${a.name}</strong><br>
                <span style="font-size:0.8rem;color:#666;">${a.type}</span><br>
                <span style="font-weight:600;color:${color};">${a.status}</span>
                ${a.description ? `<br><span style="font-size:0.7rem;color:#888;">${a.description}</span>` : ''}
            </div>
        `);
        markers.push(marker);
    });
}

function updateDistribution(dist) {
    const types = ['oleoducto', 'electrica', 'comunicaciones', 'transporte', 'agua', 'gas'];
    types.forEach(t => {
        const el = document.getElementById(`dist-${t}`);
        if (el) el.textContent = dist[t] || 0;
    });
}

function updateLastUpdate(ts) {
    document.getElementById('lastUpdate').textContent = ts ? new Date(ts).toLocaleTimeString() : new Date().toLocaleTimeString();
}

function addLog(msg) {
    const container = document.getElementById('activityLog');
    const time = new Date().toLocaleTimeString();
    const entry = document.createElement('div');
    entry.className = 'log-entry';
    entry.innerHTML = `<span class="time">[${time}]</span> ${msg}`;
    container.appendChild(entry);
    container.scrollTop = container.scrollHeight;
    while (container.children.length > 100) container.removeChild(container.firstChild);
}

window.refreshData = refreshData;
window.simulateStep = simulateStep;
window.addLog = addLog;

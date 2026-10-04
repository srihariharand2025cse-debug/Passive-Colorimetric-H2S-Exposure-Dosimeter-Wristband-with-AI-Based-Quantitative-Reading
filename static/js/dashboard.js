/**
 * Client-Side Application Logic for H2S Dosimeter Wristband Dashboard.
 * Handles interactive prediction UI, Chart.js visualizations, telemetry simulation, and history logs.
 */

document.addEventListener('DOMContentLoaded', () => {
    
    // -------------------------------------------------------------
    // Global State & Chart Instances
    // -------------------------------------------------------------
    let probChartInstance = null;
    let trendChartInstance = null;
    let riskPieChartInstance = null;
    let scatterChartInstance = null;
    let deviceBarChartInstance = null;
    let regImportChartInstance = null;
    
    let historyPage = 0;
    const historyLimit = 15;
    let autoSimInterval = null;

    // -------------------------------------------------------------
    // DOM Elements
    // -------------------------------------------------------------
    const form = document.getElementById('prediction-form');
    const inputR = document.getElementById('input-r');
    const inputG = document.getElementById('input-g');
    const inputB = document.getElementById('input-b');
    const inputTemp = document.getElementById('input-temp');
    const inputHum = document.getElementById('input-hum');
    const inputTime = document.getElementById('input-time');
    const inputDevice = document.getElementById('input-device');

    const valR = document.getElementById('val-r');
    const valG = document.getElementById('val-g');
    const valB = document.getElementById('val-b');
    const valTemp = document.getElementById('val-temp');
    const valHum = document.getElementById('val-hum');
    const valTime = document.getElementById('val-time');

    const colorSwatch = document.getElementById('color-swatch');
    const colorHexText = document.getElementById('color-hex-text');
    const responseBadge = document.getElementById('response-index-badge');

    // -------------------------------------------------------------
    // UI Helpers: Color Swatch Update
    // -------------------------------------------------------------
    function updateColorSwatch() {
        const r = parseInt(inputR.value);
        const g = parseInt(inputG.value);
        const b = parseInt(inputB.value);

        valR.textContent = r;
        valG.textContent = g;
        valB.textContent = b;

        valTemp.textContent = parseFloat(inputTemp.value).toFixed(1);
        valHum.textContent = parseFloat(inputHum.value).toFixed(1);
        valTime.textContent = parseFloat(inputTime.value).toFixed(1);

        colorSwatch.style.backgroundColor = `rgb(${r}, ${g}, ${b})`;
        colorHexText.textContent = `RGB(${r}, ${g}, ${b})`;

        // Calculate sensor response darkening percentage
        const baseline = 675.0; // r0 + g0 + b0
        const current = r + g + b;
        const darkeningPct = Math.max(0, Math.min(100, ((baseline - current) / baseline) * 100));
        responseBadge.textContent = `Sensor Darkening: ${darkeningPct.toFixed(1)}%`;
    }

    [inputR, inputG, inputB, inputTemp, inputHum, inputTime].forEach(input => {
        input.addEventListener('input', updateColorSwatch);
    });

    // Preset buttons
    document.querySelectorAll('.preset-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.preventDefault();
            inputR.value = btn.getAttribute('data-r');
            inputG.value = btn.getAttribute('data-g');
            inputB.value = btn.getAttribute('data-b');
            inputTemp.value = btn.getAttribute('data-t');
            inputHum.value = btn.getAttribute('data-h');
            inputTime.value = btn.getAttribute('data-e');
            updateColorSwatch();
            submitPrediction();
        });
    });

    // -------------------------------------------------------------
    // AI Prediction Submission
    // -------------------------------------------------------------
    async function submitPrediction() {
        const payload = {
            red_value: parseInt(inputR.value),
            green_value: parseInt(inputG.value),
            blue_value: parseInt(inputB.value),
            temperature: parseFloat(inputTemp.value),
            humidity: parseFloat(inputHum.value),
            exposure_time: parseFloat(inputTime.value),
            device_id: inputDevice.value,
            save_to_db: true
        };

        try {
            const res = await fetch('/api/predict', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });

            const data = await res.json();
            if (data.status === 'success') {
                renderPredictionResults(data.data);
            }
        } catch (err) {
            console.error('Prediction API Error:', err);
        }
    }

    form.addEventListener('submit', (e) => {
        e.preventDefault();
        submitPrediction();
    });

    function renderPredictionResults(res) {
        const ppm = res.predicted_exposure_ppm;
        const risk = res.risk_class;
        const meta = res.risk_metadata;

        document.getElementById('res-ppm').textContent = ppm.toFixed(2);
        document.getElementById('res-risk-text').textContent = risk;
        document.getElementById('res-action-text').textContent = meta.action;

        const badge = document.getElementById('result-risk-badge');
        badge.className = meta.badge_class;
        badge.textContent = risk.toUpperCase();

        const expCard = document.getElementById('exp-stat-card');
        const riskCard = document.getElementById('risk-stat-card');
        expCard.className = `stat-card ${getStatCardClass(risk)}`;
        riskCard.className = `stat-card ${getStatCardClass(risk)}`;

        // Summary table updates
        document.getElementById('table-rgb').textContent = `${res.input_parameters.red_value}, ${res.input_parameters.green_value}, ${res.input_parameters.blue_value}`;
        document.getElementById('table-darkening').textContent = `${(res.sensor_response * 100).toFixed(1)} %`;
        document.getElementById('table-env').textContent = `${res.input_parameters.temperature} °C / ${res.input_parameters.humidity} %`;
        document.getElementById('table-time').textContent = `${res.input_parameters.exposure_time} hrs`;

        // Probability Chart
        renderProbabilityChart(res.class_probabilities);
    }

    function getStatCardClass(risk) {
        switch (risk) {
            case 'Low':
            case 'Safe':
            case 'Low Risk': return 'safe';
            case 'Moderate':
            case 'Moderate Risk': return 'moderate';
            case 'High':
            case 'High Risk':
            case 'Hazardous': return 'high';
            default: return 'safe';
        }
    }

    function renderProbabilityChart(probs) {
        const labels = Object.keys(probs);
        const dataValues = Object.values(probs).map(v => (v * 100).toFixed(1));
        const ctx = document.getElementById('probChart').getContext('2d');

        const colors = ['#10b981', '#f59e0b', '#f97316', '#ef4444', '#a855f7'];

        if (probChartInstance) probChartInstance.destroy();

        probChartInstance = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Probability (%)',
                    data: dataValues,
                    backgroundColor: colors,
                    borderRadius: 4
                }]
            },
            options: {
                indexAxis: 'y',
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { display: false } },
                scales: {
                    x: { max: 100, ticks: { color: '#94a3b8' }, grid: { color: '#334155' } },
                    y: { ticks: { color: '#cbd5e1' }, grid: { display: false } }
                }
            }
        });
    }

    // -------------------------------------------------------------
    // Telemetry Teleport Simulator Controls
    // -------------------------------------------------------------
    const btnSimulateBurst = document.getElementById('btn-simulate-burst');
    const btnToggleAuto = document.getElementById('btn-toggle-auto');
    const simStatusText = document.getElementById('sim-status-text');

    btnSimulateBurst.addEventListener('click', async () => {
        simStatusText.textContent = 'Simulating telemetry packet burst...';
        try {
            const res = await fetch('/api/simulate/batch', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ count: 5 })
            });
            const data = await res.json();
            simStatusText.textContent = `Generated ${data.data.length} telemetry readings!`;
            fetchAnalytics();
            fetchHistory();
        } catch (err) {
            simStatusText.textContent = 'Simulation error.';
        }
    });

    btnToggleAuto.addEventListener('click', () => {
        if (autoSimInterval) {
            clearInterval(autoSimInterval);
            autoSimInterval = null;
            btnToggleAuto.classList.remove('btn-danger');
            btnToggleAuto.classList.add('btn-outline-info');
            btnToggleAuto.innerHTML = '<i class="fa-solid fa-play me-1"></i>Start Auto Stream (3s)';
            simStatusText.textContent = 'Auto stream stopped.';
        } else {
            autoSimInterval = setInterval(async () => {
                await fetch('/api/simulate/batch', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ count: 1 })
                });
                fetchAnalytics();
                if (document.getElementById('history-tab').classList.contains('active')) {
                    fetchHistory();
                }
            }, 3000);
            btnToggleAuto.classList.remove('btn-outline-info');
            btnToggleAuto.classList.add('btn-danger');
            btnToggleAuto.innerHTML = '<i class="fa-solid fa-stop me-1"></i>Stop Auto Stream';
            simStatusText.textContent = 'Auto streaming active (every 3s)...';
        }
    });

    // -------------------------------------------------------------
    // Telemetry Analytics Dashboard
    // -------------------------------------------------------------
    async function fetchAnalytics() {
        try {
            const res = await fetch('/api/analytics');
            const data = await res.json();
            if (data.status === 'success') {
                renderAnalytics(data.data);
            }
        } catch (err) {
            console.error('Analytics Error:', err);
        }
    }

    function renderAnalytics(analytics) {
        document.getElementById('kpi-total').textContent = analytics.total_readings;
        document.getElementById('kpi-avg').textContent = analytics.avg_exposure.toFixed(2);
        document.getElementById('kpi-max').textContent = analytics.max_exposure.toFixed(2);
        document.getElementById('kpi-devices').textContent = analytics.device_stats.length;

        // 1. Time Series Trend Chart
        const series = analytics.recent_series;
        const trendLabels = series.map(s => s.timestamp.split(' ')[1] || s.timestamp);
        const trendValues = series.map(s => s.exposure_level);

        const ctxTrend = document.getElementById('trendChart').getContext('2d');
        if (trendChartInstance) trendChartInstance.destroy();
        trendChartInstance = new Chart(ctxTrend, {
            type: 'line',
            data: {
                labels: trendLabels,
                datasets: [{
                    label: 'H₂S Exposure (PPM)',
                    data: trendValues,
                    borderColor: '#38bdf8',
                    backgroundColor: 'rgba(56, 189, 248, 0.1)',
                    fill: true,
                    tension: 0.3,
                    pointRadius: 4,
                    pointHoverRadius: 6
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { labels: { color: '#cbd5e1' } } },
                scales: {
                    x: { ticks: { color: '#94a3b8' }, grid: { color: '#334155' } },
                    y: { title: { display: true, text: 'PPM', color: '#94a3b8' }, ticks: { color: '#cbd5e1' }, grid: { color: '#334155' } }
                }
            }
        });

        // 2. Risk Pie Chart
        const riskDist = analytics.risk_distribution;
        const riskLabels = Object.keys(riskDist).length > 0 ? Object.keys(riskDist) : ['Low', 'Moderate', 'High'];
        const riskCounts = riskLabels.map(r => riskDist[r] || 0);

        const ctxPie = document.getElementById('riskPieChart').getContext('2d');
        if (riskPieChartInstance) riskPieChartInstance.destroy();
        riskPieChartInstance = new Chart(ctxPie, {
            type: 'doughnut',
            data: {
                labels: riskLabels,
                datasets: [{
                    data: riskCounts,
                    backgroundColor: ['#10b981', '#f97316', '#ef4444', '#f59e0b', '#a855f7'],
                    borderWidth: 2,
                    borderColor: '#161e2e'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { position: 'bottom', labels: { color: '#cbd5e1' } } }
            }
        });

        // 3. Scatter Plot (Darkening Index vs PPM)
        const scatterData = series.map(s => ({ x: (s.sensor_response * 100), y: s.exposure_level }));
        const ctxScatter = document.getElementById('scatterChart').getContext('2d');
        if (scatterChartInstance) scatterChartInstance.destroy();
        scatterChartInstance = new Chart(ctxScatter, {
            type: 'scatter',
            data: {
                datasets: [{
                    label: 'Readings',
                    data: scatterData,
                    backgroundColor: '#f59e0b'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    x: { title: { display: true, text: 'Sensor Darkening Index (%)', color: '#94a3b8' }, ticks: { color: '#94a3b8' }, grid: { color: '#334155' } },
                    y: { title: { display: true, text: 'H₂S PPM', color: '#94a3b8' }, ticks: { color: '#cbd5e1' }, grid: { color: '#334155' } }
                }
            }
        });

        // 4. Device Breakdown Bar Chart
        const devStats = analytics.device_stats;
        const devLabels = devStats.map(d => d.device_id);
        const devValues = devStats.map(d => d.avg_exposure.toFixed(2));

        const ctxDevice = document.getElementById('deviceBarChart').getContext('2d');
        if (deviceBarChartInstance) deviceBarChartInstance.destroy();
        deviceBarChartInstance = new Chart(ctxDevice, {
            type: 'bar',
            data: {
                labels: devLabels,
                datasets: [{
                    label: 'Avg Exposure (PPM)',
                    data: devValues,
                    backgroundColor: '#6366f1',
                    borderRadius: 4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { display: false } },
                scales: {
                    x: { ticks: { color: '#94a3b8' }, grid: { color: '#334155' } },
                    y: { ticks: { color: '#cbd5e1' }, grid: { color: '#334155' } }
                }
            }
        });
    }

    document.getElementById('refresh-analytics').addEventListener('click', fetchAnalytics);

    // -------------------------------------------------------------
    // Historical Telemetry Database Table
    // -------------------------------------------------------------
    async function fetchHistory() {
        const riskFilter = document.getElementById('filter-risk').value;
        const url = `/api/history?limit=${historyLimit}&offset=${historyPage * historyLimit}${riskFilter ? `&risk_class=${encodeURIComponent(riskFilter)}` : ''}`;

        try {
            const res = await fetch(url);
            const data = await res.json();
            if (data.status === 'success') {
                renderHistoryTable(data.data, data.total);
            }
        } catch (err) {
            console.error('History Table Error:', err);
        }
    }

    function renderHistoryTable(readings, total) {
        const tbody = document.getElementById('history-table-body');
        tbody.innerHTML = '';

        if (readings.length === 0) {
            tbody.innerHTML = '<tr><td colspan="11" class="text-center py-4 text-muted">No telemetry records found.</td></tr>';
            return;
        }

        readings.forEach(r => {
            const tr = document.createElement('tr');
            const darkPct = ((r.sensor_response || 0) * 100).toFixed(1);
            const badgeClass = getBadgeClass(r.risk_class);
            const recordId = r.prediction_id || r.record_id;
            const expLevel = (r.predicted_exposure_level !== undefined ? r.predicted_exposure_level : r.exposure_level || 0).toFixed(2);

            tr.innerHTML = `
                <td>#${recordId}</td>
                <td><span class="badge bg-secondary">${r.device_id}</span></td>
                <td>${r.timestamp}</td>
                <td>
                    <div style="width: 24px; height: 24px; border-radius: 4px; background-color: rgb(${r.red_value}, ${r.green_value}, ${r.blue_value}); border: 1px solid #475569;"></div>
                </td>
                <td>${r.red_value}, ${r.green_value}, ${r.blue_value}</td>
                <td>${r.temperature} °C</td>
                <td>${r.humidity} %</td>
                <td>${r.exposure_time} h</td>
                <td>${darkPct} %</td>
                <td class="fw-bold text-info">${expLevel} ppm</td>
                <td><span class="${badgeClass}">${r.risk_class}</span></td>
            `;
            tbody.appendChild(tr);
        });

        // Pagination Info
        const start = historyPage * historyLimit + 1;
        const end = Math.min(total, (historyPage + 1) * historyLimit);
        document.getElementById('table-info').textContent = `Showing ${start}-${end} of ${total} records`;

        document.getElementById('btn-prev-page').disabled = (historyPage === 0);
        document.getElementById('btn-next-page').disabled = (end >= total);
    }

    function getBadgeClass(risk) {
        switch (risk) {
            case 'Low':
            case 'Safe':
            case 'Low Risk': return 'badge-safe';
            case 'Moderate':
            case 'Moderate Risk': return 'badge-moderate';
            case 'High':
            case 'High Risk':
            case 'Hazardous': return 'badge-high';
            default: return 'badge-safe';
        }
    }

    document.getElementById('btn-prev-page').addEventListener('click', () => {
        if (historyPage > 0) {
            historyPage--;
            fetchHistory();
        }
    });

    document.getElementById('btn-next-page').addEventListener('click', () => {
        historyPage++;
        fetchHistory();
    });

    document.getElementById('filter-risk').addEventListener('change', () => {
        historyPage = 0;
        fetchHistory();
    });

    // -------------------------------------------------------------
    // AI Model Metrics Tab
    // -------------------------------------------------------------
    async function fetchModelMetrics() {
        try {
            const res = await fetch('/api/model/metrics');
            const data = await res.json();
            if (data.status === 'success') {
                renderModelMetrics(data.data);
            }
        } catch (err) {
            console.error('Model Metrics Error:', err);
        }
    }

    function renderModelMetrics(m) {
        // Regressor Metrics
        document.getElementById('m-r2').textContent = m.regression.r2_score.toFixed(4);
        document.getElementById('m-rmse').textContent = `${m.regression.rmse.toFixed(3)} ppm`;
        document.getElementById('m-mae').textContent = `${m.regression.mae.toFixed(3)} ppm`;

        // Classifier Metrics
        document.getElementById('m-acc').textContent = `${(m.classification.accuracy * 100).toFixed(1)}%`;
        document.getElementById('m-prec').textContent = m.classification.precision.toFixed(3);
        document.getElementById('m-rec').textContent = m.classification.recall.toFixed(3);
        document.getElementById('m-f1').textContent = m.classification.f1_score.toFixed(3);

        // Feature Importances Chart
        const imp = m.regression.feature_importances;
        const featLabels = Object.keys(imp);
        const featValues = Object.values(imp);

        const ctxImp = document.getElementById('regImportChart').getContext('2d');
        if (regImportChartInstance) regImportChartInstance.destroy();
        regImportChartInstance = new Chart(ctxImp, {
            type: 'bar',
            data: {
                labels: featLabels,
                datasets: [{
                    label: 'Feature Importance',
                    data: featValues,
                    backgroundColor: '#38bdf8',
                    borderRadius: 4
                }]
            },
            options: {
                indexAxis: 'y',
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { display: false } },
                scales: {
                    x: { ticks: { color: '#94a3b8' }, grid: { color: '#334155' } },
                    y: { ticks: { color: '#cbd5e1' }, grid: { display: false } }
                }
            }
        });

        // Render Confusion Matrix Grid
        const cm = m.classification.confusion_matrix;
        const classes = m.classification.classes;
        const cmContainer = document.getElementById('cm-container');
        
        let html = '<div class="cm-grid">';
        classes.forEach(c => {
            html += `<div class="cm-cell cm-header">${c}</div>`;
        });
        cm.forEach((row, i) => {
            row.forEach((val, j) => {
                const isDiag = (i === j);
                const bg = isDiag ? 'background: rgba(16, 185, 129, 0.2); color: #34d399;' : 'background: #1e293b; color: #94a3b8;';
                html += `<div class="cm-cell" style="${bg}">${val}</div>`;
            });
        });
        html += '</div>';
        cmContainer.innerHTML = html;
    }

    // -------------------------------------------------------------
    // Smart Wristband Fleet Modal Loader
    // -------------------------------------------------------------
    async function fetchFleetDevices() {
        const tbody = document.getElementById('fleet-table-body');
        tbody.innerHTML = '<tr><td colspan="6" class="text-center py-4 text-muted">Loading fleet devices...</td></tr>';
        try {
            const res = await fetch('/api/devices');
            const data = await res.json();
            if (data.status === 'success') {
                renderFleetTable(data.data);
            }
        } catch (err) {
            tbody.innerHTML = '<tr><td colspan="6" class="text-center py-4 text-danger">Error loading device fleet.</td></tr>';
        }
    }

    function renderFleetTable(devices) {
        const tbody = document.getElementById('fleet-table-body');
        tbody.innerHTML = '';
        if (devices.length === 0) {
            tbody.innerHTML = '<tr><td colspan="6" class="text-center py-4 text-muted">No devices registered.</td></tr>';
            return;
        }

        devices.forEach(d => {
            const tr = document.createElement('tr');
            const batteryColor = d.battery_level > 80 ? 'text-success' : d.battery_level > 40 ? 'text-warning' : 'text-danger';
            tr.innerHTML = `
                <td><span class="badge bg-primary">${d.device_id}</span></td>
                <td class="fw-semibold text-light">${d.device_name}</td>
                <td><i class="fa-solid fa-user me-1 text-info"></i>${d.assigned_user_name || 'Unassigned'}</td>
                <td><small class="text-muted">${d.user_role || d.location}</small></td>
                <td><span class="${batteryColor} fw-bold"><i class="fa-solid fa-battery-three-quarters me-1"></i>${d.battery_level}%</span></td>
                <td><span class="badge bg-success">${d.status}</span></td>
            `;
            tbody.appendChild(tr);
        });
    }

    document.getElementById('btn-open-fleet').addEventListener('click', fetchFleetDevices);
    document.getElementById('refresh-fleet-btn').addEventListener('click', fetchFleetDevices);

    // -------------------------------------------------------------
    // Tab Event Listeners
    // -------------------------------------------------------------
    document.getElementById('analytics-tab').addEventListener('click', fetchAnalytics);
    document.getElementById('history-tab').addEventListener('click', fetchHistory);
    document.getElementById('model-tab').addEventListener('click', fetchModelMetrics);

    // Initial Setup
    updateColorSwatch();
    submitPrediction();
});

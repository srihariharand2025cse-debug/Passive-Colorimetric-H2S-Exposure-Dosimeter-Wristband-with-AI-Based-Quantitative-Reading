/**
 * Comprehensive Client-Side Application Logic for H2S Dosimeter Wristband Dashboard.
 * Powers Dashboard Home, Live Sensor Data & 4 Chart.js Visualizations,
 * Real-Time AI Prediction Form & Optical Simulator, Searchable History Table,
 * Model Performance Evaluation, and Fleet Management.
 */

document.addEventListener('DOMContentLoaded', () => {

    // -------------------------------------------------------------
    // Global Chart Instances
    // -------------------------------------------------------------
    let chartExposureTrendInstance = null;
    let chartRiskPieInstance = null;
    let chartRgbValuesInstance = null;
    let chartTempHumInstance = null;
    let chartPredictProbInstance = null;
    let chartFeatureImportInstance = null;

    // Pagination & Stream State
    let historyPage = 0;
    const historyLimit = 15;
    let autoStreamTimer = null;
    let fullHistoryCache = [];

    // -------------------------------------------------------------
    // DOM Elements - Prediction Form & Swatch
    // -------------------------------------------------------------
    const formPredict = document.getElementById('form-manual-predict');
    const predDevice = document.getElementById('pred-device');
    const sliderR = document.getElementById('slider-r');
    const sliderG = document.getElementById('slider-g');
    const sliderB = document.getElementById('slider-b');
    const sliderTemp = document.getElementById('slider-temp');
    const sliderHum = document.getElementById('slider-hum');
    const sliderTime = document.getElementById('slider-time');

    const lblR = document.getElementById('lbl-r');
    const lblG = document.getElementById('lbl-g');
    const lblB = document.getElementById('lbl-b');
    const lblTemp = document.getElementById('lbl-temp');
    const lblHum = document.getElementById('lbl-hum');
    const lblTime = document.getElementById('lbl-time');

    const formColorSwatch = document.getElementById('form-color-swatch');
    const formRgbDisplay = document.getElementById('form-rgb-display');
    const formDarkeningBadge = document.getElementById('form-darkening-badge');

    // -------------------------------------------------------------
    // Helper: Optical Color Swatch Update
    // -------------------------------------------------------------
    function updateFormOpticalSwatch() {
        const r = parseInt(sliderR.value);
        const g = parseInt(sliderG.value);
        const b = parseInt(sliderB.value);
        const temp = parseFloat(sliderTemp.value).toFixed(1);
        const hum = parseFloat(sliderHum.value).toFixed(1);
        const time = parseFloat(sliderTime.value).toFixed(1);

        lblR.textContent = r;
        lblG.textContent = g;
        lblB.textContent = b;
        lblTemp.textContent = temp;
        lblHum.textContent = hum;
        lblTime.textContent = time;

        formColorSwatch.style.backgroundColor = `rgb(${r}, ${g}, ${b})`;
        formRgbDisplay.textContent = `RGB(${r}, ${g}, ${b})`;

        // Optical Substrate Darkening Index: Baseline Yellow Substrate (675.0)
        const baseline = 675.0;
        const current = r + g + b;
        const darkeningPct = Math.max(0, Math.min(100, ((baseline - current) / baseline) * 100));
        formDarkeningBadge.textContent = `Sensor Darkening: ${darkeningPct.toFixed(1)}%`;
    }

    [sliderR, sliderG, sliderB, sliderTemp, sliderHum, sliderTime].forEach(input => {
        input.addEventListener('input', updateFormOpticalSwatch);
    });

    // Preset Buttons
    document.querySelectorAll('.preset-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.preventDefault();
            sliderR.value = btn.getAttribute('data-r');
            sliderG.value = btn.getAttribute('data-g');
            sliderB.value = btn.getAttribute('data-b');
            sliderTemp.value = btn.getAttribute('data-t');
            sliderHum.value = btn.getAttribute('data-h');
            sliderTime.value = btn.getAttribute('data-e');
            updateFormOpticalSwatch();
            submitPrediction();
        });
    });

    // -------------------------------------------------------------
    // Helper: Risk Badges & Classes
    // -------------------------------------------------------------
    function getRiskBadgeClass(risk) {
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

    function getStatCardClass(risk) {
        switch (risk) {
            case 'Low':
            case 'Safe':
            case 'Low Risk': return 'low';
            case 'Moderate':
            case 'Moderate Risk': return 'moderate';
            case 'High':
            case 'High Risk':
            case 'Hazardous': return 'high';
            default: return 'low';
        }
    }

    // -------------------------------------------------------------
    // 1. DASHBOARD HOME: Fetch & Render
    // -------------------------------------------------------------
    async function fetchDashboardData() {
        try {
            const res = await fetch('/api/dashboard');
            const json = await res.json();
            if (json.status === 'success') {
                renderDashboardHome(json);
                renderCharts(json.data);
            }
        } catch (err) {
            console.error('Error fetching dashboard stats:', err);
        }
    }

    function renderDashboardHome(data) {
        // KPI Cards
        document.getElementById('kpi-total-readings').textContent = data.total_readings;
        document.getElementById('kpi-avg-exposure').textContent = data.average_exposure.toFixed(2);
        document.getElementById('kpi-max-exposure').textContent = data.highest_exposure.toFixed(2);
        
        const riskStatus = data.current_risk_status || (data.latest_reading ? data.latest_reading.risk_class : 'Low');
        const riskBadge = document.getElementById('kpi-current-risk');
        riskBadge.innerHTML = `<span class="${getRiskBadgeClass(riskStatus)}">${riskStatus.toUpperCase()}</span>`;
        
        const avgCard = document.getElementById('kpi-avg-card');
        avgCard.className = `stat-card ${getStatCardClass(riskStatus)}`;

        document.getElementById('kpi-connected-devices').textContent = data.connected_device_count || 5;
        document.getElementById('nav-fleet-count').textContent = data.connected_device_count || 5;

        // Latest / Live Sensor Reading Card
        const latest = data.latest_reading;
        if (latest) {
            document.getElementById('latest-device-badge').textContent = `Device: ${latest.device_id}`;
            document.getElementById('latest-r').textContent = latest.red_value;
            document.getElementById('latest-g').textContent = latest.green_value;
            document.getElementById('latest-b').textContent = latest.blue_value;
            document.getElementById('latest-temp').textContent = `${latest.temperature.toFixed(1)} °C`;
            document.getElementById('latest-hum').textContent = `${latest.humidity.toFixed(1)} %`;
            document.getElementById('latest-time').textContent = `${latest.exposure_time.toFixed(1)} h`;
            document.getElementById('latest-timestamp').textContent = latest.timestamp;

            const darkeningPct = ((latest.sensor_response || 0) * 100).toFixed(1);
            document.getElementById('latest-darkening-badge').textContent = `Sensor Darkening: ${darkeningPct}%`;

            const latestSwatch = document.getElementById('latest-color-swatch');
            latestSwatch.style.backgroundColor = `rgb(${latest.red_value}, ${latest.green_value}, ${latest.blue_value})`;
            document.getElementById('latest-rgb-text').textContent = `RGB(${latest.red_value}, ${latest.green_value}, ${latest.blue_value})`;

            // Active AI Exposure Assessment Card
            const expLevel = latest.predicted_exposure_level !== undefined ? latest.predicted_exposure_level : latest.exposure_level || 0;
            document.getElementById('dash-pred-ppm').textContent = expLevel.toFixed(2);
            document.getElementById('dash-pred-risk').textContent = latest.risk_class;

            const dashRiskBadge = document.getElementById('dash-pred-risk-badge');
            dashRiskBadge.className = getRiskBadgeClass(latest.risk_class);
            dashRiskBadge.textContent = `${latest.risk_class.toUpperCase()} RISK`;

            document.getElementById('dash-pred-exp-card').className = `stat-card ${getStatCardClass(latest.risk_class)}`;
            document.getElementById('dash-pred-status-card').className = `stat-card ${getStatCardClass(latest.risk_class)}`;

            // Safety Guidance
            const advisory = getAdvisoryText(latest.risk_class);
            document.getElementById('dash-advisory-text').textContent = advisory;
        }
    }

    function getAdvisoryText(risk) {
        switch (risk) {
            case 'Low':
            case 'Safe':
            case 'Low Risk':
                return 'Normal ambient levels. Exposure is well within safe 8-hr TWA occupational thresholds.';
            case 'Moderate':
            case 'Moderate Risk':
                return 'Eye & respiratory irritation threshold exceeded (OSHA 20 ppm ceiling). Don appropriate PPE and limit exposure.';
            case 'High':
            case 'High Risk':
            case 'Hazardous':
                return 'CRITICAL EVACUATION WARNING: Severe olfactory fatigue and toxic threshold exceeded! Don SCBA apparatus immediately!';
            default:
                return 'Routine occupational monitoring recommended.';
        }
    }

    // -------------------------------------------------------------
    // 2. SENSOR DATA: 4 Chart.js Visualizations
    // -------------------------------------------------------------
    function renderCharts(statsData) {
        const series = statsData.recent_series || [];
        const timestamps = series.map(s => (s.timestamp.split(' ')[1] || s.timestamp));
        const exposures = series.map(s => (s.predicted_exposure_level !== undefined ? s.predicted_exposure_level : s.exposure_level));

        // 1. Exposure Level Over Time Line Chart
        const ctxExp = document.getElementById('chartExposureTrend').getContext('2d');
        if (chartExposureTrendInstance) chartExposureTrendInstance.destroy();
        chartExposureTrendInstance = new Chart(ctxExp, {
            type: 'line',
            data: {
                labels: timestamps,
                datasets: [{
                    label: 'H₂S Exposure (PPM)',
                    data: exposures,
                    borderColor: '#38bdf8',
                    backgroundColor: 'rgba(56, 189, 248, 0.15)',
                    fill: true,
                    tension: 0.35,
                    pointRadius: 4,
                    pointHoverRadius: 6
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { labels: { color: '#cbd5e1' } } },
                scales: {
                    x: { ticks: { color: '#94a3b8' }, grid: { color: '#243044' } },
                    y: { title: { display: true, text: 'PPM', color: '#94a3b8' }, ticks: { color: '#cbd5e1' }, grid: { color: '#243044' } }
                }
            }
        });

        // 2. Low/Moderate/High Risk Distribution Chart (Doughnut)
        const riskDist = statsData.risk_distribution || {};
        const riskLabels = ['Low', 'Moderate', 'High'];
        const riskCounts = [
            riskDist['Low'] || 0,
            riskDist['Moderate'] || 0,
            riskDist['High'] || 0
        ];

        const ctxPie = document.getElementById('chartRiskPie').getContext('2d');
        if (chartRiskPieInstance) chartRiskPieInstance.destroy();
        chartRiskPieInstance = new Chart(ctxPie, {
            type: 'doughnut',
            data: {
                labels: ['Low Risk (<20 ppm)', 'Moderate Risk (20-50 ppm)', 'High Risk (>=50 ppm)'],
                datasets: [{
                    data: riskCounts,
                    backgroundColor: ['#10b981', '#f97316', '#ef4444'],
                    borderColor: '#161e2e',
                    borderWidth: 3
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { position: 'bottom', labels: { color: '#cbd5e1' } } }
            }
        });

        // 3. RGB Sensor Value Chart (Bar Chart)
        const redValues = series.map(s => s.red_value || 0);
        const greenValues = series.map(s => s.green_value || 0);
        const blueValues = series.map(s => s.blue_value || 0);

        const ctxRgb = document.getElementById('chartRgbValues').getContext('2d');
        if (chartRgbValuesInstance) chartRgbValuesInstance.destroy();
        chartRgbValuesInstance = new Chart(ctxRgb, {
            type: 'bar',
            data: {
                labels: timestamps,
                datasets: [
                    { label: 'Red Channel', data: redValues, backgroundColor: 'rgba(239, 68, 68, 0.75)' },
                    { label: 'Green Channel', data: greenValues, backgroundColor: 'rgba(16, 185, 129, 0.75)' },
                    { label: 'Blue Channel', data: blueValues, backgroundColor: 'rgba(59, 130, 246, 0.75)' }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { labels: { color: '#cbd5e1' } } },
                scales: {
                    x: { ticks: { color: '#94a3b8' }, grid: { display: false } },
                    y: { max: 255, title: { display: true, text: 'Intensity (0-255)', color: '#94a3b8' }, ticks: { color: '#cbd5e1' }, grid: { color: '#243044' } }
                }
            }
        });

        // 4. Temperature and Humidity Trend Chart (Dual-Axis)
        const temperatures = series.map(s => s.temperature || 0);
        const humidities = series.map(s => s.humidity || 0);

        const ctxTempHum = document.getElementById('chartTempHum').getContext('2d');
        if (chartTempHumInstance) chartTempHumInstance.destroy();
        chartTempHumInstance = new Chart(ctxTempHum, {
            type: 'line',
            data: {
                labels: timestamps,
                datasets: [
                    {
                        label: 'Temperature (°C)',
                        data: temperatures,
                        borderColor: '#fbbf24',
                        backgroundColor: 'rgba(251, 191, 36, 0.1)',
                        yAxisID: 'yTemp',
                        tension: 0.3
                    },
                    {
                        label: 'Humidity (%)',
                        data: humidities,
                        borderColor: '#06b6d4',
                        backgroundColor: 'rgba(6, 182, 212, 0.1)',
                        yAxisID: 'yHum',
                        tension: 0.3
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { labels: { color: '#cbd5e1' } } },
                scales: {
                    x: { ticks: { color: '#94a3b8' }, grid: { color: '#243044' } },
                    yTemp: { type: 'linear', position: 'left', title: { display: true, text: '°C', color: '#fbbf24' }, ticks: { color: '#fbbf24' }, grid: { color: '#243044' } },
                    yHum: { type: 'linear', position: 'right', title: { display: true, text: '%', color: '#06b6d4' }, ticks: { color: '#06b6d4' }, grid: { display: false } }
                }
            }
        });
    }

    // Telemetry Simulation Controls
    document.getElementById('btn-stream-burst').addEventListener('click', async () => {
        try {
            await fetch('/api/simulate/batch', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ count: 5 })
            });
            fetchDashboardData();
            fetchHistory();
        } catch (err) {
            console.error('Error in burst simulation:', err);
        }
    });

    document.getElementById('dash-btn-simulate-quick').addEventListener('click', async () => {
        try {
            await fetch('/api/simulate/batch', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ count: 5 })
            });
            fetchDashboardData();
            fetchHistory();
        } catch (err) {
            console.error('Error in quick simulation:', err);
        }
    });

    const btnAutoStream = document.getElementById('btn-stream-auto');
    btnAutoStream.addEventListener('click', () => {
        if (autoStreamTimer) {
            clearInterval(autoStreamTimer);
            autoStreamTimer = null;
            btnAutoStream.classList.remove('btn-danger');
            btnAutoStream.classList.add('btn-outline-info');
            btnAutoStream.innerHTML = '<i class="fa-solid fa-play me-1"></i>Start Auto Stream (3s)';
        } else {
            autoStreamTimer = setInterval(async () => {
                await fetch('/api/simulate/batch', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ count: 1 })
                });
                fetchDashboardData();
                if (document.getElementById('nav-history-tab').classList.contains('active')) {
                    fetchHistory();
                }
            }, 3000);
            btnAutoStream.classList.remove('btn-outline-info');
            btnAutoStream.classList.add('btn-danger');
            btnAutoStream.innerHTML = '<i class="fa-solid fa-stop me-1"></i>Stop Auto Stream';
        }
    });

    document.getElementById('btn-refresh-charts').addEventListener('click', fetchDashboardData);
    document.getElementById('dash-btn-goto-predict').addEventListener('click', () => {
        const triggerEl = document.querySelector('#nav-prediction-tab');
        bootstrap.Tab.getInstance(triggerEl) || new bootstrap.Tab(triggerEl).show();
        triggerEl.click();
    });

    // -------------------------------------------------------------
    // 3. AI PREDICTION: Dynamic Inference Form
    // -------------------------------------------------------------
    async function submitPrediction() {
        const payload = {
            device_id: predDevice.value,
            red_value: parseInt(sliderR.value),
            green_value: parseInt(sliderG.value),
            blue_value: parseInt(sliderB.value),
            temperature: parseFloat(sliderTemp.value),
            humidity: parseFloat(sliderHum.value),
            exposure_time: parseFloat(sliderTime.value)
        };

        try {
            const res = await fetch('/api/predict', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });

            const data = await res.json();
            if (data.status === 'success') {
                renderPredictionResults(data);
            }
        } catch (err) {
            console.error('Error submitting prediction:', err);
        }
    }

    formPredict.addEventListener('submit', (e) => {
        e.preventDefault();
        submitPrediction();
    });

    function renderPredictionResults(data) {
        const ppm = data.predicted_exposure_level !== undefined ? data.predicted_exposure_level : data.exposure_level;
        const risk = data.risk_class;
        const conf = ((data.confidence || 0.95) * 100).toFixed(1);

        document.getElementById('pred-res-ppm').textContent = ppm.toFixed(2);
        document.getElementById('pred-res-risk').textContent = risk;
        document.getElementById('pred-res-ts').textContent = data.timestamp;
        document.getElementById('pred-res-conf').textContent = `${conf}%`;

        const badge = document.getElementById('pred-risk-badge');
        badge.className = getRiskBadgeClass(risk);
        badge.textContent = `${risk.toUpperCase()} RISK`;

        document.getElementById('pred-exp-card').className = `stat-card ${getStatCardClass(risk)}`;
        document.getElementById('pred-risk-card').className = `stat-card ${getStatCardClass(risk)}`;

        // Advisory Message
        document.getElementById('pred-advisory-text').textContent = (data.risk_metadata && data.risk_metadata.action) ? data.risk_metadata.action : getAdvisoryText(risk);

        // Class Probability Chart
        renderProbabilityChart(data.class_probabilities || { 'Low': 0.85, 'Moderate': 0.12, 'High': 0.03 });
    }

    function renderProbabilityChart(probs) {
        const labels = Object.keys(probs);
        const values = Object.values(probs).map(v => (v * 100).toFixed(1));
        const colors = labels.map(l => l === 'Low' ? '#10b981' : l === 'Moderate' ? '#f97316' : '#ef4444');

        const ctx = document.getElementById('chartPredictProb').getContext('2d');
        if (chartPredictProbInstance) chartPredictProbInstance.destroy();

        chartPredictProbInstance = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Probability (%)',
                    data: values,
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
                    x: { max: 100, ticks: { color: '#94a3b8' }, grid: { color: '#243044' } },
                    y: { ticks: { color: '#cbd5e1' }, grid: { display: false } }
                }
            }
        });
    }

    // -------------------------------------------------------------
    // 4. SENSOR HISTORY: Searchable & Filterable Table
    // -------------------------------------------------------------
    async function fetchHistory() {
        const riskFilter = document.getElementById('history-filter-risk').value;
        const url = `/api/history?limit=${historyLimit}&offset=${historyPage * historyLimit}${riskFilter ? `&risk_class=${encodeURIComponent(riskFilter)}` : ''}`;

        try {
            const res = await fetch(url);
            const json = await res.json();
            if (json.status === 'success') {
                fullHistoryCache = json.data;
                renderHistoryTable(json.data, json.total);
            }
        } catch (err) {
            console.error('Error fetching history:', err);
        }
    }

    function renderHistoryTable(records, total) {
        const tbody = document.getElementById('history-table-body');
        tbody.innerHTML = '';

        if (!records || records.length === 0) {
            tbody.innerHTML = '<tr><td colspan="11" class="text-center py-4 text-muted">No telemetry records found.</td></tr>';
            return;
        }

        records.forEach(r => {
            const tr = document.createElement('tr');
            const darkPct = ((r.sensor_response || 0) * 100).toFixed(1);
            const badgeClass = getRiskBadgeClass(r.risk_class);
            const recordId = r.prediction_id || r.record_id;
            const expLevel = (r.predicted_exposure_level !== undefined ? r.predicted_exposure_level : r.exposure_level || 0).toFixed(2);

            tr.innerHTML = `
                <td>#${recordId}</td>
                <td><span class="badge bg-secondary">${r.device_id}</span></td>
                <td><small>${r.timestamp}</small></td>
                <td>
                    <div style="width: 22px; height: 22px; border-radius: 4px; background-color: rgb(${r.red_value}, ${r.green_value}, ${r.blue_value}); border: 1px solid #475569;"></div>
                </td>
                <td>${r.red_value}, ${r.green_value}, ${r.blue_value}</td>
                <td>${r.temperature.toFixed(1)}</td>
                <td>${r.humidity.toFixed(1)}</td>
                <td>${r.exposure_time.toFixed(1)}</td>
                <td>${darkPct}%</td>
                <td class="fw-bold text-info">${expLevel} ppm</td>
                <td><span class="${badgeClass}">${r.risk_class}</span></td>
            `;
            tbody.appendChild(tr);
        });

        // Pagination Counter
        const start = historyPage * historyLimit + 1;
        const end = Math.min(total, (historyPage + 1) * historyLimit);
        document.getElementById('history-page-info').textContent = `Showing ${start}-${end} of ${total} records`;

        document.getElementById('btn-history-prev').disabled = (historyPage === 0);
        document.getElementById('btn-history-next').disabled = (end >= total);
    }

    // Dynamic Search Filter
    document.getElementById('history-search-input').addEventListener('input', (e) => {
        const query = e.target.value.toLowerCase();
        if (!query) {
            renderHistoryTable(fullHistoryCache, fullHistoryCache.length);
            return;
        }
        const filtered = fullHistoryCache.filter(r => 
            (r.device_id && r.device_id.toLowerCase().includes(query)) ||
            (r.risk_class && r.risk_class.toLowerCase().includes(query)) ||
            (r.timestamp && r.timestamp.toLowerCase().includes(query))
        );
        renderHistoryTable(filtered, filtered.length);
    });

    document.getElementById('btn-history-prev').addEventListener('click', () => {
        if (historyPage > 0) {
            historyPage--;
            fetchHistory();
        }
    });

    document.getElementById('btn-history-next').addEventListener('click', () => {
        historyPage++;
        fetchHistory();
    });

    document.getElementById('history-filter-risk').addEventListener('change', () => {
        historyPage = 0;
        fetchHistory();
    });

    // -------------------------------------------------------------
    // 5. MODEL PERFORMANCE: Fetch Real Metrics
    // -------------------------------------------------------------
    async function fetchModelPerformance() {
        try {
            const res = await fetch('/api/model/metrics');
            const json = await res.json();
            if (json.status === 'success') {
                renderModelPerformance(json.data);
            }
        } catch (err) {
            console.error('Error fetching model performance metrics:', err);
        }
    }

    function renderModelPerformance(m) {
        // Regressor Metrics
        document.getElementById('perf-r2').textContent = m.regression.r2_score.toFixed(4);
        document.getElementById('perf-rmse').textContent = `${m.regression.rmse.toFixed(3)} ppm`;
        document.getElementById('perf-mae').textContent = `${m.regression.mae.toFixed(3)} ppm`;

        // Classifier Metrics
        document.getElementById('perf-acc').textContent = `${(m.classification.accuracy * 100).toFixed(1)}%`;
        document.getElementById('perf-prec').textContent = m.classification.precision.toFixed(3);
        document.getElementById('perf-rec').textContent = m.classification.recall.toFixed(3);
        document.getElementById('perf-f1').textContent = m.classification.f1_score.toFixed(3);

        // Feature Importance Chart
        const importances = m.regression.feature_importances;
        const featLabels = Object.keys(importances);
        const featValues = Object.values(importances);

        const ctx = document.getElementById('chartFeatureImport').getContext('2d');
        if (chartFeatureImportInstance) chartFeatureImportInstance.destroy();

        chartFeatureImportInstance = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: featLabels,
                datasets: [{
                    label: 'Feature Importance Weight',
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
                    x: { ticks: { color: '#94a3b8' }, grid: { color: '#243044' } },
                    y: { ticks: { color: '#cbd5e1' }, grid: { display: false } }
                }
            }
        });

        // 3x3 Confusion Matrix
        const cm = m.classification.confusion_matrix;
        const classes = m.classification.classes;
        const container = document.getElementById('perf-cm-container');

        let html = '<div class="cm-grid">';
        classes.forEach(c => {
            html += `<div class="cm-cell cm-header">${c}</div>`;
        });
        cm.forEach((row, i) => {
            row.forEach((val, j) => {
                const isDiagonal = (i === j);
                const bg = isDiagonal ? 'background: rgba(16, 185, 129, 0.25); color: #34d399;' : 'background: #1e293b; color: #94a3b8;';
                html += `<div class="cm-cell" style="${bg}">${val}</div>`;
            });
        });
        html += '</div>';
        container.innerHTML = html;
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
        if (!devices || devices.length === 0) {
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
    // Navigation Tab Change Event Listeners
    // -------------------------------------------------------------
    document.getElementById('nav-dashboard-tab').addEventListener('click', fetchDashboardData);
    document.getElementById('nav-sensordata-tab').addEventListener('click', fetchDashboardData);
    document.getElementById('nav-history-tab').addEventListener('click', fetchHistory);
    document.getElementById('nav-model-tab').addEventListener('click', fetchModelPerformance);

    // Initial Startup Invocation
    updateFormOpticalSwatch();
    fetchDashboardData();
    submitPrediction();
});

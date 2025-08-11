// MÁV Monitor JavaScript
class MAVMonitor {
    constructor() {
        this.charts = {};
        this.currentData = null;
        this.isLoading = false;
        this.availableDateUsed = null; // The date that actually had data
        this.defaultFallbackDate = '2025-08-06';
        this.blockOnFailure = true; // Controls whether to block UI on load failure
        
        this.init();
    }
    
    init() {
        this.setupDatePicker();
        this.setupEventListeners();
        this.loadDefaultData();
        this.updateStatus('', false);
    }
    
    setupDatePicker() {
        const datePicker = document.getElementById('date-picker');
        if (!datePicker) {
            console.error('Date picker element not found');
            return;
        }
        
        const yesterday = this.getYesterday();
        
        // Initialize Flatpickr with HU locale and nicer UX
        try {
            this.flatpickrInstance = flatpickr(datePicker, {
                defaultDate: yesterday,
                maxDate: yesterday,
                dateFormat: "Y-m-d",
                locale: (window.flatpickr && window.flatpickr.l10ns && window.flatpickr.l10ns.hu) ? window.flatpickr.l10ns.hu : undefined,
                altInput: true,
                altFormat: "Y-m-d",
                allowInput: true,
                animate: true,
                weekNumbers: false,
                disableMobile: true,
                onReady: (selectedDates, dateStr, instance) => {
                    if (instance.altInput) {
                        instance.altInput.classList.add('fp-alt-input');
                    }
                }
            });
        } catch (error) {
            console.error('Failed to initialize flatpickr:', error);
            // Fallback to basic date input
            datePicker.type = 'date';
            datePicker.value = this.formatYMD(yesterday);
            datePicker.max = this.formatYMD(yesterday);
        }
    }
    
    setupEventListeners() {
        const loadButton = document.getElementById('load-data');
        const datePicker = document.getElementById('date-picker');
        const avgDelayBtn = document.getElementById('avg-delay-btn');
        const maxDelayBtn = document.getElementById('max-delay-btn');
        const themeToggle = document.getElementById('theme-toggle');
        const iconSun = document.getElementById('icon-sun');
        const iconMoon = document.getElementById('icon-moon');
        
        if (loadButton) {
            loadButton.addEventListener('click', () => {
                this.loadDataForDate(datePicker ? datePicker.value : '', { strict: true });
            });
        }
        
        // Flatpickr change event
        if (datePicker) {
            datePicker.addEventListener('change', () => {
                this.loadDataForDate(datePicker.value, { strict: true });
            });
        }
        
        // Map toggle buttons
        if (avgDelayBtn) {
            avgDelayBtn.addEventListener('click', () => {
                this.switchMap('avg');
            });
        }
        
        if (maxDelayBtn) {
            maxDelayBtn.addEventListener('click', () => {
                this.switchMap('max');
            });
        }
        
        // Window resize handler for responsive charts
        window.addEventListener('resize', () => {
            Object.values(this.charts).forEach(chart => {
                if (chart) chart.resize();
            });
        });

        // Theme toggle (persist in localStorage)
        const applyTheme = (mode) => {
            const root = document.documentElement;
            if (mode === 'dark') {
                root.classList.add('dark');
                if (iconSun) iconSun.classList.remove('hidden');
                if (iconMoon) iconMoon.classList.add('hidden');
            } else {
                root.classList.remove('dark');
                if (iconSun) iconSun.classList.add('hidden');
                if (iconMoon) iconMoon.classList.remove('hidden');
            }
        };
        const storedTheme = (() => { try { return localStorage.getItem('theme'); } catch { return null; } })();
        const prefersDark = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
        applyTheme(storedTheme || (prefersDark ? 'dark' : 'light'));
        if (themeToggle) {
            themeToggle.addEventListener('click', () => {
                const isDark = document.documentElement.classList.contains('dark');
                const next = isDark ? 'light' : 'dark';
                applyTheme(next);
                try { localStorage.setItem('theme', next); } catch {}
            });
        }
    }
    
    // Utilities
    getYesterday() {
        const d = new Date();
        d.setUTCDate(d.getUTCDate() - 1);
        d.setUTCHours(0, 0, 0, 0);
        return d;
    }

    formatYMD(dateObj) {
        const y = dateObj.getUTCFullYear();
        const m = String(dateObj.getUTCMonth() + 1).padStart(2, '0');
        const d = String(dateObj.getUTCDate()).padStart(2, '0');
        return `${y}-${m}-${d}`;
    }

    async urlExists(url) {
        try {
            const res = await fetch(url, { cache: 'no-store' });
            return res.ok;
        } catch {
            return false;
        }
    }

    async fileExists(date, fileName) {
        const baseUrl = `https://storage.googleapis.com/mpt-all-sources/blog/mav/json_output/${date}`;
        const directUrl = `${baseUrl}/${fileName}`;
        const urlParams = new URLSearchParams(window.location.search);
        const forceProxy = urlParams.get('proxy') === '1';
        const isLocal = ['localhost', '127.0.0.1'].includes(window.location.hostname);
        const proxyUrl = `${window.location.origin}/api/mav-data/${date}/${fileName}`;
        const tryDirect = async () => {
            try {
                const r = await fetch(directUrl, { cache: 'no-store' });
                return r.ok;
            } catch { return false; }
        };
        const tryProxy = async () => {
            try {
                const r = await fetch(proxyUrl, { cache: 'no-store' });
                return r.ok;
            } catch { return false; }
        };
        if (forceProxy || isLocal) {
            return (await tryProxy()) || (await tryDirect());
        }
        return (await tryDirect()) || (await tryProxy());
    }

    async findLatestAvailableDate(preferredYMD) {
        // Try preferred date first, then go back up to 30 days
        const start = preferredYMD ? new Date(preferredYMD) : this.getYesterday();
        for (let i = 0; i < 30; i++) {
            const d = new Date(start);
            d.setUTCDate(d.getUTCDate() - i);
            const ymd = this.formatYMD(d);
            if (await this.fileExists(ymd, 'quick_stats.json')) {
                return ymd;
            }
        }
        // Fallback to a known good date if nothing is found
        return this.defaultFallbackDate;
    }
    
    generateFakeData(date) {
        // Generate realistic fake data based on the notebook patterns
        const routes = this.generateRoutes(1200 + Math.floor(Math.random() * 400));
        return {
            date: date,
            routes: routes,
            summary: this.calculateSummary(routes)
        };
    }
    
    generateRoutes(count) {
        const routes = [];
        const stationPairs = [
            'Budapest-Keleti ⟷ Debrecen',
            'Budapest-Nyugati ⟷ Szombathely',
            'Budapest-Déli ⟷ Pécs',
            'Szeged ⟷ Budapest-Nyugati',
            'Miskolc ⟷ Budapest-Keleti',
            'Győr ⟷ Budapest-Keleti',
            'Kecskemét ⟷ Budapest-Nyugati',
            'Nyíregyháza ⟷ Budapest-Keleti',
            'Szolnok ⟷ Budapest-Keleti',
            'Veszprém ⟷ Budapest-Déli'
        ];
        
        for (let i = 0; i < count; i++) {
            const route = {
                id: `route_${i}`,
                stationPair: stationPairs[Math.floor(Math.random() * stationPairs.length)],
                delay: this.generateDelay(),
                price: this.generatePrice(),
                travelTime: 60 + Math.floor(Math.random() * 240), // 1-5 hours
                transfers: Math.floor(Math.random() * 3) // 0-2 transfers
            };
            routes.push(route);
        }
        
        return routes;
    }
    
    generateDelay() {
        // Generate realistic delay distribution
        const rand = Math.random();
        if (rand < 0.6) {
            // 60% of trains are on time or have minor delays
            return Math.floor(Math.random() * 5);
        } else if (rand < 0.85) {
            // 25% have moderate delays
            return 5 + Math.floor(Math.random() * 15);
        } else if (rand < 0.95) {
            // 10% have significant delays
            return 20 + Math.floor(Math.random() * 30);
        } else {
            // 5% have major delays
            return 50 + Math.floor(Math.random() * 50);
        }
    }
    
    generatePrice() {
        // Generate realistic price distribution
        const basePrice = 500 + Math.floor(Math.random() * 2000);
        const multiplier = 0.8 + Math.random() * 0.4; // 0.8-1.2x
        return Math.round(basePrice * multiplier);
    }
    
    calculateSummary(routes) {
        const delays = routes.map(r => r.delay);
        const prices = routes.map(r => r.price);
        
        const avgDelay = delays.reduce((a, b) => a + b, 0) / delays.length;
        const maxDelay = Math.max(...delays);
        const onTimeCount = delays.filter(d => d <= 5).length;
        const onTimePercentage = (onTimeCount / delays.length) * 100;
        
        return {
            totalRoutes: routes.length,
            avgDelay: avgDelay.toFixed(1),
            maxDelay: maxDelay,
            onTimePercentage: onTimePercentage.toFixed(1)
        };
    }
    
    async loadDataForDate(date, options = { strict: false }) {
        if (this.isLoading) {
            console.warn('Data load already in progress, skipping');
            return;
        }
        if (!date) {
            console.error('No date provided');
            return;
        }
        
        this.isLoading = true;
        this.updateStatus('Adatok betöltése...', true);
        
        try {
            // Strict: always use the exact date; verify quick_stats exists
            const exists = await this.fileExists(date, 'quick_stats.json');
            if (!exists) {
                throw new Error(`No data available for selected date ${date}`);
            }
            this.availableDateUsed = date;
            // Persist last successful date
            try { localStorage.setItem('lastDate', date); } catch {}

            // Load real data from GCS
            const data = await this.loadRealData(date);
            this.currentData = data;
            
            // Update UI
            this.updateSummaryCards();
            this.updateAnalysis();
            this.updateCharts();
            this.loadMap();
            this.updateDateBanner();
            
            this.updateStatus('Adatok betöltve', false);
        } catch (error) {
            console.error('Error loading data:', error);
            if (this.blockOnFailure || (options && options.strict)) {
                this.showErrorMessage('Nem sikerült az adatok betöltése. Kérlek próbáld újra később.');
                this.updateStatus('Hiba történt az adatok betöltése közben', false);
            } else {
                // Fall back to generated data but keep banner and UI consistent
                const fallbackDate = this.availableDateUsed || date || this.defaultFallbackDate;
                this.currentData = this.generateFakeData(fallbackDate);
                this.updateSummaryCards();
                this.updateAnalysis();
                this.destroyChartsIfAny();
                this.updateCharts();
                this.loadMap();
                this.updateDateBanner();
                this.updateStatus('Adatok betöltve (mintaadatok)', false);
            }
        } finally {
            this.isLoading = false;
        }
    }
    
    async loadRealData(date) {
        const baseUrl = `https://storage.googleapis.com/mpt-all-sources/blog/mav/json_output/${date}`;
        const urlParams = new URLSearchParams(window.location.search);
        const forceProxy = urlParams.get('proxy') === '1';
        const isLocal = ['localhost', '127.0.0.1'].includes(window.location.hostname);
        const useProxyFirst = forceProxy || isLocal;
        const fetchGcsOrProxy = async (fileName) => {
            const directUrl = `${baseUrl}/${fileName}`;
            const proxyUrl = `${window.location.origin}/api/mav-data/${date}/${fileName}`;
            const tryDirect = async () => {
                const r = await fetch(directUrl, { cache: 'no-store' });
                if (!r.ok) throw new Error(`HTTP ${r.status}`);
                return r.json();
            };
            const tryProxy = async () => {
                const r = await fetch(proxyUrl, { cache: 'no-store' });
                if (!r.ok) throw new Error(`Proxy HTTP ${r.status}`);
                return r.json();
            };
            const tryAllOrigins = async () => {
                const url = `https://api.allorigins.win/raw?url=${encodeURIComponent(directUrl)}`;
                const r = await fetch(url, { cache: 'no-store' });
                if (!r.ok) throw new Error(`AllOrigins HTTP ${r.status}`);
                return r.json();
            };
            const tryCorsProxyIo = async () => {
                const url = `https://corsproxy.io/?${encodeURIComponent(directUrl)}`;
                const r = await fetch(url, { cache: 'no-store' });
                if (!r.ok) throw new Error(`corsproxy.io HTTP ${r.status}`);
                return r.json();
            };
            if (useProxyFirst) {
                // On localhost or when forced, use the local proxy
                return await tryProxy();
            }
            // Production: now that bucket CORS is fixed, go direct first for speed
            try { return await tryDirect(); } catch {}
            // If direct fails for any reason, fall back to proxy; avoid third-party proxies for performance
            return await tryProxy();
        };
        const [quickStats, routeAnalysisAlt, delayHistogram, priceHistogram, expensiveRoutes, delayedRoutes] = await Promise.all([
            fetchGcsOrProxy('quick_stats.json').catch(() => null),
            fetchGcsOrProxy('route_analysis_summary.json').catch(() => null),
            fetchGcsOrProxy('delay_histogram.json'),
            fetchGcsOrProxy('price_histogram.json'),
            fetchGcsOrProxy('expensive_routes.json'),
            fetchGcsOrProxy('delayed_routes.json'),
        ]);
        
        // Normalize histogram shapes to {bin, count}
        const normalizedDelayHist = (Array.isArray(delayHistogram) ? delayHistogram : []).map(row => ({
            bin: row['Delay Bucket (min)'] || row.bin || row.range || String(row.bucket || ''),
            count: Number(row['Count'] ?? row.count ?? row.value ?? 0)
        }));
        const normalizedPriceHist = (Array.isArray(priceHistogram) ? priceHistogram : []).map(row => ({
            bin: row['Price Bucket (HUF)'] || row.bin || row.range || String(row.bucket || ''),
            count: Number(row['Count'] ?? row.count ?? row.value ?? 0)
        }));
        
        // Normalize summary from either route_analysis_summary.json or quick_stats.json
        const normalizeSummary = (src) => {
            if (!src || typeof src !== 'object') return null;
            const d = src;
            const total = d.total_routes_analyzed ?? d.total_routes ?? d.totalRoutes ?? 0;
            const avgDelay = d.delay_performance?.average_delay_min
                ?? d.average_delay_min ?? d.avg_delay_min ?? d.avg_delay ?? 0;
            const onTime = d.delay_performance?.on_time_pct
                ?? d.on_time_pct ?? d.on_time_percentage ?? d.onTimePct ?? 0;
            const delayedPct = d.delay_performance?.delayed_pct
                ?? d.delayed_pct ?? d.delayedPercentage ?? 0;
            const signifPct = d.delay_performance?.significantly_delayed_pct
                ?? d.significantly_delayed_pct ?? d.significant_delay_pct ?? 0;
            const maxDelay = d.delay_performance?.maximum_delay_min
                ?? d.maximum_delay_min ?? d.max_delay_min ?? d.max_delay ?? 0;
            const avgTravel = d.travel_patterns?.average_travel_time_min
                ?? d.average_travel_time_min ?? 0;
            const avgPrice = d.pricing_insights?.average_ticket_price_huf
                ?? d.average_ticket_price_huf ?? 0;
            return {
                total_routes_analyzed: Number(total) || 0,
                delay_performance: {
                    average_delay_min: Number(avgDelay) || 0,
                    on_time_pct: Number(onTime) || 0,
                    delayed_pct: Number(delayedPct) || 0,
                    significantly_delayed_pct: Number(signifPct) || 0,
                    maximum_delay_min: Number(maxDelay) || 0,
                },
                travel_patterns: {
                    average_travel_time_min: Number(avgTravel) || 0,
                },
                pricing_insights: {
                    average_ticket_price_huf: Number(avgPrice) || 0,
                },
            };
        };
        const routeAnalysisSummary = normalizeSummary(routeAnalysisAlt) || normalizeSummary(quickStats) || {
            total_routes_analyzed: 0,
            delay_performance: {
                average_delay_min: 0,
                on_time_pct: 0,
                delayed_pct: 0,
                significantly_delayed_pct: 0,
                maximum_delay_min: 0,
            },
            travel_patterns: { average_travel_time_min: 0 },
            pricing_insights: { average_ticket_price_huf: 0 },
        };
        
        return {
            date,
            routeAnalysisSummary,
            delayedRoutes: Array.isArray(delayedRoutes) ? delayedRoutes : [],
            expensiveRoutes: Array.isArray(expensiveRoutes) ? expensiveRoutes : [],
            delayHistogram: normalizedDelayHist,
            priceHistogram: normalizedPriceHist,
        };
    }
    
    showErrorMessage(message) {
        // Clear existing content
        this.clearDashboard();
        
        // Show error message
        const mainContent = document.querySelector('main');
        if (mainContent) {
            const errorDiv = document.createElement('div');
            errorDiv.className = 'max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12';
            errorDiv.innerHTML = `
                <div class="bg-red-50 border border-red-200 rounded-2xl p-8 text-center">
                    <div class="text-6xl mb-4">⚠️</div>
                    <h2 class="text-2xl font-semibold text-red-800 mb-2">Adatok betöltése sikertelen</h2>
                    <p class="text-red-600 mb-6">${message}</p>
                    <div class="space-y-3">
                        <p class="text-sm text-red-500">Lehetséges okok:</p>
                        <ul class="text-sm text-red-500 space-y-1">
                            <li>• A kiválasztott dátumra nincsenek elérhető adatok</li>
                            <li>• Hálózati kapcsolat probléma</li>
                            <li>• Szerver hiba</li>
                        </ul>
                    </div>
                    <button onclick="location.reload()" class="mt-6 px-6 py-3 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors">
                        Újra próbálkozás
                    </button>
                </div>
            `;
            mainContent.appendChild(errorDiv);
        }
    }
    
    clearDashboard() {
        // Clear all dashboard content
        const mainContent = document.querySelector('main');
        if (mainContent) {
            mainContent.innerHTML = '';
        }
    }
    
    async loadDefaultData() {
        const urlParams = new URLSearchParams(window.location.search);
        const paramDate = urlParams.get('date');
        const defaultYesterday = this.formatYMD(this.getYesterday());
        const dateToUse = paramDate || defaultYesterday;
        const datePicker = document.getElementById('date-picker');
        if (datePicker) {
            datePicker.value = dateToUse;
        }
        console.log('Loading default data for date:', dateToUse);
        await this.loadDataForDate(dateToUse, { strict: true });
    }
    
    updateStatus(message, loading) {
        const statusBar = document.getElementById('status-bar');
        if (!statusBar) {
            console.warn('Status bar element not found');
            return;
        }
        
        const statusText = statusBar.querySelector('.status-text');
        const loader = statusBar.querySelector('.loader');
        
        if (statusText) {
            statusText.textContent = message;
        }
        
        if (loader) {
            loader.style.display = loading ? 'block' : 'none';
        }
        
        if (loading) {
            statusBar.classList.add('loading');
        } else {
            statusBar.classList.remove('loading');
        }
    }
    
    updateSummaryCards() {
        console.log('updateSummaryCards called, currentData:', this.currentData);
        
        if (!this.currentData || !this.currentData.routeAnalysisSummary) {
            console.warn('No real data available, skipping summary cards update');
            return;
        }
        
        // Real data from GCS - quick_stats.json normalized to routeAnalysisSummary
        const { routeAnalysisSummary } = this.currentData;
        
        console.log('Using real data from route_analysis_summary.json:', routeAnalysisSummary);
        
        // Extract the 4 best metrics for the summary cards
        const totalRoutes = routeAnalysisSummary.total_routes_analyzed || 0;
        const avgDelay = routeAnalysisSummary.delay_performance?.average_delay_min || 0;
        const onTimePct = routeAnalysisSummary.delay_performance?.on_time_pct || 0;
        const maxDelay = routeAnalysisSummary.delay_performance?.maximum_delay_min || 0;
        
        // Update the summary cards with the 4 best metrics
        const totalRoutesElem = document.getElementById('total-routes');
        const avgDelayElem = document.getElementById('avg-delay');
        const ontimePercentageElem = document.getElementById('ontime-percentage');
        const maxDelayElem = document.getElementById('max-delay');
        
        if (totalRoutesElem) totalRoutesElem.textContent = totalRoutes.toLocaleString();
        if (avgDelayElem) avgDelayElem.textContent = Number(avgDelay).toFixed(1);
        if (ontimePercentageElem) ontimePercentageElem.textContent = `${Number(onTimePct).toFixed(1)}%`;
        if (maxDelayElem) maxDelayElem.textContent = Number(maxDelay).toLocaleString();
        
        console.log('Updated summary cards with:', {
            totalRoutes,
            avgDelay,
            onTimePct,
            maxDelay
        });
        
        // Add animation
        document.querySelectorAll('.summary-card').forEach((card, index) => {
            setTimeout(() => {
                card.classList.add('fade-in');
            }, index * 100);
        });
    }
    
    updateCharts() {
        if (!this.currentData) return;
        // Ensure no duplicate chart instances
        this.destroyChartsIfAny();
        
        this.createDelayChart();
        this.createPriceChart();
    }

    destroyChartsIfAny() {
        try {
            if (this.charts.delay) { this.charts.delay.destroy(); this.charts.delay = null; }
            if (this.charts.price) { this.charts.price.destroy(); this.charts.price = null; }
        } catch {}
        const delayCanvas = document.getElementById('delay-chart');
        const priceCanvas = document.getElementById('price-chart');
        if (delayCanvas && delayCanvas.chart) { try { delayCanvas.chart.destroy(); } catch {} delayCanvas.chart = null; }
        if (priceCanvas && priceCanvas.chart) { try { priceCanvas.chart.destroy(); } catch {} priceCanvas.chart = null; }
    }
    
    createDelayChart() {
        const canvas = this.ensureFreshCanvas('delay-chart');
        if (!canvas) {
            console.error('Delay chart canvas not found');
            return;
        }
        
        const ctx = canvas.getContext('2d');
        if (!ctx) {
            console.error('Could not get 2D context for delay chart');
            return;
        }
        
        // Canvas is fresh at this point
        
        // Check if we have real histogram data
        if (!this.currentData || !this.currentData.delayHistogram || !Array.isArray(this.currentData.delayHistogram) || this.currentData.delayHistogram.length === 0) {
            console.warn('No delay histogram data available');
            return;
        }
        
        // Use real histogram data from GCS
        const histogramData = this.currentData.delayHistogram;
        
        // Extract labels and data from the histogram
        const labels = histogramData.map(item => item.bin || item.range || `${item.min}-${item.max}`);
        const data = histogramData.map(item => item.count || item.frequency || 0);
        
        this.createChart(ctx, labels, data, 'Késések eloszlása', 'Késés (perc)', 'Járatok száma', 'delay');
    }
    
    createChart(ctx, labels, data, title, xAxisLabel, yAxisLabel, chartKey = 'bar') {
        const gradient = ctx.createLinearGradient(0, 0, 0, 400);
        gradient.addColorStop(0, 'rgba(59, 130, 246, 0.8)');
        gradient.addColorStop(1, 'rgba(59, 130, 246, 0.2)');
        
        const chart = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    label: yAxisLabel,
                    data: data,
                    backgroundColor: gradient,
                    borderColor: 'rgba(59, 130, 246, 1)',
                    borderWidth: 1,
                    borderRadius: 4,
                    borderSkipped: false,
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    },
                    title: {
                        display: false
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        grid: {
                            color: 'rgba(0, 0, 0, 0.1)',
                            drawBorder: false
                        },
                        ticks: {
                            color: '#6b7280',
                            font: {
                                size: 12
                            }
                        }
                    },
                    x: {
                        grid: {
                            display: false
                        },
                        ticks: {
                            color: '#6b7280',
                            font: {
                                size: 12
                            }
                        }
                    }
                },
                elements: {
                    bar: {
                        borderRadius: 4
                    }
                }
            }
        });
        
        // Store the chart instance
        this.charts[chartKey] = chart;
        
        // Also store it on the canvas for reference
        const canvas = ctx.canvas;
        if (canvas) {
            canvas.chart = chart;
        }
        
        return chart;
    }
    
    createPriceChart() {
        const canvas = this.ensureFreshCanvas('price-chart');
        if (!canvas) {
            console.error('Price chart canvas not found');
            return;
        }
        
        const ctx = canvas.getContext('2d');
        if (!ctx) {
            console.error('Could not get 2D context for price chart');
            return;
        }
        
        // Canvas is fresh at this point
        
        // Check if we have real histogram data
        if (!this.currentData || !this.currentData.priceHistogram || !Array.isArray(this.currentData.priceHistogram) || this.currentData.priceHistogram.length === 0) {
            console.warn('No price histogram data available');
            return;
        }
        
        // Use real histogram data from GCS
        const histogramData = this.currentData.priceHistogram;
        
        // Extract labels and data from the histogram
        const labels = histogramData.map(item => item.bin || item.range || `${item.min}-${item.max} Ft`);
        const data = histogramData.map(item => item.count || item.frequency || 0);
        
        const gradient = ctx.createLinearGradient(0, 0, 0, 400);
        gradient.addColorStop(0, 'rgba(16, 185, 129, 0.8)');
        gradient.addColorStop(1, 'rgba(16, 185, 129, 0.2)');
        
        const chart = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Járatok száma',
                    data: data,
                    backgroundColor: gradient,
                    borderColor: 'rgba(16, 185, 129, 1)',
                    borderWidth: 1,
                    borderRadius: 4,
                    borderSkipped: false,
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    },
                    title: {
                        display: false
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        grid: {
                            color: 'rgba(0, 0, 0, 0.1)',
                            drawBorder: false
                        },
                        ticks: {
                            color: '#6b7280',
                            font: {
                                size: 12
                            }
                        }
                    },
                    x: {
                        grid: {
                            display: false
                        },
                        ticks: {
                            color: '#6b7280',
                            font: {
                                size: 12
                            }
                        }
                    }
                },
                elements: {
                    bar: {
                        borderRadius: 4
                    }
                }
            }
        });
        
        // Store the chart instance
        this.charts.price = chart;
        
        // Also store it on the canvas for reference
        if (canvas) {
            canvas.chart = chart;
        }
        
        return chart;
    }
    
    createHistogramBins(data, min, max, binSize) {
        const bins = [];
        const numBins = Math.ceil((max - min) / binSize);
        
        for (let i = 0; i < numBins; i++) {
            const binMin = min + (i * binSize);
            const binMax = binMin + binSize;
            const count = data.filter(value => value >= binMin && value < binMax).length;
            
            bins.push({
                min: binMin,
                max: binMax,
                count: count
            });
        }
        
        return bins;
    }
    
    updateAnalysis() {
        this.updateDelayedRoutes();
        this.updateExpensiveRoutes();
        this.updatePerformanceMetrics();
    }
    
    updateDelayedRoutes() {
        const container = document.getElementById('delayed-routes');
        if (!container) return;
        
        if (!this.currentData || !this.currentData.delayedRoutes) {
            container.innerHTML = '<p class="text-sm text-slate-500">Nincs adat</p>';
            return;
        }
        
        // Use real delayed routes data
        const delayedRoutes = this.currentData.delayedRoutes.slice(0, 5);
        
        container.innerHTML = delayedRoutes.map(route => `
            <div class="flex items-center justify-between p-3 bg-red-50 rounded-lg border-l-4 border-red-400">
                <div class="flex-1 min-w-0">
                    <p class="text-sm font-medium text-slate-800 truncate">${route.start_station_name || route.stationPair} → ${route.end_station_name || ''}</p>
                    <p class="text-xs text-slate-500">Vonat: ${route.train_name || route.id || 'N/A'}</p>
                </div>
                <div class="text-right">
                    <p class="text-lg font-bold text-red-600">${route.delay_min || route.delay || 0} perc</p>
                </div>
            </div>
        `).join('');
    }
    
    updateExpensiveRoutes() {
        const container = document.getElementById('expensive-routes');
        if (!container) return;
        
        if (!this.currentData || !this.currentData.expensiveRoutes) {
            container.innerHTML = '<p class="text-sm text-slate-500">Nincs adat</p>';
            return;
        }
        
        // Use real expensive routes data
        const expensiveRoutes = this.currentData.expensiveRoutes.slice(0, 5);
        
        container.innerHTML = expensiveRoutes.map(route => `
            <div class="flex items-center justify-between p-3 bg-amber-50 rounded-lg border-l-4 border-amber-400">
                <div class="flex-1 min-w-0">
                    <p class="text-sm font-medium text-slate-800 truncate">${route.start_station_name || route.stationPair} → ${route.end_station_name || ''}</p>
                    <p class="text-xs text-slate-500">Vonat: ${route.train_name || route.id || 'N/A'}</p>
                </div>
                <div class="text-right">
                    <p class="text-lg font-bold text-amber-600">${(route.price_huf || route.price || 0).toLocaleString()} Ft</p>
                </div>
            </div>
        `).join('');
    }
    
    updatePerformanceMetrics() {
        const container = document.getElementById('performance-metrics');
        if (!container) return;
        
        if (!this.currentData || !this.currentData.routeAnalysisSummary) {
            container.innerHTML = '<p class="text-sm text-slate-500">Nincs adat</p>';
            return;
        }
        
        const { routeAnalysisSummary } = this.currentData;
        
        // Extract metrics from real data
        const totalRoutes = routeAnalysisSummary.total_routes_analyzed || 0;
        const onTimePct = routeAnalysisSummary.delay_performance?.on_time_pct || 0;
        const delayedPct = routeAnalysisSummary.delay_performance?.delayed_pct || (100 - onTimePct);
        const significantlyDelayedPct = routeAnalysisSummary.delay_performance?.significantly_delayed_pct || 0;
        const avgDelay = routeAnalysisSummary.delay_performance?.average_delay_min || 0;
        const maxDelay = routeAnalysisSummary.delay_performance?.maximum_delay_min || 0;
        const avgTravelTime = routeAnalysisSummary.travel_patterns?.average_travel_time_min || 0;
        const avgPrice = routeAnalysisSummary.pricing_insights?.average_ticket_price_huf || 0;
        
        const metrics = [
            { label: 'Összesen járatok', value: totalRoutes.toLocaleString(), unit: '' },
            { label: 'Időben érkezők', value: Number(onTimePct).toFixed(1), unit: '%' },
            { label: 'Késő járatok', value: Number(delayedPct).toFixed(1), unit: '%' },
            { label: 'Jelentősen késő (>10 perc)', value: Number(significantlyDelayedPct).toFixed(1), unit: '%' },
            { label: 'Átlagos késés', value: Number(avgDelay).toFixed(1), unit: ' perc' },
            { label: 'Legrosszabb késés', value: maxDelay.toLocaleString(), unit: ' perc' },
            { label: 'Átlagos utazási idő', value: Math.round(avgTravelTime), unit: ' perc' },
            { label: 'Átlagos jegyár', value: Math.round(avgPrice).toLocaleString(), unit: ' HUF' }
        ];
        
        container.innerHTML = metrics.map(metric => `
            <div class="flex items-center justify-between p-2 bg-slate-50 rounded-lg">
                <span class="text-sm text-slate-600">${metric.label}</span>
                <span class="text-sm font-semibold text-slate-800">${metric.value}${metric.unit}</span>
            </div>
        `).join('');
    }
    
    loadMap() {
        // Load the default map (maximum delays) per request
        this.switchMap('max');
    }
    
    async switchMap(type) {
        const avgBtn = document.getElementById('avg-delay-btn');
        const maxBtn = document.getElementById('max-delay-btn');
        const mapFrame = document.getElementById('map-frame');
        const mapContainer = document.getElementById('map-container');
        const datePicker = document.getElementById('date-picker');
        
        // Update button states
        if (type === 'avg') {
            if (avgBtn) avgBtn.classList.add('bg-white', 'text-slate-700', 'shadow-sm');
            if (avgBtn) avgBtn.classList.remove('text-slate-600', 'hover:bg-white/50');
            if (maxBtn) maxBtn.classList.remove('bg-white', 'text-slate-700', 'shadow-sm');
            if (maxBtn) maxBtn.classList.add('text-slate-600', 'hover:bg-white/50');
        } else {
            if (maxBtn) maxBtn.classList.add('bg-white', 'text-slate-700', 'shadow-sm');
            if (maxBtn) maxBtn.classList.remove('text-slate-600', 'hover:bg-white/50');
            if (avgBtn) avgBtn.classList.remove('bg-white', 'text-slate-700', 'shadow-sm');
            if (avgBtn) avgBtn.classList.add('text-slate-600', 'hover:bg-white/50');
        }
        
        // Get selected or resolved available date
        let selectedDate = (datePicker && datePicker.value) ? datePicker.value : (this.availableDateUsed || this.formatYMD(this.getYesterday()));
        
        // Map URLs with multiple filename fallbacks
        const mapCandidates = (d) => (
            type === 'avg'
            ? [
                // with maps/ subfolder (new pipeline)
                `https://storage.googleapis.com/mpt-all-sources/blog/mav/json_output/${d}/maps/delay_aware_train_map.html`,
                `https://storage.googleapis.com/mpt-all-sources/blog/mav/json_output/${d}/maps/hungary_train_delays.html`,
                // without maps/ subfolder (older pipeline)
                `https://storage.googleapis.com/mpt-all-sources/blog/mav/json_output/${d}/delay_aware_train_map.html`,
                `https://storage.googleapis.com/mpt-all-sources/blog/mav/json_output/${d}/hungary_train_delays.html`,
              ]
            : [
                // with maps/ subfolder (new pipeline)
                `https://storage.googleapis.com/mpt-all-sources/blog/mav/json_output/${d}/maps/max_delay_train_map.html`,
                `https://storage.googleapis.com/mpt-all-sources/blog/mav/json_output/${d}/maps/max_delay_map.html`,
                // without maps/ subfolder (older pipeline)
                `https://storage.googleapis.com/mpt-all-sources/blog/mav/json_output/${d}/max_delay_train_map.html`,
                `https://storage.googleapis.com/mpt-all-sources/blog/mav/json_output/${d}/max_delay_map.html`,
              ]
        );
        const primaryList = mapCandidates(selectedDate);
        const fallbackList = mapCandidates(this.availableDateUsed || this.defaultFallbackDate);
        
        console.log(`Attempting to load ${type} map for date ${selectedDate}: ${primaryList[0]}`);
        
        if (mapFrame) {
            const tryLoadList = (urls, next) => {
                if (!urls.length) return next ? next() : this.showMapPlaceholder(mapContainer);
                const url = urls[0];
                mapFrame.src = url;
                mapFrame.style.display = 'block';
                mapFrame.onload = () => {
                    console.log(`${type} map loaded successfully for date ${selectedDate}`);
                    this.updateMapLegend(type);
                };
                mapFrame.onerror = () => {
                    console.warn(`Failed to load map ${url}, trying next candidate`);
                    tryLoadList(urls.slice(1), next);
                };
            };
            console.log(`Attempting to load ${type} map for date ${selectedDate}: ${primaryList[0]}`);
            tryLoadList(primaryList, () => tryLoadList(fallbackList));
        }
        
        this.updateMapLegend(type);
    }
    
    updateMapLegend(type) {
        const legend = document.getElementById('map-legend');
        if (!legend) return;
        
        const legendData = type === 'avg' ? [
            { color: '#10b981', label: '0-5 perc késés' },
            { color: '#f59e0b', label: '5-15 perc késés' },
            { color: '#ef4444', label: '15+ perc késés' }
        ] : [
            { color: '#10b981', label: '0-10 perc késés' },
            { color: '#f59e0b', label: '10-30 perc késés' },
            { color: '#ef4444', label: '30+ perc késés' }
        ];
        
        legend.innerHTML = `
            <h4 class="font-semibold text-slate-800 mb-3">${type === 'avg' ? 'Átlagos' : 'Maximum'} késések</h4>
            <div class="space-y-2">
                ${legendData.map(item => `
                    <div class="flex items-center gap-2">
                        <div class="w-4 h-4 rounded" style="background-color: ${item.color}"></div>
                        <span class="text-sm text-slate-600">${item.label}</span>
                    </div>
                `).join('')}
            </div>
        `;
    }
    
    showMapPlaceholder(mapContainer) {
        mapContainer.innerHTML = `
            <div class="flex items-center justify-center h-full bg-gradient-to-br from-slate-100 to-slate-200">
                <div class="text-center">
                    <div class="text-4xl mb-2">🗺️</div>
                    <p class="text-slate-600 mb-2">Térkép nem elérhető</p>
                    <p class="text-sm text-slate-500">A kiválasztott dátumra nincs elérhető térkép</p>
                </div>
            </div>
        `;
    }
    
    formatDate(dateStr) {
        const date = new Date(dateStr);
        return date.toLocaleDateString('hu-HU', {
            year: 'numeric',
            month: 'long',
            day: 'numeric'
        });
    }

    updateDateBanner() {
        const banner = document.getElementById('date-banner');
        if (!banner) return;
        const displayDate = this.availableDateUsed || this.defaultFallbackDate;
        banner.textContent = `Megjelenített dátum: ${this.formatDate(displayDate)}`;
    }

    ensureFreshCanvas(canvasId) {
        const oldCanvas = document.getElementById(canvasId);
        if (!oldCanvas) return null;
        try {
            // Destroy via Chart v4 API if present
            if (window.Chart && typeof window.Chart.getChart === 'function') {
                const existing = window.Chart.getChart(oldCanvas);
                if (existing) existing.destroy();
            }
        } catch {}
        if (oldCanvas.chart) {
            try { oldCanvas.chart.destroy(); } catch {}
            oldCanvas.chart = null;
        }
        const newCanvas = oldCanvas.cloneNode(false);
        oldCanvas.parentNode.replaceChild(newCanvas, oldCanvas);
        return newCanvas;
    }
}

// Initialize the application when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new MAVMonitor();
});

// Service Worker registration (optional)
if ('serviceWorker' in navigator) {
    window.addEventListener('load', () => {
        navigator.serviceWorker.register('sw.js')
            .then(registration => {
                console.log('SW registered: ', registration);
            })
            .catch(registrationError => {
                console.log('SW registration failed: ', registrationError);
            });
    });
} 
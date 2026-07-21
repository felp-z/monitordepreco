const STORE_COLORS = {
    kabum: '#ff6600',
    pichau: '#00b4d8',
    terabyte: '#e63946',
    amazon: '#ff9900',
    magazineluiza: '#0086ff',
    americanas: '#e60014',
    livelo: '#6b21a8',
    mercadolivre: '#ffe600',
    shopee: '#ee4d2d',
    default: '#64748b'
};

const charts = {
    createSparkline(canvasId, data, color) {
        const ctx = document.getElementById(canvasId);
        if (!ctx) return null;
        
        return new Chart(ctx, {
            type: 'line',
            data: {
                labels: data.map((_, i) => i),
                datasets: [{
                    data: data,
                    borderColor: color,
                    borderWidth: 2,
                    tension: 0.3,
                    pointRadius: 0
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { display: false }, tooltip: { enabled: false } },
                scales: {
                    x: { display: false },
                    y: { display: false }
                },
                layout: { padding: 0 }
            }
        });
    },

    createPriceChart(canvasId, history, stores, targetPrice, period) {
        const ctx = document.getElementById(canvasId);
        if (!ctx) return null;

        // Filter history based on period
        let filteredHistory = [...history];
        const now = new Date();
        if (period !== 'all') {
            const hours = period === '24h' ? 24 : period === '7d' ? 24*7 : 24*30;
            const cutoff = new Date(now.getTime() - (hours * 60 * 60 * 1000));
            filteredHistory = filteredHistory.filter(h => new Date(h.timestamp) >= cutoff);
        }

        const datasets = stores.map(store => {
            const dataPoints = filteredHistory.map(h => {
                const storeData = h.prices[store.store];
                return {
                    x: h.timestamp,
                    y: storeData && storeData.price ? storeData.price : null
                };
            }).filter(d => d.y !== null);

            return {
                label: store.store.charAt(0).toUpperCase() + store.store.slice(1),
                data: dataPoints,
                borderColor: STORE_COLORS[store.store] || STORE_COLORS.default,
                backgroundColor: (STORE_COLORS[store.store] || STORE_COLORS.default) + '33',
                borderWidth: 2,
                pointRadius: 3,
                tension: 0.2,
                spanGaps: true
            };
        });

        // Add Target Price Line
        datasets.push({
            label: 'Preço Alvo',
            data: filteredHistory.map(h => ({ x: h.timestamp, y: targetPrice })),
            borderColor: '#22c55e',
            borderWidth: 2,
            borderDash: [5, 5],
            pointRadius: 0,
            fill: false
        });

        return new Chart(ctx, {
            type: 'line',
            data: { datasets },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                interaction: {
                    mode: 'index',
                    intersect: false,
                },
                plugins: {
                    legend: {
                        position: 'top',
                        labels: { color: '#94a3b8' }
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                let label = context.dataset.label || '';
                                if (label) label += ': ';
                                if (context.parsed.y !== null) {
                                    label += new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(context.parsed.y);
                                }
                                return label;
                            }
                        }
                    }
                },
                scales: {
                    x: {
                        type: 'time',
                        time: { tooltipFormat: 'dd/MM/yyyy HH:mm' },
                        grid: { color: 'rgba(255,255,255,0.05)' },
                        ticks: { color: '#94a3b8' }
                    },
                    y: {
                        grid: { color: 'rgba(255,255,255,0.05)' },
                        ticks: {
                            color: '#94a3b8',
                            callback: function(value) {
                                return new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(value);
                            }
                        }
                    }
                }
            }
        });
    }
};

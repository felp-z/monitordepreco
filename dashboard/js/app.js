const app = {
    data: { config: null, history: null },
    chartInstance: null,
    currentDetailId: null,

    init() {
        if (!config.isConfigured) {
            document.getElementById('setup-screen').classList.remove('hidden');
        } else {
            this.loadData();
            // Auto refresh every 5 min
            setInterval(() => this.loadData(), 5 * 60 * 1000);
        }
    },

    showToast(msg, type = 'success') {
        const container = document.getElementById('toast-container');
        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        toast.textContent = msg;
        container.appendChild(toast);
        
        requestAnimationFrame(() => toast.classList.add('show'));
        
        setTimeout(() => {
            toast.classList.remove('show');
            setTimeout(() => toast.remove(), 300);
        }, 3000);
    },

    formatPrice(val) {
        if(val === null || val === undefined) return 'Indisponível';
        return new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(val);
    },

    formatDate(iso) {
        return dateFns.format(new Date(iso), "dd/MM/yyyy HH:mm");
    },

    timeAgo(iso) {
        return 'Atualizado ' + dateFns.formatDistanceToNow(new Date(iso), { addSuffix: true });
    },

    async loadData() {
        try {
            document.getElementById('loading-state').innerHTML = Array(6).fill('<div class="skeleton"></div>').join('');
            document.getElementById('loading-state').classList.remove('hidden');
            document.getElementById('products-grid').innerHTML = '';

            const [configData, historyData] = await Promise.all([
                api.getRaw('config.json'),
                api.getRaw('price_history.json')
            ]);
            
            this.data.config = configData;
            this.data.history = historyData;

            document.getElementById('last-update').textContent = new Date().toLocaleTimeString();
            this.renderProducts();
        } catch (e) {
            console.error(e);
            this.showToast('Erro ao carregar dados. Verifique configurações.', 'error');
        } finally {
            document.getElementById('loading-state').classList.add('hidden');
        }
    },

    renderProducts() {
        const grid = document.getElementById('products-grid');
        const emptyState = document.getElementById('empty-state');
        grid.innerHTML = '';

        if (!this.data.config.products || this.data.config.products.length === 0) {
            emptyState.classList.remove('hidden');
            return;
        }
        emptyState.classList.add('hidden');

        this.data.config.products.forEach(prod => {
            const histData = this.data.history[prod.id] || { history: [] };
            const lastEntry = histData.history.length > 0 ? histData.history[histData.history.length - 1] : null;
            
            let bestPrice = Infinity;
            let bestStore = '';
            
            if (lastEntry) {
                for (const [store, info] of Object.entries(lastEntry.prices)) {
                    if (info.available && info.price && info.price < bestPrice) {
                        bestPrice = info.price;
                        bestStore = store;
                    }
                }
            }

            const isAvailable = bestPrice !== Infinity;
            const diff = isAvailable ? bestPrice - prod.target_price : 0;
            const pct = isAvailable ? Math.abs((diff / prod.target_price) * 100).toFixed(1) : 0;
            const isGood = diff <= 0;

            let diffHtml = '';
            if (isAvailable) {
                if (isGood) diffHtml = `<span class="stat-good">Economia: ${this.formatPrice(Math.abs(diff))} (${pct}%)</span>`;
                else diffHtml = `<span class="stat-bad">Acima: ${this.formatPrice(diff)} (${pct}%)</span>`;
            }

            // Extract last 7 days prices for sparkline
            const sparkData = histData.history.slice(-14).map(h => {
                let min = Infinity;
                for (const v of Object.values(h.prices)) {
                    if(v.available && v.price < min) min = v.price;
                }
                return min === Infinity ? null : min;
            }).filter(v => v !== null);

            const card = document.createElement('div');
            card.className = 'product-card';
            card.onclick = () => this.openDetailModal(prod.id);
            
            card.innerHTML = `
                <div class="product-header">
                    <h3 class="product-title" title="${prod.name}">${prod.name}</h3>
                    <div class="status-indicator ${isGood ? 'good' : 'bad'}"></div>
                </div>
                <div class="product-price-main">
                    <span class="price-big">${isAvailable ? this.formatPrice(bestPrice) : 'Sem Estoque'}</span>
                    <span class="price-store">${isAvailable ? 'em ' + bestStore : '-'}</span>
                </div>
                <div class="product-stats">
                    Alvo: ${this.formatPrice(prod.target_price)}<br>
                    ${diffHtml}
                </div>
                <div class="sparkline-container">
                    <canvas id="spark-${prod.id}"></canvas>
                </div>
                <div class="store-badges">
                    ${prod.links.map(l => `<span class="badge" style="border-color: ${STORE_COLORS[l.store]||'#fff'}">${l.store}</span>`).join('')}
                </div>
            `;
            grid.appendChild(card);
            
            // Wait for DOM
            setTimeout(() => {
                charts.createSparkline(`spark-${prod.id}`, sparkData, isGood ? '#22c55e' : '#ef4444');
            }, 0);
        });
    },

    openDetailModal(productId) {
        this.currentDetailId = productId;
        const prod = this.data.config.products.find(p => p.id === productId);
        const histData = this.data.history[prod.id] || { history: [] };
        const lastEntry = histData.history.length > 0 ? histData.history[histData.history.length - 1] : null;

        document.getElementById('detail-title').textContent = prod.name;
        
        let bestPrice = Infinity;
        if (lastEntry) {
            for (const info of Object.values(lastEntry.prices)) {
                if (info.available && info.price && info.price < bestPrice) bestPrice = info.price;
            }
        }
        document.getElementById('detail-best-price').textContent = bestPrice !== Infinity ? this.formatPrice(bestPrice) : 'Indisponível';

        // Render Table
        const tbody = document.getElementById('detail-stores-list');
        tbody.innerHTML = prod.links.map(l => {
            const current = lastEntry && lastEntry.prices[l.store];
            const priceStr = current && current.available && current.price ? this.formatPrice(current.price) : '-';
            const status = current && current.available ? '<span style="color:var(--success)">Disponível</span>' : '<span style="color:var(--danger)">Indisponível</span>';
            return `
                <tr>
                    <td><span class="badge" style="border-color: ${STORE_COLORS[l.store]||'#fff'}">${l.store}</span></td>
                    <td>${priceStr}</td>
                    <td>${status}</td>
                    <td><a href="${l.url}" target="_blank" class="btn btn-secondary btn-sm">Acessar</a></td>
                </tr>
            `;
        }).join('');

        const toggleBtn = document.getElementById('btn-toggle-active');
        if (prod.active) {
            toggleBtn.textContent = 'Desativar Monitoramento';
            toggleBtn.className = 'btn btn-secondary';
        } else {
            toggleBtn.textContent = 'Ativar Monitoramento';
            toggleBtn.className = 'btn btn-primary';
        }

        this.renderChart('30d');
        
        // Setup filter listeners
        document.querySelectorAll('.btn-filter').forEach(btn => {
            btn.onclick = (e) => {
                document.querySelectorAll('.btn-filter').forEach(b => b.classList.remove('active'));
                e.target.classList.add('active');
                this.renderChart(e.target.dataset.period);
            };
        });

        document.getElementById('modal-product-detail').classList.remove('hidden');
    },

    renderChart(period) {
        const prod = this.data.config.products.find(p => p.id === this.currentDetailId);
        const histData = this.data.history[prod.id] || { history: [] };

        if (this.chartInstance) {
            this.chartInstance.destroy();
        }
        this.chartInstance = charts.createPriceChart('detail-chart', histData.history, prod.links, prod.target_price, period);
    },

    async handleToggleActive() {
        if (!this.currentDetailId) return;
        try {
            await productsService.toggleProduct(this.currentDetailId);
            this.showToast('Status do monitoramento atualizado!');
            this.closeModal('modal-product-detail');
            this.loadData();
        } catch (e) {
            console.error(e);
            this.showToast('Erro ao atualizar status', 'error');
        }
    },

    async handleDeleteProduct() {
        if (!this.currentDetailId) return;
        if (!confirm('Tem certeza de que deseja excluir este produto?')) return;
        try {
            await productsService.deleteProduct(this.currentDetailId);
            this.showToast('Produto excluído com sucesso!');
            this.closeModal('modal-product-detail');
            this.loadData();
        } catch (e) {
            console.error(e);
            this.showToast('Erro ao excluir produto', 'error');
        }
    },

    openAddProductModal() {
        document.getElementById('form-add-product').reset();
        document.getElementById('links-container').innerHTML = '';
        this.addLinkField();
        document.getElementById('modal-add-product').classList.remove('hidden');
    },

    addLinkField() {
        const container = document.getElementById('links-container');
        const row = document.createElement('div');
        row.className = 'link-row';
        row.innerHTML = `
            <input type="url" class="link-url-input" required placeholder="https://..." onblur="app.updateStoreBadge(this)">
            <span class="badge store-badge-preview" style="display:none"></span>
            <button type="button" class="btn-remove-link" onclick="this.parentElement.remove()">X</button>
        `;
        container.appendChild(row);
    },

    updateStoreBadge(input) {
        const badge = input.nextElementSibling;
        if(input.value) {
            const store = productsService.detectStore(input.value);
            badge.textContent = store;
            badge.style.display = 'inline-block';
            badge.style.borderColor = STORE_COLORS[store] || STORE_COLORS.default;
        } else {
            badge.style.display = 'none';
        }
    },

    async handleAddProduct() {
        const name = document.getElementById('product-name').value;
        const targetPrice = document.getElementById('product-target').value;
        
        const links = [];
        document.querySelectorAll('.link-url-input').forEach(input => {
            if(input.value) {
                links.push({
                    store: productsService.detectStore(input.value),
                    url: input.value
                });
            }
        });

        if (links.length === 0) {
            this.showToast('Adicione pelo menos um link', 'error');
            return;
        }

        try {
            const btn = document.querySelector('#form-add-product button[type="submit"]');
            btn.disabled = true;
            btn.textContent = 'Salvando...';

            await productsService.addProduct(name, targetPrice, links);
            this.showToast('Produto adicionado com sucesso!');
            this.closeModal('modal-add-product');
            this.loadData();
        } catch (e) {
            console.error(e);
            this.showToast('Erro ao adicionar produto', 'error');
        } finally {
            const btn = document.querySelector('#form-add-product button[type="submit"]');
            btn.disabled = false;
            btn.textContent = 'Salvar';
        }
    },

    openSettingsModal() {
        document.getElementById('settings-repo').value = config.githubRepo || '';
        document.getElementById('settings-branch').value = config.githubBranch || 'main';
        document.getElementById('settings-token').value = config.githubToken || '';
        document.getElementById('modal-settings').classList.remove('hidden');
    },

    async testConnection() {
        const repo = document.getElementById('settings-repo').value;
        const token = document.getElementById('settings-token').value;
        
        if(!repo || !token) {
            this.showToast('Preencha repositório e token', 'error');
            return;
        }

        try {
            const res = await fetch(`https://api.github.com/repos/${repo}`, {
                headers: { 'Authorization': `token ${token}` }
            });
            if(res.ok) {
                this.showToast('Conexão bem sucedida!');
            } else {
                this.showToast('Falha na conexão. Verifique repo/token.', 'error');
            }
        } catch (e) {
            this.showToast('Erro de rede ao testar', 'error');
        }
    },

    handleSaveSettings() {
        config.githubRepo = document.getElementById('settings-repo').value;
        config.githubBranch = document.getElementById('settings-branch').value;
        config.githubToken = document.getElementById('settings-token').value;
        
        this.closeModal('modal-settings');
        this.showToast('Configurações salvas');
        
        document.getElementById('setup-screen').classList.add('hidden');
        this.init();
    },

    closeModal(id) {
        document.getElementById(id).classList.add('hidden');
    }
};

window.addEventListener('DOMContentLoaded', () => app.init());

const api = {
    async fetchWithAuth(url, options = {}) {
        const headers = {
            'Authorization': `token ${config.githubToken}`,
            'Accept': 'application/vnd.github.v3+json',
            ...options.headers
        };
        const res = await fetch(url, { ...options, headers });
        if (!res.ok) throw new Error(`HTTP error! status: ${res.status}`);
        return res;
    },

    async loadConfig() {
        const res = await this.fetchWithAuth(config.apiUrl('config.json'));
        const data = await res.json();
        const content = decodeURIComponent(escape(atob(data.content.replace(/\s/g, ''))));
        return {
            sha: data.sha,
            data: JSON.parse(content)
        };
    },

    async saveConfig(newConfig, sha) {
        const content = btoa(unescape(encodeURIComponent(JSON.stringify(newConfig, null, 2))));
        await this.fetchWithAuth(config.apiUrl('config.json'), {
            method: 'PUT',
            body: JSON.stringify({
                message: 'Update config.json via Dashboard',
                content: content,
                sha: sha,
                branch: config.githubBranch
            })
        });
    },

    async getRaw(file) {
        const res = await this.fetchWithAuth(config.apiUrl(file));
        const data = await res.json();
        const content = decodeURIComponent(escape(atob(data.content.replace(/\s/g, ''))));
        return JSON.parse(content);
    }
};

const productsService = {
    detectStore(url) {
        const patterns = {
            'kabum': /kabum\.com/,
            'pichau': /pichau\.com/,
            'terabyte': /terabyteshop\.com/,
            'amazon': /amazon\.com/,
            'magazineluiza': /magazineluiza\.com/,
            'americanas': /americanas\.com/,
            'livelo': /livelo\.com/,
            'mercadolivre': /mercadolivre\.com|mlb\.com/,
            'shopee': /shopee\.com/
        };
        for (const [store, pattern] of Object.entries(patterns)) {
            if (pattern.test(url)) return store;
        }
        return 'outros';
    },

    slugify(text) {
        return text.toString().toLowerCase()
            .replace(/\s+/g, '-')
            .replace(/[^\w\-]+/g, '')
            .replace(/\-\-+/g, '-')
            .replace(/^-+/, '')
            .replace(/-+$/, '');
    },

    async addProduct(name, targetPrice, links) {
        const { sha, data } = await api.loadConfig();
        const id = this.slugify(name);
        
        const newProduct = {
            id,
            name,
            target_price: parseFloat(targetPrice),
            active: true,
            links: links.map(l => ({ store: l.store, url: l.url }))
        };

        data.products.push(newProduct);
        await api.saveConfig(data, sha);
        return newProduct;
    },
    
    async toggleProduct(productId) {
        const { sha, data } = await api.loadConfig();
        const prod = data.products.find(p => p.id === productId);
        if(prod) {
            prod.active = !prod.active;
            await api.saveConfig(data, sha);
        }
    },
    
    async deleteProduct(productId) {
        const { sha, data } = await api.loadConfig();
        data.products = data.products.filter(p => p.id !== productId);
        await api.saveConfig(data, sha);
    },

    async triggerMonitorWorkflow() {
        const url = `https://api.github.com/repos/${config.githubRepo}/actions/workflows/monitor.yml/dispatches`;
        await api.fetchWithAuth(url, {
            method: 'POST',
            body: JSON.stringify({
                ref: config.githubBranch
            })
        });
    }
};

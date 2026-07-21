const config = {
    get githubRepo() { return localStorage.getItem('mp_github_repo'); },
    set githubRepo(val) { localStorage.setItem('mp_github_repo', val); },
    
    get githubBranch() { return localStorage.getItem('mp_github_branch') || 'main'; },
    set githubBranch(val) { localStorage.setItem('mp_github_branch', val); },
    
    get githubToken() { return localStorage.getItem('mp_github_token'); },
    set githubToken(val) { localStorage.setItem('mp_github_token', val); },

    get isConfigured() {
        return !!(this.githubRepo && this.githubToken);
    },

    rawUrl(file) {
        return `https://raw.githubusercontent.com/${this.githubRepo}/${this.githubBranch}/${file}`;
    },

    apiUrl(file) {
        return `https://api.github.com/repos/${this.githubRepo}/contents/${file}`;
    }
};

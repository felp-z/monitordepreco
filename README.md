# Monitor de Preços

Sistema automatizado de monitoramento de preços de hardware e periféricos no mercado brasileiro, com painel web (dashboard) interativo e alertas de baixa latência via Telegram.

O monitor funciona de forma 100% serverless através do GitHub Actions (totalmente gratuito), sem consumir recursos da sua máquina local ou requerer servidores dedicados.

## Funcionalidades

- **Monitoramento de 9 lojas**: Kabum, Pichau, Terabyte, Amazon, Magazine Luiza, Americanas, Livelo, Mercado Livre e Shopee.
- **Alertas no Telegram**: Notificações imediatas assim que um preço cai abaixo do valor alvo.
- **Dashboard Web**: Visualização do histórico de preços por período com gráficos de linha interativos via GitHub Pages.
- **Camada Stealth**: Rotação automática de User-Agents e delays aleatórios para contornar proteções anti-bot.
- **Integração com Firecrawl**: Uso da API do Firecrawl como fallback inteligente para contornar bloqueios complexos das lojas (Shopee, Mercado Livre, etc.).

## Limitações do Plano Gratuito e Otimizações

O plano gratuito do Firecrawl fornece **1.000 créditos de scraping por mês**.
Com uma média de monitoramento de 3 produtos (contendo até 3 links cada), otimizamos o consumo da seguinte maneira:

1. **Lojas Leves** (Kabum, Pichau, Terabyte, Livelo, Americanas): Utilizam o scraping direto via requisições HTTP normais (`httpx`). Esse processo possui custo zero e não consome créditos do Firecrawl.
2. **Lojas Pesadas** (Shopee, Mercado Livre, Amazon): Usam o Firecrawl quando o scraping direto falha ou é bloqueado.
3. **Consumo Estimado**: Se você monitorar 3 links difíceis a cada 2 ou 3 horas, o consumo mensal ficará entre 720 e 900 créditos, mantendo o monitoramento totalmente gratuito e dentro da cota de 1.000 requisições do plano free.

---

## Estrutura do Projeto

```
monitordepreco/
├── .github/workflows/     # Workflows do GitHub Actions (Scraper e Deploy do Dashboard)
├── src/monitor/           # Código-fonte principal em Python
│   ├── parsers/           # Extração e tratamento do HTML de cada loja
│   ├── utils/             # Auxiliares de formatação de preço e captura de Chat ID
│   ├── config.py          # Configurações do projeto e validações
│   ├── history.py         # Registro e atualização do histórico de preços
│   ├── notifier.py        # Integração e disparo de alertas para o Telegram
│   ├── scraper.py         # Motor assíncrono de scraping
│   └── stealth.py         # Mecanismos de evasão e headers
├── dashboard/             # Código da interface gráfica (HTML, CSS e JS)
├── config.json            # Lista de produtos e preços alvo
├── price_history.json     # Histórico de preços consolidado
├── pyproject.toml         # Gerenciamento de dependências e empacotamento
└── .env.example           # Modelo de configuração das variáveis de ambiente
```

---

## Como Instalar e Executar Localmente

### 1. Clonar o projeto e instalar dependências
```bash
git clone https://github.com/SEU_USUARIO/monitordepreco.git
cd monitordepreco

# Crie e ative o ambiente virtual
python -m venv venv
.\venv\Scripts\Activate.ps1   # No Windows (PowerShell)
source venv/bin/activate      # No Linux/macOS

# Instale o pacote no modo editável com as dependências
pip install -e .
```

### 2. Configurar Variáveis de Ambiente
Copie o modelo de exemplo para criar seu arquivo local `.env`:
```bash
cp .env.example .env
```
Abra o arquivo `.env` e preencha com:
- `TELEGRAM_BOT_TOKEN`: Token gerado pelo @BotFather no Telegram.
- `FIRECRAWL_API_KEY`: API Key da sua conta no firecrawl.dev.

### 3. Capturar o Chat ID do Telegram
Para descobrir qual é o seu Chat ID:
1. Abra o Telegram e envie uma mensagem (ex: `/start`) para o seu bot.
2. Com a sua venv ativa no terminal, execute o utilitário:
   ```bash
   python src/monitor/utils/get_chat_id.py
   ```
3. O script lerá as atualizações do bot, mostrará seu Chat ID na tela e perguntará se deseja salvá-lo automaticamente no `.env`. Digite `s` e pressione Enter.

### 4. Executar o Monitoramento Local
```bash
# Execução de teste (apenas imprime no terminal e não dispara notificações)
python -m monitor --dry-run --verbose

# Execução real (salva o histórico e envia alertas no Telegram se atingir o alvo)
python -m monitor
```

---

## Configuração do Monitoramento 24/7 (Serverless)

Para que o monitor funcione de forma contínua sem depender da sua máquina ligada:

### 1. GitHub Secrets
Com o projeto hospedado no seu repositório do GitHub, acesse **Settings → Secrets and Variables → Actions** e crie os seguintes Secrets:
- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_CHAT_ID`
- `FIRECRAWL_API_KEY` (opcional, mas necessário para Shopee/ML)

### 2. GitHub Pages (Dashboard)
Acesse **Settings → Pages** no repositório do GitHub e configure:
- **Build and deployment → Source**: Mude para `GitHub Actions`.
Isso ativará o deploy automático do painel web contido na pasta `/dashboard` sempre que houver modificações.

### 3. Dashboard no Primeiro Acesso
Ao abrir a página do GitHub Pages do seu projeto (`https://seu-usuario.github.io/monitordepreco`), preencha o formulário inicial:
- **Repositório**: `seu-usuario/monitordepreco`
- **Branch**: `main`
- **GitHub Token (PAT)**: Crie um Personal Access Token clássico no seu perfil do GitHub (com a permissão `public_repo` ativa) e insira-o.
*Nota: Este token é armazenado exclusivamente no armazenamento local (localStorage) do seu navegador, mantendo a operação segura e privada.*

A partir disso, você poderá adicionar ou excluir produtos pela própria interface web, que fará commits automáticos no arquivo `config.json` do repositório.

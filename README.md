# 📊 VPS Command Center (dash-tokens-hermes)

Dashboard de monitoramento de consumo de tokens de IA e saúde do sistema da VPS.

## 🚀 Links Rápidos
O Dashboard está organizado em duas categorias:
- **VPS - Acesso Rápido**: Atalhos para os serviços hospedados na VPS (n8n, Open WebUI, SearXNG, Ollama, Easypanel, Pi-hole).
- **Serviços - Links Úteis**: Atalhos para painéis de controle externos (Oracle Cloud, AI Studio, Cloudflare, GitHub, Tailscale).

## 🛠️ Infraestrutura & Segurança
- **DNS**: Pi-hole configurado com Tailscale para filtragem global privada.
- **Acesso**: Cloudflare Tunnels para interface web e Tailscale para tráfego DNS.
- **Segurança**: SSH restrito a chaves públicas e Fail2Ban ativo.

## ⚙️ Manutenção
Para atualizar o código do dashboard a partir do GitHub:
1. Faça o push das alterações para o ramo `main`.
2. Na VPS, execute o script de sincronização:
   `~/update_dash.sh`

# 🐉 SHYYUNZ FIRE AUDITOR v2.0 - SHADOW OPS EDITION

[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue?style=for-the-badge&logo=python)](https://www.python.org/)
[![Version](https://img.shields.io/badge/version-2.0--tactical-magenta?style=for-the-badge)](https://github.com/shyyunz/shyyunz-supabase)
[![Security](https://img.shields.io/badge/role-offensive--security-red?style=for-the-badge)](https://www.supabase.com/)

> **AVISO**: Esta ferramenta foi criada exclusivamente para fins educacionais e auditorias de segurança autorizadas. O uso indevido contra sistemas sem permissão é de total responsabilidade do usuário.

---

## 🛠️ Sobre a Ferramenta

A **SHYYUNZ FIRE AUDITOR** é um ecossistema tático avançado projetado para identificar, explorar e auditar vulnerabilidades em instâncias do **Supabase** **Firebase** e **Shopify**. Criada por **shyyunz**, a ferramenta evoluiu de um simples scanner para um arsenal de guerra cibernética que utiliza **Inteligência Artificial** para realizar ataques de precisão contra Row Level Security (RLS), Buckets de Storage e Funções RPC.

---

## 🚀 Funcionalidades de Elite (v2.0)

### 🧠 Cérebro Analítico (IA Integration)
Integrada ao **Google Gemini 1.5 Flash**, a Shyyunz não apenas baixa dados; ela os compreende.
- **Deep Data Mining**: Identifica automaticamente senhas, tokens de API da AWS, e-mails de admins e hashes sensíveis em grandes volumes de dados.
- **Dynamic RLS Bypass**: A IA analisa o nome da tabela e gera filtros customizados (PostgREST) para confundir o query planner do Postgres e burlar políticas de RLS.

### 🕵️‍♂️ Deep JS Hunter (Aggressive Recon)
Capacidade de "Visão de Raio-X" para encontrar chaves do Supabase em aplicações modernas (Next.js, Vite, Vanila).
- Busca chaves em arquivos ofuscados, CDNs e caminhos de configuração comuns (`js/config.js`, `_next/static/chunks/main.js`).
- Suporte total para chaves legadas (JWT) e novas chaves (`sb_publishable_`, `pk_`).

### 🗡️ Tactical Exploits
- **`[E] Exploit Escalation`**: Tenta criar contas com 15+ variações de metadados (`role:admin`, `is_admin:true`) para ganhar permissões elevadas automaticamente.
- **`[B] Deep Bucket Scan`**: Testa permissões de escrita (Upload/Defacement) em buckets como `backups`, `avatars` e `configs`.
- **`[R] RPC Sniper & SQLi Probe`**: Brute-force de funções ocultas e teste automático de SQL Injection por design via parâmetros RPC.
- **`[D] Mass Exfiltration`**: Dump completo de todas as tabelas vulneráveis em arquivos JSON organizados.

### 🛡️ Shadow Ops Core
- **Rotação de Proxies**: Suporte nativo para `proxies.txt`.
- **Análise de Token JWT**: Decodificação instantânea de roles e metadados.
- **Learning Knowledge**: Sistema de aprendizado que memoriza nomes de tabelas e RPCs descobertos para futuras auditorias.

---

## 📥 Instalação

```bash
# Clone o repositório
git clone https://github.com/shyyunz/shyyunz-fire.git
cd shyyunz-fire

# Instale as dependências
pip install -r requirements.txt
```

---

## 🎮 Como Usar

1. Obtenha sua API Key do Gemini no [Google AI Studio](https://aistudio.google.com/app/apikey).
2. Execute a ferramenta:
```bash
python3 shyyunz
```
3. Insira a URL do site alvo e deixe o **JS Hunter** fazer o resto.

---

## 👤 Criador

Este projeto foi idealizado e desenvolvido por:
- **shyyunz** - *Líder de Desenvolvimento e Especialista em Offensive Security.*

"Onde o RLS falha, o dragão encontra seu caminho." 🐉🔥

---

## 📄 Licença

Distribuído sob a licença MIT. Veja `LICENSE` para mais informações.
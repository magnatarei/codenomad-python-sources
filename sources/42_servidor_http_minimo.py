#!/usr/bin/env python3
# ============================================================
# CodeNomad Academy  |  Sources Python  |  42. Servidor HTTP mínimo
# ------------------------------------------------------------
# O que faz: Serve os arquivos de uma pasta e responde JSON em duas rotas:
#            /api/hora (hora do servidor) e /api/eco (devolve o que recebeu,
#            por GET ou POST). Cada pedido vira uma linha de log com hora,
#            cliente, método, caminho e status.
# Como usar: python 42_servidor_http_minimo.py --pasta ./site --porta 8000
#            python 42_servidor_http_minimo.py --demo
# O que você aprende: http.server, herança e sobrescrita de métodos,
#            cabeçalhos HTTP, urllib.parse, json, threading, porta livre (0)
# Requisitos: Python 3.10+, só biblioteca padrão
# Licença MIT. Um projeto da CodeNomad Academy (codenomad.org)
# ============================================================
from __future__ import annotations

import argparse
import json
import socket
import sys
import tempfile
import threading
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

# Vários pedidos podem chegar ao mesmo tempo; a trava evita linhas de log misturadas.
TRAVA_DO_LOG = threading.Lock()


def registrar(linha: str) -> None:
    """Escreve uma linha de log inteira de uma vez, mesmo com pedidos simultâneos."""
    with TRAVA_DO_LOG:
        sys.stdout.write(linha + "\n")
        sys.stdout.flush()


def dados_da_hora() -> dict[str, Any]:
    """Hora local e UTC em formato ISO, mais o timestamp em segundos."""
    agora = datetime.now().astimezone()
    return {
        "local": agora.isoformat(timespec="seconds"),
        "utc": agora.astimezone(timezone.utc).isoformat(timespec="seconds"),
        "timestamp": int(agora.timestamp()),
        "fuso": agora.tzname(),
    }


class Manipulador(SimpleHTTPRequestHandler):
    """Atende as rotas de API e deixa os arquivos por conta da classe mãe."""

    server_version = "CodeNomadAcademy/1.0"

    def do_GET(self) -> None:
        """Rotas /api/... respondem JSON; qualquer outro caminho é arquivo da pasta."""
        caminho, _, consulta = self.path.partition("?")
        if caminho == "/api/hora":
            self.responder_json(dados_da_hora())
        elif caminho == "/api/eco":
            self.responder_json(self.dados_do_eco(consulta, corpo=""))
        else:
            super().do_GET()  # a classe mãe cuida de arquivos, listagem de pasta e 404

    def do_POST(self) -> None:
        """Só /api/eco aceita POST: devolve o corpo que o cliente enviou."""
        caminho, _, consulta = self.path.partition("?")
        if caminho != "/api/eco":
            self.send_error(405, "Método não permitido nesta rota")
            return
        # O corpo não vem sozinho: é preciso ler exatamente Content-Length bytes.
        tamanho = int(self.headers.get("Content-Length") or 0)
        corpo = self.rfile.read(tamanho).decode("utf-8", errors="replace")
        self.responder_json(self.dados_do_eco(consulta, corpo))

    def dados_do_eco(self, consulta: str, corpo: str) -> dict[str, Any]:
        """Monta o dicionário com tudo o que o cliente mandou."""
        return {
            "metodo": self.command,
            "caminho": self.path,
            "parametros": urllib.parse.parse_qs(consulta),  # nome=Ana&nota=10 vira {"nome": ["Ana"], ...}
            "cabecalhos": {
                "Host": self.headers.get("Host", ""),
                "User-Agent": self.headers.get("User-Agent", ""),
            },
            "corpo": corpo,
        }

    def responder_json(self, dados: dict[str, Any], status: int = 200) -> None:
        """Serializa, informa tipo e tamanho e envia. Sem Content-Length o cliente fica esperando."""
        corpo = json.dumps(dados, ensure_ascii=False, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(corpo)))
        self.end_headers()
        self.wfile.write(corpo)

    def log_request(self, code: int | str = "-", size: int | str = "-") -> None:
        """Uma linha por pedido: hora, cliente, método, caminho e status."""
        hora = datetime.now().strftime("%H:%M:%S")
        registrar(f"[{hora}] {self.client_address[0]} {self.command} {self.path} -> {code}")

    def log_message(self, format: str, *args: Any) -> None:
        """Silencia o log padrão da classe mãe, que escreveria em stderr."""
        return


class Servidor(ThreadingHTTPServer):
    """Servidor com threads que avisa de porta ocupada em qualquer sistema."""

    # Armadilha do Windows: com SO_REUSEADDR (ligado por padrão no HTTPServer) dois
    # programas conseguem abrir a mesma porta sem erro nenhum e um rouba os pedidos
    # do outro. SO_EXCLUSIVEADDRUSE, que só existe lá, garante o erro "porta em uso".
    allow_reuse_address = not hasattr(socket, "SO_EXCLUSIVEADDRUSE")

    def server_bind(self) -> None:
        """Marca o socket como exclusivo antes de ligar à porta."""
        if hasattr(socket, "SO_EXCLUSIVEADDRUSE"):
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
        super().server_bind()


def criar_servidor(pasta: Path, host: str, porta: int) -> Servidor:
    """Liga o servidor ao endereço pedido. Porta 0 faz o sistema escolher uma livre."""
    manipulador = partial(Manipulador, directory=str(pasta))
    return Servidor((host, porta), manipulador)


def servir(pasta: Path, host: str, porta: int) -> None:
    """Modo normal: roda até o usuário apertar Ctrl+C."""
    try:
        servidor = criar_servidor(pasta, host, porta)
    except OSError as erro:
        sys.exit(f"Erro: não consegui abrir {host}:{porta} ({erro.strerror}). A porta já está em uso?")
    host_real, porta_real = servidor.server_address[:2]
    print(f"Servindo {pasta} em http://{host_real}:{porta_real}/  (Ctrl+C para parar)")
    print("Rotas de API: /api/hora e /api/eco?nome=Ana", flush=True)
    try:
        servidor.serve_forever()
    except KeyboardInterrupt:
        print("\nEncerrando.")
    finally:
        servidor.server_close()


def pedir(url: str, dados: bytes | None = None) -> tuple[int, str]:
    """Cliente mínimo usado pelo --demo: devolve (status, corpo)."""
    try:
        with urllib.request.urlopen(url, data=dados, timeout=5) as resp:
            return resp.status, resp.read().decode("utf-8")
    except urllib.error.HTTPError as erro:  # 404 e 405 também trazem corpo
        return erro.code, erro.read().decode("utf-8", errors="replace")


def demo() -> None:
    """Sobe numa porta livre, faz pedidos a si mesmo, mostra as respostas e desliga."""
    print("=== Servidor HTTP mínimo: demonstração ===")
    with tempfile.TemporaryDirectory() as temporaria:
        pasta = Path(temporaria)
        (pasta / "index.html").write_text("<h1>Olá, CodeNomad Academy</h1>\n", encoding="utf-8")
        (pasta / "dados.json").write_text('{"curso": "Python", "aula": 42}\n', encoding="utf-8")
        servidor = criar_servidor(pasta, "127.0.0.1", 0)
        porta = servidor.server_address[1]
        threading.Thread(target=servidor.serve_forever, daemon=True).start()
        base = f"http://127.0.0.1:{porta}"
        print(f"Servidor no ar em {base}, servindo a pasta temporária:\n{pasta}\n")
        pedidos = [
            ("GET", "/api/hora", None),
            ("GET", "/api/eco?nome=Ana&curso=Python", None),
            ("POST", "/api/eco", b'{"mensagem": "oi"}'),
            ("GET", "/dados.json", None),
            ("GET", "/inexistente.txt", None),
        ]
        for metodo, rota, corpo in pedidos:
            status, texto = pedir(base + rota, corpo)
            registrar(f"{metodo} {rota} respondeu {status}")
            for linha in texto.strip().splitlines()[:10]:
                registrar("   " + linha)
            registrar("")
        servidor.shutdown()
        servidor.server_close()
    print("Servidor desligado e pasta temporária apagada.")


def main() -> None:
    """Lê os argumentos e decide entre servir de verdade ou demonstrar."""
    parser = argparse.ArgumentParser(
        description="Servidor HTTP de arquivos com rotas de API, só com a biblioteca padrão.")
    parser.add_argument("--pasta", default=".", help="pasta a servir (padrão: a atual)")
    parser.add_argument("--porta", type=int, default=8000, help="porta TCP (padrão: 8000; 0 escolhe uma livre)")
    parser.add_argument("--host", default="127.0.0.1", help="endereço de escuta (0.0.0.0 abre para a rede local)")
    parser.add_argument("--demo", action="store_true", help="sobe numa porta livre, pede a si mesmo e desliga")
    args = parser.parse_args()

    if args.demo:
        demo()
        return
    if len(sys.argv) == 1:
        parser.print_help()
        return
    pasta = Path(args.pasta).expanduser().resolve()
    if not pasta.is_dir():
        parser.error(f"a pasta '{args.pasta}' não existe ou não é uma pasta")
    if not 0 <= args.porta <= 65535:
        parser.error("--porta precisa estar entre 0 e 65535")
    servir(pasta, args.host, args.porta)


if __name__ == "__main__":
    main()

# ------------------------------------------------------------
# Para ir além
# 1. Crie a rota /api/arquivos que lista os arquivos da pasta em JSON
#    (nome, tamanho e data), usando pathlib e os.stat.
# 2. Guarde em memória as mensagens recebidas por POST em /api/eco e
#    devolva todas em GET /api/mensagens (cuidado: proteja a lista com Lock).
# 3. Responda 304 Not Modified quando o cliente mandar If-Modified-Since
#    com data igual ou posterior à do arquivo.
# ------------------------------------------------------------

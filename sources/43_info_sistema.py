#!/usr/bin/env python3
# ============================================================
# CodeNomad Academy  |  Sources Python  |  43. Informações do sistema
# ------------------------------------------------------------
# O que faz: Mostra o sistema operacional, a versão do Python, o usuário,
#            a pasta atual, o número de CPUs, a memória física (quando a
#            biblioteca padrão consegue ler), o espaço em disco e as
#            variáveis de ambiente que você pedir, escondendo segredos.
# Como usar: python 43_info_sistema.py --tudo
#            python 43_info_sistema.py --disco C:\ --env PYTHON --json
#            python 43_info_sistema.py --demo
# O que você aprende: platform, os, sys, shutil.disk_usage, getpass,
#            ctypes, leitura de /proc no Linux, dicionários, json, argparse
# Requisitos: Python 3.10+, só biblioteca padrão
# Licença MIT. Um projeto da CodeNomad Academy (codenomad.org)
# ============================================================
from __future__ import annotations

import argparse
import ctypes
import getpass
import json
import os
import platform
import shutil
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

# Nomes de variáveis que costumam guardar segredos: o valor nunca é mostrado.
PALAVRAS_SENSIVEIS = ("SECRET", "TOKEN", "PASSWORD", "PASSWD", "CREDENTIAL", "AUTH", "PRIVATE", "APIKEY", "API_KEY")
# Variáveis seguras que vale a pena ver quando nenhum prefixo é pedido.
VARIAVEIS_COMUNS = ("HOME", "USERPROFILE", "SHELL", "COMSPEC", "LANG", "TERM", "TMP", "TMPDIR",
                    "NUMBER_OF_PROCESSORS", "PYTHONPATH", "VIRTUAL_ENV")


def formatar_bytes(quantidade: int | None) -> str:
    """Converte bytes em KB, MB, GB... com vírgula, como se escreve no Brasil."""
    if quantidade is None:
        return "não disponível neste sistema"
    valor = float(quantidade)
    for unidade in ("B", "KB", "MB", "GB", "TB"):
        if valor < 1024 or unidade == "TB":
            return f"{valor:.1f} {unidade}".replace(".", ",")
        valor /= 1024
    return f"{quantidade} B"


def secao_sistema() -> dict[str, Any]:
    """Dados do sistema operacional, do usuário e do momento atual."""
    try:
        usuario = getpass.getuser()
    except (OSError, KeyError):  # ambientes sem usuário definido (contêineres, por exemplo)
        usuario = "desconhecido"
    agora = datetime.now().astimezone()
    return {
        "sistema": f"{platform.system()} {platform.release()}",
        "versao_detalhada": platform.version(),
        "arquitetura": platform.machine(),
        "nome_da_maquina": platform.node(),
        "usuario": usuario,
        "pasta_atual": str(Path.cwd()),
        "pasta_pessoal": str(Path.home()),
        "hora_local": agora.strftime("%d/%m/%Y %H:%M:%S"),
        "fuso_horario": f"{agora.tzname()} (UTC{agora.strftime('%z')})",
    }


def secao_python() -> dict[str, Any]:
    """Como o interpretador que está rodando foi construído e configurado."""
    return {
        "versao": platform.python_version(),
        "implementacao": platform.python_implementation(),
        "compilador": platform.python_compiler(),
        "executavel": sys.executable,
        "bits": platform.architecture()[0],
        "codificacao_de_arquivos": sys.getfilesystemencoding(),
        "pastas_de_modulos": len(sys.path),
    }


def memoria_windows() -> tuple[int | None, int | None]:
    """Pergunta ao kernel32 via ctypes. A struct precisa ter os campos na ordem da API."""

    class MemoryStatusEx(ctypes.Structure):
        _fields_ = [("dwLength", ctypes.c_ulong), ("dwMemoryLoad", ctypes.c_ulong),
                    ("ullTotalPhys", ctypes.c_ulonglong), ("ullAvailPhys", ctypes.c_ulonglong),
                    ("ullTotalPageFile", ctypes.c_ulonglong), ("ullAvailPageFile", ctypes.c_ulonglong),
                    ("ullTotalVirtual", ctypes.c_ulonglong), ("ullAvailVirtual", ctypes.c_ulonglong),
                    ("ullAvailExtendedVirtual", ctypes.c_ulonglong)]

    estado = MemoryStatusEx()
    estado.dwLength = ctypes.sizeof(MemoryStatusEx)  # a API exige o tamanho preenchido
    if ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(estado)):
        return estado.ullTotalPhys, estado.ullAvailPhys
    return None, None


def memoria_fisica() -> tuple[int | None, int | None]:
    """Devolve (total, disponível) em bytes, ou None quando o sistema não expõe o dado."""
    if sys.platform == "win32":
        return memoria_windows()
    meminfo = Path("/proc/meminfo")
    if meminfo.exists():  # Linux: um arquivo de texto com uma linha por medida
        valores: dict[str, int] = {}
        for linha in meminfo.read_text(encoding="utf-8").splitlines():
            chave, _, resto = linha.partition(":")
            if resto.strip():
                valores[chave] = int(resto.split()[0]) * 1024  # o arquivo usa kB
        return valores.get("MemTotal"), valores.get("MemAvailable")
    if hasattr(os, "sysconf"):  # macOS e outros Unix: só o total
        try:
            return os.sysconf("SC_PAGE_SIZE") * os.sysconf("SC_PHYS_PAGES"), None
        except (ValueError, OSError):
            pass
    return None, None


def secao_hardware() -> dict[str, Any]:
    """CPUs e memória física."""
    total, disponivel = memoria_fisica()
    return {
        "cpus_logicas": os.cpu_count() or "desconhecido",
        "memoria_total": formatar_bytes(total),
        "memoria_disponivel": formatar_bytes(disponivel),
    }


def secao_disco(pasta: Path) -> dict[str, Any]:
    """Espaço do disco onde a pasta está."""
    uso = shutil.disk_usage(pasta)
    return {
        "pasta_consultada": str(pasta.resolve()),
        "total": formatar_bytes(uso.total),
        "usado": formatar_bytes(uso.used),
        "livre": formatar_bytes(uso.free),
        "percentual_usado": f"{uso.used / uso.total * 100:.1f}%".replace(".", ","),
    }


def mascarar(nome: str, valor: str) -> str:
    """Esconde valores que parecem segredos e resume o PATH, que é enorme."""
    if any(palavra in nome.upper() for palavra in PALAVRAS_SENSIVEIS):
        return "****** (escondido)"
    if nome.upper() == "PATH":
        partes = valor.split(os.pathsep)
        return f"{len(partes)} pastas, começando por {partes[:2]}"
    return valor


def secao_ambiente(prefixo: str | None) -> dict[str, str]:
    """Variáveis de ambiente: as comuns, ou todas as que começam com o prefixo."""
    if prefixo is None:
        nomes = [n for n in VARIAVEIS_COMUNS if n in os.environ] + ["PATH"]
    else:
        nomes = sorted(n for n in os.environ if n.upper().startswith(prefixo.upper()))
    return {nome: mascarar(nome, os.environ.get(nome, "")) for nome in nomes}


def imprimir_secao(titulo: str, dados: dict[str, Any]) -> None:
    """Imprime um bloco com as chaves alinhadas."""
    print(f"\n{titulo}")
    print("-" * len(titulo))
    if not dados:
        print("  (nada encontrado)")
    for chave, valor in dados.items():
        print(f"  {chave:<26} {valor}")


def main() -> None:
    """Monta as seções pedidas e imprime em texto ou JSON."""
    parser = argparse.ArgumentParser(description="Informações do sistema, só com a biblioteca padrão.")
    parser.add_argument("--sistema", action="store_true", help="sistema operacional, usuário, pastas e hora")
    parser.add_argument("--python", action="store_true", help="versão e configuração do interpretador")
    parser.add_argument("--hardware", action="store_true", help="CPUs e memória")
    parser.add_argument("--disco", nargs="?", const=".", metavar="PASTA", help="espaço em disco (padrão: pasta atual)")
    parser.add_argument("--env", nargs="?", const="", metavar="PREFIXO",
                        help="variáveis de ambiente; com prefixo, só as que começam com ele")
    parser.add_argument("--tudo", action="store_true", help="todas as seções")
    parser.add_argument("--json", action="store_true", help="saída em JSON em vez de texto")
    parser.add_argument("--demo", action="store_true", help="mostra tudo o que conseguir do sistema atual")
    args = parser.parse_args()

    if args.demo:
        print("=== Informações do sistema: demonstração (tudo o que a biblioteca padrão alcança) ===")
    if not any([args.sistema, args.python, args.hardware, args.disco, args.env is not None, args.tudo, args.demo]):
        parser.print_help()
        return
    tudo = args.tudo or args.demo
    secoes: dict[str, dict[str, Any]] = {}
    if tudo or args.sistema:
        secoes["Sistema"] = secao_sistema()
    if tudo or args.python:
        secoes["Python"] = secao_python()
    if tudo or args.hardware:
        secoes["Hardware"] = secao_hardware()
    if tudo or args.disco:
        pasta = Path(args.disco or ".")
        if not pasta.is_dir():
            parser.error(f"a pasta '{pasta}' não existe, não dá para medir o disco dela")
        secoes["Disco"] = secao_disco(pasta)
    if tudo or args.env is not None:
        prefixo = args.env if args.env else None
        secoes["Ambiente" + (f" (prefixo {prefixo})" if prefixo else "")] = secao_ambiente(prefixo)

    if args.json:
        print(json.dumps(secoes, ensure_ascii=False, indent=2))
        return
    for titulo, dados in secoes.items():
        imprimir_secao(titulo, dados)


if __name__ == "__main__":
    main()

# ------------------------------------------------------------
# Para ir além
# 1. Mostre há quanto tempo a máquina está ligada: /proc/uptime no Linux,
#    GetTickCount64 do kernel32 no Windows (ctypes de novo).
# 2. Liste os discos montados (psutil não vale: tente os.listdrives no
#    Windows 3.12+ e /proc/mounts no Linux) com o espaço livre de cada um.
# 3. Grave a saída JSON num arquivo com data no nome e compare duas
#    execuções, apontando o que mudou (memória livre, disco, variáveis).
# ------------------------------------------------------------

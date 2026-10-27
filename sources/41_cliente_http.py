#!/usr/bin/env python3
# ============================================================
# CodeNomad Academy  |  Sources Python  |  41. Cliente HTTP sem dependências
# ------------------------------------------------------------
# O que faz: Faz um GET em qualquer URL e mostra status, cabeçalhos e corpo.
#            Se a resposta for JSON, interpreta e extrai campos por caminho
#            (ex.: loja.nome, produtos.0.preco). Timeout e falhas de rede
#            viram mensagens claras em vez de erro cru na tela.
# Como usar: python 41_cliente_http.py https://exemplo.org/api/loja --campo loja.nome
#            python 41_cliente_http.py https://exemplo.org/ --timeout 5 --cabecalho "Accept: text/html"
#            python 41_cliente_http.py --demo
# O que você aprende: urllib.request, tratamento de exceções de rede,
#            dataclasses, json, navegação em dicionários aninhados, argparse
# Requisitos: Python 3.10+, só biblioteca padrão
# Licença MIT. Um projeto da CodeNomad Academy (codenomad.org)
# ============================================================
from __future__ import annotations

import argparse
import http.client
import json
import socket
import sys
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from typing import Any

AGENTE = "CodeNomadAcademy-ClienteHTTP/1.0"

# Resposta usada pelo --demo: um JSON como o que uma API de loja devolveria.
RESPOSTA_EXEMPLO = {
    "loja": {"nome": "Papelaria Exemplo", "cidade": "Curitiba", "aberta": True},
    "produtos": [
        {"nome": "Caderno pautado", "preco": 18.9, "estoque": 42},
        {"nome": "Caneta azul", "preco": 2.5, "estoque": 300},
        {"nome": "Mochila escolar", "preco": 129.0, "estoque": 7},
    ],
    "total_produtos": 3,
}


@dataclass
class Resposta:
    """Resultado de um pedido HTTP, independente do objeto interno da urllib."""

    url: str
    status: int
    motivo: str
    cabecalhos: dict[str, str] = field(default_factory=dict)
    corpo: bytes = b""

    def charset(self) -> str:
        """Lê o charset do Content-Type; usa UTF-8 quando o servidor não informa."""
        for parte in self.cabecalhos.get("Content-Type", "").split(";"):
            parte = parte.strip()
            if parte.lower().startswith("charset="):
                return parte.split("=", 1)[1].strip('" ')
        return "utf-8"

    def texto(self) -> str:
        """Decodifica o corpo; bytes inválidos viram '?' em vez de derrubar o programa."""
        try:
            return self.corpo.decode(self.charset(), errors="replace")
        except LookupError:  # charset que o Python não conhece
            return self.corpo.decode("utf-8", errors="replace")

    def json(self) -> Any | None:
        """Tenta interpretar o corpo como JSON; devolve None quando não é JSON."""
        try:
            return json.loads(self.texto())
        except json.JSONDecodeError:
            return None


def validar_url(url: str) -> str:
    """Aceita só http(s) com host; sem esquema, assume https://."""
    partes = urllib.parse.urlsplit(url if "://" in url else "https://" + url)
    if partes.scheme not in ("http", "https"):
        raise ValueError(f"URL inválida: esquema '{partes.scheme}' não é suportado, use http:// ou https://")
    if not partes.netloc:
        raise ValueError("URL inválida: falta o host, por exemplo https://exemplo.org/caminho")
    return urllib.parse.urlunsplit(partes)


def interpretar_cabecalhos(itens: list[str]) -> dict[str, str]:
    """Converte ['Accept: text/html'] em {'Accept': 'text/html'}, validando o formato."""
    cabecalhos: dict[str, str] = {}
    for item in itens:
        nome, separador, valor = item.partition(":")
        if not separador or not nome.strip():
            raise ValueError(f"cabeçalho '{item}' precisa do formato 'Nome: valor'")
        cabecalhos[nome.strip()] = valor.strip()
    return cabecalhos


def buscar(url: str, timeout: float = 10.0, cabecalhos: dict[str, str] | None = None) -> Resposta:
    """Faz o GET e devolve uma Resposta, inclusive quando o servidor responde 4xx ou 5xx."""
    pedido = urllib.request.Request(url, headers={"User-Agent": AGENTE, **(cabecalhos or {})})
    try:
        with urllib.request.urlopen(pedido, timeout=timeout) as resp:
            return Resposta(resp.geturl(), resp.status, resp.reason, dict(resp.headers), resp.read())
    except urllib.error.HTTPError as erro:
        # 404 e 500 também são respostas: o servidor falou, só não gostou do pedido.
        return Resposta(erro.geturl() or url, erro.code, erro.reason, dict(erro.headers), erro.read())


def explicar_erro(erro: Exception) -> str:
    """Traduz as exceções de rede mais comuns para uma frase que o usuário entende."""
    if isinstance(erro, urllib.error.URLError):
        motivo = erro.reason
        if isinstance(motivo, TimeoutError):
            return "o servidor não respondeu dentro do tempo limite (timeout)"
        if isinstance(motivo, socket.gaierror):
            return "não foi possível resolver o nome do host (DNS); confira a URL ou a conexão"
        if isinstance(motivo, ConnectionRefusedError):
            return "conexão recusada: nada está ouvindo nesse endereço e porta"
        return f"falha de rede: {motivo}"
    if isinstance(erro, TimeoutError):
        return "a leitura demorou demais e foi interrompida (timeout)"
    if isinstance(erro, http.client.HTTPException):
        return f"resposta malformada do servidor: {erro}"
    return str(erro)


def extrair_campo(dados: Any, caminho: str) -> Any:
    """Percorre dicionários e listas seguindo um caminho como 'produtos.0.nome'."""
    atual = dados
    for parte in caminho.split("."):
        if isinstance(atual, dict):
            if parte not in atual:
                raise KeyError(f"chave '{parte}' não existe; chaves disponíveis: {list(atual)[:6]}")
            atual = atual[parte]
        elif isinstance(atual, list):
            # Índices negativos valem, como em qualquer lista do Python.
            if not parte.lstrip("-").isdigit() or not -len(atual) <= int(parte) < len(atual):
                raise KeyError(f"'{parte}' não é um índice válido para uma lista de {len(atual)} itens")
            atual = atual[int(parte)]
        else:
            raise KeyError(f"não dá para entrar em '{parte}': o valor atual é {type(atual).__name__}")
    return atual


def mostrar_resposta(resp: Resposta, campos: list[str], limite: int) -> None:
    """Imprime status, cabeçalhos, corpo (JSON formatado quando possível) e os campos pedidos."""
    print(f"URL final : {resp.url}")
    print(f"Status    : {resp.status} {resp.motivo}")
    print("Cabeçalhos:")
    for nome, valor in resp.cabecalhos.items():
        print(f"  {nome}: {valor}")
    dados = resp.json()
    print()
    if dados is None:
        conteudo = resp.texto()
        print(f"Corpo ({len(resp.corpo)} bytes, texto):")
    else:
        conteudo = json.dumps(dados, indent=2, ensure_ascii=False)
        print(f"Corpo ({len(resp.corpo)} bytes, JSON interpretado):")
    print(conteudo[:limite] + (" [...]" if len(conteudo) > limite else ""))
    if not campos:
        return
    print()
    print("Campos extraídos:")
    for caminho in campos:
        if dados is None:
            print(f"  {caminho}: o corpo não é JSON")
            continue
        try:
            print(f"  {caminho} = {extrair_campo(dados, caminho)!r}")
        except KeyError as erro:
            print(f"  {caminho}: {erro.args[0]}")


def resposta_de_exemplo() -> Resposta:
    """Monta uma Resposta como se tivesse vindo da rede, para o modo --demo."""
    corpo = json.dumps(RESPOSTA_EXEMPLO, ensure_ascii=False).encode("utf-8")
    cabecalhos = {
        "Content-Type": "application/json; charset=utf-8",
        "Content-Length": str(len(corpo)),
        "Server": "exemplo/1.0",
        "Cache-Control": "no-cache",
    }
    return Resposta("https://exemplo.org/api/loja", 200, "OK", cabecalhos, corpo)


def demo() -> None:
    """Processa uma resposta embutida, sem rede, e mostra como os erros são explicados."""
    print("=== Cliente HTTP: demonstração sem acesso à rede ===")
    print("Resposta de exemplo recebida de https://exemplo.org/api/loja\n")
    campos = ["loja.nome", "produtos.1.preco", "produtos.-1.nome", "produtos.5.nome", "loja.telefone"]
    mostrar_resposta(resposta_de_exemplo(), campos, limite=600)
    print("\nComo os erros de rede são explicados ao usuário:")
    simulados = [
        ("servidor que não responde", urllib.error.URLError(TimeoutError("timed out"))),
        ("host que não existe", urllib.error.URLError(socket.gaierror(11001, "getaddrinfo failed"))),
        ("porta fechada", urllib.error.URLError(ConnectionRefusedError(111, "Connection refused"))),
        ("esquema errado", ValueError("URL inválida: esquema 'ftp' não é suportado, use http:// ou https://")),
    ]
    for cenario, erro in simulados:
        print(f"  {cenario:<26} -> {explicar_erro(erro)}")


def main() -> None:
    """Lê os argumentos, faz o pedido e mostra o resultado."""
    parser = argparse.ArgumentParser(description="Cliente HTTP de linha de comando, só com a biblioteca padrão.")
    parser.add_argument("url", nargs="?", help="endereço a consultar (http:// ou https://)")
    parser.add_argument("--campo", action="append", default=[], metavar="CAMINHO",
                        help="campo do JSON a extrair, ex.: loja.nome (pode repetir)")
    parser.add_argument("--cabecalho", action="append", default=[], metavar="'Nome: valor'",
                        help="cabeçalho extra a enviar (pode repetir)")
    parser.add_argument("--timeout", type=float, default=10.0, help="segundos de espera (padrão: 10)")
    parser.add_argument("--limite", type=int, default=1500, help="tamanho máximo do corpo mostrado (padrão: 1500)")
    parser.add_argument("--demo", action="store_true", help="processa uma resposta de exemplo, sem usar a rede")
    args = parser.parse_args()

    if args.demo:
        demo()
        return
    if not args.url:
        parser.print_help()
        return
    if args.timeout <= 0:
        parser.error("--timeout precisa ser maior que zero")
    try:
        cabecalhos = interpretar_cabecalhos(args.cabecalho)
        url = validar_url(args.url)
        resposta = buscar(url, args.timeout, cabecalhos)
    except (ValueError, OSError, http.client.HTTPException) as erro:
        # URLError é uma OSError: timeout, DNS e conexão recusada caem aqui.
        print(f"Erro: {explicar_erro(erro)}", file=sys.stderr)
        sys.exit(1)
    mostrar_resposta(resposta, args.campo, args.limite)
    sys.exit(0 if resposta.status < 400 else 1)


if __name__ == "__main__":
    main()

# ------------------------------------------------------------
# Para ir além
# 1. Adicione --metodo POST com --dados para enviar um JSON no corpo do pedido
#    (dica: Request aceita data=bytes e method="POST").
# 2. Grave o corpo num arquivo com --salvar caminho, usando pathlib e modo binário.
# 3. Siga redirecionamentos na mão: desative-os com um HTTPRedirectHandler
#    próprio e mostre a cadeia de URLs até a resposta final.
# ------------------------------------------------------------

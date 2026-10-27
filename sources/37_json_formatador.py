#!/usr/bin/env python3
# ============================================================
# CodeNomad Academy  |  Sources Python  |  37. Validador e formatador de JSON
# ------------------------------------------------------------
# O que faz: Valida um arquivo JSON apontando linha e coluna do erro (com a
#            linha problemática e uma seta), formata com recuo, compacta numa
#            linha só, extrai um valor por caminho (ex.: cliente.pedidos[0].total)
#            e lista todas as chaves existentes, com o caminho completo.
# Como usar: python 37_json_formatador.py validar pedido.json
#            python 37_json_formatador.py formatar pedido.json --recuo 4 --gravar bonito.json
#            python 37_json_formatador.py extrair pedido.json cliente.pedidos[0].total
#            python 37_json_formatador.py --demo
# O que você aprende: json.loads/dumps e JSONDecodeError (lineno, colno,
#            msg), expressões regulares simples com re.findall, recursão
#            para percorrer dicionários e listas, isinstance e argparse com
#            subcomandos.
# Requisitos: Python 3.10+, só biblioteca padrão
# Licença MIT. Um projeto da CodeNomad Academy (codenomad.org)
# ============================================================
from __future__ import annotations

import argparse
import json
import re
import sys
import tempfile
from pathlib import Path
from typing import Any


class ErroDeUso(Exception):
    """Erro causado pela entrada do usuário; a mensagem é mostrada sem traceback."""


def apontar_erro(texto: str, erro: json.JSONDecodeError) -> list[str]:
    """Mostra a linha do problema e uma seta embaixo da coluna, como um compilador faz."""
    linhas = texto.splitlines()
    # Quando falta fechar um colchete, o erro cai depois da última linha: avisa em vez de inventar.
    linha = linhas[erro.lineno - 1] if erro.lineno <= len(linhas) else "(fim do arquivo)"
    return [
        f"JSON inválido na linha {erro.lineno}, coluna {erro.colno}: {erro.msg}",
        f"  {erro.lineno:>4} | {linha}",
        f"       | {' ' * (erro.colno - 1)}^",
    ]


def validar(texto: str) -> tuple[Any, list[str]]:
    """Devolve (objeto, []) quando é válido ou (None, mensagens) quando não é."""
    try:
        return json.loads(texto), []
    except json.JSONDecodeError as erro:
        return None, apontar_erro(texto, erro)


def carregar(texto: str) -> Any:
    """Igual a validar, mas transforma o erro em ErroDeUso para os outros comandos."""
    objeto, mensagens = validar(texto)
    if mensagens:
        raise ErroDeUso("\n".join(mensagens))
    return objeto


def formatar(objeto: Any, recuo: int = 2, ordenar: bool = False) -> str:
    """ensure_ascii=False mantém "ação" legível em vez de "a\\u00e7\\u00e3o"."""
    return json.dumps(objeto, indent=recuo, ensure_ascii=False, sort_keys=ordenar)


def compactar(objeto: Any) -> str:
    """Sem espaços depois de vírgulas e dois pontos: o menor JSON possível."""
    return json.dumps(objeto, separators=(",", ":"), ensure_ascii=False)


def analisar_caminho(caminho: str) -> list[str | int]:
    """"cliente.pedidos[0].total" vira ["cliente", "pedidos", 0, "total"]."""
    if not caminho.strip():
        raise ErroDeUso("o caminho não pode ficar vazio")
    # Cada pedaço é um índice entre colchetes ou um nome sem ponto nem colchete.
    pedacos = re.findall(r"\[(\d+)\]|([^.\[\]]+)", caminho)
    return [int(indice) if indice else nome for indice, nome in pedacos]


def extrair(objeto: Any, caminho: str) -> Any:
    """Desce pelo objeto um pedaço de cada vez, explicando onde parou se algo falhar."""
    atual, percorrido = objeto, ""
    for pedaco in analisar_caminho(caminho):
        if isinstance(pedaco, int):
            if not isinstance(atual, list):
                raise ErroDeUso(f"'{percorrido or 'raiz'}' não é uma lista, não dá para usar [{pedaco}]")
            if pedaco >= len(atual):
                raise ErroDeUso(f"índice {pedaco} fora do alcance: '{percorrido}' tem {len(atual)} item(ns)")
            atual, percorrido = atual[pedaco], f"{percorrido}[{pedaco}]"
        else:
            if not isinstance(atual, dict):
                raise ErroDeUso(f"'{percorrido or 'raiz'}' não é um objeto, não tem a chave '{pedaco}'")
            if pedaco not in atual:
                disponiveis = ", ".join(sorted(atual)) or "nenhuma"
                raise ErroDeUso(f"chave '{pedaco}' não existe em '{percorrido or 'raiz'}' (chaves: {disponiveis})")
            atual, percorrido = atual[pedaco], f"{percorrido}.{pedaco}" if percorrido else pedaco
    return atual


def listar_chaves(objeto: Any, prefixo: str = "") -> list[str]:
    """Recursão: cada dicionário acrescenta ".chave" e cada lista acrescenta "[i]"."""
    caminhos: list[str] = []
    if isinstance(objeto, dict):
        for chave, valor in objeto.items():
            caminho = f"{prefixo}.{chave}" if prefixo else chave
            caminhos.append(caminho)
            caminhos += listar_chaves(valor, caminho)
    elif isinstance(objeto, list):
        for indice, valor in enumerate(objeto):
            caminhos += listar_chaves(valor, f"{prefixo}[{indice}]")
    return caminhos


def executar(args: argparse.Namespace) -> list[str]:
    """Lê o arquivo, despacha para o comando e devolve as linhas de saída."""
    caminho = Path(args.arquivo)
    if not caminho.is_file():
        raise ErroDeUso(f"arquivo não encontrado: {caminho}")
    texto = caminho.read_text(encoding="utf-8")
    # Qualquer comando começa validando; JSON inválido vira ErroDeUso e código de saída 2.
    objeto = carregar(texto)
    if args.comando == "validar":
        return [f"JSON válido: {caminho} ({len(listar_chaves(objeto))} chave(s) no total)"]
    if args.comando == "extrair":
        valor = extrair(objeto, args.caminho)
        return [valor if isinstance(valor, str) else compactar(valor)]
    if args.comando == "chaves":
        return listar_chaves(objeto) or ["(nenhuma chave: a raiz não é um objeto)"]
    resultado = formatar(objeto, args.recuo, args.ordenar) if args.comando == "formatar" else compactar(objeto)
    if args.gravar:
        Path(args.gravar).write_text(resultado + "\n", encoding="utf-8")
        return [f"Gravado em {args.gravar} ({len(resultado)} caracteres)"]
    return [resultado]


def montar_parser() -> argparse.ArgumentParser:
    """Cinco subcomandos que compartilham o argumento arquivo; só alguns têm opções extras."""
    parser = argparse.ArgumentParser(description="Valida, formata, compacta e consulta arquivos JSON.")
    parser.add_argument("--demo", action="store_true", help="roda uma demonstração completa")
    sub = parser.add_subparsers(dest="comando")
    for nome, ajuda in [("validar", "confere a sintaxe"), ("formatar", "reescreve com recuo"),
                        ("compactar", "reescreve numa linha"), ("extrair", "pega um valor pelo caminho"),
                        ("chaves", "lista todos os caminhos de chave")]:
        comando = sub.add_parser(nome, help=ajuda)
        comando.add_argument("arquivo")
        if nome == "extrair":
            comando.add_argument("caminho", help="ex.: cliente.pedidos[0].total")
        if nome == "formatar":
            comando.add_argument("--recuo", type=int, default=2, help="espaços por nível (padrão 2)")
            comando.add_argument("--ordenar", action="store_true", help="ordena as chaves")
        if nome in ("formatar", "compactar"):
            comando.add_argument("--gravar", metavar="ARQUIVO", help="grava o resultado neste arquivo")
    return parser


JSON_EXEMPLO = """{"cliente": {"nome": "Loja da Esquina", "cidade": "Curitiba", "ativo": true},
 "pedidos": [{"id": 101, "total": 249.9, "itens": ["caderno", "caneta"]},
             {"id": 102, "total": 89.0, "itens": ["livro"]}], "observação": null}"""

JSON_QUEBRADO = """{
  "cliente": "Loja da Esquina",
  "pedidos": [101, 102,],
  "ativo": true
}"""


def demo() -> None:
    """Formata, compacta, consulta e lista um JSON embutido; depois mostra um erro apontado."""
    print("=== Demonstração: validador e formatador de JSON ===")
    parser = montar_parser()
    with tempfile.TemporaryDirectory() as temporaria:
        bom, ruim = Path(temporaria) / "pedido.json", Path(temporaria) / "quebrado.json"
        bom.write_text(JSON_EXEMPLO, encoding="utf-8")
        ruim.write_text(JSON_QUEBRADO, encoding="utf-8")
        roteiro = [
            ["validar", str(bom)],
            ["formatar", str(bom), "--recuo", "2"],
            ["compactar", str(bom)],
            ["extrair", str(bom), "cliente.nome"],
            ["extrair", str(bom), "pedidos[1].itens[0]"],
            ["extrair", str(bom), "pedidos[0]"],
            ["chaves", str(bom)],
            ["validar", str(ruim)],
            ["extrair", str(bom), "pedidos[5].total"],
            ["extrair", str(bom), "cliente.telefone"],
        ]
        for comando in roteiro:
            bonito = " ".join(c.replace(temporaria, ".").replace("\\", "/") for c in comando)
            print(f"\n$ python 37_json_formatador.py {bonito}")
            try:
                for linha in executar(parser.parse_args(comando)):
                    print(linha.replace(temporaria, "."))
            except ErroDeUso as erro:
                print(f"Erro: {erro}")


def main() -> None:
    """Ponto de entrada: --demo demonstra; sem subcomando mostra o uso; senão executa."""
    parser = montar_parser()
    args = parser.parse_args()
    if args.demo:
        demo()
        return
    if args.comando is None:
        parser.print_help()
        sys.exit(1)
    try:
        for linha in executar(args):
            print(linha)
    except ErroDeUso as erro:
        print(f"Erro: {erro}", file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()

# ------------------------------------------------------------
# Para ir além
# 1. Aceite "-" como nome de arquivo para ler da entrada padrão
#    (sys.stdin.read()) e encadear com outros comandos no terminal.
# 2. Crie o subcomando "definir" que grava um valor num caminho
#    (criando as chaves que faltam) e salva o arquivo de volta.
# 3. Faça "chaves --tipos" mostrar o tipo de cada valor (str, int, list...)
#    e "chaves --contar" dizer quantas folhas o documento tem.
# ------------------------------------------------------------

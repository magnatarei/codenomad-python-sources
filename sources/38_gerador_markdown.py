#!/usr/bin/env python3
# ============================================================
# CodeNomad Academy  |  Sources Python  |  38. Gerador de relatório em Markdown
# ------------------------------------------------------------
# O que faz: Monta um documento Markdown (títulos, parágrafos, listas, tabela
#            com colunas alinhadas e blocos de código) a partir de dados
#            estruturados num arquivo JSON, e também converte qualquer CSV
#            numa tabela Markdown com números alinhados à direita.
# Como usar: python 38_gerador_markdown.py --json relatorio.json --gravar relatorio.md
#            python 38_gerador_markdown.py --csv vendas.csv --titulo "Vendas de outubro"
#            python 38_gerador_markdown.py --demo
# O que você aprende: funções puras que devolvem texto, despacho por
#            dicionário (tipo do bloco -> função), csv.reader, cálculo de
#            largura de colunas com zip e max, str.ljust/rjust, json.load e
#            argparse com grupo de opções mutuamente exclusivas.
# Requisitos: Python 3.10+, só biblioteca padrão
# Licença MIT. Um projeto da CodeNomad Academy (codenomad.org)
# ============================================================
from __future__ import annotations

import argparse
import csv
import json
import sys
import tempfile
from pathlib import Path
from typing import Any, Callable


class ErroDeUso(Exception):
    """Erro causado pela entrada do usuário; a mensagem é mostrada sem traceback."""


def titulo(texto: str, nivel: int = 1) -> str:
    """"# Texto" para nível 1, "## Texto" para nível 2, e assim por diante."""
    if not 1 <= nivel <= 6:
        raise ErroDeUso(f"nível de título inválido: {nivel} (use de 1 a 6)")
    return "#" * nivel + " " + texto.strip()


def paragrafo(texto: str) -> str:
    """Junta o texto numa linha só, com um espaço entre as palavras."""
    return " ".join(texto.split())


def lista(itens: list[str], ordenada: bool = False) -> str:
    """Lista com "-" ou numerada com "1.", "2."..."""
    if not itens:
        raise ErroDeUso("a lista precisa de pelo menos um item")
    marcador = (lambda i: f"{i}.") if ordenada else (lambda i: "-")
    return "\n".join(f"{marcador(numero)} {item}" for numero, item in enumerate(itens, start=1))


def bloco_codigo(codigo: str, linguagem: str = "") -> str:
    """Três crases abrem e fecham; a linguagem logo após as crases liga o realce."""
    return f"```{linguagem}\n{codigo.rstrip()}\n```"


def eh_numero(texto: str) -> bool:
    """Aceita "1250", "12.5" e "12,5"; usado para decidir o alinhamento da coluna."""
    try:
        float(texto.strip().replace(".", "").replace(",", ".") if "," in texto else texto.strip())
        return True
    except ValueError:
        return False


def tabela(cabecalho: list[str], linhas: list[list[Any]]) -> str:
    """Tabela com colunas alinhadas; colunas só de números ficam à direita."""
    if not cabecalho:
        raise ErroDeUso("a tabela precisa de um cabeçalho")
    celulas = [[str(c) for c in linha] for linha in linhas]
    for numero, linha in enumerate(celulas, start=1):
        if len(linha) != len(cabecalho):
            raise ErroDeUso(f"a linha {numero} da tabela tem {len(linha)} coluna(s), mas o cabeçalho tem {len(cabecalho)}")
    # zip(*celulas) transpõe: entrega uma coluna de cada vez em vez de uma linha.
    colunas = list(zip(cabecalho, *celulas))
    larguras = [max(len(valor) for valor in coluna) for coluna in colunas]
    numericas = [all(eh_numero(v) for v in coluna[1:]) and len(coluna) > 1 for coluna in colunas]

    def formatar_linha(valores: list[str]) -> str:
        """Uma linha da tabela com cada célula alinhada à largura da coluna."""
        partes = [v.rjust(l) if n else v.ljust(l) for v, l, n in zip(valores, larguras, numericas)]
        return "| " + " | ".join(partes) + " |"

    separador = "| " + " | ".join(("-" * (l - 1) + ":") if n else ("-" * l) for l, n in zip(larguras, numericas)) + " |"
    return "\n".join([formatar_linha(cabecalho), separador] + [formatar_linha(linha) for linha in celulas])


def csv_para_tabela(caminho: Path) -> str:
    """A primeira linha do CSV vira o cabeçalho; as demais, o corpo da tabela."""
    if not caminho.is_file():
        raise ErroDeUso(f"arquivo não encontrado: {caminho}")
    with caminho.open(encoding="utf-8", newline="") as arquivo:
        linhas = [linha for linha in csv.reader(arquivo) if linha]
    if len(linhas) < 2:
        raise ErroDeUso("o CSV precisa de um cabeçalho e pelo menos uma linha de dados")
    return tabela(linhas[0], linhas[1:])


# Despacho por dicionário: o tipo do bloco escolhe a função que o renderiza.
RENDERIZADORES: dict[str, Callable[[dict[str, Any]], str]] = {
    "titulo": lambda b: titulo(b["texto"], int(b.get("nivel", 1))),
    "paragrafo": lambda b: paragrafo(b["texto"]),
    "lista": lambda b: lista(b["itens"], bool(b.get("ordenada", False))),
    "tabela": lambda b: tabela(b["cabecalho"], b["linhas"]),
    "codigo": lambda b: bloco_codigo(b["codigo"], b.get("linguagem", "")),
}


def montar_documento(blocos: list[dict[str, Any]]) -> str:
    """Renderiza cada bloco na ordem e separa tudo com uma linha em branco."""
    partes = []
    for posicao, bloco in enumerate(blocos, start=1):
        tipo = bloco.get("tipo")
        if tipo not in RENDERIZADORES:
            raise ErroDeUso(f"bloco {posicao}: tipo desconhecido {tipo!r} (use {', '.join(RENDERIZADORES)})")
        try:
            partes.append(RENDERIZADORES[tipo](bloco))
        except KeyError as faltando:
            raise ErroDeUso(f"bloco {posicao} ({tipo}): falta o campo {faltando}") from None
    return "\n\n".join(partes) + "\n"


BLOCOS_EXEMPLO: list[dict[str, Any]] = [
    {"tipo": "titulo", "texto": "Relatório mensal da Papelaria Central"},
    {"tipo": "paragrafo", "texto": "Resumo de outubro: as vendas cresceram 12% em relação a setembro, "
                                   "puxadas pelo material escolar."},
    {"tipo": "titulo", "texto": "Produtos mais vendidos", "nivel": 2},
    {"tipo": "tabela", "cabecalho": ["Produto", "Categoria", "Unidades", "Receita (R$)"],
     "linhas": [["Caderno pautado", "papelaria", 182, "3.439,80"], ["Caneta gel", "papelaria", 341, "1.534,50"],
                ["Mochila escolar", "acessórios", 27, "4.023,00"]]},
    {"tipo": "titulo", "texto": "Próximos passos", "nivel": 2},
    {"tipo": "lista", "ordenada": True, "itens": ["Repor o estoque de cadernos", "Negociar frete das mochilas",
                                                  "Lançar a promoção de novembro"]},
    {"tipo": "codigo", "linguagem": "python", "codigo": "total = sum(v.receita for v in vendas)\nprint(total)"},
]


def demo() -> None:
    """Gera um relatório a partir dos blocos de exemplo, converte um CSV temporário e provoca um erro."""
    print("=== Demonstração: gerador de relatório em Markdown ===")
    print("Documento montado a partir de 7 blocos estruturados:\n")
    print(montar_documento(BLOCOS_EXEMPLO))
    with tempfile.TemporaryDirectory() as temporaria:
        caminho = Path(temporaria) / "estoque.csv"
        caminho.write_text("item,quantidade,preco\nLápis,120,1.50\nBorracha branca,45,0.80\nRégua 30 cm,12,3.25\n",
                           encoding="utf-8")
        print("$ python 38_gerador_markdown.py --csv estoque.csv --titulo Estoque\n")
        print(titulo("Estoque") + "\n\n" + csv_para_tabela(caminho))
    print("\nTabela com uma linha de 2 colunas num cabeçalho de 3:")
    try:
        tabela(["a", "b", "c"], [[1, 2, 3], [4, 5]])
    except ErroDeUso as erro:
        print(f"Erro: {erro}")


def main() -> None:
    """Ponto de entrada: --demo demonstra; --json ou --csv geram o Markdown."""
    parser = argparse.ArgumentParser(description="Gera Markdown a partir de JSON estruturado ou de um CSV.")
    origem = parser.add_mutually_exclusive_group()
    origem.add_argument("--json", metavar="ARQUIVO", help="lista de blocos em JSON")
    origem.add_argument("--csv", metavar="ARQUIVO", help="CSV que vira uma tabela")
    origem.add_argument("--demo", action="store_true", help="roda uma demonstração completa")
    parser.add_argument("--titulo", help="título colocado antes da tabela do CSV")
    parser.add_argument("--gravar", metavar="ARQUIVO.md", help="grava o resultado em vez de imprimir")
    args = parser.parse_args()
    if args.demo:
        demo()
        return
    if not args.json and not args.csv:
        parser.print_help()
        sys.exit(1)
    try:
        if args.json:
            caminho = Path(args.json)
            if not caminho.is_file():
                raise ErroDeUso(f"arquivo não encontrado: {caminho}")
            blocos = json.loads(caminho.read_text(encoding="utf-8"))
            if not isinstance(blocos, list):
                raise ErroDeUso("o JSON precisa ser uma lista de blocos")
            resultado = montar_documento(blocos)
        else:
            corpo = csv_para_tabela(Path(args.csv))
            resultado = (titulo(args.titulo) + "\n\n" if args.titulo else "") + corpo + "\n"
        if args.gravar:
            Path(args.gravar).write_text(resultado, encoding="utf-8")
            print(f"Markdown gravado em {args.gravar}")
        else:
            print(resultado, end="")
    except json.JSONDecodeError as erro:
        print(f"Erro: o JSON não é válido (linha {erro.lineno}: {erro.msg})", file=sys.stderr)
        sys.exit(2)
    except ErroDeUso as erro:
        print(f"Erro: {erro}", file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()

# ------------------------------------------------------------
# Para ir além
# 1. Acrescente os blocos "citacao" (linhas começando com ">") e "imagem"
#    (![alt](caminho)) ao dicionário de renderizadores.
# 2. Gere um sumário automático no topo com links para cada título
#    (Markdown aceita [texto](#ancora-em-minusculas)).
# 3. Converta o Markdown gerado para HTML simples com expressões regulares
#    e abra o resultado no navegador com webbrowser.open.
# ------------------------------------------------------------

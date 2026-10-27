#!/usr/bin/env python3
# ============================================================
# CodeNomad Academy  |  Sources Python  |  17. Conversor de formatos de texto
# ------------------------------------------------------------
# O que faz: Converte um texto entre snake_case, camelCase, PascalCase,
#            kebab-case, CONSTANTE e Title Case; gera slug para URL; remove
#            acentos; inverte o texto e capitaliza frases. Entende também
#            camelCase na entrada ("totalDeVendas" vira "total de vendas").
# Como usar: python 17_conversor_texto.py "Relatório de vendas do mês" --para slug
#            python 17_conversor_texto.py "totalDeVendasAnuais" --todos
#            python 17_conversor_texto.py --demo
# O que você aprende: re.sub com lookbehind e lookahead, unicodedata,
#            dicionário de funções (despacho por nome), str.join, fatiamento
#            e a diferença entre identificadores de código e texto para pessoas.
# Requisitos: Python 3.10+, só biblioteca padrão
# Licença MIT. Um projeto da CodeNomad Academy (codenomad.org)
# ============================================================
import argparse
import re
import sys
import unicodedata
from collections.abc import Callable

# Palavras curtas que ficam em minúsculas no meio de um título em português.
MINUSCULAS_NO_TITULO = {"a", "o", "as", "os", "de", "da", "do", "das", "dos",
                        "e", "ou", "em", "no", "na", "nos", "nas", "para", "com", "por"}


def remover_acentos(texto: str) -> str:
    """Troca é por e, ç por c etc. NFD separa a letra da marca; a marca sai."""
    decomposto = unicodedata.normalize("NFD", texto)
    return "".join(c for c in decomposto if unicodedata.category(c) != "Mn")


def separar_palavras(texto: str) -> list[str]:
    """Quebra qualquer formato em palavras minúsculas e sem acento.

    Funciona com espaços, hífens e sublinhados, e também com camelCase:
    a fronteira entre palavras é a troca de minúscula para maiúscula.
    """
    sem_acento = remover_acentos(texto)
    # (?<=...) olha para trás e (?=...) olha para a frente sem consumir nada:
    # "totalDeVendas" vira "total De Vendas".
    espacado = re.sub(r"(?<=[a-z0-9])(?=[A-Z])", " ", sem_acento)
    # Sigla seguida de palavra: "HTTPServer" vira "HTTP Server".
    espacado = re.sub(r"(?<=[A-Z])(?=[A-Z][a-z])", " ", espacado)
    return [p.lower() for p in re.findall(r"[A-Za-z0-9]+", espacado)]


def para_snake(texto: str) -> str:
    """Minúsculas unidas por sublinhado, o padrão de nomes em Python: total_de_vendas."""
    return "_".join(separar_palavras(texto))


def para_constante(texto: str) -> str:
    """Maiúsculas unidas por sublinhado, usado em constantes: TOTAL_DE_VENDAS."""
    return para_snake(texto).upper()


def para_kebab(texto: str) -> str:
    """Minúsculas unidas por hífen, comum em CSS e nomes de arquivo: total-de-vendas."""
    return "-".join(separar_palavras(texto))


def para_pascal(texto: str) -> str:
    """Cada palavra com inicial maiúscula, sem separador, como nomes de classe: TotalDeVendas."""
    return "".join(p.capitalize() for p in separar_palavras(texto))


def para_camel(texto: str) -> str:
    """relatorioDeVendas: igual ao Pascal, mas a primeira palavra fica minúscula."""
    palavras = separar_palavras(texto)
    if not palavras:
        return ""
    return palavras[0] + "".join(p.capitalize() for p in palavras[1:])


def para_slug(texto: str) -> str:
    """relatorio-de-vendas, como em endereços de páginas na web."""
    baixo = remover_acentos(texto).lower()
    return re.sub(r"[^a-z0-9]+", "-", baixo).strip("-")


def para_titulo(texto: str) -> str:
    """Relatório de Vendas do Mês: mantém acentos e artigos em minúsculas."""
    palavras = texto.split()
    resultado = []
    for i, palavra in enumerate(palavras):
        baixa = palavra.lower()
        if i > 0 and baixa in MINUSCULAS_NO_TITULO:
            resultado.append(baixa)
        else:
            resultado.append(baixa[:1].upper() + baixa[1:])
    return " ".join(resultado)


def inverter(texto: str) -> str:
    """Inverte a ordem dos símbolos: 'abc' vira 'cba'."""
    return texto[::-1]


def capitalizar(texto: str) -> str:
    """Primeira letra de cada frase em maiúscula e o resto em minúsculas."""
    baixo = texto.lower()
    # Casa o início do texto ou um fim de frase, e em seguida a primeira letra.
    return re.sub(r"(^|[.!?]\s+)(\w)", lambda m: m.group(1) + m.group(2).upper(), baixo)


# Despacho por nome: o argumento --para escolhe a função nesta tabela.
FORMATOS: dict[str, Callable[[str], str]] = {
    "snake": para_snake,
    "camel": para_camel,
    "pascal": para_pascal,
    "kebab": para_kebab,
    "constante": para_constante,
    "titulo": para_titulo,
    "slug": para_slug,
    "sem-acentos": remover_acentos,
    "inverter": inverter,
    "capitalizar": capitalizar,
}


def imprimir_todos(texto: str) -> None:
    """Aplica todas as conversões ao texto e imprime uma tabela."""
    print(f"Entrada: {texto!r}")
    for nome, funcao in FORMATOS.items():
        print(f"  {nome:<12} {funcao(texto)}")


def demo() -> None:
    """Converte três frases com acento e uma entrada em camelCase."""
    print("=" * 64)
    print("Conversor de formatos de texto: demonstração")
    print("=" * 64)
    frases = ["Relatório de vendas do mês", "função que calcula a média",
              "Configuração avançada do usuário. já está pronta!"]
    for frase in frases:
        print()
        imprimir_todos(frase)
    print("\nA entrada também pode vir em camelCase ou com sigla:")
    for identificador in ("totalDeVendasAnuais", "servidorHTTPLocal"):
        print(f"  {identificador:<22} -> palavras: {separar_palavras(identificador)}")


def construir_parser() -> argparse.ArgumentParser:
    """Define a linha de comando do programa."""
    parser = argparse.ArgumentParser(
        description="Converte texto entre snake_case, camelCase, slug e outros formatos.",
        epilog="Formatos: " + ", ".join(FORMATOS),
    )
    parser.add_argument("texto", nargs="?", help="o texto entre aspas")
    parser.add_argument("--para", choices=list(FORMATOS), metavar="FORMATO",
                        help="formato de destino (veja a lista abaixo)")
    parser.add_argument("--todos", action="store_true",
                        help="mostra o texto em todos os formatos")
    parser.add_argument("--demo", action="store_true",
                        help="roda uma demonstração completa sem pedir nada")
    return parser


def main(argv: list[str] | None = None) -> int:
    """Ponto de entrada: devolve 1 quando o texto está vazio."""
    argv = sys.argv[1:] if argv is None else argv
    parser = construir_parser()
    args = parser.parse_args(argv)
    if args.demo:
        demo()
        return 0
    if args.texto is None:
        parser.print_help()
        return 0
    if not args.texto.strip():
        print("Erro: o texto está vazio", file=sys.stderr)
        return 1
    if not args.para and not args.todos:
        parser.error("escolha --para FORMATO ou --todos")
    if args.todos:
        imprimir_todos(args.texto)
    else:
        print(FORMATOS[args.para](args.texto))
    return 0


if __name__ == "__main__":
    sys.exit(main())

# ------------------------------------------------------------
# Para ir além
#   1. Leia um arquivo .py e liste os nomes de função que não seguem o
#      snake_case, usando o módulo ast para achar as definições.
#   2. Converta todas as chaves de um JSON de camelCase para snake_case,
#      inclusive dentro de listas e dicionários aninhados.
#   3. Preserve siglas no camelCase: "url do servidor" deveria virar
#      "urlDoServidor", mas "servidor URL" poderia manter "servidorURL".
# ------------------------------------------------------------

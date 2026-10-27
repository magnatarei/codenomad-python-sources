#!/usr/bin/env python3
# ============================================================
# CodeNomad Academy  |  Sources Python  |  14. Contador de palavras e frequência
# ------------------------------------------------------------
# O que faz: Lê um texto (argumento ou arquivo) e conta símbolos, palavras,
#            linhas, frases e parágrafos; calcula o tamanho médio das
#            palavras e a riqueza do vocabulário; lista as N palavras mais
#            frequentes ignorando acentos e as palavras vazias do português.
# Como usar: python 14_contador_palavras.py "Um texto curto. Outro texto!"
#            python 14_contador_palavras.py --arquivo redacao.txt --top 15
#            python 14_contador_palavras.py --demo
# O que você aprende: collections.Counter, re.findall e re.split,
#            unicodedata para tirar acentos, pathlib para ler arquivos,
#            frozenset, dataclass com método calculado e tabelas no print.
# Requisitos: Python 3.10+, só biblioteca padrão
# Licença MIT. Um projeto da CodeNomad Academy (codenomad.org)
# ============================================================
import argparse
import re
import sys
import unicodedata
from collections import Counter
from dataclasses import dataclass
from pathlib import Path


def normalizar(texto: str) -> str:
    """Tira acentos e passa para minúsculas, para comparar palavras.

    NFD separa cada letra acentuada em letra + marca; a marca tem a
    categoria Mn (mark, nonspacing) e é descartada.
    """
    decomposto = unicodedata.normalize("NFD", texto)
    return "".join(c for c in decomposto if unicodedata.category(c) != "Mn").lower()


# Palavras tão comuns que só atrapalham a lista de frequência. Guardamos
# a versão normalizada para comparar com as palavras do texto.
PALAVRAS_VAZIAS = frozenset(normalizar(p) for p in (
    "a o e de da do das dos em um uma uns umas para com não que se por os as "
    "no na nos nas ao aos à às é são foi era ser como mais mas ou seu sua seus "
    "suas ele ela eles elas eu você nós isso isto esse essa este esta já também "
    "muito até quando onde porque pelo pela pelos pelas me te lhe há tem têm "
    "ter está estão sobre entre depois antes sem só ainda cada todo toda todos "
    "todas mesmo dez"
).split())

# Uma palavra é uma sequência de letras ou dígitos, com hífen ou apóstrofo
# no meio (guarda-chuva, d'água) mas nunca nas pontas. [^\W_] significa
# "letra ou dígito de qualquer idioma", então ç e ã também entram.
PALAVRA_RE = re.compile(r"[^\W_]+(?:['-][^\W_]+)*")
FIM_DE_FRASE_RE = re.compile(r"[.!?]+(?:\s|$)")
PARAGRAFO_RE = re.compile(r"\n\s*\n")

TEXTO_DEMO = "\n\n".join([
    "Aprender a programar é parecido com aprender um instrumento. No começo, "
    "cada acorde exige atenção total e os dedos tropeçam. Com prática diária, "
    "os movimentos viram hábito e a atenção fica livre para a música.",
    "Com código acontece o mesmo. As primeiras funções parecem longas e cheias "
    "de detalhes. Depois de algumas semanas, você lê uma função inteira de uma "
    "olhada e enxerga a estrutura antes dos detalhes. Esse salto não vem de "
    "talento: vem de repetição com atenção.",
    "Um bom hábito é escrever programas pequenos todos os dias. Um contador de "
    "palavras, uma calculadora, um conversor de unidades. Programas pequenos "
    "terminam, e terminar é o que dá confiança. Cada programa terminado ensina "
    "mais do que dez programas abandonados!",
    "Outro hábito é ler código escrito por outras pessoas. A biblioteca padrão "
    "do Python é uma escola aberta: cada módulo mostra uma forma de resolver um "
    "problema real com clareza. Leia, copie, modifique e quebre. Depois conserte. "
    "É assim que a prática vira conhecimento.",
])


@dataclass(frozen=True)
class Estatisticas:
    """Os números de um texto. frozen=True impede alterações acidentais."""

    simbolos: int
    simbolos_sem_espaco: int
    linhas: int
    palavras: int
    palavras_distintas: int
    frases: int
    paragrafos: int

    def tamanho_medio(self, lista: list[str]) -> float:
        """Tamanho médio das palavras, protegido contra lista vazia."""
        return sum(map(len, lista)) / len(lista) if lista else 0.0

    def riqueza(self) -> float:
        """Proporção de palavras distintas: perto de 1 é vocabulário variado."""
        return self.palavras_distintas / self.palavras if self.palavras else 0.0


def extrair_palavras(texto: str) -> list[str]:
    """Devolve as palavras do texto em minúsculas, na ordem em que aparecem."""
    return [p.lower() for p in PALAVRA_RE.findall(texto)]


def contar_frases(texto: str) -> int:
    """Conta trechos terminados em ponto, exclamação ou interrogação."""
    partes = FIM_DE_FRASE_RE.split(texto)
    return sum(1 for p in partes if p.strip())


def calcular(texto: str) -> Estatisticas:
    """Reúne todas as contagens em um único objeto."""
    palavras = extrair_palavras(texto)
    paragrafos = [p for p in PARAGRAFO_RE.split(texto.strip()) if p.strip()]
    return Estatisticas(
        simbolos=len(texto),
        simbolos_sem_espaco=sum(1 for c in texto if not c.isspace()),
        linhas=len(texto.splitlines()),
        palavras=len(palavras),
        palavras_distintas=len({normalizar(p) for p in palavras}),
        frases=contar_frases(texto),
        paragrafos=len(paragrafos),
    )


def mais_frequentes(texto: str, quantas: int, ignorar_vazias: bool = True) -> list[tuple[str, int]]:
    """As palavras mais comuns, sem as vazias e sem palavras de uma letra.

    "Atenção" e "atencao" contam como a mesma palavra; na lista aparece a
    grafia da primeira ocorrência.
    """
    grafia: dict[str, str] = {}
    chaves: list[str] = []
    for palavra in extrair_palavras(texto):
        chave = normalizar(palavra)
        if ignorar_vazias and (chave in PALAVRAS_VAZIAS or len(chave) < 2):
            continue
        grafia.setdefault(chave, palavra)  # guarda só a primeira grafia vista
        chaves.append(chave)
    # Counter conta tudo em uma linha e most_common já ordena.
    return [(grafia[chave], vezes) for chave, vezes in Counter(chaves).most_common(quantas)]


def imprimir_relatorio(texto: str, top: int, ignorar_vazias: bool) -> None:
    """Mostra as estatísticas e a tabela de frequência."""
    est = calcular(texto)
    palavras = extrair_palavras(texto)
    print("Estatísticas")
    print(f"  símbolos (com espaços):  {est.simbolos}")
    print(f"  símbolos (sem espaços):  {est.simbolos_sem_espaco}")
    print(f"  linhas:                  {est.linhas}")
    print(f"  parágrafos:              {est.paragrafos}")
    print(f"  frases:                  {est.frases}")
    print(f"  palavras:                {est.palavras}")
    print(f"  palavras distintas:      {est.palavras_distintas}")
    print(f"  tamanho médio:           {est.tamanho_medio(palavras):.2f} letras")
    print(f"  riqueza do vocabulário:  {est.riqueza():.0%}")

    ranking = mais_frequentes(texto, top, ignorar_vazias)
    if not ranking:
        print("\nNenhuma palavra para listar.")
        return
    maior = ranking[0][1]
    print(f"\nTop {len(ranking)} palavras" + ("" if ignorar_vazias else " (com palavras vazias)"))
    for posicao, (palavra, vezes) in enumerate(ranking, start=1):
        barra = "#" * round(20 * vezes / maior)
        print(f"  {posicao:>2}. {palavra:<16} {vezes:>3}  {barra}")


def ler_arquivo(caminho: str) -> str:
    """Lê o arquivo como UTF-8 e traduz os erros mais comuns em mensagens claras."""
    arquivo = Path(caminho)
    if not arquivo.is_file():
        raise ValueError(f"arquivo não encontrado: {caminho}")
    try:
        return arquivo.read_text(encoding="utf-8")
    except UnicodeDecodeError as erro:
        raise ValueError(f"não consegui ler {caminho} como UTF-8: {erro.reason}") from None


def demo() -> None:
    """Analisa um texto embutido de quatro parágrafos."""
    print("=" * 64)
    print("Contador de palavras e frequência: demonstração")
    print("=" * 64)
    print("\nTexto analisado (início):")
    print("  " + TEXTO_DEMO[:72] + "...\n")
    imprimir_relatorio(TEXTO_DEMO, top=10, ignorar_vazias=True)
    print("\nAs palavras vazias (de, a, que...) ficam de fora do ranking.")


def construir_parser() -> argparse.ArgumentParser:
    """Define a linha de comando do programa."""
    parser = argparse.ArgumentParser(
        description="Conta palavras, frases e parágrafos e lista as palavras mais frequentes.",
        epilog="Exemplo: python 14_contador_palavras.py --arquivo texto.txt --top 5",
    )
    parser.add_argument("texto", nargs="?", help="o texto entre aspas")
    parser.add_argument("--arquivo", metavar="CAMINHO", help="lê o texto de um arquivo UTF-8")
    parser.add_argument("--top", type=int, default=10,
                        help="quantas palavras listar no ranking (padrão: 10)")
    parser.add_argument("--com-vazias", action="store_true",
                        help="inclui as palavras vazias no ranking")
    parser.add_argument("--demo", action="store_true",
                        help="roda uma demonstração completa sem pedir nada")
    return parser


def main(argv: list[str] | None = None) -> int:
    """Ponto de entrada: devolve 1 quando a entrada não pode ser lida."""
    argv = sys.argv[1:] if argv is None else argv
    parser = construir_parser()
    args = parser.parse_args(argv)
    if args.demo:
        demo()
        return 0
    if args.texto is None and not args.arquivo:
        parser.print_help()
        return 0
    if args.texto is not None and args.arquivo:
        parser.error("passe o texto OU --arquivo, não os dois")
    if args.top < 1:
        parser.error("--top precisa ser pelo menos 1")
    try:
        texto = ler_arquivo(args.arquivo) if args.arquivo else args.texto
    except ValueError as erro:
        print(f"Erro: {erro}", file=sys.stderr)
        return 1
    if not texto.strip():
        print("Erro: o texto está vazio", file=sys.stderr)
        return 1
    imprimir_relatorio(texto, args.top, ignorar_vazias=not args.com_vazias)
    return 0


if __name__ == "__main__":
    sys.exit(main())

# ------------------------------------------------------------
# Para ir além
#   1. Conte bigramas (pares de palavras seguidas) e mostre os dez mais
#      comuns: eles revelam expressões, não só palavras.
#   2. Compare dois textos e liste as palavras que aparecem só em um deles.
#   3. Calcule o tempo de leitura estimado (200 palavras por minuto) e o
#      tamanho da maior frase, com um aviso quando passar de 30 palavras.
# ------------------------------------------------------------

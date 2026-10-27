#!/usr/bin/env python3
# ============================================================
# CodeNomad Academy  |  Sources Python  |  16. Palíndromos e anagramas
# ------------------------------------------------------------
# O que faz: Verifica se uma frase é palíndromo ignorando acentos, espaços,
#            maiúsculas e pontuação; verifica se duas frases são anagramas
#            uma da outra; agrupa uma lista de palavras pelos anagramas; e
#            encontra palíndromos escondidos dentro de um texto.
# Como usar: python 16_palindromo_anagrama.py palindromo "A base do teto desaba"
#            python 16_palindromo_anagrama.py anagrama "amor" "Roma"
#            python 16_palindromo_anagrama.py agrupar amor roma pedra perda gato
#            python 16_palindromo_anagrama.py --demo
# O que você aprende: normalização de texto com unicodedata, fatiamento com
#            passo negativo ([::-1]), sorted como assinatura de uma palavra,
#            defaultdict de listas, Counter e subcomandos do argparse.
# Requisitos: Python 3.10+, só biblioteca padrão
# Licença MIT. Um projeto da CodeNomad Academy (codenomad.org)
# ============================================================
import argparse
import re
import sys
import unicodedata
from collections import Counter, defaultdict

PALAVRA_RE = re.compile(r"[^\W_]+")  # letras e dígitos de qualquer idioma


def normalizar(texto: str) -> str:
    """Deixa só letras e dígitos, sem acento e em minúsculas.

    "Socorram-me, subi no ônibus" vira "socorrammesubinoonibus". NFD separa
    a letra da marca de acento, e a marca (categoria Mn) é descartada.
    """
    decomposto = unicodedata.normalize("NFD", texto)
    sem_marcas = (c for c in decomposto if unicodedata.category(c) != "Mn")
    return "".join(c for c in sem_marcas if c.isalnum()).lower()


def eh_palindromo(texto: str) -> bool:
    """Um texto é palíndromo quando lido de trás para frente dá o mesmo."""
    limpo = normalizar(texto)
    # [::-1] percorre a string com passo -1, ou seja, de trás para frente.
    return len(limpo) > 0 and limpo == limpo[::-1]


def sao_anagramas(a: str, b: str) -> bool:
    """Anagramas têm as mesmas letras na mesma quantidade, em ordem diferente."""
    limpo_a, limpo_b = normalizar(a), normalizar(b)
    if not limpo_a or not limpo_b or limpo_a == limpo_b:
        return False  # a mesma palavra não conta como anagrama dela mesma
    return Counter(limpo_a) == Counter(limpo_b)


def assinatura(palavra: str) -> str:
    """Letras em ordem alfabética: anagramas têm a mesma assinatura."""
    return "".join(sorted(normalizar(palavra)))


def agrupar_anagramas(palavras: list[str]) -> list[list[str]]:
    """Junta em uma lista as palavras que são anagramas entre si.

    Mantém a ordem de chegada e ignora repetições da mesma palavra.
    """
    grupos: defaultdict[str, list[str]] = defaultdict(list)
    vistas: set[str] = set()
    for palavra in palavras:
        chave = normalizar(palavra)
        if not chave or chave in vistas:
            continue
        vistas.add(chave)
        grupos[assinatura(palavra)].append(palavra)
    return list(grupos.values())


def palindromos_no_texto(texto: str, minimo: int = 3) -> list[str]:
    """Palavras do texto que são palíndromos e têm o tamanho mínimo pedido."""
    encontrados: list[str] = []
    for palavra in PALAVRA_RE.findall(texto):
        baixa = palavra.lower()
        if len(normalizar(baixa)) >= minimo and eh_palindromo(baixa) and baixa not in encontrados:
            encontrados.append(baixa)
    return encontrados


def imprimir_palindromo(texto: str) -> bool:
    """Imprime o veredito de uma frase e devolve o resultado."""
    resultado = eh_palindromo(texto)
    marca = "[SIM]" if resultado else "[NÃO]"
    print(f"{marca} {texto!r:<48} -> {normalizar(texto)}")
    return resultado


def imprimir_anagrama(a: str, b: str) -> bool:
    """Imprime se duas frases são anagramas e devolve o resultado."""
    resultado = sao_anagramas(a, b)
    marca = "[SIM]" if resultado else "[NÃO]"
    print(f"{marca} {a!r} e {b!r}  (letras: {assinatura(a)} / {assinatura(b)})")
    return resultado


def imprimir_grupos(palavras: list[str]) -> None:
    """Mostra os grupos de anagramas, marcando as palavras sem par."""
    for grupo in agrupar_anagramas(palavras):
        if len(grupo) > 1:
            print(f"  {assinatura(grupo[0]):<10} {', '.join(grupo)}")
        else:
            print(f"  {assinatura(grupo[0]):<10} {grupo[0]} (sem par)")


def demo() -> None:
    """Testa frases famosas, pares de palavras e agrupa uma lista."""
    print("=" * 64)
    print("Palíndromos e anagramas: demonstração")
    print("=" * 64)
    print("\nPalíndromos (acentos, espaços e pontuação são ignorados):\n")
    frases = ["Socorram-me, subi no ônibus em Marrocos", "A base do teto desaba",
              "Anotaram a data da maratona", "Roma me tem amor", "A grama é amarga",
              "Python é divertido", "12321"]
    for frase in frases:
        imprimir_palindromo(frase)

    print("\nAnagramas:\n")
    pares = [("amor", "Roma"), ("pedra", "perda"), ("alegria", "galeria"),
             ("irmã", "mira"), ("casa", "saco"), ("Python", "python")]
    for a, b in pares:
        imprimir_anagrama(a, b)

    print("\nAgrupando uma lista de palavras pela assinatura:\n")
    lista = ["amor", "Roma", "mora", "ramo", "pedra", "perda", "corpo", "porco",
             "coral", "claro", "manga", "magna", "python", "rato", "tora", "rota"]
    imprimir_grupos(lista)

    texto = "Ana e Otto levaram a arara e o radar para a sala e viram um osso."
    print(f"\nPalíndromos escondidos em: {texto!r}")
    print("  " + ", ".join(palindromos_no_texto(texto)))


def construir_parser() -> argparse.ArgumentParser:
    """Define os subcomandos palindromo, anagrama, agrupar e buscar."""
    parser = argparse.ArgumentParser(
        description="Palíndromos, anagramas e grupos de anagramas.",
        epilog="Nos subcomandos palindromo e anagrama o código de saída é 0 para sim e 1 para não.",
    )
    parser.add_argument("--demo", action="store_true",
                        help="roda uma demonstração completa sem pedir nada")
    sub = parser.add_subparsers(dest="comando", metavar="COMANDO")

    p_pal = sub.add_parser("palindromo", help="verifica se a frase é palíndromo")
    p_pal.add_argument("texto")

    p_ana = sub.add_parser("anagrama", help="verifica se duas frases são anagramas")
    p_ana.add_argument("texto_a")
    p_ana.add_argument("texto_b")

    p_agr = sub.add_parser("agrupar", help="agrupa palavras que são anagramas entre si")
    p_agr.add_argument("palavras", nargs="+")

    p_bus = sub.add_parser("buscar", help="encontra palavras palíndromas em um texto")
    p_bus.add_argument("texto")
    p_bus.add_argument("--minimo", type=int, default=3,
                       help="tamanho mínimo da palavra (padrão: 3)")
    return parser


def main(argv: list[str] | None = None) -> int:
    """Ponto de entrada: devolve 0 para sim, 1 para não e 2 para entrada ruim."""
    argv = sys.argv[1:] if argv is None else argv
    parser = construir_parser()
    args = parser.parse_args(argv)
    if args.demo:
        demo()
        return 0
    if args.comando is None:
        parser.print_help()
        return 0
    if args.comando == "palindromo":
        if not normalizar(args.texto):
            parser.error("o texto não tem letras nem dígitos")
        return 0 if imprimir_palindromo(args.texto) else 1
    if args.comando == "anagrama":
        if not normalizar(args.texto_a) or not normalizar(args.texto_b):
            parser.error("os dois textos precisam ter letras ou dígitos")
        return 0 if imprimir_anagrama(args.texto_a, args.texto_b) else 1
    if args.comando == "agrupar":
        imprimir_grupos(args.palavras)
        return 0
    if args.minimo < 1:
        parser.error("--minimo precisa ser pelo menos 1")
    achados = palindromos_no_texto(args.texto, args.minimo)
    print(", ".join(achados) if achados else "nenhum palíndromo encontrado")
    return 0


if __name__ == "__main__":
    sys.exit(main())

# ------------------------------------------------------------
# Para ir além
#   1. Encontre o maior trecho palíndromo dentro de uma string qualquer,
#      como "banana" contendo "anana".
#   2. Leia um dicionário de palavras de um arquivo (uma por linha) e
#      liste os cinco maiores grupos de anagramas.
#   3. Verifique palíndromos de datas, como 02/02/2020, e descubra a
#      próxima data palíndroma a partir de hoje com o módulo datetime.
# ------------------------------------------------------------

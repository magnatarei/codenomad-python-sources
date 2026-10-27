#!/usr/bin/env python3
# ============================================================
# CodeNomad Academy  |  Sources Python  |  20. Gerador de texto de preenchimento
# ------------------------------------------------------------
# O que faz: Gera parágrafos, frases ou palavras de texto de preenchimento
#            (o "lorem ipsum" usado em protótipos de telas e documentos),
#            em latim clássico ou em português, com quantidade à escolha,
#            largura de linha ajustável e semente para repetir o resultado.
# Como usar: python 20_gerador_lorem.py --paragrafos 3 --idioma portugues
#            python 20_gerador_lorem.py --palavras 20 --semente 7
#            python 20_gerador_lorem.py --demo
# O que você aprende: random.Random com semente, dataclasses, textwrap,
#            grupos mutuamente exclusivos do argparse, tuplas como listas
#            imutáveis e funções pequenas que se combinam.
# Requisitos: Python 3.10+, só biblioteca padrão
# Licença MIT. Um projeto da CodeNomad Academy (codenomad.org)
# ============================================================
import argparse
import random
import sys
import textwrap
from dataclasses import dataclass

FRASE_CLASSICA = "Lorem ipsum dolor sit amet, consectetur adipiscing elit."

# Vocabulários como tuplas: não mudam durante o programa.
LATIM = tuple(
    "lorem ipsum dolor sit amet consectetur adipiscing elit sed do eiusmod tempor "
    "incididunt ut labore et dolore magna aliqua enim ad minim veniam quis nostrud "
    "exercitation ullamco laboris nisi aliquip ex ea commodo consequat duis aute "
    "irure in reprehenderit voluptate velit esse cillum fugiat nulla pariatur "
    "excepteur sint occaecat cupidatat non proident sunt culpa qui officia deserunt "
    "mollit anim id est laborum vitae nunc augue mauris fermentum ornare tristique "
    "porta cursus vestibulum sagittis rhoncus fringilla ligula tellus lectus "
    "pellentesque habitant morbi senectus netus malesuada fames turpis egestas "
    "integer quam nibh euismod lacinia arcu facilisis tortor posuere ultrices "
    "viverra accumsan".split()
)
PORTUGUES = tuple(
    "casa cidade caminho janela livro escola aluno professora código função "
    "variável projeto tempo manhã tarde noite chuva sol mar montanha rio ponte "
    "mesa café pão música história memória ideia página número mês ano dia "
    "semana bairro rua praça jardim árvore flor pássaro vento nuvem estrela "
    "aprende escreve lê corre pensa cria constrói descobre pergunta responde "
    "começa termina guarda abre fecha conta mede desenha repete melhora explica "
    "entende simples claro rápido lento novo antigo pequeno grande azul verde "
    "calmo forte leve pronto aberto curioso atento útil raro comum e ou mas com "
    "sem para por entre sobre quando enquanto porque também ainda sempre nunca "
    "hoje amanhã depois antes aqui ali assim cada todo muito pouco mais menos "
    "bem já até só".split()
)
IDIOMAS = {"latim": LATIM, "portugues": PORTUGUES}


@dataclass
class Gerador:
    """Sorteia palavras de um vocabulário com um gerador próprio.

    Ter o random.Random dentro do objeto, em vez de usar o módulo random
    direto, permite repetir o mesmo texto quando a semente é a mesma.
    """

    vocabulario: tuple[str, ...]
    rng: random.Random

    def palavras(self, quantidade: int) -> list[str]:
        """Lista de palavras soltas, em minúsculas."""
        return [self.rng.choice(self.vocabulario) for _ in range(quantidade)]

    def frase(self) -> str:
        """Uma frase de 6 a 14 palavras, com vírgula nas mais longas."""
        quantidade = self.rng.randint(6, 14)
        palavras = self.palavras(quantidade)
        if quantidade >= 9:
            # Coloca a vírgula em uma palavra do meio, nunca na primeira nem na última.
            palavras[self.rng.randint(3, quantidade - 4)] += ","
        texto = " ".join(palavras)
        return texto[0].upper() + texto[1:] + "."

    def paragrafo(self, frases: int | None = None, abertura: str | None = None) -> str:
        """Um parágrafo de 3 a 6 frases; a abertura opcional entra como primeira frase."""
        quantidade = frases if frases is not None else self.rng.randint(3, 6)
        partes = [abertura] if abertura else []
        partes += [self.frase() for _ in range(quantidade - len(partes))]
        return " ".join(partes)


def criar_gerador(idioma: str, semente: int | None) -> Gerador:
    """Escolhe o vocabulário pelo nome e prepara o sorteio."""
    if idioma not in IDIOMAS:
        raise ValueError(f"idioma desconhecido: {idioma} (use {' ou '.join(IDIOMAS)})")
    return Gerador(IDIOMAS[idioma], random.Random(semente))


def gerar_paragrafos(gerador: Gerador, quantidade: int, classico: bool) -> list[str]:
    """Vários parágrafos; o primeiro pode começar com a frase clássica."""
    paragrafos = []
    for i in range(quantidade):
        abertura = FRASE_CLASSICA if classico and i == 0 else None
        paragrafos.append(gerador.paragrafo(abertura=abertura))
    return paragrafos


def formatar(paragrafos: list[str], largura: int) -> str:
    """Quebra cada parágrafo na largura pedida (0 deixa as linhas inteiras)."""
    if largura <= 0:
        return "\n\n".join(paragrafos)
    # textwrap.fill quebra só em espaços, sem partir palavras no meio.
    return "\n\n".join(textwrap.fill(p, width=largura) for p in paragrafos)


def demo() -> None:
    """Gera dois parágrafos em cada idioma e uma lista de palavras."""
    print("=" * 64)
    print("Gerador de texto de preenchimento: demonstração (semente 2024)")
    print("=" * 64)
    for idioma in IDIOMAS:
        gerador = criar_gerador(idioma, semente=2024)
        print(f"\n[{idioma}] dois parágrafos:\n")
        print(formatar(gerar_paragrafos(gerador, 2, classico=idioma == "latim"), largura=72))
    gerador = criar_gerador("portugues", semente=2024)
    print("\n[portugues] doze palavras soltas:\n")
    print("  " + ", ".join(gerador.palavras(12)))
    print("\nRode de novo com a mesma semente e o texto será idêntico.")


def construir_parser() -> argparse.ArgumentParser:
    """Define a linha de comando do programa."""
    parser = argparse.ArgumentParser(
        description="Gera texto de preenchimento em latim ou português.",
        epilog="Exemplo: python 20_gerador_lorem.py --frases 5 --idioma portugues --semente 1",
    )
    # Só uma das três quantidades pode ser escolhida por vez.
    grupo = parser.add_mutually_exclusive_group()
    grupo.add_argument("--paragrafos", type=int, metavar="N", help="quantos parágrafos gerar")
    grupo.add_argument("--frases", type=int, metavar="N", help="quantas frases gerar")
    grupo.add_argument("--palavras", type=int, metavar="N", help="quantas palavras gerar")
    parser.add_argument("--idioma", choices=list(IDIOMAS), default="latim",
                        help="vocabulário usado (padrão: latim)")
    parser.add_argument("--semente", type=int, help="semente do sorteio, para repetir o texto")
    parser.add_argument("--largura", type=int, default=72,
                        help="largura máxima da linha; 0 não quebra (padrão: 72)")
    parser.add_argument("--sem-classico", action="store_true",
                        help="não começa o latim com a frase clássica")
    parser.add_argument("--demo", action="store_true",
                        help="roda uma demonstração completa sem pedir nada")
    return parser


def main(argv: list[str] | None = None) -> int:
    """Ponto de entrada: sem argumentos mostra o uso; devolve 0 no sucesso."""
    argv = sys.argv[1:] if argv is None else argv
    parser = construir_parser()
    if not argv:
        parser.print_help()
        return 0
    args = parser.parse_args(argv)
    if args.demo:
        demo()
        return 0
    quantidades = [q for q in (args.paragrafos, args.frases, args.palavras) if q is not None]
    if quantidades and quantidades[0] < 1:
        parser.error("a quantidade precisa ser pelo menos 1")
    gerador = criar_gerador(args.idioma, args.semente)
    classico = args.idioma == "latim" and not args.sem_classico
    if args.palavras:
        print(" ".join(gerador.palavras(args.palavras)))
    elif args.frases:
        print(formatar([" ".join(gerador.frase() for _ in range(args.frases))], args.largura))
    else:
        print(formatar(gerar_paragrafos(gerador, args.paragrafos or 3, classico), args.largura))
    return 0


if __name__ == "__main__":
    sys.exit(main())

# ------------------------------------------------------------
# Para ir além
#   1. Acrescente um idioma novo com o seu próprio vocabulário e veja que
#      nada mais precisa mudar: o dicionário IDIOMAS faz o resto.
#   2. Gere também títulos e listas em Markdown, para preencher páginas
#      inteiras de documentação de exemplo.
#   3. Treine uma cadeia de Markov com um texto real (pares de palavras
#      seguidas) para gerar frases que soem mais naturais.
# ------------------------------------------------------------

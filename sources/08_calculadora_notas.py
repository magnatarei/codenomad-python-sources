#!/usr/bin/env python3
# ============================================================
# CodeNomad Academy  |  Sources Python  |  08. Calculadora de notas e média ponderada
# ------------------------------------------------------------
# O que faz: recebe notas com pesos (ex.: 7.5:2 quer dizer nota 7,5 com peso
#            2), calcula a média ponderada, diz a situação (aprovado,
#            recuperação ou reprovado) e quanto é preciso tirar na próxima
#            prova para alcançar a média de aprovação. Os limites são ajustáveis.
# Como usar: python 08_calculadora_notas.py --nota 7.5:2 --nota 6:1 --nota 8:3 --nome Ana
#            python 08_calculadora_notas.py --nota 4 --nota 5.5 --aprovacao 6 --peso-prova 2
#            python 08_calculadora_notas.py --demo
# O que você aprende: argparse com action="append" e um tipo próprio que
#            separa "nota:peso", média ponderada com sum() e expressões
#            geradoras, álgebra simples invertida em código e o uso de None
#            para dizer "não se aplica".
# Requisitos: Python 3.10+, só biblioteca padrão
# Licença MIT. Um projeto da CodeNomad Academy (codenomad.org)
# ============================================================

import argparse
import sys
from dataclasses import dataclass

NOTA_MAXIMA = 10.0


@dataclass(frozen=True)
class Nota:
    """Uma nota de 0 a 10 e o peso dela na média."""

    valor: float
    peso: float


@dataclass(frozen=True)
class Boletim:
    """O resultado de um aluno depois das contas."""

    nome: str
    media_ponderada: float
    situacao: str
    precisa_na_proxima: float | None  # None quando a aprovação já está garantida


def analisar_nota(texto: str) -> Nota:
    """Transforma '7.5:2' em Nota(7.5, 2). Sem ':' o peso é 1. Aceita vírgula."""
    valor_texto, _, peso_texto = texto.partition(":")
    try:
        valor = float(valor_texto.strip().replace(",", "."))
        peso = float(peso_texto.strip().replace(",", ".")) if peso_texto else 1.0
    except ValueError:
        raise argparse.ArgumentTypeError(f"'{texto}' não está no formato nota ou nota:peso") from None
    if not 0 <= valor <= NOTA_MAXIMA:
        raise argparse.ArgumentTypeError(f"nota {valor_texto} fora da faixa de 0 a {NOTA_MAXIMA:.0f}")
    if peso <= 0:
        raise argparse.ArgumentTypeError(f"peso {peso_texto} precisa ser maior que zero")
    return Nota(valor, peso)


def limite(texto: str) -> float:
    """Média de corte entre 0 e 10 (usada em --aprovacao e --recuperacao)."""
    try:
        valor = float(texto.strip().replace(",", "."))
    except ValueError:
        raise argparse.ArgumentTypeError(f"'{texto}' não é um número válido") from None
    if not 0 <= valor <= NOTA_MAXIMA:
        raise argparse.ArgumentTypeError(f"'{texto}' fora da faixa de 0 a {NOTA_MAXIMA:.0f}")
    return valor


def calcular_media(notas: list[Nota]) -> float:
    """Média ponderada: soma de nota vezes peso, dividida pela soma dos pesos."""
    soma_pesos = sum(nota.peso for nota in notas)
    return sum(nota.valor * nota.peso for nota in notas) / soma_pesos


def classificar(media_ponderada: float, aprovacao: float, recuperacao: float) -> str:
    """Compara a média com os dois cortes, do maior para o menor."""
    if media_ponderada >= aprovacao:
        return "Aprovado"
    if media_ponderada >= recuperacao:
        return "Recuperação"
    return "Reprovado"


def nota_necessaria(notas: list[Nota], alvo: float, peso_proxima: float) -> float:
    """Quanto tirar na próxima prova (com o peso dado) para a média chegar ao alvo.

    Queremos x tal que (S + x * p) / (P + p) >= alvo, onde S é a soma de
    nota vezes peso, P a soma dos pesos e p o peso da próxima prova.
    Isolando x: x = (alvo * (P + p) - S) / p.
    """
    soma = sum(nota.valor * nota.peso for nota in notas)
    soma_pesos = sum(nota.peso for nota in notas)
    return (alvo * (soma_pesos + peso_proxima) - soma) / peso_proxima


def montar_boletim(nome: str, notas: list[Nota], aprovacao: float, recuperacao: float,
                   peso_proxima: float) -> Boletim:
    """Faz todas as contas de um aluno e devolve o Boletim pronto para imprimir."""
    media_ponderada = calcular_media(notas)
    situacao = classificar(media_ponderada, aprovacao, recuperacao)
    precisa: float | None = None
    if media_ponderada < aprovacao:
        precisa = nota_necessaria(notas, aprovacao, peso_proxima)
    return Boletim(nome, media_ponderada, situacao, precisa)


def descrever_proxima(precisa: float | None, peso_proxima: float) -> str:
    """Frase sobre a próxima prova, cobrindo os três casos possíveis."""
    if precisa is None:
        return "aprovação já garantida com as notas atuais"
    peso_texto = f" (peso {peso_proxima:g})" if peso_proxima != 1 else ""
    precisa_texto = f"{precisa:.1f}".replace(".", ",")
    if precisa > NOTA_MAXIMA:
        return f"não alcança a média com uma prova só{peso_texto}: precisaria de {precisa_texto}"
    return f"precisa tirar pelo menos {precisa_texto} na próxima prova{peso_texto}"


def formatar_notas(notas: list[Nota]) -> str:
    """'7,5 (peso 2), 6,0 (peso 1)' para aparecer no relatório."""
    return ", ".join(f"{nota.valor:.1f} (peso {nota.peso:g})".replace(".", ",") for nota in notas)


def imprimir_boletim(boletim: Boletim, notas: list[Nota], peso_proxima: float) -> None:
    """Imprime o boletim de um aluno, linha a linha."""
    print(f"Aluno(a)      : {boletim.nome}")
    print(f"Notas         : {formatar_notas(notas)}")
    print(f"Média         : {boletim.media_ponderada:.2f}".replace(".", ","))
    print(f"Situação      : {boletim.situacao}")
    print(f"Próxima prova : {descrever_proxima(boletim.precisa_na_proxima, peso_proxima)}")


def demo() -> int:
    """Demonstração sem teclado: três alunos com pesos diferentes e uma tabela final."""
    print("=" * 72)
    print("CodeNomad Academy | Calculadora de notas e média ponderada | demonstração")
    print("=" * 72)
    aprovacao, recuperacao, peso_proxima = 7.0, 5.0, 2.0
    cortes = f"aprovação {aprovacao:.1f}, recuperação {recuperacao:.1f}".replace(".", ",")
    print(f"Cortes: {cortes}; próxima prova com peso {peso_proxima:g}\n")
    turma: list[tuple[str, list[Nota]]] = [
        ("Ana", [Nota(8.0, 1), Nota(7.5, 1), Nota(9.0, 2)]),
        ("Bruno", [Nota(5.0, 2), Nota(6.5, 1), Nota(4.0, 1)]),
        ("Carla", [Nota(3.0, 1), Nota(4.0, 1), Nota(2.5, 1)]),
    ]
    boletins: list[Boletim] = []
    for nome, notas in turma:
        boletim = montar_boletim(nome, notas, aprovacao, recuperacao, peso_proxima)
        boletins.append(boletim)
        imprimir_boletim(boletim, notas, peso_proxima)
        print()
    print(f"{'Aluno(a)':<10}{'Média':>7}  {'Situação':<13}Próxima prova")
    print("-" * 72)
    for boletim in boletins:
        media_texto = f"{boletim.media_ponderada:.2f}".replace(".", ",")
        print(f"{boletim.nome:<10}{media_texto:>7}  {boletim.situacao:<13}"
              f"{descrever_proxima(boletim.precisa_na_proxima, peso_proxima)}")
    return 0


def montar_parser() -> argparse.ArgumentParser:
    """Define os argumentos da linha de comando."""
    parser = argparse.ArgumentParser(
        description="Média ponderada, situação e nota necessária na próxima prova (CodeNomad Academy).",
        epilog="Exemplo: --nota 7.5:2 --nota 6:1 --nota 8:3 --nome Ana",
    )
    parser.add_argument("--nota", action="append", default=[], type=analisar_nota, metavar="NOTA[:PESO]",
                        help="uma nota de 0 a 10 com peso opcional; repita para cada nota")
    parser.add_argument("--nome", default="Aluno(a)", help="nome para o relatório (opcional)")
    parser.add_argument("--aprovacao", type=limite, default=7.0, help="média para aprovar (padrão 7)")
    parser.add_argument("--recuperacao", type=limite, default=5.0, help="média para recuperação (padrão 5)")
    parser.add_argument("--peso-prova", type=float, default=1.0, help="peso da próxima prova (padrão 1)")
    parser.add_argument("--demo", action="store_true", help="roda uma demonstração completa sem pedir nada")
    return parser


def main() -> None:
    """Ponto de entrada: sem argumentos mostra o uso; com --demo demonstra; senão calcula."""
    parser = montar_parser()
    if len(sys.argv) == 1:
        parser.print_help()
        return
    args = parser.parse_args()
    if args.demo:
        sys.exit(demo())
    if not args.nota:
        parser.error("informe ao menos uma --nota (ou use --demo)")
    if args.recuperacao > args.aprovacao:
        parser.error("a média de recuperação não pode ser maior que a de aprovação")
    if args.peso_prova <= 0:
        parser.error("--peso-prova precisa ser maior que zero")
    boletim = montar_boletim(args.nome, args.nota, args.aprovacao, args.recuperacao, args.peso_prova)
    imprimir_boletim(boletim, args.nota, args.peso_prova)


if __name__ == "__main__":
    main()

# ------------------------------------------------------------
# Para ir além
# 1. Leia a turma inteira de um CSV (nome;nota:peso;nota:peso;...) e imprima a tabela.
# 2. Acrescente --faltas e --limite-faltas: quem passa do limite reprova mesmo com média.
# 3. Mostre também a nota necessária para escapar da recuperação, não só para aprovar.
# ------------------------------------------------------------

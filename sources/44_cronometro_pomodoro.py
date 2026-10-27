#!/usr/bin/env python3
# ============================================================
# CodeNomad Academy  |  Sources Python  |  44. Cronômetro Pomodoro no terminal
# ------------------------------------------------------------
# O que faz: Alterna ciclos de foco e pausa com contagem regressiva na mesma
#            linha, barra de progresso, aviso sonoro ao fim de cada ciclo e
#            pausa longa a cada quatro focos. No fim (ou no Ctrl+C) mostra
#            quanto tempo de foco você acumulou.
# Como usar: python 44_cronometro_pomodoro.py --foco 25 --pausa 5 --ciclos 4
#            python 44_cronometro_pomodoro.py --foco 10 --pausa 3 --ciclos 2 --segundos
#            python 44_cronometro_pomodoro.py --demo
# O que você aprende: time.sleep e time.monotonic, print com \r e flush,
#            sys.stdout.isatty, dataclasses, datetime, KeyboardInterrupt
# Requisitos: Python 3.10+, só biblioteca padrão
# Licença MIT. Um projeto da CodeNomad Academy (codenomad.org)
# ============================================================
from __future__ import annotations

import argparse
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime

LARGURA_DA_BARRA = 24


@dataclass
class Configuracao:
    """Durações em segundos e quantidade de ciclos."""

    foco: int
    pausa: int
    pausa_longa: int
    ciclos: int
    a_cada: int = 4  # pausa longa depois de tantos focos seguidos
    pausa_apos_ultimo: bool = False  # normalmente o último foco encerra a sessão


@dataclass
class Relatorio:
    """O que aconteceu na sessão, para o resumo final."""

    inicio: datetime = field(default_factory=datetime.now)
    focos_completos: int = 0
    segundos_de_foco: int = 0
    interrompido: bool = False


def formatar(segundos: int) -> str:
    """Segundos em mm:ss, ou h:mm:ss quando passa de uma hora."""
    horas, resto = divmod(segundos, 3600)
    minutos, seg = divmod(resto, 60)
    return f"{horas}:{minutos:02d}:{seg:02d}" if horas else f"{minutos:02d}:{seg:02d}"


def barra(decorrido: int, total: int) -> str:
    """Barra de progresso em texto puro: [########........]."""
    cheios = round(LARGURA_DA_BARRA * decorrido / total) if total else LARGURA_DA_BARRA
    return "[" + "#" * cheios + "." * (LARGURA_DA_BARRA - cheios) + "]"


def contar(rotulo: str, total: int, interativo: bool) -> int:
    """Conta de total até zero, um segundo por vez. Devolve os segundos contados."""
    inicio = time.monotonic()  # relógio que nunca anda para trás, mesmo se a hora do sistema mudar
    decorrido = 0
    while decorrido < total:
        linha = f"{rotulo:<12} {barra(decorrido, total)} {formatar(total - decorrido)} restante"
        if interativo:
            print("\r" + linha, end="", flush=True)  # \r volta ao começo da mesma linha
        else:
            print(linha, flush=True)  # sem terminal (arquivo ou pipe), uma linha por segundo
        time.sleep(1)
        # Recalcular pelo relógio evita acumular o atraso do sleep ao longo de 25 minutos.
        decorrido = min(total, round(time.monotonic() - inicio))
    print(("\r" if interativo else "") + f"{rotulo:<12} {barra(total, total)} {formatar(0)} concluído", flush=True)
    return total


def avisar(mensagem: str) -> None:
    """Toca o sino do terminal (o caractere \\a) e mostra a mensagem."""
    print("\a" + mensagem, flush=True)


def rodar_sessao(config: Configuracao, interativo: bool) -> Relatorio:
    """Executa os ciclos de foco e pausa até completar ou até o usuário apertar Ctrl+C."""
    relatorio = Relatorio()
    try:
        for numero in range(1, config.ciclos + 1):
            print(f"\nCiclo {numero} de {config.ciclos}: foco por {formatar(config.foco)}")
            relatorio.segundos_de_foco += contar("Foco", config.foco, interativo)
            relatorio.focos_completos += 1
            avisar("Fim do foco! Levante, alongue, beba água.")
            if numero == config.ciclos and not config.pausa_apos_ultimo:
                break
            longa = numero % config.a_cada == 0
            rotulo = "Pausa longa" if longa else "Pausa"
            duracao = config.pausa_longa if longa else config.pausa
            print(f"{rotulo} por {formatar(duracao)}")
            contar(rotulo, duracao, interativo)
            avisar("Fim da pausa! De volta ao foco.")
    except KeyboardInterrupt:
        print("\nInterrompido pelo usuário.")
        relatorio.interrompido = True
    return relatorio


def resumo(relatorio: Relatorio) -> None:
    """Mostra o balanço da sessão."""
    fim = datetime.now()
    duracao = int((fim - relatorio.inicio).total_seconds())
    print("\nResumo da sessão")
    print(f"  início:           {relatorio.inicio:%H:%M:%S}")
    print(f"  fim:              {fim:%H:%M:%S}")
    print(f"  duração total:    {formatar(duracao)}")
    print(f"  focos completos:  {relatorio.focos_completos}")
    print(f"  tempo em foco:    {formatar(relatorio.segundos_de_foco)}")
    if relatorio.interrompido:
        print("  a sessão foi encerrada antes do fim")


def demo() -> None:
    """Um foco e uma pausa de 2 segundos cada, linha a linha, sem esperar de verdade."""
    print("=== Pomodoro: demonstração com ciclos de 2 segundos ===")
    config = Configuracao(foco=2, pausa=2, pausa_longa=2, ciclos=1, pausa_apos_ultimo=True)
    print(f"Configuração: foco {config.foco}s, pausa {config.pausa}s, {config.ciclos} ciclo")
    resumo(rodar_sessao(config, interativo=False))


def main() -> None:
    """Lê as durações, valida e roda a sessão."""
    parser = argparse.ArgumentParser(description="Cronômetro Pomodoro para o terminal.")
    parser.add_argument("--foco", type=int, default=25, help="duração do foco (padrão: 25 minutos)")
    parser.add_argument("--pausa", type=int, default=5, help="duração da pausa curta (padrão: 5)")
    parser.add_argument("--pausa-longa", type=int, default=15, help="pausa a cada 4 focos (padrão: 15)")
    parser.add_argument("--ciclos", type=int, default=4, help="quantos focos fazer (padrão: 4)")
    parser.add_argument("--segundos", action="store_true", help="interpreta as durações em segundos, não minutos")
    parser.add_argument("--demo", action="store_true", help="roda um foco e uma pausa de 2 segundos")
    args = parser.parse_args()

    if args.demo:
        demo()
        return
    if len(sys.argv) == 1:
        parser.print_help()
        return
    for nome in ("foco", "pausa", "pausa_longa", "ciclos"):
        if getattr(args, nome) <= 0:
            parser.error(f"--{nome.replace('_', '-')} precisa ser maior que zero")
    fator = 1 if args.segundos else 60
    config = Configuracao(args.foco * fator, args.pausa * fator, args.pausa_longa * fator, args.ciclos)
    # Com a saída num terminal a contagem fica na mesma linha; num arquivo, uma linha por segundo.
    interativo = sys.stdout.isatty()
    print(f"Pomodoro: {args.ciclos} ciclo(s) de {formatar(config.foco)} de foco, pausas de {formatar(config.pausa)}")
    print("Ctrl+C encerra e mostra o resumo.")
    resumo(rodar_sessao(config, interativo))


if __name__ == "__main__":
    main()

# ------------------------------------------------------------
# Para ir além
# 1. Registre cada foco concluído num arquivo CSV (data, hora, duração) e
#    mostre o total da semana com o módulo csv e datetime.
# 2. Aceite --tarefa "nome" e mostre a tarefa na linha da contagem; ao fim,
#    pergunte se ela foi concluída e guarde a resposta.
# 3. Troque o sino por uma notificação do sistema: no Linux chame
#    notify-send com subprocess; no Windows use ctypes e MessageBeep.
# ------------------------------------------------------------

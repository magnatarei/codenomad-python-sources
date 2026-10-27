#!/usr/bin/env python3
# ============================================================
# CodeNomad Academy  |  Sources Python  |  09. Calculadora de datas
# ------------------------------------------------------------
# O que faz: cinco operações com datas: dias entre duas datas, dia da
#            semana de uma data, idade exata em anos, meses e dias, somar ou
#            subtrair dias de uma data, e quantos dias faltam para uma data.
#            Aceita datas nos formatos 2026-12-25 e 25/12/2026.
# Como usar: python 09_calculadora_datas.py dias-entre 2026-01-01 25/12/2026
#            python 09_calculadora_datas.py dia-da-semana 15/11/1889
#            python 09_calculadora_datas.py idade 10/03/1990 --em 2026-10-27
#            python 09_calculadora_datas.py somar 2026-10-27 90
#            python 09_calculadora_datas.py faltam 25/12/2026
#            python 09_calculadora_datas.py --demo
# O que você aprende: argparse com subcomandos, o módulo datetime (date,
#            timedelta e strptime), calendar.monthrange e isleap, o comando
#            match do Python 3.10 e por que idade em meses não é só dividir
#            dias por 30.
# Requisitos: Python 3.10+, só biblioteca padrão
# Licença MIT. Um projeto da CodeNomad Academy (codenomad.org)
# ============================================================

import argparse
import calendar
import sys
from datetime import date, datetime, timedelta

# weekday() devolve 0 para segunda-feira e 6 para domingo: a lista segue essa ordem.
DIAS_DA_SEMANA = ["segunda-feira", "terça-feira", "quarta-feira", "quinta-feira",
                  "sexta-feira", "sábado", "domingo"]
MESES = ["janeiro", "fevereiro", "março", "abril", "maio", "junho", "julho",
         "agosto", "setembro", "outubro", "novembro", "dezembro"]
FORMATOS = ("%Y-%m-%d", "%d/%m/%Y")


def analisar_data(texto: str) -> date:
    """Tenta cada formato aceito; se nenhum servir, explica ao usuário quais são."""
    for formato in FORMATOS:
        try:
            return datetime.strptime(texto.strip(), formato).date()
        except ValueError:
            continue  # não era este formato, tenta o próximo
    raise argparse.ArgumentTypeError(f"'{texto}' não é uma data válida (use AAAA-MM-DD ou DD/MM/AAAA)")


def por_extenso(d: date) -> str:
    """'terça-feira, 27 de outubro de 2026'."""
    return f"{DIAS_DA_SEMANA[d.weekday()]}, {d.day} de {MESES[d.month - 1]} de {d.year}"


def dias_entre(inicio: date, fim: date) -> int:
    """Diferença em dias. Fica negativa quando o fim vem antes do início."""
    return (fim - inicio).days


def plural(n: int, singular: str, muitos: str) -> str:
    """'1 dia' ou '358 dias': o plural certo deixa a saída natural."""
    return f"{n} {singular if abs(n) == 1 else muitos}"


def idade_exata(nascimento: date, referencia: date) -> tuple[int, int, int]:
    """Anos, meses e dias completos entre as duas datas.

    Subtraímos campo a campo e depois "pedimos emprestado", como em uma conta
    de subtração: dias negativos tomam um mês (com o tamanho real do mês
    anterior à referência) e meses negativos tomam um ano.
    """
    anos = referencia.year - nascimento.year
    meses = referencia.month - nascimento.month
    dias = referencia.day - nascimento.day
    if dias < 0:
        meses -= 1
        ano_anterior = referencia.year if referencia.month > 1 else referencia.year - 1
        mes_anterior = referencia.month - 1 if referencia.month > 1 else 12
        dias += calendar.monthrange(ano_anterior, mes_anterior)[1]
    if meses < 0:
        anos -= 1
        meses += 12
    return anos, meses, dias


def proximo_aniversario(nascimento: date, referencia: date) -> date:
    """Primeiro aniversário igual ou depois da referência. Quem nasceu em 29/02 comemora em 28/02."""
    for ano in (referencia.year, referencia.year + 1):
        ultimo_dia = calendar.monthrange(ano, nascimento.month)[1]
        candidato = date(ano, nascimento.month, min(nascimento.day, ultimo_dia))
        if candidato >= referencia:
            return candidato
    return candidato  # nunca chega aqui: o ano seguinte sempre serve


def comando_dias_entre(inicio: date, fim: date) -> None:
    """Imprime a diferença em dias e em semanas."""
    dias = dias_entre(inicio, fim)
    semanas, resto = divmod(abs(dias), 7)
    print(f"De {por_extenso(inicio)} até {por_extenso(fim)}:")
    print(f"  {plural(dias, 'dia', 'dias')} ({plural(semanas, 'semana', 'semanas')} e {plural(resto, 'dia', 'dias')})")
    if dias < 0:
        print("  A segunda data vem antes da primeira, por isso o resultado é negativo.")


def comando_dia_da_semana(d: date) -> None:
    """Imprime o dia da semana e alguns extras do calendário."""
    bissexto = "bissexto" if calendar.isleap(d.year) else "comum"
    print(f"{d.isoformat()} é {por_extenso(d)}")
    print(f"  dia {d.timetuple().tm_yday} do ano, semana ISO {d.isocalendar()[1]}, ano {bissexto}")


def comando_idade(nascimento: date, referencia: date) -> None:
    """Imprime a idade exata, o total de dias e o próximo aniversário."""
    if nascimento > referencia:
        raise ValueError(f"a data de nascimento ({nascimento.isoformat()}) é depois da referência")
    anos, meses, dias = idade_exata(nascimento, referencia)
    proximo = proximo_aniversario(nascimento, referencia)
    print(f"Nascimento em {por_extenso(nascimento)}")
    print(f"  Em {referencia.isoformat()}: {plural(anos, 'ano', 'anos')}, {plural(meses, 'mês', 'meses')} e "
          f"{plural(dias, 'dia', 'dias')} ({dias_entre(nascimento, referencia)} dias vividos)")
    print(f"  Próximo aniversário: {por_extenso(proximo)}, daqui a {plural(dias_entre(referencia, proximo), 'dia', 'dias')}")


def comando_somar(d: date, dias: int) -> None:
    """Soma (ou subtrai, se negativo) dias e mostra a data resultante."""
    resultado = d + timedelta(days=dias)
    sinal = "mais" if dias >= 0 else "menos"
    print(f"{d.isoformat()} {sinal} {plural(abs(dias), 'dia', 'dias')} = {resultado.isoformat()} ({por_extenso(resultado)})")


def comando_faltam(alvo: date, hoje: date) -> None:
    """Quantos dias faltam para a data, ou há quantos dias ela passou."""
    dias = dias_entre(hoje, alvo)
    if dias > 0:
        verbo = "Falta" if dias == 1 else "Faltam"
        print(f"{verbo} {plural(dias, 'dia', 'dias')} para {por_extenso(alvo)} (contando a partir de {hoje.isoformat()}).")
    elif dias == 0:
        print(f"{por_extenso(alvo)} é hoje!")
    else:
        print(f"{por_extenso(alvo)} já passou há {plural(-dias, 'dia', 'dias')} (contando a partir de {hoje.isoformat()}).")


def demo() -> int:
    """Demonstração sem teclado: cada operação com datas de exemplo."""
    print("=" * 72)
    print("CodeNomad Academy | Calculadora de datas | demonstração")
    print("=" * 72)
    print("1) Dias entre duas datas")
    comando_dias_entre(date(2026, 1, 1), date(2026, 12, 25))
    print("\n2) Dia da semana")
    comando_dia_da_semana(date(1889, 11, 15))
    comando_dia_da_semana(date(2024, 2, 29))
    print("\n3) Idade exata")
    comando_idade(date(1990, 3, 10), date(2026, 10, 27))
    comando_idade(date(2000, 2, 29), date(2026, 2, 28))
    print("\n4) Somar e subtrair dias")
    comando_somar(date(2026, 10, 27), 90)
    comando_somar(date(2026, 3, 1), -1)
    print("\n5) Quantos dias faltam")
    comando_faltam(date(2026, 12, 25), date(2026, 10, 27))
    comando_faltam(date(2026, 12, 25), date.today())
    return 0


def montar_parser() -> argparse.ArgumentParser:
    """Define um subcomando para cada operação."""
    parser = argparse.ArgumentParser(description="Calculadora de datas (CodeNomad Academy).")
    parser.add_argument("--demo", action="store_true", help="roda uma demonstração completa sem pedir nada")
    sub = parser.add_subparsers(dest="comando", metavar="comando")

    p = sub.add_parser("dias-entre", help="dias entre duas datas")
    p.add_argument("inicio", type=analisar_data)
    p.add_argument("fim", type=analisar_data)

    p = sub.add_parser("dia-da-semana", help="dia da semana de uma data")
    p.add_argument("data", type=analisar_data)

    p = sub.add_parser("idade", help="idade exata em anos, meses e dias")
    p.add_argument("nascimento", type=analisar_data)
    p.add_argument("--em", type=analisar_data, default=None, help="data de referência (padrão: hoje)")

    p = sub.add_parser("somar", help="soma dias a uma data (negativo subtrai)")
    p.add_argument("data", type=analisar_data)
    p.add_argument("dias", type=int)

    p = sub.add_parser("faltam", help="quantos dias faltam para uma data")
    p.add_argument("data", type=analisar_data)
    p.add_argument("--hoje", type=analisar_data, default=None, help="data de referência (padrão: hoje)")
    return parser


def main() -> None:
    """Ponto de entrada: sem argumentos mostra o uso; --demo demonstra; senão executa o subcomando."""
    parser = montar_parser()
    if len(sys.argv) == 1:
        parser.print_help()
        return
    args = parser.parse_args()
    if args.demo:
        sys.exit(demo())
    if args.comando is None:
        parser.error("escolha um comando (dias-entre, dia-da-semana, idade, somar, faltam) ou use --demo")
    try:
        match args.comando:  # o match do Python 3.10 deixa o despacho mais legível que uma cadeia de if
            case "dias-entre":
                comando_dias_entre(args.inicio, args.fim)
            case "dia-da-semana":
                comando_dia_da_semana(args.data)
            case "idade":
                comando_idade(args.nascimento, args.em or date.today())
            case "somar":
                comando_somar(args.data, args.dias)
            case "faltam":
                comando_faltam(args.data, args.hoje or date.today())
    except OverflowError:
        print("Erro: a data resultante sai do intervalo suportado (anos 1 a 9999)", file=sys.stderr)
        sys.exit(1)
    except ValueError as erro:
        print(f"Erro: {erro}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

# ------------------------------------------------------------
# Para ir além
# 1. Acrescente o subcomando "dias-uteis", pulando sábados, domingos e uma lista de feriados.
# 2. Mostre o calendário do mês de uma data com calendar.TextCalendar.
# 3. Aceite também "hoje", "amanhã" e "ontem" como datas na entrada.
# ------------------------------------------------------------

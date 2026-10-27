#!/usr/bin/env python3
# ============================================================
# CodeNomad Academy  |  Sources Python  |  39. Diário de hábitos com sequência
# ------------------------------------------------------------
# O que faz: Registra, dia a dia, quais hábitos você cumpriu, guarda tudo
#            num arquivo JSON e calcula a sequência atual e a maior sequência
#            (recorde) de cada hábito. O resumo desenha uma grade semanal em
#            texto, com um X por dia cumprido, para as últimas N semanas.
# Como usar: python 39_diario_habitos.py marcar "Ler 20 páginas"
#            python 39_diario_habitos.py marcar "Exercício" --data 2026-10-20
#            python 39_diario_habitos.py resumo --semanas 4
#            python 39_diario_habitos.py --demo
# O que você aprende: date e timedelta (aritmética de dias, weekday),
#            conjuntos de datas, dataclasses, json com conversão de tipos,
#            laços que contam sequências e formatação de grade com ljust.
# Requisitos: Python 3.10+, só biblioteca padrão
# Licença MIT. Um projeto da CodeNomad Academy (codenomad.org)
# ============================================================
from __future__ import annotations

import argparse
import json
import sys
import tempfile
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from pathlib import Path

DIAS_DA_SEMANA = "S T Q Q S S D"  # segunda a domingo, como a grade é desenhada


class ErroDeUso(Exception):
    """Erro causado pela entrada do usuário; a mensagem é mostrada sem traceback."""


@dataclass
class Diario:
    """Para cada hábito, o conjunto de dias cumpridos. Conjunto evita marcar o mesmo dia duas vezes."""

    habitos: dict[str, set[date]] = field(default_factory=dict)


def carregar(caminho: Path) -> Diario:
    """JSON só guarda texto; cada "2026-10-05" vira um objeto date na leitura."""
    if not caminho.exists():
        return Diario()
    try:
        dados = json.loads(caminho.read_text(encoding="utf-8"))
        habitos = {nome: {date.fromisoformat(d) for d in dias} for nome, dias in dados["habitos"].items()}
    except (json.JSONDecodeError, KeyError, ValueError, AttributeError) as erro:
        raise ErroDeUso(f"não consegui ler {caminho}: {erro}") from erro
    return Diario(habitos)


def salvar(caminho: Path, diario: Diario) -> None:
    """Grava o diário em JSON: cada date vira texto ISO, em ordem."""
    dados = {"habitos": {nome: sorted(d.isoformat() for d in dias) for nome, dias in diario.habitos.items()}}
    caminho.write_text(json.dumps(dados, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def interpretar_data(texto: str | None, hoje: date) -> date:
    """Sem data, vale hoje. Não aceita futuro: ninguém cumpre um hábito amanhã."""
    if texto is None:
        return hoje
    try:
        dia = datetime.strptime(texto, "%Y-%m-%d").date()
    except ValueError as erro:
        raise ErroDeUso(f"data inválida: {texto!r} (use AAAA-MM-DD)") from erro
    if dia > hoje:
        raise ErroDeUso(f"{dia:%d/%m/%Y} ainda não chegou")
    return dia


def marcar(diario: Diario, habito: str, dia: date) -> bool:
    """Devolve True se o dia foi acrescentado, False se já estava marcado."""
    dias = diario.habitos.setdefault(habito, set())
    if dia in dias:
        return False
    dias.add(dia)
    return True


def desmarcar(diario: Diario, habito: str, dia: date) -> None:
    """Apaga um registro; erro claro se o hábito ou o dia não existem."""
    if habito not in diario.habitos:
        raise ErroDeUso(f"hábito desconhecido: {habito!r} (existem: {', '.join(sorted(diario.habitos)) or 'nenhum'})")
    if dia not in diario.habitos[habito]:
        raise ErroDeUso(f"{habito!r} não estava marcado em {dia:%d/%m/%Y}")
    diario.habitos[habito].discard(dia)


def sequencia_atual(dias: set[date], hoje: date) -> int:
    """Conta para trás a partir de hoje. Se hoje ainda não foi marcado, começa de ontem:
    o dia não acabou e a sequência não deve quebrar antes da hora."""
    atual = hoje if hoje in dias else hoje - timedelta(days=1)
    contagem = 0
    while atual in dias:
        contagem += 1
        atual -= timedelta(days=1)
    return contagem


def maior_sequencia(dias: set[date]) -> int:
    """Percorre os dias em ordem e reinicia a contagem sempre que há um buraco."""
    melhor = corrente = 0
    anterior: date | None = None
    for dia in sorted(dias):
        corrente = corrente + 1 if anterior is not None and dia - anterior == timedelta(days=1) else 1
        melhor = max(melhor, corrente)
        anterior = dia
    return melhor


def grade_semanal(diario: Diario, hoje: date, semanas: int) -> list[str]:
    """Uma linha por hábito, uma coluna por dia, agrupadas em blocos de 7 a partir da segunda-feira."""
    if not diario.habitos:
        return ["(nenhum hábito registrado ainda)"]
    # weekday() dá 0 para segunda; subtraindo, chegamos à segunda-feira da semana atual.
    inicio = hoje - timedelta(days=hoje.weekday()) - timedelta(weeks=semanas - 1)
    dias = [inicio + timedelta(days=i) for i in range(semanas * 7)]
    largura = max(len(nome) for nome in diario.habitos)
    blocos_cabecalho = [f"{dias[s * 7]:%d/%m}".ljust(13) for s in range(semanas)]
    linhas = [
        "hábito".ljust(largura) + "  " + "  ".join(blocos_cabecalho) + "  cumpriu   atual  recorde",
        " " * largura + "  " + "  ".join([DIAS_DA_SEMANA] * semanas),
    ]
    for nome in sorted(diario.habitos):
        marcados = diario.habitos[nome]
        celulas = ["X" if dia in marcados else "." for dia in dias]
        blocos = [" ".join(celulas[s * 7:(s + 1) * 7]) for s in range(semanas)]
        cumpriu = sum(1 for dia in dias if dia in marcados)
        linhas.append(f"{nome.ljust(largura)}  {'  '.join(blocos)}  {cumpriu:>3}/{len(dias):<3}  "
                      f"{sequencia_atual(marcados, hoje):>5}  {maior_sequencia(marcados):>7}")
    completos = sum(1 for dia in dias if all(dia in m for m in diario.habitos.values()))
    linhas.append(f"\nDias em que todos os hábitos foram cumpridos: {completos} de {len(dias)}")
    return linhas


def montar_parser() -> argparse.ArgumentParser:
    """Um subcomando por ação; --arquivo e --hoje valem para todos."""
    parser = argparse.ArgumentParser(description="Diário de hábitos com sequências.")
    parser.add_argument("--arquivo", default="habitos.json", help="arquivo JSON do diário")
    parser.add_argument("--hoje", help="data de referência AAAA-MM-DD (padrão: hoje)")
    parser.add_argument("--demo", action="store_true", help="roda uma demonstração completa")
    sub = parser.add_subparsers(dest="comando")
    for nome, ajuda in [("marcar", "registra o hábito como cumprido"), ("desmarcar", "apaga um registro")]:
        comando = sub.add_parser(nome, help=ajuda)
        comando.add_argument("habito")
        comando.add_argument("--data", help="dia AAAA-MM-DD (padrão: hoje)")
    sub.add_parser("listar", help="hábitos e total de dias")
    sub.add_parser("resumo", help="grade semanal").add_argument("--semanas", type=int, default=3)
    return parser


def executar(args: argparse.Namespace) -> list[str]:
    """Carrega o diário, aplica o comando, salva se algo mudou e devolve as linhas de saída."""
    # A referência pode ser qualquer dia (date.max libera o passado e o futuro); sem --hoje, é hoje mesmo.
    hoje = date.today() if args.hoje is None else interpretar_data(args.hoje, date.max)
    caminho, diario = Path(args.arquivo), carregar(Path(args.arquivo))
    if args.comando in ("marcar", "desmarcar"):
        dia = interpretar_data(args.data, hoje)
        if args.comando == "marcar":
            novo = marcar(diario, args.habito, dia)
            salvar(caminho, diario)
            situacao = "marcado" if novo else "já estava marcado"
            return [f"{args.habito}: {situacao} em {dia:%d/%m/%Y}; "
                    f"sequência atual de {sequencia_atual(diario.habitos[args.habito], hoje)} dia(s)"]
        desmarcar(diario, args.habito, dia)
        salvar(caminho, diario)
        return [f"{args.habito}: registro de {dia:%d/%m/%Y} apagado"]
    if args.comando == "listar":
        return [f"{nome}: {len(dias)} dia(s), recorde de {maior_sequencia(dias)}"
                for nome, dias in sorted(diario.habitos.items())] or ["(nenhum hábito registrado ainda)"]
    if not 1 <= args.semanas <= 12:
        raise ErroDeUso("--semanas precisa ficar entre 1 e 12")
    return grade_semanal(diario, hoje, args.semanas)


def demo() -> None:
    """Três semanas de registros fictícios num arquivo temporário, depois os comandos reais."""
    print("=== Demonstração: diário de hábitos com sequência ===")
    hoje = date(2026, 10, 25)
    diario = Diario()
    for passo in range(21):
        dia = date(2026, 10, 5) + timedelta(days=passo)
        if dia not in (date(2026, 10, 12), date(2026, 10, 24)):
            marcar(diario, "Ler 20 páginas", dia)
        if dia.weekday() in (0, 2, 4):  # segunda, quarta e sexta
            marcar(diario, "Exercício", dia)
        if dia >= date(2026, 10, 17) or 6 <= dia.day <= 8:
            marcar(diario, "Meditar", dia)
    parser = montar_parser()
    with tempfile.TemporaryDirectory() as temporaria:
        arquivo = str(Path(temporaria) / "habitos_demo.json")
        salvar(Path(arquivo), diario)
        print(f"Arquivo criado com {len(diario.habitos)} hábitos e registros de 05/10 a 25/10/2026.")
        roteiro = [["marcar", "Beber 2 L de água"], ["marcar", "Beber 2 L de água", "--data", "2026-10-24"],
                   ["marcar", "Meditar"], ["listar"], ["resumo", "--semanas", "3"],
                   ["desmarcar", "Exercício", "--data", "2026-10-25"], ["marcar", "Meditar", "--data", "2026-11-01"]]
        for comando in roteiro:
            bonito = " ".join(f'"{c}"' if " " in c else c for c in comando)
            print(f"\n$ python 39_diario_habitos.py --hoje 2026-10-25 {bonito}")
            try:
                for linha in executar(parser.parse_args(["--arquivo", arquivo, "--hoje", "2026-10-25", *comando])):
                    print(linha)
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
# 1. Permita hábitos com meta semanal (ex.: "3 vezes por semana") e mostre
#    na grade se a meta da semana foi batida.
# 2. Crie o subcomando "renomear" e o "apagar" para cuidar da lista de
#    hábitos sem editar o JSON na mão.
# 3. Exporte a grade como CSV (um dia por linha, um hábito por coluna) para
#    abrir numa planilha e montar gráficos.
# ------------------------------------------------------------

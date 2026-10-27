#!/usr/bin/env python3
# ============================================================
# CodeNomad Academy  |  Sources Python  |  31. Lista de tarefas em arquivo JSON
# ------------------------------------------------------------
# O que faz: Guarda tarefas num arquivo JSON e deixa você adicionar, listar,
#            concluir, remover e buscar pela linha de comando. Cada tarefa tem
#            prioridade (alta, normal ou baixa) e data opcional; a listagem
#            sai ordenada por prioridade e depois pela data mais próxima.
# Como usar: python 31_lista_tarefas.py adicionar "Revisar capítulo 3" --prioridade alta --data 2026-11-05
#            python 31_lista_tarefas.py listar --todas
#            python 31_lista_tarefas.py concluir 1
#            python 31_lista_tarefas.py --demo
# O que você aprende: dataclasses, json (dump e load), pathlib, argparse com
#            subcomandos, ordenação com chave composta, datetime e tratamento
#            de erros com uma exceção própria.
# Requisitos: Python 3.10+, só biblioteca padrão
# Licença MIT. Um projeto da CodeNomad Academy (codenomad.org)
# ============================================================
from __future__ import annotations

import argparse
import json
import sys
import tempfile
from dataclasses import asdict, dataclass, field
from datetime import date, datetime
from pathlib import Path

ARQUIVO_PADRAO = "tarefas.json"
# Peso menor aparece primeiro na listagem.
PESO_PRIORIDADE = {"alta": 0, "normal": 1, "baixa": 2}


class ErroDeUso(Exception):
    """Erro causado pela entrada do usuário (id inexistente, data inválida...)."""


@dataclass
class Tarefa:
    """Uma tarefa da lista. O id nunca é reaproveitado depois de uma remoção."""

    id: int
    titulo: str
    prioridade: str = "normal"
    data: str | None = None
    concluida: bool = False
    criada_em: str = field(default_factory=lambda: date.today().isoformat())


def carregar(caminho: Path) -> list[Tarefa]:
    """Lê o arquivo JSON; se ele ainda não existir, começa com a lista vazia."""
    if not caminho.exists():
        return []
    try:
        dados = json.loads(caminho.read_text(encoding="utf-8"))
    except json.JSONDecodeError as erro:
        raise ErroDeUso(f"o arquivo {caminho} não é um JSON válido: {erro}") from erro
    if not isinstance(dados, list):
        raise ErroDeUso(f"o arquivo {caminho} deveria conter uma lista de tarefas")
    # Tarefa(**item) espalha as chaves do dicionário nos campos da dataclass.
    return [Tarefa(**item) for item in dados]


def salvar(caminho: Path, tarefas: list[Tarefa]) -> None:
    """Grava a lista inteira. ensure_ascii=False mantém os acentos legíveis no arquivo."""
    conteudo = json.dumps([asdict(t) for t in tarefas], ensure_ascii=False, indent=2)
    caminho.write_text(conteudo + "\n", encoding="utf-8")


def validar_data(texto: str | None) -> str | None:
    """Aceita só o formato AAAA-MM-DD e devolve o texto normalizado."""
    if texto is None:
        return None
    try:
        return datetime.strptime(texto, "%Y-%m-%d").date().isoformat()
    except ValueError as erro:
        raise ErroDeUso(f"data inválida: {texto!r} (use AAAA-MM-DD)") from erro


def encontrar(tarefas: list[Tarefa], id_tarefa: int) -> Tarefa:
    """Devolve a tarefa com aquele id ou levanta ErroDeUso."""
    for tarefa in tarefas:
        if tarefa.id == id_tarefa:
            return tarefa
    raise ErroDeUso(f"não existe tarefa com id {id_tarefa}")


def adicionar(tarefas: list[Tarefa], titulo: str, prioridade: str, data: str | None) -> Tarefa:
    """Cria a tarefa com o próximo id livre e a coloca na lista."""
    titulo = titulo.strip()
    if not titulo:
        raise ErroDeUso("o título não pode ficar vazio")
    novo_id = max((t.id for t in tarefas), default=0) + 1
    tarefa = Tarefa(id=novo_id, titulo=titulo, prioridade=prioridade, data=validar_data(data))
    tarefas.append(tarefa)
    return tarefa


def concluir(tarefas: list[Tarefa], id_tarefa: int) -> Tarefa:
    """Marca a tarefa como concluída (uma vez só)."""
    tarefa = encontrar(tarefas, id_tarefa)
    if tarefa.concluida:
        raise ErroDeUso(f"a tarefa {id_tarefa} já estava concluída")
    tarefa.concluida = True
    return tarefa


def remover(tarefas: list[Tarefa], id_tarefa: int) -> Tarefa:
    """Tira a tarefa da lista e a devolve, para mostrar o que saiu."""
    tarefa = encontrar(tarefas, id_tarefa)
    tarefas.remove(tarefa)
    return tarefa


def buscar(tarefas: list[Tarefa], termo: str) -> list[Tarefa]:
    """Busca sem diferenciar maiúsculas: casefold é mais forte que lower."""
    termo = termo.casefold()
    return [t for t in tarefas if termo in t.titulo.casefold()]


def ordenar(tarefas: list[Tarefa]) -> list[Tarefa]:
    """Pendentes primeiro; entre elas, prioridade alta e depois a data mais próxima."""
    # Tarefa sem data vai para o fim: "9999-12-31" perde para qualquer data real.
    return sorted(tarefas, key=lambda t: (t.concluida, PESO_PRIORIDADE[t.prioridade], t.data or "9999-12-31", t.id))


def formatar(tarefa: Tarefa) -> str:
    """Uma linha alinhada por tarefa, como numa lista de papel."""
    marca = "[x]" if tarefa.concluida else "[ ]"
    data = tarefa.data or "sem data"
    return f"{marca} #{tarefa.id:<3} {tarefa.prioridade:<6} {data:<10} {tarefa.titulo}"


def listar(tarefas: list[Tarefa], todas: bool) -> list[str]:
    """Monta as linhas da listagem, escondendo as concluídas a menos que peçam todas."""
    visiveis = [t for t in ordenar(tarefas) if todas or not t.concluida]
    if not visiveis:
        return ["(nenhuma tarefa para mostrar)"]
    pendentes = sum(1 for t in tarefas if not t.concluida)
    cabecalho = f"{len(tarefas)} tarefa(s), {pendentes} pendente(s):"
    return [cabecalho] + [formatar(t) for t in visiveis]


def montar_parser() -> argparse.ArgumentParser:
    """Um subcomando por ação; cada um com os próprios argumentos."""
    parser = argparse.ArgumentParser(description="Lista de tarefas guardada em JSON.")
    parser.add_argument("--arquivo", default=ARQUIVO_PADRAO, help="arquivo JSON (padrão: tarefas.json)")
    parser.add_argument("--demo", action="store_true", help="roda uma demonstração completa")
    sub = parser.add_subparsers(dest="comando")
    novo = sub.add_parser("adicionar", help="cria uma tarefa")
    novo.add_argument("titulo")
    novo.add_argument("--prioridade", choices=list(PESO_PRIORIDADE), default="normal")
    novo.add_argument("--data", help="prazo no formato AAAA-MM-DD")
    sub.add_parser("listar", help="mostra as tarefas").add_argument("--todas", action="store_true")
    sub.add_parser("concluir", help="marca como concluída").add_argument("id", type=int)
    sub.add_parser("remover", help="apaga a tarefa").add_argument("id", type=int)
    sub.add_parser("buscar", help="procura no título").add_argument("termo")
    return parser


def executar(args: argparse.Namespace) -> list[str]:
    """Carrega o arquivo, aplica o comando, salva se algo mudou e devolve as linhas de saída."""
    caminho = Path(args.arquivo)
    tarefas = carregar(caminho)
    if args.comando == "adicionar":
        tarefa = adicionar(tarefas, args.titulo, args.prioridade, args.data)
        salvar(caminho, tarefas)
        return [f"Adicionada: {formatar(tarefa)}"]
    if args.comando == "concluir":
        tarefa = concluir(tarefas, args.id)
        salvar(caminho, tarefas)
        return [f"Concluída: {formatar(tarefa)}"]
    if args.comando == "remover":
        tarefa = remover(tarefas, args.id)
        salvar(caminho, tarefas)
        return [f"Removida: {formatar(tarefa)}"]
    if args.comando == "buscar":
        achadas = buscar(tarefas, args.termo)
        return [f"{len(achadas)} resultado(s) para {args.termo!r}:"] + [formatar(t) for t in ordenar(achadas)]
    return listar(tarefas, args.todas)


def demo() -> None:
    """Roda um roteiro completo de comandos num arquivo temporário."""
    print("=== Demonstração: lista de tarefas em JSON ===")
    roteiro = [
        ["adicionar", "Revisar capítulo 3 do curso", "--prioridade", "alta", "--data", "2026-11-05"],
        ["adicionar", "Comprar café"],
        ["adicionar", "Enviar relatório mensal", "--prioridade", "alta", "--data", "2026-11-02"],
        ["adicionar", "Organizar fotos da viagem", "--prioridade", "baixa"],
        ["listar"],
        ["concluir", "2"],
        ["buscar", "relat"],
        ["remover", "4"],
        ["listar", "--todas"],
        ["concluir", "99"],
        ["adicionar", "Data no formato errado", "--data", "05/11/2026"],
    ]
    parser = montar_parser()
    with tempfile.TemporaryDirectory() as pasta:
        arquivo = str(Path(pasta) / "tarefas_demo.json")
        for comando in roteiro:
            bonito = " ".join(f'"{c}"' if " " in c else c for c in comando)
            print(f"\n$ python 31_lista_tarefas.py {bonito}")
            args = parser.parse_args(["--arquivo", arquivo, *comando])
            try:
                for linha in executar(args):
                    print("  " + linha)
            except ErroDeUso as erro:
                print(f"  Erro: {erro}")
        print("\nConteúdo final do arquivo JSON:")
        print(Path(arquivo).read_text(encoding="utf-8"))


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
# 1. Adicione o subcomando "editar" para trocar título, prioridade ou data
#    de uma tarefa existente sem precisar removê-la.
# 2. Mostre as tarefas atrasadas (data menor que hoje) com um aviso na
#    listagem e crie o filtro --atrasadas.
# 3. Troque o JSON por sqlite3 (também da biblioteca padrão) mantendo a
#    mesma interface de linha de comando.
# ------------------------------------------------------------

#!/usr/bin/env python3
# ============================================================
# CodeNomad Academy  |  Sources Python  |  32. Agenda de contatos em CSV
# ------------------------------------------------------------
# O que faz: Mantém uma agenda num arquivo CSV com nome, telefone, e-mail e
#            etiqueta. Adiciona contatos, busca por qualquer campo, ordena,
#            exporta um filtro para outro CSV e aponta os duplicados (mesmo
#            telefone, mesmo e-mail ou mesmo nome escrito de jeitos diferentes).
# Como usar: python 32_agenda_contatos.py --arquivo agenda.csv adicionar "Ana Souza" "(11) 99999-0001" ana@exemplo.com --etiqueta trabalho
#            python 32_agenda_contatos.py --arquivo agenda.csv buscar souza
#            python 32_agenda_contatos.py --arquivo agenda.csv exportar so_trabalho.csv --etiqueta trabalho
#            python 32_agenda_contatos.py --demo
# O que você aprende: csv.DictReader e DictWriter, dataclasses, normalização
#            de texto com unicodedata (acentos e maiúsculas), sorted com key,
#            defaultdict para agrupar e argparse com subcomandos.
# Requisitos: Python 3.10+, só biblioteca padrão
# Licença MIT. Um projeto da CodeNomad Academy (codenomad.org)
# ============================================================
from __future__ import annotations

import argparse
import csv
import sys
import tempfile
import unicodedata
from collections import defaultdict
from dataclasses import asdict, dataclass
from pathlib import Path

CAMPOS = ["nome", "telefone", "email", "etiqueta"]


class ErroDeUso(Exception):
    """Erro causado pela entrada do usuário; a mensagem é mostrada sem traceback."""


@dataclass
class Contato:
    nome: str
    telefone: str
    email: str
    etiqueta: str = "geral"


def normalizar(texto: str) -> str:
    """Minúsculas, sem acento e sem espaços repetidos: "José  Lima" vira "jose lima"."""
    # NFKD separa a letra do acento; encode("ascii", "ignore") descarta o acento.
    sem_acento = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode()
    return " ".join(sem_acento.casefold().split())


def apenas_digitos(telefone: str) -> str:
    """"(11) 99999-0001" e "11999990001" são o mesmo telefone."""
    return "".join(ch for ch in telefone if ch.isdigit())


def validar(contato: Contato) -> None:
    """Regras mínimas: nome preenchido, telefone com 8+ dígitos, e-mail com @ e ponto."""
    if not contato.nome.strip():
        raise ErroDeUso("o nome não pode ficar vazio")
    if len(apenas_digitos(contato.telefone)) < 8:
        raise ErroDeUso(f"telefone inválido: {contato.telefone!r} (precisa de pelo menos 8 dígitos)")
    usuario, arroba, dominio = contato.email.partition("@")
    if not arroba or not usuario or "." not in dominio:
        raise ErroDeUso(f"e-mail inválido: {contato.email!r}")


def carregar(caminho: Path) -> list[Contato]:
    """Lê o CSV; a primeira linha precisa ter exatamente as colunas esperadas."""
    if not caminho.exists():
        return []
    # newline="" é obrigatório com o módulo csv para não duplicar quebras de linha.
    with caminho.open(encoding="utf-8", newline="") as arquivo:
        leitor = csv.DictReader(arquivo)
        if leitor.fieldnames != CAMPOS:
            raise ErroDeUso(f"colunas inesperadas em {caminho}: {leitor.fieldnames}")
        return [Contato(**linha) for linha in leitor]


def salvar(caminho: Path, contatos: list[Contato]) -> None:
    """Grava a agenda inteira no CSV, com o cabeçalho na primeira linha."""
    with caminho.open("w", encoding="utf-8", newline="") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=CAMPOS)
        escritor.writeheader()
        escritor.writerows(asdict(c) for c in contatos)


def buscar(contatos: list[Contato], termo: str) -> list[Contato]:
    """Procura o termo em qualquer campo, ignorando acentos; números batem com o telefone."""
    chave = normalizar(termo)
    digitos = apenas_digitos(termo)
    achados = []
    for c in contatos:
        campos = " ".join(normalizar(v) for v in asdict(c).values())
        if chave in campos or (digitos and digitos in apenas_digitos(c.telefone)):
            achados.append(c)
    return achados


def ordenar(contatos: list[Contato], campo: str) -> list[Contato]:
    """Ordena pelo campo pedido sem que "Álvaro" vá parar depois de "Zélia"."""
    return sorted(contatos, key=lambda c: normalizar(getattr(c, campo)))


def exportar(contatos: list[Contato], destino: Path, etiqueta: str | None, termo: str | None) -> int:
    """Grava num novo CSV só os contatos que passam nos filtros; devolve quantos foram."""
    selecionados = buscar(contatos, termo) if termo else list(contatos)
    if etiqueta:
        selecionados = [c for c in selecionados if normalizar(c.etiqueta) == normalizar(etiqueta)]
    salvar(destino, selecionados)
    return len(selecionados)


def duplicados(contatos: list[Contato]) -> list[tuple[str, list[Contato]]]:
    """Agrupa por telefone, por e-mail e por nome normalizado; devolve os grupos com 2+."""
    criterios = {
        "mesmo telefone": lambda c: apenas_digitos(c.telefone),
        "mesmo e-mail": lambda c: c.email.casefold(),
        "mesmo nome": lambda c: normalizar(c.nome),
    }
    grupos: list[tuple[str, list[Contato]]] = []
    for motivo, chave_de in criterios.items():
        por_chave: dict[str, list[Contato]] = defaultdict(list)
        for c in contatos:
            por_chave[chave_de(c)].append(c)
        grupos += [(motivo, grupo) for grupo in por_chave.values() if len(grupo) > 1]
    return grupos


def tabela(contatos: list[Contato]) -> list[str]:
    """Colunas alinhadas pela largura do maior valor de cada campo."""
    if not contatos:
        return ["(nenhum contato)"]
    larguras = {campo: max(len(campo), *(len(getattr(c, campo)) for c in contatos)) for campo in CAMPOS}
    linhas = ["  ".join(campo.ljust(larguras[campo]) for campo in CAMPOS)]
    linhas.append("  ".join("-" * larguras[campo] for campo in CAMPOS))
    for c in contatos:
        linhas.append("  ".join(getattr(c, campo).ljust(larguras[campo]) for campo in CAMPOS))
    return linhas


def montar_parser() -> argparse.ArgumentParser:
    """Um subcomando por ação; --arquivo vale para todos."""
    parser = argparse.ArgumentParser(description="Agenda de contatos guardada em CSV.")
    parser.add_argument("--arquivo", default="agenda.csv", help="arquivo CSV da agenda")
    parser.add_argument("--demo", action="store_true", help="roda uma demonstração completa")
    sub = parser.add_subparsers(dest="comando")
    novo = sub.add_parser("adicionar", help="cria um contato")
    novo.add_argument("nome")
    novo.add_argument("telefone")
    novo.add_argument("email")
    novo.add_argument("--etiqueta", default="geral")
    sub.add_parser("listar", help="mostra todos").add_argument("--ordenar-por", choices=CAMPOS, default="nome")
    sub.add_parser("buscar", help="procura em qualquer campo").add_argument("termo")
    exp = sub.add_parser("exportar", help="grava um filtro em outro CSV")
    exp.add_argument("destino")
    exp.add_argument("--etiqueta")
    exp.add_argument("--termo")
    sub.add_parser("duplicados", help="aponta contatos repetidos")
    return parser


def executar(args: argparse.Namespace) -> list[str]:
    """Carrega o CSV, aplica o comando, salva se algo mudou e devolve as linhas de saída."""
    caminho = Path(args.arquivo)
    contatos = carregar(caminho)
    if args.comando == "adicionar":
        contato = Contato(args.nome.strip(), args.telefone.strip(), args.email.strip(), args.etiqueta.strip())
        validar(contato)
        contatos.append(contato)
        salvar(caminho, contatos)
        return [f"Adicionado: {contato.nome} ({contato.etiqueta}), agora com {len(contatos)} contato(s)"]
    if args.comando == "buscar":
        achados = buscar(contatos, args.termo)
        return [f"{len(achados)} resultado(s) para {args.termo!r}:"] + tabela(achados)
    if args.comando == "exportar":
        total = exportar(contatos, Path(args.destino), args.etiqueta, args.termo)
        return [f"{total} contato(s) exportado(s) para {args.destino}"]
    if args.comando == "duplicados":
        grupos = duplicados(contatos)
        if not grupos:
            return ["Nenhum duplicado encontrado."]
        linhas = [f"{len(grupos)} grupo(s) de duplicados:"]
        for motivo, grupo in grupos:
            linhas.append(f"- {motivo}: " + " | ".join(f"{c.nome} <{c.email}>" for c in grupo))
        return linhas
    return tabela(ordenar(contatos, args.ordenar_por))


CONTATOS_EXEMPLO = [
    Contato("Ana Souza", "(11) 99999-0001", "ana.souza@exemplo.com", "trabalho"),
    Contato("Bruno Martins", "(21) 98888-0002", "bruno@exemplo.com", "amigos"),
    Contato("Carla Nogueira", "(31) 97777-0003", "carla.n@exemplo.com", "trabalho"),
    Contato("José Lima", "(41) 96666-0004", "jose.lima@exemplo.com", "família"),
    Contato("jose lima", "41966660004", "JOSE.LIMA@exemplo.com", "geral"),
    Contato("Álvaro Pires", "(51) 95555-0005", "alvaro@exemplo.com", "amigos"),
    Contato("Zélia Castro", "(61) 94444-0006", "zelia@exemplo.com", "trabalho"),
]


def demo() -> None:
    """Cria uma agenda temporária com contatos fictícios e passa por cada operação."""
    print("=== Demonstração: agenda de contatos em CSV ===")
    parser = montar_parser()
    with tempfile.TemporaryDirectory() as pasta:
        agenda = Path(pasta) / "agenda_demo.csv"
        salvar(agenda, CONTATOS_EXEMPLO)
        print(f"Agenda inicial com {len(CONTATOS_EXEMPLO)} contatos gravada em CSV.")
        roteiro = [
            ["adicionar", "Diego Ramos", "(71) 93333-0007", "diego@exemplo.com", "--etiqueta", "trabalho"],
            ["listar", "--ordenar-por", "nome"],
            ["buscar", "lima"],
            ["buscar", "9333"],
            ["exportar", str(Path(pasta) / "trabalho.csv"), "--etiqueta", "trabalho"],
            ["duplicados"],
            ["adicionar", "Sem Arroba", "(11) 91111-0000", "email-sem-arroba"],
        ]
        for comando in roteiro:
            bonito = " ".join(f'"{c}"' if " " in c else c for c in comando)
            print(f"\n$ python 32_agenda_contatos.py {bonito}")
            try:
                for linha in executar(parser.parse_args(["--arquivo", str(agenda), *comando])):
                    print("  " + linha)
            except ErroDeUso as erro:
                print(f"  Erro: {erro}")
        print("\nConteúdo de trabalho.csv:")
        print((Path(pasta) / "trabalho.csv").read_text(encoding="utf-8").strip())


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
# 1. Crie o subcomando "remover" que apaga pelo e-mail e o "editar" que
#    troca um campo de um contato existente.
# 2. Faça "duplicados --unir" juntar cada grupo num contato só, preferindo
#    o telefone formatado e a etiqueta mais específica.
# 3. Adicione o campo "aniversario" e um subcomando que liste quem faz
#    aniversário nos próximos 30 dias usando datetime.
# ------------------------------------------------------------

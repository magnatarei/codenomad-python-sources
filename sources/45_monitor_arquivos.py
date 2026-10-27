#!/usr/bin/env python3
# ============================================================
# CodeNomad Academy  |  Sources Python  |  45. Monitor de alterações numa pasta
# ------------------------------------------------------------
# O que faz: Observa uma pasta por consulta periódica (polling): tira uma
#            "foto" dos arquivos (data de modificação e tamanho), compara com
#            a foto anterior e registra, com hora, o que foi criado, alterado
#            ou removido. Aceita filtro por padrão (*.py) e subpastas.
# Como usar: python 45_monitor_arquivos.py ./projeto --intervalo 2 --recursivo --filtro "*.py"
#            python 45_monitor_arquivos.py ./downloads --ciclos 30
#            python 45_monitor_arquivos.py --demo
# O que você aprende: pathlib (glob, rglob, stat), dicionário como índice,
#            operações de conjunto para comparar estados, dataclasses, tempfile
# Requisitos: Python 3.10+, só biblioteca padrão
# Licença MIT. Um projeto da CodeNomad Academy (codenomad.org)
# ============================================================
from __future__ import annotations

import argparse
import tempfile
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

# Uma "foto" da pasta: caminho relativo -> (momento da modificação, tamanho em bytes).
Foto = dict[str, tuple[float, int]]


@dataclass(frozen=True)
class Evento:
    """Uma mudança detectada entre duas fotos."""

    tipo: str  # criado, alterado ou removido
    caminho: str
    tamanho: int
    hora: datetime

    def __str__(self) -> str:
        """Formato de uma linha de log."""
        return f"[{self.hora:%H:%M:%S}] {self.tipo.upper():<8} {self.caminho} ({self.tamanho} bytes)"


def tirar_foto(pasta: Path, padrao: str, recursivo: bool) -> Foto:
    """Lista os arquivos (não as pastas) que casam com o padrão, com data e tamanho."""
    caminhos = pasta.rglob(padrao) if recursivo else pasta.glob(padrao)
    foto: Foto = {}
    for caminho in caminhos:
        try:
            if caminho.is_file():
                info = caminho.stat()
                foto[str(caminho.relative_to(pasta))] = (info.st_mtime, info.st_size)
        except OSError:
            continue  # o arquivo sumiu entre a listagem e o stat; a próxima foto resolve
    return foto


def comparar(antes: Foto, depois: Foto) -> list[Evento]:
    """Descobre o que mudou entre duas fotos usando operações de conjunto sobre as chaves."""
    agora = datetime.now()
    eventos = [Evento("criado", c, depois[c][1], agora) for c in sorted(depois.keys() - antes.keys())]
    eventos += [Evento("removido", c, antes[c][1], agora) for c in sorted(antes.keys() - depois.keys())]
    for caminho in sorted(antes.keys() & depois.keys()):
        # Data ou tamanho diferente: o conteúdo mudou. Mesmo tamanho e mesma data passam
        # despercebidos; é o limite do polling (veja o exercício 1 no fim do arquivo).
        if antes[caminho] != depois[caminho]:
            eventos.append(Evento("alterado", caminho, depois[caminho][1], agora))
    return eventos


def monitorar(pasta: Path, intervalo: float, padrao: str, recursivo: bool, ciclos: int | None) -> int:
    """Laço principal: tira fotos a cada intervalo e imprime as diferenças. Devolve o total de eventos."""
    anterior = tirar_foto(pasta, padrao, recursivo)
    print(f"Observando {pasta.resolve()}")
    print(f"{len(anterior)} arquivo(s) no início, padrão '{padrao}', consulta a cada {intervalo:g}s. Ctrl+C para parar.",
          flush=True)
    total = 0
    feitos = 0
    try:
        while ciclos is None or feitos < ciclos:
            time.sleep(intervalo)
            atual = tirar_foto(pasta, padrao, recursivo)
            for evento in comparar(anterior, atual):
                print(evento, flush=True)
                total += 1
            anterior = atual
            feitos += 1
    except KeyboardInterrupt:
        print("\nMonitor encerrado pelo usuário.")
    return total


def demo() -> None:
    """Cria uma pasta temporária, provoca os três tipos de evento e mostra a detecção."""
    print("=== Monitor de pasta: demonstração ===")
    with tempfile.TemporaryDirectory() as temporaria:
        pasta = Path(temporaria)
        (pasta / "notas.txt").write_text("primeira versão\n", encoding="utf-8")
        foto = tirar_foto(pasta, "*", recursivo=False)
        print(f"Pasta temporária: {pasta}")
        print(f"Foto inicial: {sorted(foto)}\n")

        passos = [
            ("criar relatorio.csv",
             lambda: (pasta / "relatorio.csv").write_text("nome,nota\nAna,9\n", encoding="utf-8")),
            ("acrescentar uma linha em notas.txt",
             lambda: (pasta / "notas.txt").write_text("primeira versão\nsegunda linha\n", encoding="utf-8")),
            ("não mexer em nada", lambda: None),
            ("remover notas.txt", lambda: (pasta / "notas.txt").unlink()),
        ]
        for descricao, acao in passos:
            print(f"Ação: {descricao}")
            acao()
            nova = tirar_foto(pasta, "*", recursivo=False)
            eventos = comparar(foto, nova)
            for evento in eventos:
                print("   " + str(evento))
            if not eventos:
                print("   (nenhuma mudança detectada)")
            foto = nova
        print(f"\nFoto final: {sorted(foto)}")
    print("Pasta temporária apagada.")


def main() -> None:
    """Lê os argumentos, valida a pasta e inicia o monitor."""
    parser = argparse.ArgumentParser(description="Observa uma pasta e registra arquivos criados, alterados e removidos.")
    parser.add_argument("pasta", nargs="?", help="pasta a observar")
    parser.add_argument("--intervalo", type=float, default=1.0, help="segundos entre consultas (padrão: 1)")
    parser.add_argument("--filtro", default="*", help="padrão de nome, ex.: *.py (padrão: todos)")
    parser.add_argument("--recursivo", action="store_true", help="inclui as subpastas")
    parser.add_argument("--ciclos", type=int, help="para depois de N consultas (padrão: só com Ctrl+C)")
    parser.add_argument("--demo", action="store_true", help="demonstra numa pasta temporária e encerra")
    args = parser.parse_args()

    if args.demo:
        demo()
        return
    if not args.pasta:
        parser.print_help()
        return
    pasta = Path(args.pasta).expanduser()
    if not pasta.is_dir():
        parser.error(f"'{args.pasta}' não existe ou não é uma pasta")
    if args.intervalo <= 0:
        parser.error("--intervalo precisa ser maior que zero")
    if args.ciclos is not None and args.ciclos <= 0:
        parser.error("--ciclos precisa ser maior que zero")
    total = monitorar(pasta, args.intervalo, args.filtro, args.recursivo, args.ciclos)
    print(f"Total de eventos registrados: {total}")


if __name__ == "__main__":
    main()

# ------------------------------------------------------------
# Para ir além
# 1. Guarde na foto também o hash do conteúdo (hashlib.sha256) para pegar
#    alterações que mantêm tamanho e data; meça o custo em pastas grandes.
# 2. Grave cada evento num arquivo de log em JSON Lines (um JSON por linha)
#    com --log caminho, e escreva um segundo script que resume o log por dia.
# 3. Reaja aos eventos: com --executar "comando", rode o comando via
#    subprocess sempre que um arquivo .py for alterado (um mini "auto-reload").
# ------------------------------------------------------------

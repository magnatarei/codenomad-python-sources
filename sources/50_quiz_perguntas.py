#!/usr/bin/env python3
# ============================================================
# CodeNomad Academy  |  Sources Python  |  50. Quiz de perguntas e respostas
# ------------------------------------------------------------
# O que faz: Aplica um quiz de múltipla escolha lido de um arquivo de texto
#            simples (ou do banco embutido sobre programação), embaralha as
#            perguntas e as alternativas, pontua e, no fim, revisa as erradas
#            mostrando a resposta certa.
# Como usar: python 50_quiz_perguntas.py                      (banco embutido, interativo)
#            python 50_quiz_perguntas.py --arquivo meu_quiz.txt --quantidade 5
#            python 50_quiz_perguntas.py --modelo exemplo.txt  (grava um arquivo de exemplo)
#            python 50_quiz_perguntas.py --demo
# O que você aprende: leitura e validação de arquivo texto, dataclasses,
#            embaralhar sem perder a resposta certa, Callable, pathlib
# Requisitos: Python 3.10+, só biblioteca padrão
# Licença MIT. Um projeto da CodeNomad Academy (codenomad.org)
# ============================================================
from __future__ import annotations

import argparse
import random
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

LETRAS = "ABCDEFGH"
# O banco embutido usa o mesmo formato do arquivo: assim o mesmo código lê os dois.
BANCO_EMBUTIDO = """\
# Formato: blocos separados por linha em branco. Linhas com # são comentários.
# P: enunciado, alternativas como A) B) C) D), e R: com a letra certa.
P: Qual palavra-chave cria uma função em Python?
A) def
B) function
C) lambda
R: A

P: O que len("código") devolve?
A) 5
B) 6
C) 7
D) Um erro
R: B

P: Qual estrutura guarda pares de chave e valor?
A) list
B) tuple
C) dict
D) set
R: C

P: Qual é o resultado de 7 // 2?
A) 3.5
B) 3
C) 4
R: B

P: Como se chama o erro de acessar uma chave que não existe num dict?
A) IndexError
B) ValueError
C) KeyError
D) NameError
R: C

P: O que faz o método strip() de uma string?
A) Divide a string em palavras
B) Remove espaços das pontas
C) Troca maiúsculas por minúsculas
R: B

P: Para que serve o bloco finally?
A) Rodar só quando não houve erro
B) Rodar sempre, com ou sem erro
C) Capturar qualquer exceção
R: B

P: Qual módulo da biblioteca padrão lê argumentos da linha de comando?
A) sys.path
B) argparse
C) json
D) pathlib
R: B
"""


@dataclass
class Pergunta:
    """Enunciado, alternativas (sem a letra) e o índice da correta."""

    enunciado: str
    alternativas: list[str]
    correta: int


def interpretar_quiz(texto: str) -> list[Pergunta]:
    """Converte o texto no formato do quiz em perguntas, validando bloco a bloco."""
    perguntas: list[Pergunta] = []
    for numero, bloco in enumerate(re.split(r"\n\s*\n", texto.strip()), start=1):
        enunciado, resposta = "", ""
        letras: list[str] = []
        alternativas: list[str] = []
        for linha in bloco.splitlines():
            linha = linha.strip()
            if not linha or linha.startswith("#"):
                continue
            if linha.startswith("P:"):
                enunciado = linha[2:].strip()
            elif linha.startswith("R:"):
                resposta = linha[2:].strip().upper()
            elif len(linha) > 2 and linha[1] == ")" and linha[0].isalpha():
                letras.append(linha[0].upper())
                alternativas.append(linha[2:].strip())
            else:
                raise ValueError(f"bloco {numero}: linha não reconhecida: '{linha}'")
        if not enunciado and not alternativas:
            continue  # bloco só de comentários
        if not enunciado:
            raise ValueError(f"bloco {numero}: falta a linha 'P:' com a pergunta")
        if len(alternativas) < 2:
            raise ValueError(f"bloco {numero}: precisa de pelo menos duas alternativas, como 'A) ...' e 'B) ...'")
        if resposta not in letras:
            raise ValueError(f"bloco {numero}: a resposta 'R: {resposta}' não é uma das alternativas {letras}")
        perguntas.append(Pergunta(enunciado, alternativas, letras.index(resposta)))
    if not perguntas:
        raise ValueError("nenhuma pergunta encontrada")
    return perguntas


def embaralhar(perguntas: list[Pergunta], rng: random.Random) -> list[Pergunta]:
    """Embaralha a ordem das perguntas e das alternativas sem perder qual é a certa."""
    resultado = []
    for pergunta in rng.sample(perguntas, len(perguntas)):
        indices = list(range(len(pergunta.alternativas)))
        rng.shuffle(indices)
        novas = [pergunta.alternativas[i] for i in indices]
        # A correta tinha um índice; a nova posição dela é onde esse índice foi parar.
        resultado.append(Pergunta(pergunta.enunciado, novas, indices.index(pergunta.correta)))
    return resultado


def aplicar(perguntas: list[Pergunta],
            responder: Callable[[Pergunta], int | None]) -> list[tuple[Pergunta, int]]:
    """Mostra cada pergunta, pede a resposta e corrige na hora. None em 'responder' interrompe."""
    respostas: list[tuple[Pergunta, int]] = []  # (pergunta, índice da alternativa marcada)
    for numero, pergunta in enumerate(perguntas, start=1):
        print(f"\nPergunta {numero} de {len(perguntas)}: {pergunta.enunciado}")
        for i, alternativa in enumerate(pergunta.alternativas):
            print(f"  {LETRAS[i]}) {alternativa}")
        escolhida = responder(pergunta)
        if escolhida is None:
            print("\nQuiz interrompido.")
            break
        certa = LETRAS[pergunta.correta]
        veredito = "Certo!" if escolhida == pergunta.correta else f"Errado, a certa é {certa}."
        print(f"  Sua resposta: {LETRAS[escolhida]}. {veredito}")
        respostas.append((pergunta, escolhida))
    return respostas


def revisar(respostas: list[tuple[Pergunta, int]]) -> None:
    """Pontuação final e revisão das perguntas erradas."""
    if not respostas:
        print("Nenhuma pergunta respondida.")
        return
    erradas = [(p, e) for p, e in respostas if e != p.correta]
    acertos = len(respostas) - len(erradas)
    print(f"\nResultado: {acertos} de {len(respostas)} ({acertos / len(respostas) * 100:.0f}%)")
    if not erradas:
        print("Nenhum erro. Parabéns!")
        return
    print("\nRevisão do que você errou:")
    for pergunta, escolhida in erradas:
        print(f"  {pergunta.enunciado}")
        print(f"     você marcou: {pergunta.alternativas[escolhida]}")
        print(f"     resposta certa: {pergunta.alternativas[pergunta.correta]}")


def resposta_do_teclado(pergunta: Pergunta) -> int | None:
    """Lê uma letra válida para a pergunta; None se a entrada acabar."""
    validas = LETRAS[:len(pergunta.alternativas)]
    while True:
        try:
            texto = input(f"  Resposta ({'/'.join(validas)}): ").strip().upper()
        except (EOFError, KeyboardInterrupt):
            return None
        if len(texto) == 1 and texto in validas:
            return validas.index(texto)
        print(f"  Digite uma das letras: {', '.join(validas)}.")


def demo() -> None:
    """Responde 8 perguntas automaticamente, errando três de propósito, e mostra a revisão."""
    print("=== Quiz: demonstração com respostas automáticas ===")
    perguntas = embaralhar(interpretar_quiz(BANCO_EMBUTIDO), random.Random(50))[:8]
    erradas_de_proposito = {2, 5, 7}
    numero = 0

    def responder(pergunta: Pergunta) -> int:
        """Acerta tudo, menos nas perguntas marcadas, em que escolhe a alternativa seguinte."""
        nonlocal numero  # a função de dentro altera a variável da função de fora
        numero += 1
        if numero in erradas_de_proposito:
            return (pergunta.correta + 1) % len(pergunta.alternativas)
        return pergunta.correta

    revisar(aplicar(perguntas, responder))


def main() -> None:
    """Lê os argumentos, carrega as perguntas e aplica o quiz."""
    parser = argparse.ArgumentParser(description="Quiz de múltipla escolha a partir de um arquivo de texto.")
    parser.add_argument("--arquivo", help="arquivo de perguntas (padrão: banco embutido sobre programação)")
    parser.add_argument("--quantidade", type=int, help="quantas perguntas aplicar (padrão: todas)")
    parser.add_argument("--semente", type=int, help="semente do embaralhamento, para repetir a mesma ordem")
    parser.add_argument("--sem-embaralhar", action="store_true", help="mantém a ordem do arquivo")
    parser.add_argument("--modelo", metavar="CAMINHO", help="grava um arquivo de exemplo para você editar")
    parser.add_argument("--demo", action="store_true", help="responde automaticamente e mostra a revisão")
    args = parser.parse_args()

    if args.demo:
        demo()
        return
    if args.modelo:
        destino = Path(args.modelo)
        if destino.exists():
            sys.exit(f"Erro: '{destino}' já existe; escolha outro nome para não sobrescrever.")
        destino.write_text(BANCO_EMBUTIDO, encoding="utf-8")
        print(f"Modelo gravado em {destino}. Edite as perguntas e rode com --arquivo {destino}.")
        return
    if args.quantidade is not None and args.quantidade < 1:
        parser.error("--quantidade precisa ser pelo menos 1")
    try:
        texto = Path(args.arquivo).read_text(encoding="utf-8") if args.arquivo else BANCO_EMBUTIDO
        perguntas = interpretar_quiz(texto)
    except OSError as erro:
        motivo = "arquivo não encontrado" if isinstance(erro, FileNotFoundError) else str(erro)
        sys.exit(f"Erro ao ler '{args.arquivo}': {motivo}")
    except ValueError as erro:
        sys.exit(f"Erro no formato do quiz: {erro}")
    if not args.sem_embaralhar:
        perguntas = embaralhar(perguntas, random.Random(args.semente))
    perguntas = perguntas[:args.quantidade]
    print(f"Quiz com {len(perguntas)} pergunta(s). Responda com a letra da alternativa.")
    revisar(aplicar(perguntas, resposta_do_teclado))


if __name__ == "__main__":
    main()

# ------------------------------------------------------------
# Para ir além
# 1. Adicione um cronômetro por pergunta com time.monotonic e mostre o tempo
#    médio de resposta no resultado.
# 2. Guarde o histórico de resultados em JSON (data, acertos, total) e mostre
#    a evolução das últimas cinco tentativas.
# 3. Aceite perguntas com mais de uma resposta certa ("R: A,C") e exija que o
#    jogador marque todas: use conjuntos para comparar.
# ------------------------------------------------------------

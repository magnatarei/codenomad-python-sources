#!/usr/bin/env python3
# ============================================================
# CodeNomad Academy  |  Sources Python  |  27. Calculadora de expressões matemáticas
# ------------------------------------------------------------
# O que faz: lê uma expressão em texto com + - * / ^, parênteses e números
#            com casas decimais, respeita a precedência (algoritmo shunting-yard),
#            mostra a notação posfixa gerada e calcula o resultado, com erros
#            claros para expressão mal formada e divisão por zero.
# Como usar: python sources/27_calculadora_expressoes.py "(2 + 3) * 4 - 10 / 4"
#            python sources/27_calculadora_expressoes.py "2 ^ 3 ^ 2" --posfixa
#            python sources/27_calculadora_expressoes.py --demo
# O que você aprende: analisador léxico (tokens), pilha de operadores,
#            precedência e associatividade, exceção própria por herança,
#            isinstance, alias de tipo e o truque do menos unário.
# Requisitos: Python 3.10+, só biblioteca padrão
# Licença MIT. Um projeto da CodeNomad Academy (codenomad.org)
# ============================================================
import argparse
import math
import sys

Token = float | str  # um token é um número ou um símbolo (operador ou parêntese)

PRECEDENCIA = {"+": 1, "-": 1, "*": 2, "/": 2, "neg": 3, "^": 4}
ASSOCIA_A_DIREITA = {"^"}  # 2^3^2 = 2^(3^2); os outros associam à esquerda


class ErroExpressao(ValueError):
    """Expressão mal formada ou conta impossível, com mensagem para quem digitou."""


def tokenizar(texto: str) -> list[Token]:
    """Quebra o texto em números (float) e símbolos (str), apontando a posição dos erros."""
    tokens: list[Token] = []
    i = 0
    while i < len(texto):
        ch = texto[i]
        if ch.isspace():
            i += 1
        elif ch.isdigit() or ch == ".":
            j = i
            while j < len(texto) and (texto[j].isdigit() or texto[j] == "."):
                j += 1
            trecho = texto[i:j]
            try:
                tokens.append(float(trecho))
            except ValueError:
                raise ErroExpressao(f"número mal formado '{trecho}' na posição {i}") from None
            i = j
        elif ch in "+-*/^()":
            # menos unário: no começo, depois de outro operador ou depois de "("
            if ch == "-" and (not tokens or tokens[-1] in PRECEDENCIA or tokens[-1] == "("):
                tokens.append("neg")
            else:
                tokens.append(ch)
            i += 1
        else:
            raise ErroExpressao(f"símbolo inesperado '{ch}' na posição {i}")
    if not tokens:
        raise ErroExpressao("a expressão está vazia")
    return tokens


def sai_antes(no_topo: str, novo: str) -> bool:
    """O operador do topo sai antes do novo se tem precedência maior, ou igual e associa à esquerda."""
    if PRECEDENCIA[no_topo] > PRECEDENCIA[novo]:
        return True
    return PRECEDENCIA[no_topo] == PRECEDENCIA[novo] and novo not in ASSOCIA_A_DIREITA


def para_posfixa(tokens: list[Token]) -> list[Token]:
    """Shunting-yard: números vão direto para a saída; operadores esperam numa pilha."""
    saida: list[Token] = []
    pilha: list[str] = []
    for t in tokens:
        if isinstance(t, float):
            saida.append(t)
        elif t == "(":
            pilha.append(t)
        elif t == ")":
            while pilha and pilha[-1] != "(":
                saida.append(pilha.pop())
            if not pilha:
                raise ErroExpressao("tem um ')' sem o '(' correspondente")
            pilha.pop()  # descarta o "(" que casou
        elif t == "neg":
            pilha.append(t)  # operador que vem ANTES do número: entra sem tirar ninguém
        else:
            while pilha and pilha[-1] != "(" and sai_antes(pilha[-1], t):
                saida.append(pilha.pop())
            pilha.append(t)
    while pilha:
        op = pilha.pop()
        if op == "(":
            raise ErroExpressao("tem um '(' que nunca foi fechado")
        saida.append(op)
    return saida


def operar(a: float, op: str, b: float) -> float:
    """Aplica um operador binário, traduzindo os erros do Python em mensagens claras."""
    if op == "+":
        return a + b
    if op == "-":
        return a - b
    if op == "*":
        return a * b
    if op == "/":
        if b == 0:
            raise ErroExpressao("divisão por zero")
        return a / b
    try:
        return math.pow(a, b)  # math.pow recusa raiz de negativo e zero elevado a negativo
    except (ValueError, OverflowError):
        raise ErroExpressao(f"não dá para calcular {formatar(a)} ^ {formatar(b)}") from None


def avaliar_posfixa(posfixa: list[Token]) -> float:
    """Percorre a posfixa com uma pilha de números: cada operador consome e devolve."""
    pilha: list[float] = []
    for t in posfixa:
        if isinstance(t, float):
            pilha.append(t)
        elif t == "neg":
            if not pilha:
                raise ErroExpressao("falta um número depois do sinal de menos")
            pilha.append(-pilha.pop())
        else:
            if len(pilha) < 2:
                raise ErroExpressao(f"o operador '{t}' precisa de dois números")
            b = pilha.pop()
            a = pilha.pop()  # a ordem importa: em 10 / 2, o 10 entrou antes do 2
            pilha.append(operar(a, t, b))
    if len(pilha) != 1:
        raise ErroExpressao("sobrou número sem operador entre eles")
    return pilha[0]


def formatar(x: float) -> str:
    """Mostra 6.0 como 6 e 0.1 + 0.2 como 0.3, sem o ruído do ponto flutuante."""
    if not math.isfinite(x):
        return "infinito" if x > 0 else "-infinito"
    if x == int(x) and abs(x) < 1e15:
        return str(int(x))
    return f"{x:.10g}"


def posfixa_como_texto(posfixa: list[Token]) -> str:
    """Junta os tokens da posfixa numa linha legível."""
    return " ".join(formatar(t) if isinstance(t, float) else t for t in posfixa)


def calcular(texto: str) -> tuple[float, list[Token]]:
    """Caminho completo: texto -> tokens -> posfixa -> valor."""
    posfixa = para_posfixa(tokenizar(texto))
    return avaliar_posfixa(posfixa), posfixa


def demo() -> None:
    """Avalia cinco expressões, mostra a posfixa de uma e exibe erros tratados."""
    print("=== Calculadora de expressões: CodeNomad Academy ===\n")
    print("Cinco expressões avaliadas:")
    for exp in ["2 + 3 * 4", "(2 + 3) * 4", "2 ^ 3 ^ 2", "-3 + 10 / 4", "(1.5 + 2.5) * (4 - 1) ^ 2"]:
        valor, _ = calcular(exp)
        print(f"  {exp:<28} = {formatar(valor)}")
    exp = "(2 + 3) * 4 - 10 / 2"
    tokens = tokenizar(exp)
    posfixa = para_posfixa(tokens)
    print(f"\nPasso a passo de '{exp}':")
    print(f"  tokens : {[formatar(t) if isinstance(t, float) else t for t in tokens]}")
    print(f"  posfixa: {posfixa_como_texto(posfixa)}")
    print(f"  valor  : {formatar(avaliar_posfixa(posfixa))}")
    print("  Na posfixa não existem parênteses: a ordem dos operadores já diz quem vem antes.")
    print("\nErros tratados:")
    for exp in ["5 / (3 - 3)", "2 + * 3", "(1 + 2", "3 $ 4"]:
        try:
            calcular(exp)
        except ErroExpressao as e:
            print(f"  {exp:<14} -> {e}")


def main() -> None:
    """Lê os argumentos e decide entre a demonstração e o uso normal."""
    ap = argparse.ArgumentParser(description="Avalia expressões com + - * / ^ e parênteses.")
    ap.add_argument("expressao", nargs="?", help='a expressão entre aspas, como "(2 + 3) * 4"')
    ap.add_argument("--posfixa", action="store_true", help="mostra também a notação posfixa")
    ap.add_argument("--demo", action="store_true", help="roda a demonstração completa")
    args = ap.parse_args()
    if args.demo:
        demo()
        return
    if args.expressao is None:
        ap.print_help()
        sys.exit(2)
    try:
        valor, posfixa = calcular(args.expressao)
    except ErroExpressao as e:
        sys.exit(f"Erro: {e}")
    if args.posfixa:
        print(f"posfixa: {posfixa_como_texto(posfixa)}")
    print(formatar(valor))


if __name__ == "__main__":
    main()

# ------------------------------------------------------------
# Para ir além
# 1. Acrescente o operador % (resto) e a função raiz(x), que exige
#    reconhecer palavras no tokenizador.
# 2. Permita variáveis: "x = 3" guarda, e "x * 2" usa. Um dicionário basta.
# 3. Em vez de posfixa, monte uma árvore (cada operador com dois filhos)
#    e imprima a expressão de volta com os parênteses mínimos.
# ------------------------------------------------------------

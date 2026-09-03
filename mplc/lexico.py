"""
Entrega 1 — analise lexica.

Transformar o texto do programa numa lista de tokens.

O que voces tem que devolver: uma lista de Token. O ultimo elemento e sempre
um token FIM_ARQUIVO. A regra de posicao dele esta em CONTRATOS.md, secao 7.

Leiam antes: LINGUAGEM.md secao 2, e CONTRATOS.md secao 2.
"""
from mplc.erros import ErroMPL


class Token:
    __slots__ = ('tipo', 'lexema', 'linha', 'coluna')

    def __init__(self, tipo, lexema, linha, coluna):
        self.tipo = tipo  # 'ID', 'INTEIRO', 'MAIS', ... (a lista esta no contrato)
        self.lexema = lexema  # o texto exato como apareceu no fonte
        self.linha = linha
        self.coluna = coluna  # a coluna do PRIMEIRO caractere do token

    def __str__(self):
        # esta e a linha que o --tokens imprime; nao mexam no formato
        return f"{self.linha},{self.coluna},{self.tipo},{self.lexema}"


PALAVRAS_RESERVADAS_E_LITERAIS = {
    'funcao': 'FUNCAO',
    'retorne': 'RETORNE',
    'se': 'SE',
    'senao': 'SENAO',
    'enquanto': 'ENQUANTO',
    'escreva': 'ESCREVA',
    'inteiro': 'TIPO_INTEIRO',
    'real': 'TIPO_REAL',
    'logico': 'TIPO_LOGICO',
    'texto': 'TIPO_TEXTO',
    'vazio': 'TIPO_VAZIO',
    'verdadeiro': 'LOGICO',
    'falso': 'LOGICO',
    'e': 'E',
    'ou': 'OU',
    'nao': 'NAO',
}

OPERADORES_DE_TAMANHO_DOIS = {
    '==': 'IGUAL',
    '!=': 'DIFERENTE',
    '<=': 'MENOR_IGUAL',
    '>=': 'MAIOR_IGUAL',
}

OPERADORES_DELIMITADORES_DE_TAMANHO_UM = {
    '+': 'MAIS',
    '-': 'MENOS',
    '*': 'VEZES',
    '/': 'DIVIDE',
    '%': 'RESTO',
    '<': 'MENOR',
    '>': 'MAIOR',
    '=': 'ATRIBUI',
    '(': 'ABRE_PAR',
    ')': 'FECHA_PAR',
    '{': 'ABRE_CHAVE',
    '}': 'FECHA_CHAVE',
    ',': 'VIRGULA',
    ';': 'PONTO_VIRGULA',
}

ESCAPES_VALIDOS = {'n', 't', '"', '\\'}


def _eh_letra(c):
    return ('a' <= c <= 'z') or ('A' <= c <= 'Z') or c == '_'


def _eh_digito(c):
    return '0' <= c <= '9'


def _eh_alfanumerico(c):
    return _eh_letra(c) or _eh_digito(c)


def analisar(fonte):
    """Recebe o texto do programa. Devolve a lista de Token."""
    tokens = []
    i = 0
    n = len(fonte)
    linha = 1
    coluna = 1

    def atual(deslocamento=0):
        posicao = i + deslocamento

        if posicao >= n:
            return ''

        return fonte[posicao]

    def avancar(quantidade=1):
        nonlocal i, linha, coluna

        for _ in range(quantidade):
            c = fonte[i]
            i += 1

            if c == '\n':
                linha += 1
                coluna = 1
            else:
                coluna += 1

    def adicionar_token(tipo, lexema, linha_token=None, coluna_token=None):
        tokens.append(Token(
            tipo,
            lexema,
            linha if linha_token is None else linha_token,
            coluna if coluna_token is None else coluna_token,
        ))

    while i < n:
        c = atual()

        if c in ' \t\r\n':
            avancar()
            continue

        if c == '/' and atual(1) == '/':
            avancar(2)

            while i < n and atual() != '\n':
                avancar()

            continue

        if c == '/' and atual(1) == '*':
            l0, c0 = linha, coluna
            avancar(2)
            fechado = False

            while i < n:
                if atual() == '*' and atual(1) == '/':
                    avancar(2)
                    fechado = True
                    break

                avancar()

            if not fechado:
                raise ErroMPL('lexico', l0, c0, 'comentario de bloco nao fechado')

            continue

        if _eh_letra(c):
            l0, c0 = linha, coluna
            inicio = i

            while i < n and _eh_alfanumerico(atual()):
                avancar()

            palavra = fonte[inicio:i]
            tipo = PALAVRAS_RESERVADAS_E_LITERAIS.get(palavra, 'ID')
            adicionar_token(tipo, palavra, l0, c0)
            continue

        if _eh_digito(c):
            l0, c0 = linha, coluna
            inicio = i

            while i < n and _eh_digito(atual()):
                avancar()

            if atual() == '.':
                if not _eh_digito(atual(1)):
                    raise ErroMPL('lexico', linha, coluna,
                                  'o ponto do numero real exige digito antes e depois')

                avancar()

                while i < n and _eh_digito(atual()):
                    avancar()

                lexema = fonte[inicio:i]
                adicionar_token('REAL', lexema, l0, c0)
                continue

            lexema = fonte[inicio:i]
            adicionar_token('INTEIRO', lexema, l0, c0)
            continue

        if c == '"':
            l0, c0 = linha, coluna
            inicio = i
            avancar()
            fechado = False

            while i < n:
                cj = atual()

                if cj == '"':
                    avancar()
                    fechado = True
                    break

                if cj == '\n':
                    break

                if cj == '\\':
                    linha_barra = linha
                    coluna_barra = coluna

                    avancar()

                    if atual() not in ESCAPES_VALIDOS:
                        raise ErroMPL('lexico', linha_barra, coluna_barra,
                                      'escape desconhecido dentro de texto')

                    avancar()
                    continue

                avancar()

            if not fechado:
                raise ErroMPL('lexico', l0, c0, 'texto sem fechar na mesma linha')

            lexema = fonte[inicio:i]
            adicionar_token('TEXTO', lexema, l0, c0)
            continue

        dois = fonte[i:i + 2]

        if dois in OPERADORES_DE_TAMANHO_DOIS:
            adicionar_token(OPERADORES_DE_TAMANHO_DOIS[dois], dois)
            avancar(2)
            continue

        if c in OPERADORES_DELIMITADORES_DE_TAMANHO_UM:
            adicionar_token(OPERADORES_DELIMITADORES_DE_TAMANHO_UM[c], c)
            avancar()
            continue

        raise ErroMPL('lexico', linha, coluna, f'caractere invalido {c!r}')

    tokens.append(Token('FIM_ARQUIVO', '', linha, coluna))
    return tokens


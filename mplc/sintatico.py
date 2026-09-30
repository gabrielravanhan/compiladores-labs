"""
Entrega 2 — analise sintatica.

Transformar a lista de tokens numa arvore.

Sugestao forte: descida recursiva, uma funcao por nivel de precedencia, na
ordem da secao 3.3 da especificacao. E como voces vao enxergar a precedencia
virar formato de arvore.

Gerador de parser (ANTLR, PLY, yacc) esta proibido nesta entrega e na
anterior — o objetivo e entender, e o gerador esconde exatamente a parte
que esta sendo ensinada.

Leiam antes: LINGUAGEM.md secoes 3 a 5, e CONTRATOS.md secao 3.
"""
from mplc.erros import ErroMPL


class No:
    """Um no da arvore. O rotulo e o que sai no --ast."""

    def __init__(self, rotulo, filhos=None, linha=0, coluna=0, **extra):
        self.rotulo = rotulo      # 'binario +', 'literal inteiro 1', 'bloco', ...
        self.filhos = filhos or []
        self.linha = linha
        self.coluna = coluna
        self.extra = extra        # o que a semantica quiser pendurar depois


# Tipos que uma variavel ou parametro pode ter. 'vazio' so vale como retorno.
TIPOS_DE_DADO = {
    'TIPO_INTEIRO': 'inteiro',
    'TIPO_REAL': 'real',
    'TIPO_LOGICO': 'logico',
    'TIPO_TEXTO': 'texto',
}

TIPOS_DE_RETORNO = dict(TIPOS_DE_DADO, TIPO_VAZIO='vazio')

TIPOS_LITERAIS = {
    'INTEIRO': 'inteiro',
    'REAL': 'real',
    'LOGICO': 'logico',
    'TEXTO': 'texto',
}


def _descrever(token):
    if token.tipo == 'FIM_ARQUIVO':
        return 'o fim do arquivo'

    return f"'{token.lexema}'"


def analisar(tokens):
    """Recebe a lista de Token. Devolve a raiz da arvore (um No 'programa')."""
    i = 0

    def atual():
        return tokens[i]

    def proximo():
        # o FIM_ARQUIVO e sempre o ultimo; nunca olhamos alem dele
        return tokens[min(i + 1, len(tokens) - 1)]

    def avancar():
        nonlocal i
        token = tokens[i]

        if token.tipo != 'FIM_ARQUIVO':
            i += 1

        return token

    def erro(esperado):
        # o erro e relatado no token que apareceu, nao no fim do anterior
        token = atual()
        raise ErroMPL('sintatico', token.linha, token.coluna,
                      f'esperava {esperado}, mas apareceu {_descrever(token)}')

    def esperar(tipo, descricao):
        if atual().tipo != tipo:
            erro(descricao)

        return avancar()

    # programa = { funcao } FIM_ARQUIVO
    def programa():
        funcoes = []

        while atual().tipo != 'FIM_ARQUIVO':
            funcoes.append(funcao())

        return No('programa', funcoes, 1, 1)

    # funcao = 'funcao' tipo_retorno ID '(' [ parametro { ',' parametro } ] ')' bloco
    def funcao():
        inicio = esperar('FUNCAO', "'funcao'")

        if atual().tipo not in TIPOS_DE_RETORNO:
            erro('o tipo de retorno da funcao')

        tipo = TIPOS_DE_RETORNO[avancar().tipo]
        nome = esperar('ID', 'o nome da funcao').lexema

        abre = esperar('ABRE_PAR', "'('")
        params = []

        if atual().tipo != 'FECHA_PAR':
            params.append(parametro())

            while atual().tipo == 'VIRGULA':
                avancar()
                params.append(parametro())

        esperar('FECHA_PAR', "')'")
        corpo = bloco()

        parametros = No('parametros', params, abre.linha, abre.coluna)
        return No(f'funcao {nome} {tipo}', [parametros, corpo],
                  inicio.linha, inicio.coluna, nome=nome, tipo=tipo)

    # parametro = tipo_dado ID
    def parametro():
        if atual().tipo not in TIPOS_DE_DADO:
            erro('o tipo do parametro')

        token_tipo = avancar()
        tipo = TIPOS_DE_DADO[token_tipo.tipo]
        nome = esperar('ID', 'o nome do parametro').lexema

        return No(f'parametro {nome} {tipo}', [], token_tipo.linha, token_tipo.coluna,
                  nome=nome, tipo=tipo)

    # bloco = '{' { comando } '}'
    def bloco():
        abre = esperar('ABRE_CHAVE', "'{'")
        comandos = []

        while atual().tipo != 'FECHA_CHAVE':
            if atual().tipo == 'FIM_ARQUIVO':
                erro("'}'")

            comandos.append(comando())

        avancar()
        return No('bloco', comandos, abre.linha, abre.coluna)

    # comando = declaracao | atribuicao | chamada ';' | se | enquanto
    #         | escreva | retorne | bloco
    def comando():
        tipo = atual().tipo

        if tipo in TIPOS_DE_DADO:
            return declaracao()

        if tipo == 'SE':
            return se()

        if tipo == 'ENQUANTO':
            return enquanto()

        if tipo == 'ESCREVA':
            return escreva()

        if tipo == 'RETORNE':
            return retorne()

        if tipo == 'ABRE_CHAVE':
            return bloco()

        if tipo == 'ID':
            if proximo().tipo == 'ATRIBUI':
                return atribuicao()

            if proximo().tipo == 'ABRE_PAR':
                no = chamada()
                esperar('PONTO_VIRGULA', "';'")
                return no

            avancar()
            erro("'=' ou '(' depois do nome")

        erro('um comando')

    # declaracao = tipo_dado ID [ '=' expressao ] ';'
    def declaracao():
        token_tipo = avancar()
        tipo = TIPOS_DE_DADO[token_tipo.tipo]
        nome = esperar('ID', 'o nome da variavel').lexema
        filhos = []

        if atual().tipo == 'ATRIBUI':
            avancar()
            filhos.append(expressao())

        esperar('PONTO_VIRGULA', "';'")
        return No(f'declaracao {nome} {tipo}', filhos, token_tipo.linha, token_tipo.coluna,
                  nome=nome, tipo=tipo)

    # atribuicao = ID '=' expressao ';'
    def atribuicao():
        token_nome = avancar()
        esperar('ATRIBUI', "'='")
        valor = expressao()
        esperar('PONTO_VIRGULA', "';'")

        return No(f'atribuicao {token_nome.lexema}', [valor],
                  token_nome.linha, token_nome.coluna, nome=token_nome.lexema)

    # se = 'se' '(' expressao ')' bloco [ 'senao' bloco ]
    def se():
        inicio = avancar()
        esperar('ABRE_PAR', "'(' depois do se")
        condicao = expressao()
        esperar('FECHA_PAR', "')'")
        filhos = [condicao, bloco()]

        if atual().tipo == 'SENAO':
            avancar()
            filhos.append(bloco())

        return No('se', filhos, inicio.linha, inicio.coluna)

    # enquanto = 'enquanto' '(' expressao ')' bloco
    def enquanto():
        inicio = avancar()
        esperar('ABRE_PAR', "'(' depois do enquanto")
        condicao = expressao()
        esperar('FECHA_PAR', "')'")
        corpo = bloco()

        return No('enquanto', [condicao, corpo], inicio.linha, inicio.coluna)

    # escreva = 'escreva' '(' expressao ')' ';'
    def escreva():
        inicio = avancar()
        esperar('ABRE_PAR', "'(' depois do escreva")
        valor = expressao()
        esperar('FECHA_PAR', "')'")
        esperar('PONTO_VIRGULA', "';'")

        return No('escreva', [valor], inicio.linha, inicio.coluna)

    # retorne = 'retorne' [ expressao ] ';'
    def retorne():
        inicio = avancar()
        filhos = []

        if atual().tipo != 'PONTO_VIRGULA':
            filhos.append(expressao())

        esperar('PONTO_VIRGULA', "';'")
        return No('retorne', filhos, inicio.linha, inicio.coluna)

    # Uma funcao por nivel de precedencia (secao 3.3), do mais fraco para o
    # mais forte. Cada uma so chama a do nivel seguinte, mais forte.
    #
    # Nos binarios, o laco (e nao a recursao a direita) e o que da a
    # associatividade a esquerda: 10 - 4 - 3 vira (10 - 4) - 3.

    def novo_binario(op, esquerda, direita):
        return No(f'binario {op.lexema}', [esquerda, direita],
                  op.linha, op.coluna, op=op.lexema)

    # expressao = ou
    def expressao():
        return ou()

    # ou = e { 'ou' e }
    def ou():
        esquerda = e()

        while atual().tipo == 'OU':
            op = avancar()
            esquerda = novo_binario(op, esquerda, e())

        return esquerda

    # e = igualdade { 'e' igualdade }
    def e():
        esquerda = igualdade()

        while atual().tipo == 'E':
            op = avancar()
            esquerda = novo_binario(op, esquerda, igualdade())

        return esquerda

    # igualdade = relacional { ( '==' | '!=' ) relacional }
    def igualdade():
        esquerda = relacional()

        while atual().tipo in ('IGUAL', 'DIFERENTE'):
            op = avancar()
            esquerda = novo_binario(op, esquerda, relacional())

        return esquerda

    # relacional = aditivo { ( '<' | '<=' | '>' | '>=' ) aditivo }
    def relacional():
        esquerda = aditivo()

        while atual().tipo in ('MENOR', 'MENOR_IGUAL', 'MAIOR', 'MAIOR_IGUAL'):
            op = avancar()
            esquerda = novo_binario(op, esquerda, aditivo())

        return esquerda

    # aditivo = multiplicativo { ( '+' | '-' ) multiplicativo }
    def aditivo():
        esquerda = multiplicativo()

        while atual().tipo in ('MAIS', 'MENOS'):
            op = avancar()
            esquerda = novo_binario(op, esquerda, multiplicativo())

        return esquerda

    # multiplicativo = unario { ( '*' | '/' | '%' ) unario }
    def multiplicativo():
        esquerda = unario()

        while atual().tipo in ('VEZES', 'DIVIDE', 'RESTO'):
            op = avancar()
            esquerda = novo_binario(op, esquerda, unario())

        return esquerda

    # unario = ( 'nao' | '-' ) unario | primario
    # Aqui a recursao a direita e proposital: nao nao x vira nao (nao x).
    def unario():
        if atual().tipo in ('NAO', 'MENOS'):
            op = avancar()
            operando = unario()
            return No(f'unario {op.lexema}', [operando], op.linha, op.coluna, op=op.lexema)

        return primario()

    # primario = literal | ID | chamada | '(' expressao ')'
    def primario():
        token = atual()

        if token.tipo in TIPOS_LITERAIS:
            return literal()

        if token.tipo == 'ID':
            if proximo().tipo == 'ABRE_PAR':
                return chamada()

            avancar()
            return No(f'variavel {token.lexema}', [], token.linha, token.coluna,
                      nome=token.lexema)

        if token.tipo == 'ABRE_PAR':
            avancar()
            dentro = expressao()
            esperar('FECHA_PAR', "')'")
            return dentro

        erro('uma expressao')

    # chamada = ID '(' [ expressao { ',' expressao } ] ')'
    def chamada():
        token_nome = avancar()
        avancar()  # o '(' ja foi conferido por quem chamou
        argumentos = []

        if atual().tipo != 'FECHA_PAR':
            argumentos.append(expressao())

            while atual().tipo == 'VIRGULA':
                avancar()
                argumentos.append(expressao())

        esperar('FECHA_PAR', "')'")
        return No(f'chamada {token_nome.lexema}', argumentos,
                  token_nome.linha, token_nome.coluna, nome=token_nome.lexema)

    def literal():
        token = avancar()
        tipo = TIPOS_LITERAIS[token.tipo]

        if tipo == 'real':
            valor = f'{float(token.lexema):.6f}'
        else:
            # inteiro em digitos, logico por extenso, texto com aspas e escapes
            valor = token.lexema

        return No(f'literal {tipo} {valor}', [], token.linha, token.coluna,
                  tipo=tipo, valor=valor)

    return programa()


def despejar(no, nivel=0, saida=None):
    """Imprime a arvore no formato do --ast. Ja esta pronto: dois espacos por nivel."""
    saida = saida if saida is not None else []
    saida.append('  ' * nivel + no.rotulo)
    for f in no.filhos:
        despejar(f, nivel + 1, saida)
    return saida

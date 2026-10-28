"""
Entrega 3 — analise semantica.

Tabela de simbolos, escopos aninhados e verificacao de tipos.

Tres coisas que costumam ser esquecidas e valem nota:
  - o corpo de uma funcao abre DOIS escopos (o dos parametros e o do bloco);
  - uma funcao pode ser chamada antes de aparecer no arquivo, entao a
    primeira passada so coleta assinaturas;
  - funcao com retorno declarado precisa garantir o retorno em TODOS os
    caminhos.

Leiam antes: LINGUAGEM.md secoes 3 a 5, e CONTRATOS.md secao 4.
"""
from mplc.erros import ErroMPL


class Simbolo:
    """Uma declaracao: nome, categoria, tipo e posicao no fonte."""

    def __init__(self, no, categoria, parametros=()):
        self.nome = no.extra['nome']
        self.categoria = categoria
        self.tipo = no.extra['tipo']
        self.linha = no.linha
        self.parametros = tuple(parametros)


class Escopo:
    """Dicionario de nomes ligado ao escopo que o contem."""

    def __init__(self, numero, descricao, pai=None):
        self.numero = numero
        self.descricao = descricao
        self.pai = pai
        self.simbolos = {}  # dict preserva a ordem de declaracao

    def declarar(self, no, categoria, parametros=()):
        nome = no.extra['nome']
        if nome in self.simbolos:
            _erro(no, f"'{nome}' ja foi declarado neste escopo")
        simbolo = Simbolo(no, categoria, parametros)
        self.simbolos[nome] = simbolo
        return simbolo

    def buscar(self, no):
        nome = no.extra['nome']
        escopo = self
        while escopo is not None:
            if nome in escopo.simbolos:
                return escopo.simbolos[nome]
            escopo = escopo.pai
        _erro(no, f"nome '{nome}' nao declarado")


def _erro(no, mensagem):
    raise ErroMPL('semantico', no.linha, no.coluna, mensagem)


def _cabe(destino, origem):
    """A unica conversao implicita da MPL e inteiro para real."""
    return destino == origem or (destino == 'real' and origem == 'inteiro')


def _exigir_tipo(no, destino, origem):
    if not _cabe(destino, origem):
        _erro(no, f'esperava {destino}, mas recebeu {origem}')


def _variavel(no, escopo):
    simbolo = escopo.buscar(no)
    if simbolo.categoria == 'funcao':
        _erro(no, f"'{simbolo.nome}' e funcao, nao variavel")
    no.extra['simbolo'] = simbolo
    return simbolo


def _chamada(no, escopo):
    simbolo = escopo.buscar(no)
    if simbolo.categoria != 'funcao':
        _erro(no, f"'{simbolo.nome}' nao e uma funcao")
    if len(no.filhos) != len(simbolo.parametros):
        _erro(no, f"'{simbolo.nome}' espera {len(simbolo.parametros)} argumento(s), "
                  f'mas recebeu {len(no.filhos)}')
    for argumento, esperado in zip(no.filhos, simbolo.parametros):
        _exigir_tipo(argumento, esperado, _expressao(argumento, escopo))
    no.extra['simbolo'] = simbolo
    no.extra['tipo'] = simbolo.tipo
    return simbolo.tipo


def _tipo_binario(no, esquerda, direita):
    op = no.extra['op']
    numericos = esquerda in ('inteiro', 'real') and direita in ('inteiro', 'real')
    if op == '+' and esquerda == direita == 'texto':
        return 'texto'
    if op in ('+', '-', '*', '/') and numericos:
        return 'real' if 'real' in (esquerda, direita) else 'inteiro'
    if op == '%' and esquerda == direita == 'inteiro':
        return 'inteiro'
    if op in ('<', '<=', '>', '>=') and numericos:
        return 'logico'
    if op in ('==', '!=') and (esquerda == direita or numericos):
        return 'logico'
    if op in ('e', 'ou') and esquerda == direita == 'logico':
        return 'logico'
    _erro(no, f"operador '{op}' nao aceita {esquerda} e {direita}")


def _expressao(no, escopo):
    """Calcula tipos, sem executar a expressao nem mudar o despejo da AST."""
    especie = no.rotulo.split(' ', 1)[0]
    if especie == 'literal':
        tipo = no.extra['tipo']
    elif especie == 'variavel':
        tipo = _variavel(no, escopo).tipo
    elif especie == 'chamada':
        tipo = _chamada(no, escopo)
        if tipo == 'vazio':
            _erro(no, 'chamada de funcao vazio so pode aparecer como comando')
    elif especie == 'binario':
        esquerda = _expressao(no.filhos[0], escopo)
        direita = _expressao(no.filhos[1], escopo)
        tipo = _tipo_binario(no, esquerda, direita)
    elif especie == 'unario':
        tipo = _expressao(no.filhos[0], escopo)
        op = no.extra['op']
        if op == 'nao':
            _exigir_tipo(no, 'logico', tipo)
        elif tipo not in ('inteiro', 'real'):
            _erro(no, f"operador '-' nao aceita {tipo}")
    else:
        raise ValueError(f'no de expressao desconhecido: {no.rotulo}')
    no.extra['tipo'] = tipo
    return tipo


def analisar(arvore):
    """Percorre a arvore, monta a tabela e confere os tipos. Devolve a tabela."""
    tabela = []

    def abrir_escopo(no, descricao, pai=None):
        escopo = Escopo(len(tabela), descricao, pai)
        tabela.append(escopo)
        no.extra['escopo'] = escopo
        return escopo

    global_ = abrir_escopo(arvore, 'global')

    # Primeira passada: todas as assinaturas existem antes de analisar corpos.
    for funcao in arvore.filhos:
        parametros = [p.extra['tipo'] for p in funcao.filhos[0].filhos]
        funcao.extra['simbolo'] = global_.declarar(funcao, 'funcao', parametros)

    principal = global_.simbolos.get('principal')
    if principal is None:
        _erro(arvore, 'falta a funcao vazio principal()')
    for funcao in arvore.filhos:
        if funcao.extra['nome'] == 'principal':
            if principal.tipo != 'vazio' or principal.parametros:
                _erro(funcao, 'principal deve retornar vazio e nao receber parametros')

    def bloco(no, pai, retorno):
        escopo = abrir_escopo(no, 'bloco', pai)
        garante_retorno = False
        for filho in no.filhos:
            # Mesmo depois de retorne, conferimos tipos e registramos escopos.
            retorna = comando(filho, escopo, retorno)
            garante_retorno = garante_retorno or retorna
        return garante_retorno

    def comando(no, escopo, retorno):
        especie = no.rotulo.split(' ', 1)[0]
        if especie == 'bloco':
            return bloco(no, escopo, retorno)
        if especie == 'declaracao':
            simbolo = escopo.declarar(no, 'variavel')
            no.extra['simbolo'] = simbolo
            if no.filhos:
                _exigir_tipo(no, simbolo.tipo, _expressao(no.filhos[0], escopo))
        elif especie == 'atribuicao':
            simbolo = _variavel(no, escopo)
            _exigir_tipo(no, simbolo.tipo, _expressao(no.filhos[0], escopo))
        elif especie == 'chamada':
            _chamada(no, escopo)  # como comando, o retorno pode ser vazio
        elif especie == 'escreva':
            _expressao(no.filhos[0], escopo)
        elif especie in ('se', 'enquanto'):
            condicao = no.filhos[0]
            _exigir_tipo(condicao, 'logico', _expressao(condicao, escopo))
            retorna_entao = bloco(no.filhos[1], escopo, retorno)
            if especie == 'se' and len(no.filhos) == 3:
                retorna_senao = bloco(no.filhos[2], escopo, retorno)
                return retorna_entao and retorna_senao
            # Sem senao, ou em um laco, o corpo pode nao ser executado.
            return False
        elif especie == 'retorne':
            if retorno == 'vazio':
                if no.filhos:
                    _erro(no, 'funcao vazio exige retorne sem expressao')
            else:
                if not no.filhos:
                    _erro(no, f'retorne precisa de uma expressao do tipo {retorno}')
                _exigir_tipo(no, retorno, _expressao(no.filhos[0], escopo))
            return True
        else:
            raise ValueError(f'no de comando desconhecido: {no.rotulo}')
        return False

    # Segunda passada: parametros e bloco do corpo tem escopos distintos.
    for funcao in arvore.filhos:
        nome, tipo = funcao.extra['nome'], funcao.extra['tipo']
        escopo = abrir_escopo(funcao, f'funcao {nome}', global_)
        for parametro in funcao.filhos[0].filhos:
            parametro.extra['simbolo'] = escopo.declarar(parametro, 'parametro')
        retorna = bloco(funcao.filhos[1], escopo, tipo)
        if tipo != 'vazio' and not retorna:
            _erro(funcao, f"funcao '{nome}' nao garante retorno em todos os caminhos")
    return tabela


def despejar(tabela):
    """Devolve as linhas do --tabela, no formato da secao 4 do contrato."""
    linhas = []
    for escopo in tabela:
        cabecalho = f'escopo {escopo.numero} {escopo.descricao}'
        if escopo.pai is not None:
            cabecalho += f' pai {escopo.pai.numero}'
        linhas.append(cabecalho)
        for simbolo in escopo.simbolos.values():
            tipo = simbolo.tipo
            if simbolo.categoria == 'funcao':
                tipo += '(' + ','.join(simbolo.parametros) + ')'
            linhas.append(f'  {simbolo.nome}|{simbolo.categoria}|{tipo}|{simbolo.linha}')
    return linhas

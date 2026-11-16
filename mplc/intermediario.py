"""Entrega 4: traduz a arvore tipada para codigo de tres enderecos."""
import json
from dataclasses import dataclass, field


@dataclass
class Instrucao:
    operacao: str
    destino: str | None
    argumentos: tuple
    tipo: str | None
    linha: int
    coluna: int


@dataclass
class Funcao:
    nome: str
    retorno: str
    parametros: list
    instrucoes: list = field(default_factory=list)


PADROES = {'inteiro': 0, 'real': 0.0, 'logico': False, 'texto': ''}


class GeradorIntermediario:
    def __init__(self, tabela):
        # A identidade do simbolo distingue nomes iguais em escopos diferentes.
        self.posicoes = {}
        for escopo in tabela:
            for simbolo in escopo.simbolos.values():
                if simbolo.categoria != 'funcao':
                    self.posicoes[simbolo] = f'v{len(self.posicoes)}'
        self.proximo_temporario = 0
        self.proximo_rotulo = 0
        self.funcao = None

    def temporario(self):
        nome = f't{self.proximo_temporario}'
        self.proximo_temporario += 1
        return nome

    def rotulo(self):
        nome = f'L{self.proximo_rotulo}'
        self.proximo_rotulo += 1
        return nome

    def emitir(self, operacao, comando, destino=None, argumentos=(), tipo=None):
        self.funcao.instrucoes.append(Instrucao(
            operacao, destino, tuple(argumentos), tipo, comando.linha, comando.coluna))

    def constante(self, valor, tipo, comando):
        destino = self.temporario()
        self.emitir('constante', comando, destino, (valor,), tipo)
        return destino

    def converter(self, valor, origem, destino, comando):
        if origem == 'inteiro' and destino == 'real':
            convertido = self.temporario()
            self.emitir('converter', comando, convertido, (valor,), 'real')
            return convertido
        return valor

    def expressao(self, no, comando):
        especie = no.rotulo.split(' ', 1)[0]
        tipo = no.extra['tipo']
        if especie == 'literal':
            lexema = no.extra.get('lexema', no.extra['valor'])
            if tipo == 'inteiro':
                valor = int(lexema)
            elif tipo == 'real':
                valor = float(lexema)
            elif tipo == 'logico':
                valor = lexema == 'verdadeiro'
            else:
                valor = json.loads(lexema, strict=False)
            return self.constante(valor, tipo, comando)
        if especie == 'variavel':
            destino = self.temporario()
            origem = self.posicoes[no.extra['simbolo']]
            self.emitir('copiar', comando, destino, (origem,), tipo)
            return destino
        if especie == 'chamada':
            return self.chamada(no, comando)
        if especie == 'unario':
            valor = self.expressao(no.filhos[0], comando)
            destino = self.temporario()
            self.emitir('unario', comando, destino, (no.extra['op'], valor), tipo)
            return destino
        if especie == 'binario':
            esquerda, direita = no.filhos
            valor_esquerda = self.expressao(esquerda, comando)
            valor_direita = self.expressao(direita, comando)
            tipos = (esquerda.extra['tipo'], direita.extra['tipo'])
            if 'real' in tipos and 'inteiro' in tipos:
                valor_esquerda = self.converter(valor_esquerda, tipos[0], 'real', comando)
                valor_direita = self.converter(valor_direita, tipos[1], 'real', comando)
            destino = self.temporario()
            self.emitir('binario', comando, destino,
                        (no.extra['op'], valor_esquerda, valor_direita), tipo)
            return destino
        raise ValueError(f'expressao desconhecida: {no.rotulo}')

    def chamada(self, no, comando):
        simbolo = no.extra['simbolo']
        argumentos = []
        for argumento, esperado in zip(no.filhos, simbolo.parametros):
            valor = self.expressao(argumento, comando)
            argumentos.append(self.converter(valor, argumento.extra['tipo'], esperado, comando))
        destino = self.temporario() if simbolo.tipo != 'vazio' else None
        self.emitir('chamar', comando, destino, (simbolo.nome, *argumentos), simbolo.tipo)
        return destino

    def bloco(self, no):
        for comando in no.filhos:
            self.comando(comando)

    def comando(self, no):
        especie = no.rotulo.split(' ', 1)[0]
        if especie == 'bloco':
            self.bloco(no)
        elif especie in ('declaracao', 'atribuicao'):
            simbolo = no.extra['simbolo']
            destino = self.posicoes[simbolo]
            if especie == 'declaracao':
                # Executada a cada entrada no bloco, inclusive dentro de lacos.
                padrao = self.constante(PADROES[simbolo.tipo], simbolo.tipo, no)
                self.emitir('copiar', no, destino, (padrao,), simbolo.tipo)
            if no.filhos:
                expressao = no.filhos[0]
                valor = self.expressao(expressao, no)
                valor = self.converter(valor, expressao.extra['tipo'], simbolo.tipo, no)
                self.emitir('copiar', no, destino, (valor,), simbolo.tipo)
        elif especie == 'chamada':
            self.chamada(no, no)
        elif especie == 'escreva':
            expressao = no.filhos[0]
            valor = self.expressao(expressao, no)
            self.emitir('escrever', no, argumentos=(valor,), tipo=expressao.extra['tipo'])
        elif especie == 'retorne':
            argumentos = ()
            if no.filhos:
                expressao = no.filhos[0]
                valor = self.expressao(expressao, no)
                valor = self.converter(valor, expressao.extra['tipo'], self.funcao.retorno, no)
                argumentos = (valor,)
            self.emitir('retornar', no, argumentos=argumentos)
        elif especie == 'se':
            alternativa = self.rotulo()
            condicao = self.expressao(no.filhos[0], no)
            self.emitir('se_falso', no, argumentos=(condicao, alternativa))
            self.bloco(no.filhos[1])
            if len(no.filhos) == 3:
                fim = self.rotulo()
                self.emitir('desviar', no, argumentos=(fim,))
                self.emitir('rotulo', no, argumentos=(alternativa,))
                self.bloco(no.filhos[2])
                self.emitir('rotulo', no, argumentos=(fim,))
            else:
                self.emitir('rotulo', no, argumentos=(alternativa,))
        elif especie == 'enquanto':
            inicio, fim = self.rotulo(), self.rotulo()
            self.emitir('rotulo', no, argumentos=(inicio,))
            condicao = self.expressao(no.filhos[0], no)
            self.emitir('se_falso', no, argumentos=(condicao, fim))
            self.bloco(no.filhos[1])
            self.emitir('desviar', no, argumentos=(inicio,))
            self.emitir('rotulo', no, argumentos=(fim,))
        else:
            raise ValueError(f'comando desconhecido: {no.rotulo}')

    def gerar(self, arvore):
        funcoes = []
        for no in arvore.filhos:
            parametros = [(self.posicoes[p.extra['simbolo']], p.extra['tipo'])
                          for p in no.filhos[0].filhos]
            self.funcao = Funcao(no.extra['nome'], no.extra['tipo'], parametros)
            funcoes.append(self.funcao)
            self.bloco(no.filhos[1])
            if self.funcao.retorno == 'vazio':
                self.emitir('retornar', no)
        return funcoes


def gerar(arvore, tabela):
    """Recebe a AST anotada pela semantica e devolve as funcoes do IR."""
    return GeradorIntermediario(tabela).gerar(arvore)


def despejar(codigo):
    """Uma operacao por linha; todos os operandos calculados sao temporarios."""
    linhas = []
    for funcao in codigo:
        parametros = ', '.join(f'{nome} {tipo}' for nome, tipo in funcao.parametros)
        linhas.append(f'funcao {funcao.nome} {funcao.retorno} ({parametros})')
        for instrucao in funcao.instrucoes:
            op, destino, args = instrucao.operacao, instrucao.destino, instrucao.argumentos
            if op == 'rotulo':
                linhas.append(f'{args[0]}:')
                continue
            if op == 'constante':
                valor = json.dumps(args[0], ensure_ascii=False)
                if instrucao.tipo == 'logico':
                    valor = 'verdadeiro' if args[0] else 'falso'
                texto = f'{destino} = {valor}'
            elif op == 'copiar':
                texto = f'{destino} = {args[0]}'
            elif op == 'converter':
                texto = f'{destino} = real {args[0]}'
            elif op == 'unario':
                texto = f'{destino} = {args[0]} {args[1]}'
            elif op == 'binario':
                texto = f'{destino} = {args[1]} {args[0]} {args[2]}'
            elif op == 'chamar':
                texto = f'chama {args[0]}'
                if len(args) > 1:
                    texto += ' ' + ', '.join(args[1:])
                if destino is not None:
                    texto = f'{destino} = {texto}'
            elif op == 'escrever':
                texto = f'escreva {args[0]}'
            elif op == 'retornar':
                texto = 'retorne' + (f' {args[0]}' if args else '')
            elif op == 'desviar':
                texto = f'desvie {args[0]}'
            elif op == 'se_falso':
                texto = f'seFalso {args[0]} desvie {args[1]}'
            else:
                raise ValueError(f'operacao desconhecida: {op}')
            linhas.append('  ' + texto)
        linhas.append('fim')
    return linhas

"""Entrega 4 — maquina de pilha com um registro de ativacao por chamada."""
import json
import operator

from mplc.erros import ErroMPL


LIMITE_CHAMADAS = 1000

OPERACOES = {
    '+': operator.add,
    '-': operator.sub,
    '*': operator.mul,
    '==': operator.eq,
    '!=': operator.ne,
    '<': operator.lt,
    '<=': operator.le,
    '>': operator.gt,
    '>=': operator.ge,
    'e': operator.and_,
    'ou': operator.or_,
}


class Registro:
    """Os locais, operandos e ponto de execucao de uma chamada."""

    def __init__(self, funcao, rotulos, argumentos):
        self.codigo = funcao['codigo']
        self.retorno = funcao['retorno']
        self.rotulos = rotulos
        self.locais = dict(zip(funcao['parametros'], argumentos))
        self.pilha = []
        self.pc = 0
        self.linha = 1
        self.coluna = 1

    def erro(self, mensagem):
        raise ErroMPL('execucao', self.linha, self.coluna, mensagem)


def _binario(operador, tipo, esquerda, direita):
    if operador in ('/', '%'):
        if direita == 0:
            raise ZeroDivisionError
        if operador == '/' and tipo == 'real':
            return esquerda / direita

        # // em negativos arredonda para baixo. A MPL trunca em direcao a zero.
        quociente = abs(esquerda) // abs(direita)
        if (esquerda < 0) != (direita < 0):
            quociente = -quociente
        if operador == '%':
            return esquerda - quociente * direita
        return quociente

    return OPERACOES[operador](esquerda, direita)


def _imprimir(valor, tipo, saida):
    if tipo == 'real':
        texto = f'{valor:.6f}'
    elif tipo == 'logico':
        texto = 'verdadeiro' if valor else 'falso'
    else:
        texto = str(valor)
    saida.write(texto + '\n')


def executar(texto_mplb, saida):
    """Le o JSON do .mplb e executa principal, escrevendo somente os escreva."""
    try:
        programa = json.loads(texto_mplb)
        if programa['formato'] != 'mplb-1':
            raise ValueError('formato desconhecido')
        funcoes = programa['funcoes']
        rotulos = {}
        for nome, funcao in funcoes.items():
            rotulos[nome] = {
                instrucao[1]: posicao
                for posicao, instrucao in enumerate(funcao['codigo'])
                if instrucao[0] == 'LABEL'
            }
        principal = funcoes['principal']
        registros = [Registro(principal, rotulos['principal'], [])]
    except (KeyError, TypeError, ValueError, IndexError, AttributeError) as erro:
        raise ErroMPL('execucao', 1, 1, 'arquivo .mplb invalido') from erro

    while registros:
        atual = registros[-1]
        if atual.pc >= len(atual.codigo):
            atual.erro('funcao terminou sem instrucao RET')

        instrucao = atual.codigo[atual.pc]
        atual.pc += 1
        pilha = atual.pilha

        try:
            operacao = instrucao[0]
            if operacao == 'CONST':
                pilha.append(instrucao[1])
            elif operacao == 'LOAD':
                pilha.append(atual.locais[instrucao[1]])
            elif operacao == 'STORE':
                atual.locais[instrucao[1]] = pilha.pop()
            elif operacao == 'I2R':
                pilha.append(float(pilha.pop()))
            elif operacao == 'BIN':
                direita = pilha.pop()
                esquerda = pilha.pop()
                pilha.append(_binario(instrucao[1], instrucao[2], esquerda, direita))
            elif operacao == 'UN':
                valor = pilha.pop()
                if instrucao[1] == '-':
                    pilha.append(-valor)
                elif instrucao[1] == 'nao':
                    pilha.append(not valor)
                else:
                    atual.erro('operador unario desconhecido')
            elif operacao == 'PRINT':
                _imprimir(pilha.pop(), instrucao[1], saida)
            elif operacao == 'LABEL':
                pass
            elif operacao == 'JUMP':
                atual.pc = atual.rotulos[instrucao[1]]
            elif operacao == 'JUMP_FALSE':
                if not pilha.pop():
                    atual.pc = atual.rotulos[instrucao[1]]
            elif operacao == 'CALL':
                if len(registros) >= LIMITE_CHAMADAS:
                    atual.erro('estouro de pilha')
                nome, quantidade = instrucao[1:]
                funcao = funcoes[nome]
                if quantidade != len(funcao['parametros']):
                    atual.erro('quantidade de argumentos invalida no .mplb')
                argumentos = [pilha.pop() for _ in range(quantidade)]
                argumentos.reverse()
                registros.append(Registro(funcao, rotulos[nome], argumentos))
            elif operacao == 'RET':
                tem_valor = instrucao[1] == 1
                if tem_valor != (atual.retorno != 'vazio'):
                    atual.erro('retorno invalido no .mplb')
                valor = pilha.pop() if tem_valor else None
                registros.pop()
                if registros and tem_valor:
                    registros[-1].pilha.append(valor)
            elif operacao == 'POP':
                pilha.pop()
            elif operacao == 'LINHA':
                atual.linha, atual.coluna = instrucao[1:]
            else:
                atual.erro(f'instrucao desconhecida: {operacao}')
        except ZeroDivisionError:
            atual.erro('divisao ou resto por zero')
        except OverflowError:
            atual.erro('valor numerico fora do intervalo suportado')
        except (KeyError, IndexError, TypeError, ValueError) as erro:
            raise ErroMPL('execucao', atual.linha, atual.coluna,
                          'instrucao ou operando invalido no .mplb') from erro

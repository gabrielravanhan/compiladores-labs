"""Entrega 4: traduz o IR para instrucoes de pilha em JSON legivel."""
import json


def gerar(codigo_intermediario):
    """Devolve as linhas do .mplb, independente da AST e do arquivo fonte."""
    funcoes = {}
    for funcao in codigo_intermediario:
        codigo = []
        for instrucao in funcao.instrucoes:
            op, destino, args = instrucao.operacao, instrucao.destino, instrucao.argumentos
            # Repetir LINHA garante a posicao certa mesmo apos um desvio.
            codigo.append(['LINHA', instrucao.linha, instrucao.coluna])
            if op == 'constante':
                codigo.append(['CONST', args[0]])
                codigo.append(['STORE', destino])
            elif op == 'copiar':
                codigo.append(['LOAD', args[0]])
                codigo.append(['STORE', destino])
            elif op == 'converter':
                codigo.append(['LOAD', args[0]])
                codigo.append(['I2R'])
                codigo.append(['STORE', destino])
            elif op == 'unario':
                codigo.append(['LOAD', args[1]])
                codigo.append(['UN', args[0]])
                codigo.append(['STORE', destino])
            elif op == 'binario':
                codigo.append(['LOAD', args[1]])
                codigo.append(['LOAD', args[2]])
                codigo.append(['BIN', args[0], instrucao.tipo])
                codigo.append(['STORE', destino])
            elif op == 'chamar':
                for argumento in args[1:]:
                    codigo.append(['LOAD', argumento])
                codigo.append(['CALL', args[0], len(args) - 1])
                if destino is not None:
                    codigo.append(['STORE', destino])
            elif op == 'escrever':
                codigo.append(['LOAD', args[0]])
                codigo.append(['PRINT', instrucao.tipo])
            elif op == 'retornar':
                if args:
                    codigo.append(['LOAD', args[0]])
                codigo.append(['RET', len(args)])
            elif op == 'rotulo':
                codigo.append(['LABEL', args[0]])
            elif op == 'desviar':
                codigo.append(['JUMP', args[0]])
            elif op == 'se_falso':
                codigo.append(['LOAD', args[0]])
                codigo.append(['JUMP_FALSE', args[1]])
            else:
                raise ValueError(f'operacao intermediaria desconhecida: {op}')
        funcoes[funcao.nome] = {
            'parametros': [nome for nome, _ in funcao.parametros],
            'retorno': funcao.retorno,
            'codigo': codigo,
        }
    # Uma instrucao por linha facilita acompanhar o programa na apresentacao.
    linhas = ['{', '  "formato": "mplb-1",', '  "funcoes": {']
    for indice, (nome, funcao) in enumerate(funcoes.items()):
        linhas.append('    ' + json.dumps(nome, ensure_ascii=False) + ': {')
        linhas.append('      "parametros": ' + json.dumps(funcao['parametros']) + ',')
        linhas.append('      "retorno": ' + json.dumps(funcao['retorno']) + ',')
        linhas.append('      "codigo": [')
        for numero, instrucao in enumerate(funcao['codigo']):
            virgula = ',' if numero + 1 < len(funcao['codigo']) else ''
            linhas.append('        ' + json.dumps(instrucao, ensure_ascii=False) + virgula)
        linhas.append('      ]')
        linhas.append('    }' + (',' if indice + 1 < len(funcoes) else ''))
    linhas.extend(['  }', '}'])
    return linhas

"""Casos complementares da E3; so usa unittest, da biblioteca padrao.

Execute: python -m unittest discover -s testes -p "test_*.py" -v
"""
import unittest

from mplc import lexico, sintatico, semantica
from mplc.erros import ErroMPL
from mplc.principal import compilar_ate


def analisar(fonte):
    arvore = sintatico.analisar(lexico.analisar(fonte))
    tabela = semantica.analisar(arvore)
    return arvore, tabela


def programa(comandos):
    return 'funcao vazio principal() {\n' + comandos + '\n}'


class SemanticaTest(unittest.TestCase):
    def recusa(self, fonte, linha=None):
        with self.assertRaises(ErroMPL) as contexto:
            analisar(fonte)
        erro = contexto.exception
        self.assertEqual(erro.fase, 'semantico')
        self.assertGreaterEqual(erro.coluna, 1)
        if linha is not None:
            self.assertEqual(erro.linha, linha)

    def test_escopos_vazios_e_ordem(self):
        _, tabela = analisar(programa('se (verdadeiro) {} senao {} enquanto (falso) {}'))
        self.assertEqual(semantica.despejar(tabela), [
            'escopo 0 global', '  principal|funcao|vazio()|1',
            'escopo 1 funcao principal pai 0', 'escopo 2 bloco pai 1',
            'escopo 3 bloco pai 2', 'escopo 4 bloco pai 2', 'escopo 5 bloco pai 2',
        ])

    def test_sombreamento_e_retorno_ao_escopo_externo(self):
        analisar('funcao inteiro f(inteiro x) { texto x = "local"; '
                 '{ logico x = verdadeiro; escreva(nao x); } '
                 'escreva(x + "!"); retorne 1; }\n' + programa('f(2);'))
        analisar(programa('inteiro x = 1; { texto x = "a"; escreva(x + "b"); } x = x + 1;'))

    def test_nomes_fora_de_escopo_ou_antes_da_declaracao(self):
        for comandos in ('escreva(x); inteiro x;', 'x = 1; inteiro x;',
                         '{ inteiro x; } escreva(x);',
                         '{ inteiro x; } { escreva(x); }'):
            with self.subTest(comandos=comandos):
                self.recusa(programa(comandos), 2)
        self.recusa('funcao vazio f() { inteiro x; }\n' + programa('escreva(x);'), 3)

    def test_redeclaracoes(self):
        self.recusa('funcao vazio f() {}\nfuncao vazio f() {}\n' + programa(''), 2)
        self.recusa('funcao vazio f(inteiro x, real x) {}\n' + programa(''), 1)
        self.recusa(programa('inteiro x;\nreal x;'), 3)

    def test_principal(self):
        for fonte in ('', 'funcao vazio outra() {}',
                      'funcao inteiro principal() { retorne 1; }',
                      'funcao vazio principal(inteiro x) {}'):
            with self.subTest(fonte=fonte):
                self.recusa(fonte, 1)

    def test_chamadas_e_conversoes(self):
        analisar(programa('real x = f(2); x = 3; f(4); nada();') +
                 '\nfuncao real f(real x) { retorne 1; }\nfuncao vazio nada() { retorne; }')
        for chamada in ('f();', 'f(1, 2);', 'f(1.5);', 'f(verdadeiro);', 'f("a");'):
            with self.subTest(chamada=chamada):
                self.recusa('funcao inteiro f(inteiro x) { retorne x; }\n' + programa(chamada), 3)

    def test_vazio_so_como_comando(self):
        prefixo = 'funcao vazio nada() {}\nfuncao vazio f(inteiro x) {}\n'
        for comandos in ('escreva(nada());', 'inteiro x = nada();',
                         'escreva(nada() == nada());', 'f(nada());'):
            with self.subTest(comandos=comandos):
                self.recusa(prefixo + programa(comandos), 4)

    def test_categoria_do_nome(self):
        for comandos in ('inteiro x; x();', 'principal = 1;', 'escreva(principal);'):
            with self.subTest(comandos=comandos):
                self.recusa(programa(comandos), 2)

    def test_tipos_de_atribuicoes(self):
        valores = {'inteiro': '1', 'real': '1.5', 'logico': 'verdadeiro', 'texto': '"a"'}
        for destino in valores:
            for origem, valor in valores.items():
                for comandos in (f'{destino} x = {valor};', f'{destino} x; x = {valor};'):
                    with self.subTest(comandos=comandos):
                        if destino == origem or (destino, origem) == ('real', 'inteiro'):
                            analisar(programa(comandos))
                        else:
                            self.recusa(programa(comandos), 2)

    def test_operadores_binarios(self):
        valores = {'inteiro': '2', 'real': '2.5', 'logico': 'verdadeiro', 'texto': '"a"'}
        for op in ('+', '-', '*', '/', '%', '<', '<=', '>', '>=', '==', '!=', 'e', 'ou'):
            for esquerda, a in valores.items():
                for direita, b in valores.items():
                    esperado = None
                    numeros = esquerda in ('inteiro', 'real') and direita in ('inteiro', 'real')
                    if op in ('+', '-', '*', '/') and numeros:
                        esperado = 'real' if 'real' in (esquerda, direita) else 'inteiro'
                    if op == '+' and esquerda == direita == 'texto':
                        esperado = 'texto'
                    if op == '%' and esquerda == direita == 'inteiro':
                        esperado = 'inteiro'
                    if op in ('<', '<=', '>', '>=') and numeros:
                        esperado = 'logico'
                    if op in ('==', '!=') and (esquerda == direita or numeros):
                        esperado = 'logico'
                    if op in ('e', 'ou') and esquerda == direita == 'logico':
                        esperado = 'logico'
                    fonte = programa(f'escreva({a} {op} {b});')
                    with self.subTest(op=op, esquerda=esquerda, direita=direita):
                        if esperado is None:
                            self.recusa(fonte, 2)
                        else:
                            arvore, _ = analisar(fonte)
                            expressao = arvore.filhos[0].filhos[1].filhos[0].filhos[0]
                            self.assertEqual(expressao.extra['tipo'], esperado)

    def test_unarios_e_condicoes(self):
        analisar(programa('escreva(-1); escreva(-1.5); escreva(nao falso);'))
        for comandos in ('escreva(-verdadeiro);', 'escreva(-"a");',
                         'escreva(nao 1);', 'escreva(nao 1.5);', 'escreva(nao "a");',
                         'enquanto (1) {}', 'se ("a") {}'):
            with self.subTest(comandos=comandos):
                self.recusa(programa(comandos), 2)

    def test_retorno_em_todos_os_caminhos(self):
        for corpo in ('{ retorne 1; }',
                      'se (verdadeiro) { retorne 1; } senao { retorne 2; }',
                      'se (verdadeiro) { retorne 1; } retorne 2;'):
            with self.subTest(corpo=corpo):
                analisar('funcao inteiro f() {' + corpo + '}\n' + programa(''))
        for corpo in ('', 'se (verdadeiro) { retorne 1; }',
                      'enquanto (verdadeiro) { retorne 1; }',
                      'se (verdadeiro) { retorne 1; } senao {}'):
            with self.subTest(corpo=corpo):
                self.recusa('funcao inteiro f() {' + corpo + '}\n' + programa(''), 1)

    def test_tipo_do_retorno_e_codigo_apos_retorne(self):
        for corpo in ('retorne;', 'retorne 1.5;', 'retorne "a";',
                      'retorne 1; escreva(inexistente);'):
            with self.subTest(corpo=corpo):
                self.recusa('funcao inteiro f() {\n' + corpo + '\n}\n' + programa(''), 2)
        self.recusa(programa('retorne 1;'), 2)
        _, tabela = analisar(programa('retorne; { inteiro x; }'))
        self.assertEqual(len(tabela), 4)

    def test_nao_avalia_expressoes_na_compilacao(self):
        analisar(programa('escreva(1 / 0); escreva(1 % 0);'))
        self.recusa(programa('escreva(falso e desconhecida());'), 2)

    def test_fases_anteriores_e_divisao_inteira(self):
        fonte = programa('real x = 7 / 2;')
        arvore = sintatico.analisar(lexico.analisar(fonte))
        antes = sintatico.despejar(arvore)
        semantica.analisar(arvore)
        self.assertEqual(sintatico.despejar(arvore), antes)
        divisao = arvore.filhos[0].filhos[1].filhos[0].filhos[0]
        self.assertEqual(divisao.extra['tipo'], 'inteiro')
        self.assertTrue(compilar_ate(programa('escreva(x);'), 'ast'))
        self.assertTrue(compilar_ate(programa('inteiro x = ;'), 'tokens'))


if __name__ == '__main__':
    unittest.main()

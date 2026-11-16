"""Casos da E4 que complementam o corpus do professor.

Execute com: python -m unittest discover -s testes -p "test_entrega4.py" -v
"""
import io
import re
import unittest

from mplc import vm
from mplc.erros import ErroMPL
from mplc.principal import compilar_ate
from verificar import conta_operadores


def executar(fonte):
    codigo = '\n'.join(compilar_ate(fonte, 'bytecode'))
    saida = io.StringIO()
    vm.executar(codigo, saida)
    return saida.getvalue()


def programa(comandos):
    return 'funcao vazio principal() {\n' + comandos + '\n}\n'


class Entrega4Test(unittest.TestCase):
    def test_conversoes_acontecem_depois_da_divisao_inteira(self):
        fonte = '''
funcao real recebe(real x) { retorne x; }
funcao real calcula() { retorne 7 / 2; }
funcao vazio principal() {
  real x = 7 / 2;
  escreva(x);
  x = -7 / 2;
  escreva(x);
  escreva(recebe(7 / 2));
  escreva(calcula());
  escreva(7 / 2.0);
  escreva(2 + 0.5);
  escreva(2 == 2.0);
}
'''
        self.assertEqual(executar(fonte),
                         '3.000000\n-3.000000\n3.000000\n3.000000\n'
                         '3.500000\n2.500000\nverdadeiro\n')

    def test_divisao_e_resto_com_todos_os_sinais(self):
        casos = [(7, 3, 2, 1), (-7, 3, -2, -1),
                 (7, -3, -2, 1), (-7, -3, 2, -1),
                 (-2, 3, 0, -2), (2, -3, 0, 2)]
        for dividendo, divisor, quociente, resto in casos:
            with self.subTest(dividendo=dividendo, divisor=divisor):
                fonte = programa(f'escreva({dividendo} / ({divisor}));\n'
                                 f'escreva({dividendo} % ({divisor}));')
                self.assertEqual(executar(fonte), f'{quociente}\n{resto}\n')

    def test_divisao_inteira_preserva_precisao(self):
        fonte = programa('escreva(9007199254740995 / 3);\n'
                         'escreva(-9007199254740995 % 3);')
        self.assertEqual(executar(fonte), '3002399751580331\n-2\n')

    def test_logicos_avaliam_ambos_os_lados(self):
        fonte = '''
funcao logico marca(inteiro n, logico valor) {
  escreva(n);
  retorne valor;
}
funcao vazio principal() {
  escreva(marca(1, falso) e marca(2, verdadeiro));
  escreva(marca(3, verdadeiro) ou marca(4, falso));
}
'''
        self.assertEqual(executar(fonte),
                         '1\n2\nfalso\n3\n4\nverdadeiro\n')

    def test_recursao_preserva_locais_e_temporarios(self):
        fonte = '''
funcao inteiro soma(inteiro n) {
  inteiro local = n * 10;
  se (n == 0) { retorne 0; }
  inteiro anterior = soma(n - 1);
  retorne local + anterior + n;
}
funcao inteiro junta(inteiro a, inteiro b) { retorne a * 100 + b; }
funcao vazio principal() {
  escreva(soma(4));
  escreva(junta(soma(2), junta(1, soma(1))));
}
'''
        self.assertEqual(executar(fonte), '110\n3411\n')

    def test_recursao_mutua_e_parametros_por_valor(self):
        fonte = '''
funcao inteiro primeira(inteiro n) {
  inteiro local = n;
  se (n == 0) { retorne 0; }
  n = n - 1;
  retorne segunda(n) + local;
}
funcao inteiro segunda(inteiro n) {
  inteiro local = n * 10;
  se (n == 0) { retorne 0; }
  retorne primeira(n - 1) + local;
}
funcao vazio principal() {
  inteiro n = 4;
  escreva(primeira(n));
  escreva(n);
}
'''
        self.assertEqual(executar(fonte), '46\n4\n')

    def test_sombreamento_e_reinicializacao_do_bloco(self):
        fonte = '''
funcao vazio principal() {
  inteiro x = 99;
  inteiro i = 0;
  enquanto (i < 3) {
    inteiro x;
    real r;
    logico b;
    texto t;
    escreva(x);
    escreva(r);
    escreva(b);
    escreva(t);
    x = 42;
    i = i + 1;
  }
  escreva(x);
}
'''
        self.assertEqual(executar(fonte),
                         '0\n0.000000\nfalso\n\n' * 3 + '99\n')

    def test_texto_unicode_e_escapes(self):
        fonte = programa(r'escreva("ação\n" + "\t\"fim\"\\");')
        self.assertEqual(executar(fonte), 'ação\n\t"fim"\\\n')

    def test_chamada_como_comando_descarta_retorno(self):
        fonte = '''
funcao inteiro valor() { retorne 7; }
funcao vazio mostra() { escreva("ok"); retorne; }
funcao vazio principal() {
  inteiro i = 0;
  enquanto (i < 2000) { valor(); i = i + 1; }
  mostra();
  escreva(1 + valor());
}
'''
        self.assertEqual(executar(fonte), 'ok\n8\n')

    def test_literal_real_preserva_casas_antes_do_calculo(self):
        fonte = programa('escreva(0.0000004 * 10000000.0);')
        self.assertEqual(executar(fonte), '4.000000\n')

    def test_zero_aponta_o_comando_multilinha(self):
        for expressao in ('7 / 0', '7.0 / 0.0', '7 % 0'):
            with self.subTest(expressao=expressao):
                fonte = programa('  escreva(\n    ' + expressao + '\n  );')
                with self.assertRaises(ErroMPL) as contexto:
                    executar(fonte)
                self.assertEqual(contexto.exception.fase, 'execucao')
                self.assertEqual(contexto.exception.linha, 2)

    def test_estouro_aponta_o_comando_da_chamada(self):
        fonte = ('funcao inteiro repete(inteiro n) {\n'
                 '  retorne\n'
                 '    repete(n + 1);\n'
                 '}\n'
                 'funcao vazio principal() { escreva(repete(0)); }\n')
        with self.assertRaises(ErroMPL) as contexto:
            executar(fonte)
        self.assertEqual(contexto.exception.fase, 'execucao')
        self.assertEqual(contexto.exception.linha, 2)

    def test_ir_tem_funcoes_rotulos_e_operacoes_simples(self):
        fonte = '''
funcao inteiro dobro(inteiro x) { retorne x * 2; }
funcao vazio sem_chamada() { escreva("+ - * / e ou nao"); }
funcao vazio principal() {
  inteiro x = 1;
  enquanto (x < 3) {
    se (x == 1) { escreva(dobro(x + 2 * 3)); }
    senao { escreva(-x); }
    x = x + 1;
  }
}
'''
        linhas = compilar_ate(fonte, 'ir')
        funcoes = set()
        rotulos = set()
        destinos = set()
        for linha in linhas:
            self.assertLessEqual(conta_operadores(linha), 1, linha)
            funcao = re.match(r'\s*funcao\s+(\w+)\b', linha)
            if funcao:
                funcoes.add(funcao.group(1))
                rotulos = set()
                destinos = set()
            rotulo = re.fullmatch(r'\s*(\w+):\s*', linha)
            if rotulo:
                self.assertNotIn(rotulo.group(1), rotulos)
                rotulos.add(rotulo.group(1))
            destino = re.search(r'\bdesvie\s+(\w+)\b', linha)
            if destino:
                destinos.add(destino.group(1))
            if linha.strip() == 'fim':
                self.assertTrue(destinos.issubset(rotulos), destinos - rotulos)
        self.assertEqual(funcoes, {'dobro', 'sem_chamada', 'principal'})


if __name__ == '__main__':
    unittest.main()

# Minha pequena linguagem

Trabalho semestral de **Compiladores** — Ciência da Computação, UNISAGRADO.
Prof. Luiz Ricardo Mantovani da Silva · 2026-2

Cada grupo escreve um **compilador completo** para a MPL, uma linguagem
pequena de palavras-chave em português. O compilador de vocês vai ler um
programa em `.mpl`, atravessar as quatro fases da disciplina e produzir um
arquivo que **roda de verdade** numa máquina virtual que vocês também vão
escrever.

No fim do semestre vocês executam um programa escrito por vocês, numa
linguagem compilada por vocês.

---

## Comece por aqui

```bash
git clone https://github.com/LuizRMSilva1973/compiladores-lab.git
cd compiladores-lab
```

```bash
make verificar E=1
```

Vai dar vermelho — é para dar. O esqueleto responde à linha de comando mas
ainda não tem nenhuma fase escrita. O vermelho é o seu ponto de partida, e
ele vai virando verde conforme vocês preenchem `mplc/`.

Não precisa instalar nada além do Python 3. Se o notebook de vocês der
trabalho, o [Google Cloud Shell](https://shell.cloud.google.com) já vem com
Python 3.12, Java 21 e git — e é o mesmo ambiente da correção.

---

## Os três documentos que mandam

| Arquivo | O que decide |
|---|---|
| [LINGUAGEM.md](LINGUAGEM.md) | **o que** o compilador aceita: a sintaxe e as regras de tipo da MPL |
| [CONTRATOS.md](CONTRATOS.md) | **como** ele se comunica: a linha de comando e o formato de cada despejo |
| [entregas/](entregas/) | o enunciado de cada entrega, com o que vale nota |

Quando a sua intuição discordar de um deles, é o arquivo que vale. Se o
arquivo estiver errado, me procurem — já aconteceu de eu escrever um exemplo
errado no contrato e só descobrir rodando.

---

## As entregas

| # | Entrega | Turma A (quarta) | Turma B (segunda) | Vale |
|---|---|---|---|---|
| [E1](entregas/E1.md) | Analisador léxico | 02/09 | 31/08 | 0,8 |
| [E2](entregas/E2.md) | Analisador sintático e árvore | 30/09 | 28/09 | 1,2 |
| [E3](entregas/E3.md) | Tabela de símbolos e tipos | 28/10 | 26/10 | 1,2 |
| [E4](entregas/E4.md) | Código intermediário, geração e VM | 18/11 | 16/11 | 1,8 |
| [Apres.](entregas/APRESENTACAO.md) | Demonstração e defesa | 25/11 | 23/11 | 1,0 |

São **quatro entregas sobre o mesmo compilador**, não quatro trabalhos. O que
vocês escreverem na E1 continua rodando na E4 — e o verificador da E4 confere
tudo o que veio antes. Deixar a E1 pela metade custa caro em novembro.

---

## Regras do jogo

**A entrega é o repositório, nunca a máquina de vocês.** A correção clona o
repositório numa máquina limpa e roda `make verificar E=n`. Se não passar
lá, não conta como entregue. Testem antes de entregar — de preferência na
Cloud Shell, que é o ambiente da correção.

**Grupos de até 3.** O mesmo grupo do começo ao fim. Mudança de grupo só até
a E1.

**Gerador de parser proibido nas Entregas 1 e 2.** ANTLR, PLY, yacc, lark e
parentes escondem exatamente a parte que está sendo ensinada. Da E3 em diante
o assunto é outro, e aí não faz diferença. Na apresentação vocês podem — e
devem — comparar o parser de vocês com o que um gerador produziria.

**A linguagem de implementação é de vocês, entre as que o ambiente da correção
já tem:** Python 3.12, Java 21, C e C++ (gcc 13), Ruby 3.2 ou PHP 8.3. O
verificador não olha para dentro — ele roda `./compilar` e `./executar` e
compara o que sai. O esqueleto em `mplc/` é Python porque é o caminho mais
curto, mas ninguém é obrigado a usá-lo.

A lista existe por um motivo prático: a correção roda numa Cloud Shell limpa, e
o que não estiver lá não roda. Querem outra linguagem? Falem comigo **antes** de
começar — o critério é ela existir no ambiente sem instalação. Em nenhum caso
dependam de biblioteca externa: só a biblioteca padrão.

**Escrever o compilador é a tarefa.** Usar IA para explicar um conceito,
revisar uma mensagem de erro ou entender um trecho é bem-vindo, e eu faço
isso também. Entregar um compilador que vocês não sabem alterar é outra
coisa — e a apresentação foi desenhada para separar os dois casos: cada grupo
recebe **uma alteração pequena na linguagem, na hora, com 10 minutos para
fazer**. Quem escreveu o compilador faz. Não é desconfiança; é o formato.

---

## Tabela de tokens da MPL

O analisador léxico transforma o código-fonte em uma lista de tokens no seguinte formato:

```text
linha,coluna,TIPO,lexema
```

A coluna indica a posição do primeiro caractere do token, começando em 1.

### Palavras reservadas

| Lexema | Token gerado |
|---|---|
| `funcao` | `FUNCAO` |
| `retorne` | `RETORNE` |
| `se` | `SE` |
| `senao` | `SENAO` |
| `enquanto` | `ENQUANTO` |
| `escreva` | `ESCREVA` |
| `inteiro` | `TIPO_INTEIRO` |
| `real` | `TIPO_REAL` |
| `logico` | `TIPO_LOGICO` |
| `texto` | `TIPO_TEXTO` |
| `vazio` | `TIPO_VAZIO` |
| `verdadeiro` | `LOGICO` |
| `falso` | `LOGICO` |
| `e` | `E` |
| `ou` | `OU` |
| `nao` | `NAO` |

### Identificadores e literais

| Forma no código-fonte | Token gerado | Exemplo |
|---|---|---|
| Nome iniciado por letra ou `_`, seguido de letras, dígitos ou `_` | `ID` | `principal`, `idade`, `_contador` |
| Um ou mais dígitos | `INTEIRO` | `0`, `42`, `1000` |
| Dígitos, ponto e dígitos | `REAL` | `3.14`, `0.5`, `10.0` |
| Texto entre aspas duplas | `TEXTO` | `"oi"`, `"linha\n"` |
| `verdadeiro` ou `falso` | `LOGICO` | `verdadeiro`, `falso` |

### Operadores

| Lexema | Token gerado |
|---|---|
| `+` | `MAIS` |
| `-` | `MENOS` |
| `*` | `VEZES` |
| `/` | `DIVIDE` |
| `%` | `RESTO` |
| `==` | `IGUAL` |
| `!=` | `DIFERENTE` |
| `<` | `MENOR` |
| `<=` | `MENOR_IGUAL` |
| `>` | `MAIOR` |
| `>=` | `MAIOR_IGUAL` |
| `=` | `ATRIBUI` |

### Delimitadores

| Lexema | Token gerado |
|---|---|
| `(` | `ABRE_PAR` |
| `)` | `FECHA_PAR` |
| `{` | `ABRE_CHAVE` |
| `}` | `FECHA_CHAVE` |
| `,` | `VIRGULA` |
| `;` | `PONTO_VIRGULA` |

### Fim do arquivo

| Situação | Token gerado | Lexema |
|---|---|---|
| Final do programa | `FIM_ARQUIVO` | vazio |

O token `FIM_ARQUIVO` é sempre o último token da lista. Como o lexema é vazio, a linha impressa termina com vírgula.

Exemplo:

```text
4,1,FIM_ARQUIVO,
```

### Comentários e espaços

Comentários e espaços não geram tokens.

| Forma | Comportamento |
|---|---|
| `// comentário` | Ignorado até o fim da linha |
| `/* comentário */` | Ignorado até encontrar o primeiro `*/` |
| Espaço, tabulação, `\r` e `\n` | Ignorados, servindo apenas para separar tokens |

---

## Gramática da MPL

O analisador sintático (`mplc/sintatico.py`) é de descida recursiva: cada
regra abaixo virou uma função com o mesmo nome, com uma função por nível de
precedência. As duas exceções são `tipo_dado` e `tipo_retorno`, que são só
uma escolha entre tokens e por isso são conferidas pelos dicionários
`TIPOS_DE_DADO` e `TIPOS_DE_RETORNO`. Os terminais são os tipos de token da
tabela acima. Notação EBNF: `{ x }` repete zero ou mais vezes e
`[ x ]` é opcional.

```ebnf
programa      = { funcao } FIM_ARQUIVO ;
funcao        = FUNCAO tipo_retorno ID ABRE_PAR [ parametro { VIRGULA parametro } ] FECHA_PAR bloco ;
parametro     = tipo_dado ID ;
tipo_dado     = TIPO_INTEIRO | TIPO_REAL | TIPO_LOGICO | TIPO_TEXTO ;
tipo_retorno  = tipo_dado | TIPO_VAZIO ;

bloco         = ABRE_CHAVE { comando } FECHA_CHAVE ;
comando       = declaracao | atribuicao | chamada PONTO_VIRGULA | se | enquanto
              | escreva | retorne | bloco ;
declaracao    = tipo_dado ID [ ATRIBUI expressao ] PONTO_VIRGULA ;
atribuicao    = ID ATRIBUI expressao PONTO_VIRGULA ;
se            = SE ABRE_PAR expressao FECHA_PAR bloco [ SENAO bloco ] ;
enquanto      = ENQUANTO ABRE_PAR expressao FECHA_PAR bloco ;
escreva       = ESCREVA ABRE_PAR expressao FECHA_PAR PONTO_VIRGULA ;
retorne       = RETORNE [ expressao ] PONTO_VIRGULA ;

expressao     = ou ;
ou            = e { OU e } ;
e             = igualdade { E igualdade } ;
igualdade     = relacional { ( IGUAL | DIFERENTE ) relacional } ;
relacional    = aditivo { ( MENOR | MENOR_IGUAL | MAIOR | MAIOR_IGUAL ) aditivo } ;
aditivo       = multiplicativo { ( MAIS | MENOS ) multiplicativo } ;
multiplicativo = unario { ( VEZES | DIVIDE | RESTO ) unario } ;
unario        = ( NAO | MENOS ) unario | primario ;
primario      = INTEIRO | REAL | LOGICO | TEXTO | ID | chamada
              | ABRE_PAR expressao FECHA_PAR ;
chamada       = ID ABRE_PAR [ expressao { VIRGULA expressao } ] FECHA_PAR ;
```

**Como a precedência está codificada:** cada nível de precedência é uma regra,
e cada regra só chama a do nível **imediatamente mais forte**. Por isso o
operador mais fraco (`ou`) fica mais perto da raiz da árvore, e o mais forte
(unário, parênteses) fica nas folhas. Os binários usam repetição `{ ... }`,
implementada como um laço que vai pendurando a árvore à esquerda. É o que faz
`10 - 4 - 3` virar `(10 - 4) - 3`. Já `unario` chama a si mesmo à direita, o
que dá a associatividade à direita de `nao` e do `-` unário.

**Onde a gramática precisa olhar dois tokens:** um comando que começa com `ID`
pode ser uma atribuição (`x = ...`) ou uma chamada (`f(...)`). O parser olha
o token seguinte (`ATRIBUI` ou `ABRE_PAR`) para decidir. O mesmo vale em
`primario`, para separar variável de chamada.

**Erros:** o erro sintático é relatado na linha e coluna do token que apareceu
no lugar do esperado. O parser para no primeiro erro.

---

## O verificador

```bash
make verificar E=2      # confere a Entrega 2 e, junto, a 1
make verificar          # confere as quatro
make evidencias E=2     # grava evidencias/verificacao-2.txt, que vai na entrega
```

**Antes de entregar, rodem `make prova`.** Ele clona o repositório de vocês num
diretório limpo e verifica lá — que é exatamente o que a correção faz. É o
teste que pega o defeito mais comum de todos, e que não tem nada a ver com
compiladores: *funciona aqui e não no clone*. Arquivo esquecido fora do commit,
caminho absoluto, passo de compilação que ninguém roda. Vale para qualquer
linguagem, e é a única prova que realmente antecipa a correção.

Ele não lê o código de vocês. Ele roda o compilador e compara a saída com um
corpus de **10 programas válidos**, **26 programas que precisam ser
recusados na compilação** e **3 que precisam falhar na execução** — com a
fase e a linha do erro conferidas.

Os programas recusados são metade da nota escondida do trabalho. Um
compilador que aceita tudo passa em todos os testes positivos e não vale
nada: é por isso que o corpus tem mais programas errados do que certos.

**A correção usa um segundo corpus, que vocês não têm.** Mesma linguagem,
mesmas regras, programas diferentes. Um compilador de verdade passa nos dois
sem que vocês precisem fazer nada; um programa que apenas reproduza as saídas
esperadas deste corpus passa aqui e reprova lá. Estou dizendo isto abertamente
para ninguém perder tempo pelo caminho errado.

---

## Como entregar

1. `git push` no repositório do grupo.
2. Abram a [página do trabalho](https://profluiz.mantovanitec.com/disciplinas/aulas/compiladores/trabalho.html).
3. No formulário do fim da página: escolham a entrega, identifiquem os
   integrantes (nome, RA e e-mail), colem a URL do repositório e anexem o
   `evidencias/verificacao-N.txt`.
4. Cada integrante recebe uma cópia por e-mail. **Guardem esse e-mail**: é o
   comprovante.

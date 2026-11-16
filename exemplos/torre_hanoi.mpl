// Move tres discos da torre A para a torre C, usando B como auxiliar.
// Cada chamada guarda sua propria quantidade de movimentos.
funcao inteiro mover(inteiro discos, texto origem, texto destino, texto auxiliar) {
  se (discos == 0) {
    retorne 0;
  }

  inteiro antes = mover(discos - 1, origem, auxiliar, destino);
  escreva(origem + " -> " + destino);
  inteiro depois = mover(discos - 1, auxiliar, destino, origem);
  retorne antes + 1 + depois;
}

funcao vazio principal() {
  escreva("Torre de Hanoi - 3 discos");
  inteiro total = mover(3, "A", "C", "B");
  escreva("Total de movimentos:");
  escreva(total);
}

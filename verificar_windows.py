"""Executa as mesmas provas de verificar.py usando Python no lugar do shell.

No PowerShell: python -X utf8 verificar_windows.py 3
Isto nao substitui a prova dos lancadores em Linux/Cloud Shell.
"""
import sys

import verificar


def main(argv):
    rodar_original = verificar.rodar

    def rodar_python(cmd, entrada=None, limite=20):
        if cmd[0] in ('./compilar', './executar'):
            argumentos = ['--rodar'] if cmd[0] == './executar' else []
            cmd = [sys.executable, '-X', 'utf8', '-m', 'mplc.principal',
                   *argumentos, *cmd[1:]]
        return rodar_original(cmd, entrada, limite)

    verificar.rodar = rodar_python
    try:
        print('Windows: lancadores shell substituidos por python -m mplc.principal.')
        return verificar.main(argv)
    finally:
        verificar.rodar = rodar_original


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))

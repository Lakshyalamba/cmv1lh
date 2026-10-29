"""Native POSIX startup/SIGTERM smoke check; does not validate Docker."""
import os
import signal
import socket
import subprocess
import sys
import time
from urllib.request import urlopen
from pipeline.fetch import ROOT


def main():
    with socket.socket() as listener:
        listener.bind(('127.0.0.1', 0))
        port = listener.getsockname()[1]
    process = subprocess.Popen([sys.executable, '-m', 'backend.run'], cwd=ROOT,
        env=dict(os.environ, PORT=str(port), LOG_LEVEL='info'), stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT, text=True)
    try:
        for _ in range(100):
            try:
                with urlopen(f'http://127.0.0.1:{port}/health/ready', timeout=.2) as response:
                    if response.status == 200:
                        break
            except OSError:
                time.sleep(.05)
        else:
            raise RuntimeError('Child process readiness timed out')
        process.terminate()
        output = process.communicate(timeout=25)[0]
        if process.returncode not in (0, -signal.SIGTERM) or 'Application shutdown complete' not in output:
            raise RuntimeError(f'Shutdown failed ({process.returncode}): {output}')
        print(f'SIGTERM graceful shutdown verified; return code {process.returncode}.')
    finally:
        if process.poll() is None:
            process.kill()
            process.wait()


if __name__ == '__main__':
    main()

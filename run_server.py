import sys
import subprocess

try:
    subprocess.run(f"pqi-server", check=True)
except subprocess.CalledProcessError:
    subprocess.run(f"pip install git+https://git-cc.nie.netease.com/pc/pyqtinspect.git@dev_alpha", check=True)
    try:
        subprocess.run(f"pqi-server", check=True)
    except subprocess.CalledProcessError:
        print("Failed to run pqi-server", file=sys.stderr)
        exit(1)

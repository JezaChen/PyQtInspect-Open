import sys
import subprocess

try:
    p = subprocess.Popen("pqi-server")
    p.wait()
except Exception:
    try:
        subprocess.Popen("python --version").wait()
        p = subprocess.Popen("python -m pip install git+https://git-cc.nie.netease.com/pc/pyqtinspect.git@dev_alpha".split())
        status = p.wait()
        print(status)
        p = subprocess.Popen("pqi-server")
        p.wait()
    except Exception as e:
        print(f"Failed to run pqi-server: {e}", file=sys.stderr)
        exit(1)

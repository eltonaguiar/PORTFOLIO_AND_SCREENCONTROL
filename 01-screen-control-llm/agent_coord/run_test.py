"""Orchestrate the cross-machine concurrency test: two writers on each host, started together.

Shell backgrounding is not available in this environment, so the parallelism lives here in Python:
two local subprocesses plus one ssh session that starts two remote writers, all launched before any
of them is awaited.
"""
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))


def main():
    pw = os.environ.get("COORD_PW")
    if not pw:
        sys.exit("COORD_PW not set")
    rows = sys.argv[1] if len(sys.argv) > 1 else "100"
    env = dict(os.environ, COORD_PW=pw)

    procs = []
    # two Windows-side writers
    for seat in ("windows-A", "windows-B"):
        procs.append(subprocess.Popen(
            [sys.executable, os.path.join(HERE, "test_concurrency.py"), "--seat", seat, "--rows", rows],
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, env=env))
    # one ssh session that starts two Linux-side writers concurrently
    remote = (f'PW=$(grep -E "^stocks[0-9]+$" ~/dbpasses.txt|head -1); export COORD_PW=$PW; cd /tmp; '
              f'python3 /tmp/test_concurrency.py --seat linux-A --rows {rows} & '
              f'python3 /tmp/test_concurrency.py --seat linux-B --rows {rows} & wait')
    procs.append(subprocess.Popen(
        ["ssh", "-o", "BatchMode=yes", "-o", "StrictHostKeyChecking=no", "eltonsGX10", remote],
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, env=env))

    t0 = time.time()
    for p in procs:
        out, _ = p.communicate(timeout=600)
        for line in (out or "").splitlines():
            if "ok=" in line or "error" in line.lower():
                print(line.strip())
    print(f"\nall writers finished in {time.time()-t0:.1f}s")
    subprocess.run([sys.executable, os.path.join(HERE, "test_concurrency.py"), "--count"], env=env)


if __name__ == "__main__":
    main()

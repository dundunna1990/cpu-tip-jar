"""Constrained, explicit-consent XMRig downloader and process controller."""
import hashlib
import io
import math
import os
import pathlib
import platform
import queue
import re
import signal
import subprocess
import tarfile
import threading
import time
import urllib.request
import zipfile
from .public_config import DONATION_ADDRESS
from . import lifecycle

VERSION = "6.26.0"
UPSTREAM = f"https://github.com/xmrig/xmrig/releases/download/v{VERSION}"
ARCHIVES = {
    "Linux": ("xmrig-6.26.0-linux-static-x64.tar.gz",
              "fc6f8ae5f64e4f17481f7e3be29a1c56949f216a998414188003eae1db20c9e5"),
    "Windows": ("xmrig-6.26.0-windows-x64.zip",
                "bba8097cb37d9b458a1cb1137876b27cde6740d17fe4ccbc086ba07d87d9e147")
}
# Digest of the extracted executable; prevents substitute binaries in the local cache.
EXECUTABLE_SHA256 = {
    "Linux": "b20f39fc00d242e706b6c30367ad811c676e0575050a4ec2f30104b696944b49",
    "Windows": "6fa80698d7268f6e88aa88c06fb27ee99e1bcee747c2e76911e6206a5b1aeeb3",
}
POOL = "gulf.moneroocean.stream:20001"
SPEED = re.compile(r"\bspeed\s+10s/60s/15m\s+([0-9.]+|n/a)", re.I)

def os_name():
    system = platform.system()
    if system not in ARCHIVES or platform.machine().lower() not in ("x86_64", "amd64"):
        raise RuntimeError("This release supports x86-64 Linux and Windows only.")
    return system

def miner_path():
    if os_name() == "Windows":
        folder = pathlib.Path(os.environ.get("LOCALAPPDATA", str(pathlib.Path.home() / "AppData" / "Local")))
        return folder / "CPUTipJar" / "bin" / "xmrig.exe"
    folder = pathlib.Path(os.environ.get("XDG_DATA_HOME", str(pathlib.Path.home() / ".local" / "share")))
    return folder / "cpu-tip-jar" / "bin" / "xmrig"

def valid_address(value):
    return bool(re.fullmatch(r"4[1-9A-HJ-NP-Za-km-z]{94}", value))

def threads_for(preset, cpu=None):
    cpu = (os.cpu_count() or 1) if cpu is None else cpu
    if not isinstance(cpu, int) or cpu < 1: raise ValueError("Invalid CPU count")
    options = {"Low": .25, "Medium": .5, "High": .75}
    if preset not in options: raise ValueError("Invalid CPU setting")
    return min(cpu, max(1, math.floor(cpu * options[preset])))

def seconds_for(duration):
    options = {"1 hour":3600, "1 day":86400, "10 days":864000, "30 days":2592000}
    if duration not in options: raise ValueError("Invalid duration")
    return options[duration]

def verify_bytes(data, expected):
    if hashlib.sha256(data).hexdigest() != expected:
        raise ValueError("SHA-256 mismatch: download rejected")

def extract_executable(data, system):
    if system == "Windows":
        with zipfile.ZipFile(io.BytesIO(data)) as archive:
            matches = [m for m in archive.infolist() if
                       pathlib.PurePosixPath(m.filename).name.lower() == "xmrig.exe" and not m.is_dir()]
            if len(matches) != 1 or matches[0].file_size > 32_000_000: raise ValueError("Invalid ZIP contents")
            with archive.open(matches[0]) as stream: binary = stream.read(32_000_001)
    elif system == "Linux":
        with tarfile.open(fileobj=io.BytesIO(data), mode="r:gz") as archive:
            matches = [m for m in archive.getmembers() if
                       pathlib.PurePosixPath(m.name).name == "xmrig" and m.isfile()]
            if len(matches) != 1 or matches[0].size > 32_000_000: raise ValueError("Invalid TAR contents")
            with archive.extractfile(matches[0]) as stream: binary = stream.read(32_000_001)
    else:
        raise ValueError("Unsupported OS")
    if len(binary) > 32_000_000: raise ValueError("Unexpected executable size")
    return binary

def install_verified(progress=None, opener=None):
    system = os_name()
    name, expected = ARCHIVES[system]
    request = urllib.request.Request(UPSTREAM + "/" + name, headers={"User-Agent":"CPUTipJar/0.1"})
    if progress: progress("Downloading official XMRig archive...")
    with (opener or urllib.request.urlopen)(request, timeout=40) as response:
        if int(response.headers.get("Content-Length") or 0) > 100_000_000:
            raise ValueError("Archive exceeds size limit")
        chunks = []
        total = 0
        while True:
            block = response.read(1024 * 1024)
            if not block: break
            total += len(block)
            if total > 100_000_000: raise ValueError("Archive exceeds size limit")
            chunks.append(block)
    archive_bytes = b"".join(chunks)
    verify_bytes(archive_bytes, expected)
    if progress: progress("Checksum verified; installing executable...")
    binary = extract_executable(archive_bytes, system)
    verify_bytes(binary, EXECUTABLE_SHA256[system])
    dst = miner_path()
    dst.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    tmp = dst.with_suffix(dst.suffix + ".tmp")
    try:
        with open(tmp, "wb") as f: f.write(binary)
        if system == "Linux": os.chmod(tmp, 0o700)
        os.replace(tmp, dst)
    finally:
        tmp.unlink(missing_ok=True)
    return dst

def verified_local_executable(path=None):
    path = pathlib.Path(path) if path else miner_path()
    if not path.is_file() or path.is_symlink():
        raise FileNotFoundError("No verified local XMRig executable. Download it first.")
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    if digest != EXECUTABLE_SHA256[os_name()]:
        raise ValueError("The local miner no longer matches the verified upstream executable; remove and re-download it.")
    return path

def command(executable, preset, wallet=DONATION_ADDRESS):
    if not valid_address(wallet): raise ValueError("Missing or invalid public donation address")
    return [str(executable), "--algo=rx/0", "--url=" + POOL,
            "--user=" + wallet, "--pass=support-volunteer", "--tls",
            "--threads=" + str(threads_for(preset)), "--cpu-priority=0",
            "--no-huge-pages", "--randomx-wrmsr=-1", "--no-dmi",
            "--print-time=10", "--no-color", "--donate-level=1"]

def parse_hashrate(line):
    match = SPEED.search(line)
    return float(match.group(1)) if match and match.group(1).lower() != "n/a" else None

def stop_process(proc, timeout=5):
    if proc is None or proc.poll() is not None: return
    try:
        if os.name == "nt": proc.terminate()
        else: os.killpg(proc.pid, signal.SIGTERM)
        proc.wait(timeout=timeout)
    except (subprocess.TimeoutExpired, OSError):
        if proc.poll() is None:
            try:
                if os.name == "nt": proc.kill()
                else: os.killpg(proc.pid, signal.SIGKILL)
                proc.wait(timeout=2)
            except (OSError, subprocess.TimeoutExpired): pass

class Session:
    def __init__(self):
        self.proc = None
        self.deadline = 0
        self.messages = queue.Queue()
        self.lock = threading.RLock()
        self.reader = None
        self.guard = None

    def start(self, preset, duration, executable=None):
        with self.lock:
            if self.running(): raise RuntimeError("Mining already running")
            if self.guard is not None:
                self.guard.close()
                self.guard = None
            path = pathlib.Path(executable) if executable else verified_local_executable()
            if not path.is_file(): raise FileNotFoundError("Download verified XMRig first")
            args = lifecycle.protected_command(command(path, preset))
            deadline = time.monotonic() + seconds_for(duration)
            kw = dict(stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                      stdin=subprocess.DEVNULL, text=True, bufsize=1)
            if os.name == "nt": kw["creationflags"] = subprocess.CREATE_NO_WINDOW
            else: kw["start_new_session"] = True
            proc = None
            try:
                proc = subprocess.Popen(args, **kw)
                # Windows: hold a kill-on-close Job Object. Linux: setpriv
                # has installed a kernel parent-death signal on the child.
                self.guard = lifecycle.CrashGuard(proc)
            except BaseException:
                stop_process(proc)
                raise
            self.proc = proc
            self.deadline = deadline
            self.reader = threading.Thread(target=self._read, args=(self.proc,), daemon=True)
            self.reader.start()
            return self.proc.pid

    def _read(self, proc):
        try:
            for line in proc.stdout:
                rate = parse_hashrate(line)
                if rate is not None: self.messages.put(("rate", rate))
                elif "accepted" in line.lower() or "rejected" in line.lower():
                    self.messages.put(("shares", line.strip()[-130:]))
        except (OSError, ValueError): pass
        finally:
            if proc.stdout is not None:
                proc.stdout.close()
            self.messages.put(("exit", proc.poll()))

    def running(self):
        return self.proc is not None and self.proc.poll() is None

    def stop(self):
        with self.lock:
            stop_process(self.proc)
            # Windows: closing the job also kills any child still surviving
            # a normal stop. Kernel closes it automatically on GUI crash.
            if self.guard is not None:
                self.guard.close()
                self.guard = None
            if self.reader is not None and self.reader is not threading.current_thread():
                self.reader.join(timeout=2)
            self.deadline = 0

    def tick(self):
        if self.running() and time.monotonic() >= self.deadline:
            self.stop()
            return "duration"
        return None

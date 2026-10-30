"""Harmless process-lifetime tests; these never run XMRig or mine."""
import os
import pathlib
import signal
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

from cpu_tip_jar import engine, lifecycle


class LifecycleTests(unittest.TestCase):
    @unittest.skipUnless(sys.platform.startswith("linux"), "Linux-only")
    def test_linux_helper_required_and_parent_death_flag(self):
        with patch.object(lifecycle.shutil, "which", return_value=None):
            with self.assertRaisesRegex(RuntimeError, "setpriv"):
                lifecycle.protected_command(["fake-miner"])
        with patch.object(lifecycle.shutil, "which", return_value="/usr/bin/setpriv"):
            self.assertEqual(lifecycle.protected_command(["fake-miner", "--foo"]),
                             ["/usr/bin/setpriv", "--pdeathsig", "SIGKILL",
                              "--", "fake-miner", "--foo"])

    @unittest.skipUnless(sys.platform.startswith("linux"), "Linux-only")
    def test_linux_fake_miner_stops_if_parent_killed(self):
        with tempfile.TemporaryDirectory() as tmp:
            fake = pathlib.Path(tmp) / "fake_miner"
            heartbeat = pathlib.Path(tmp) / "heartbeat.txt"
            fake.write_text(
                "#!/usr/bin/env python3\n"
                "from pathlib import Path\n"
                "import time\n"
                f"p = Path({str(heartbeat)!r})\n"
                "while True:\n"
                "    with p.open('a') as f: f.write('X')\n"
                "    time.sleep(0.05)\n"
            )
            fake.chmod(0o700)
            source_dir = pathlib.Path(__file__).resolve().parent.parent
            childcode = (
                "from cpu_tip_jar.engine import Session; import time; "
                "s=Session(); "
                f"s.start('Low', '1 hour', {str(fake)!r}); "
                "print(s.proc.pid, flush=True); time.sleep(30)"
            )
            parent = subprocess.Popen(
                [sys.executable, "-c", childcode], cwd=str(source_dir),
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            miner_pid = None
            try:
                miner_pid = int(parent.stdout.readline().strip())
                for _ in range(30):
                    if heartbeat.exists() and heartbeat.stat().st_size >= 2:
                        break
                    time.sleep(0.05)
                self.assertTrue(heartbeat.exists(), "Fake miner never launched")
                os.kill(parent.pid, signal.SIGKILL)
                parent.wait(timeout=3)
                # A stopped heartbeat demonstrates kernel parent-death kill.
                time.sleep(0.2)
                before = heartbeat.stat().st_size
                time.sleep(0.35)
                self.assertEqual(before, heartbeat.stat().st_size,
                                 "Miner continued after GUI process died")
            finally:
                if parent.poll() is None:
                    parent.kill()
                    parent.wait(timeout=3)
                if miner_pid:
                    try:
                        os.kill(miner_pid, signal.SIGKILL)
                    except ProcessLookupError:
                        pass
                parent.stdout.close()
                parent.stderr.close()

    @unittest.skipUnless(os.name == "nt", "Windows-only")
    def test_windows_job_close_kills_fake_process(self):
        proc = subprocess.Popen(
            [sys.executable, "-c", "import time; time.sleep(30)"],
            creationflags=subprocess.CREATE_NO_WINDOW)
        guard = None
        try:
            guard = lifecycle.CrashGuard(proc)
            guard.close()
            proc.wait(timeout=5)
            self.assertIsNotNone(proc.returncode)
        finally:
            if guard is not None:
                guard.close()
            if proc.poll() is None:
                proc.kill()
                proc.wait(timeout=5)


if __name__ == "__main__":
    unittest.main()

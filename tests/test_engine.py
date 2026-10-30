"""No real mining is started by this test suite."""
import hashlib
import io
import os
import pathlib
import stat
import tarfile
import tempfile
import time
import unittest
import zipfile
from unittest.mock import patch
from cpu_tip_jar import engine

class CoreTests(unittest.TestCase):
    def test_wallet(self):
        self.assertTrue(engine.valid_address(engine.DONATION_ADDRESS))
        for v in ("", "not-a-wallet", "0"*95, engine.DONATION_ADDRESS+"x"):
            self.assertFalse(engine.valid_address(v))
    def test_thread_limits(self):
        self.assertEqual(engine.threads_for("Low",8),2)
        self.assertEqual(engine.threads_for("Medium",8),4)
        self.assertEqual(engine.threads_for("High",8),6)
        self.assertEqual(engine.threads_for("Low",1),1)
        with self.assertRaises(ValueError): engine.threads_for("unlimited",8)
        with self.assertRaises(ValueError): engine.threads_for("High",0)
    def test_durations(self):
        self.assertEqual(engine.seconds_for("10 days"),864000)
        with self.assertRaises(ValueError): engine.seconds_for("forever")
    def test_pinned_digest_rejects_changes(self):
        d=b"archive"
        engine.verify_bytes(d,hashlib.sha256(d).hexdigest())
        with self.assertRaises(ValueError): engine.verify_bytes(d+b"evil",hashlib.sha256(d).hexdigest())
    def test_windows_zip_single_binary(self):
        buf=io.BytesIO()
        with zipfile.ZipFile(buf,"w") as z:
            z.writestr("xmrig-6.26.0/xmrig.exe",b"safe")
            z.writestr("../../unrelated",b"ignore")
        self.assertEqual(engine.extract_executable(buf.getvalue(),"Windows"),b"safe")
    def test_linux_tar_single_binary(self):
        buf=io.BytesIO()
        with tarfile.open(fileobj=buf,mode="w:gz") as t:
            data=b"safe"
            info=tarfile.TarInfo("xmrig-6.26.0/xmrig")
            info.size=len(data)
            t.addfile(info,io.BytesIO(data))
        self.assertEqual(engine.extract_executable(buf.getvalue(),"Linux"),b"safe")
    def test_link_not_executable(self):
        buf=io.BytesIO()
        with tarfile.open(fileobj=buf,mode="w:gz") as t:
            link=tarfile.TarInfo("xmrig")
            link.type=tarfile.SYMTYPE
            link.linkname="/etc/passwd"
            t.addfile(link)
        with self.assertRaises(ValueError): engine.extract_executable(buf.getvalue(),"Linux")
    def test_cached_binary_tamper_blocked(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = pathlib.Path(tmp) / "xmrig"
            path.write_bytes(b"not-real-xmrig")
            with self.assertRaises(ValueError): engine.verified_local_executable(path)
    def test_command_safety(self):
        args=engine.command(pathlib.Path("/tmp/miner"),"Low")
        commandline=" ".join(args)
        self.assertIn("--tls", args)
        self.assertIn("--no-huge-pages", args)
        self.assertIn("--randomx-wrmsr=-1", args)
        self.assertNotIn("--background",commandline)
        self.assertNotIn("--cpu-priority=5",commandline)
        self.assertIn("--user="+engine.DONATION_ADDRESS,args)
    def test_rate_parser(self):
        self.assertEqual(engine.parse_hashrate("speed 10s/60s/15m 102.3 120.3 n/a H/s"),102.3)
        self.assertIsNone(engine.parse_hashrate("speed 10s/60s/15m n/a n/a n/a H/s"))
    @unittest.skipIf(os.name=="nt", "POSIX-only simulated miner test")
    def test_simulated_process_stop_and_timeout(self):
        with tempfile.TemporaryDirectory() as tmp:
            exe=pathlib.Path(tmp)/"fake_xmrig"
            exe.write_text("#!/usr/bin/env python3\nimport time\nprint('speed 10s/60s/15m 42.0 n/a n/a H/s',flush=True)\nwhile True: time.sleep(0.2)\n")
            exe.chmod(exe.stat().st_mode|stat.S_IXUSR)
            s=engine.Session()
            try:
                s.start("Low","1 hour",exe)
                self.assertTrue(s.running())
                for i in range(40):
                    if not s.messages.empty(): break
                    time.sleep(.05)
                self.assertEqual(s.messages.get(timeout=3)[0],"rate")
                s.deadline=time.monotonic()-1
                self.assertEqual(s.tick(),"duration")
                self.assertFalse(s.running())
            finally: s.stop()
    def test_no_process_at_import(self):
        session=engine.Session()
        self.assertFalse(session.running())

if __name__=="__main__":
    unittest.main()

import subprocess,sys
from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[1]
class TestPortalGate(unittest.TestCase):
 def test_gate_entrypoint(self):
  result=subprocess.run([sys.executable,str(ROOT/'scripts/github_portal_analitico_final_gate.py')],cwd=ROOT,capture_output=True,text=True)
  self.assertEqual(result.returncode,0,result.stdout+result.stderr); self.assertIn('PASS_PORTAL_ANALITICO_FINAL_OFFLINE_READY_FOR_BUILD',result.stdout)
if __name__=='__main__': unittest.main()

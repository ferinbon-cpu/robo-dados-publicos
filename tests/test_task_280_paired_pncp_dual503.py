import unittest
from robo_dados_publicos.research.task280_paired_pncp_dual503 import validate
class T(unittest.TestCase):
 def test_validate(self): self.assertEqual(validate()["status"],"PASS_TASK280_PAIRED_PNCP_DUAL503_CANONIZATION")
if __name__=="__main__":unittest.main()

import unittest
from robo_dados_publicos.research.task273_history_8of8_canonization import validate,rows
class T(unittest.TestCase):
 def test_validate(self):self.assertEqual(validate()["events"],49)
 def test_result_refs_zero(self):self.assertTrue(all(x["result_reference_count"]==0 for x in rows()))
if __name__=="__main__":unittest.main()

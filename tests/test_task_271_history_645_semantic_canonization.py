import unittest
from robo_dados_publicos.research.task271_history_645_semantic_canonization import validate,rows
class T(unittest.TestCase):
 def test_validate(self): self.assertEqual(validate()["events"],3)
 def test_no_user(self): self.assertTrue(all("usuarioNome" not in x for x in rows()))
if __name__=="__main__":unittest.main()

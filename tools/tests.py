from django.test import TestCase
from .l_tools import djconfig

class djconfigtest(TestCase):

  def test_schreiben_lesen_strings(self):
    """
    We write a db line with strings and read it
    """
    djconf = djconfig()
    djconf.setconfig('DontUseThisOneInRealLife', 'DoesNotMatter1')
    self.assertIs(djconf.getconfig('DontUseThisOneInRealLife') == 'DoesNotMatter1', True)
    djconf.setconfig('DontUseThisOneInRealLife', 'DoesNotMatter2')
    self.assertIs(djconf.getconfig('DontUseThisOneInRealLife') == 'DoesNotMatter2', True)
    djconf.delconfig('DontUseThisOneInRealLife')
    self.assertIs(djconf.getconfig('DontUseThisOneInRealLife') is None, True)
    self.assertIs(djconf.getconfig('DontUseThisOneInRealLife', 'DoesNotMatter3')  == 'DoesNotMatter3', True)

  def test_schreiben_lesen_int(self):
    """
    We write a db line with integers and read it
    """
    djconf = djconfig()
    djconf.setconfigint('DontUseThisOneInRealLife', 123456)
    self.assertIs(djconf.getconfigint('DontUseThisOneInRealLife') == 123456, True)
    djconf.setconfigint('DontUseThisOneInRealLife', 234567)
    self.assertIs(djconf.getconfigint('DontUseThisOneInRealLife') == 234567, True)
    djconf.delconfig('DontUseThisOneInRealLife')
    self.assertIs(djconf.getconfigint('DontUseThisOneInRealLife') is None, True)
    self.assertIs(djconf.getconfigint('DontUseThisOneInRealLife', 345678)  == 345678, True)

  def test_schreiben_lesen_float(self):
    """
    We write a db line with floats and read it
    """
    djconf = djconfig()
    djconf.setconfigfloat('DontUseThisOneInRealLife', 123.456)
    self.assertIs(djconf.getconfigfloat('DontUseThisOneInRealLife') == 123.456, True)
    djconf.setconfigfloat('DontUseThisOneInRealLife', 2.34567)
    self.assertIs(djconf.getconfigfloat('DontUseThisOneInRealLife') == 2.34567, True)
    djconf.delconfig('DontUseThisOneInRealLife')
    self.assertIs(djconf.getconfigfloat('DontUseThisOneInRealLife') is None, True)
    self.assertIs(djconf.getconfigfloat('DontUseThisOneInRealLife', 34567.8)  == 34567.8, True)

  def test_schreiben_lesen_bool(self):
    """
    We write a db line with floats and read it
    """
    djconf = djconfig()
    djconf.setconfigbool('DontUseThisOneInRealLife', True)
    self.assertIs(djconf.getconfigbool('DontUseThisOneInRealLife'), True)
    djconf.setconfigbool('DontUseThisOneInRealLife', False)
    self.assertIs(djconf.getconfigbool('DontUseThisOneInRealLife'), False)
    djconf.delconfig('DontUseThisOneInRealLife')
    self.assertIs(djconf.getconfigbool('DontUseThisOneInRealLife') is None, True)
    self.assertIs(djconf.getconfigbool('DontUseThisOneInRealLife', True), True)
    self.assertIs(djconf.getconfigbool('DontUseThisOneInRealLife', False), False)
    djconf.setconfig('DontUseThisOneInRealLife', '1')
    self.assertIs(djconf.getconfigbool('DontUseThisOneInRealLife'), True)
    djconf.setconfig('DontUseThisOneInRealLife', '0')
    self.assertIs(djconf.getconfigbool('DontUseThisOneInRealLife'), False)
    djconf.setconfig('DontUseThisOneInRealLife', 'Ja')
    self.assertIs(djconf.getconfigbool('DontUseThisOneInRealLife'), True)
    djconf.setconfig('DontUseThisOneInRealLife', 'Nein')
    self.assertIs(djconf.getconfigbool('DontUseThisOneInRealLife'), False)

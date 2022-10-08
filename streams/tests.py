from django.test import TestCase

class djconfigtest(TestCase):

  def test_dummy(self):
    """
    der liefert einfach nur OK
    """
    self.assertIs(True, True)

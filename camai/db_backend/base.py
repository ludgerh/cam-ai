from django.db.backends.mysql.base import DatabaseWrapper as BaseDatabaseWrapper

class DatabaseWrapper(BaseDatabaseWrapper):

  def ensure_connection(self):
    if self.connection:
      if not self.is_usable():
        self.close()
    super().ensure_connection()

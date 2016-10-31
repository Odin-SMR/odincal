"""The database model to register a file in the database"""
from datetime import datetime, timedelta
from os.path import basename, splitext

from sqlalchemy import func, Column, String, Date, DateTime
from odincal.database import OdincalDB


class Level0File(OdincalDB.Base):
    """A class to register level0-files"""
    __tablename__ = 'level0_files'

    file = Column(String, primary_key=True)
    measurement_date = Column(Date)
    created = Column(DateTime, default=func.now())

    def __init__(self, filename):
        self.file = basename(filename)
        self.name, self.extension = splitext(self.file)
        self.check_file_type()
        self.measurement_date = self.timestamp_from_filename()
        self.created = datetime.utcnow()

    def timestamp_from_filename(self):
        """ return datetime from filename """
        stw = int(self.name + '0', base=16)
        # reference stw and mjd
        stw0 = 6161431982
        mjd0 = 56416.7782534
        rate = 1 / 16.0016444
        # calculate mjd for the filename stw
        mjd = mjd0 + (stw - stw0) * rate / 86400.0
        # get a time stamp
        timestamp = datetime.date(datetime(1858, 11, 17) + timedelta(days=mjd))
        return timestamp

    def check_file_type(self):
        """ import one file """
        if self.extension not in ['.ac1', '.ac2', '.shk', '.att', '.fba']:
            raise ValueError

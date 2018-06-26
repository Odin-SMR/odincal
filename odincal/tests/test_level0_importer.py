"""Import file to database"""
from odincal.level0_file_importer import Level0File


def test_timestamp():
    """Check STW to date approximation"""
    filename = '/long/path/to/file/1a5ed04b.fba'
    test_file = Level0File(filename)
    assert test_file.measurement_date.isoformat() == '2015-02-27'


def test_file_imported():
    """Check that files are imported"""
    filename = '1a5ed04b.fba'
    test_file = Level0File(filename)
    assert test_file.extension == '.fba'


def test_file_not_imported():
    """Check that 'other' files are not imported"""
    filename = 'other'
    try:
        Level0File(filename)
    except ValueError:
        assert True
    else:
        assert False

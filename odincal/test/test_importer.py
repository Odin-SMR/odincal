"""tester"""
from Queue import Queue
from mockito import when
from odincal.level0_fileserver import Importer  # pylint: disable=import-error


def test_import_function():
    """imports from queue"""
    queue = Queue()
    queue.put('first')
    queue.put('last')
    when(Importer).import_to_database('first').thenReturn(None)
    when(Importer).import_to_database('last').thenRaise(KeyboardInterrupt)
    importer = Importer(queue)
    importer.import_files()

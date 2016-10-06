""" A directory fileserver """
from os.path import isdir
from time import sleep
import threading
import Queue

import logging

from pyinotify import (   # pylint: disable=no-name-in-module
    WatchManager, ProcessEvent, ThreadedNotifier, IN_CREATE, IN_MOVED_TO
)
from odincal.level0_file_importer import import_file


class EventHandler(ProcessEvent):
    """ Event handler """
    def __init__(self, queue):
        self.logger = logging.getLogger('filesystem list')
        self.logger.debug('started filesystem sensor')
        self.queue = queue
        ProcessEvent.__init__(self)

    def process_IN_CREATE(self, event):  # pylint: disable=invalid-name
        """ dick string """
        if isdir(event.pathname):
            self.logger.info(
                "Detected new directory: %s",
                event.pathname
            )
        else:
            self.logger.info(
                'Adding (CREATE) to processing queue: %s',
                event.pathname
            )
            self.queue.put(event.pathname)

    def process_IN_MOVED_TO(self, event):  # pylint: disable=invalid-name
        """A file is moved to..."""
        self.logger.info(
            'Adding (MOVED) to processing queue: %s',
            event.pathname
        )
        self.queue.put(event.pathname)


class Worker(threading.Thread):
    """ A workder thread """
    def __init__(self, queue):
        self.logger = logging.getLogger('worker process')
        self.queue = queue
        threading.Thread.__init__(self)
        self.logger.debug('started worker')

    def run(self):
        while 1:
            try:
                newfile = self.queue.get()
                self.logger.info('processing file %s', newfile)
                import_file(newfile)
                self.queue.task_done()
            except Queue.Empty:
                self.logger.info('Queue is empty')
                break
        self.logger.debug('Worker stopped')


def main():
    """set up fileserver"""
    logging.basicConfig(level=logging.DEBUG)
    logger = logging.getLogger('test_server')
    logger.info('starting testserver')
    queue = Queue.Queue()
    worker = Worker(queue)
    worker.daemon = True
    worker.start()
    manager = WatchManager()
    handler = EventHandler(queue)
    notifier = ThreadedNotifier(manager, handler)
    directory = '/odindata/odin/level0'
    manager.add_watch(
        directory,
        IN_CREATE | IN_MOVED_TO,
        rec=True,
        auto_add=True,
        quiet=False
    )
    logger.info('watching %s', format(directory))
    notifier.start()
    while 1:
        try:
            sleep(60)
            logger.debug(
                'mark - worker[%s] - notifier[%s]',
                str(worker.is_alive()),
                str(notifier.is_alive()),
            )
        except KeyboardInterrupt:
            logger.warn('C-c pressed exiting')
            break
    logger.info('Waiting for worker to finish')
    queue.join()
    notifier.stop()
    logger.info('all jobs done.  normal exit')

if __name__ == '__main__':
    main()

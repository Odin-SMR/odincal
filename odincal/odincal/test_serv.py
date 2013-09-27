from os.path import isdir
from pyinotify import WatchManager,ProcessEvent, ThreadedNotifier, IN_ISDIR, IN_CREATE, IN_CLOSE_WRITE, IN_MOVED_TO
from time import sleep
import threading
import Queue

from pkg_resources import resource_filename
import logging
from odincal.logclient import set_odin_logging

from odincal.level0_file_importer import import_file

class EventHandler(ProcessEvent):
    def __init__(self,queue):
        self.logger = logging.getLogger('filesystem list')
        self.logger.debug('started filesystem sensor')
        self.queue = queue
        ProcessEvent.__init__(self)

    def process_IN_CREATE(self, event):
        if isdir(event.pathname):
            self.logger.info("Detected new directory: {0}".format(event.pathname))
#            wm.add_watch(event.pathname,IN_CREATE|IN_MOVED_TO, rec=True)
        else:
            self.logger.info('Adding (CREATE) to processing queue: {0}'.format(event.pathname))
            self.queue.put(event.pathname)

    def process_IN_MOVED_TO(self, event):
        self.logger.info('Adding (MOVED) to processing queue: {0}'.format(event.pathname))
        self.queue.put(event.pathname)

class Worker(threading.Thread):
    def __init__(self,queue):
        self.logger = logging.getLogger('worker process')
        self.queue = queue
        threading.Thread.__init__(self)
        self.logger.debug('started worker')

    def run(self):
        while 1:
            try:
	        f = self.queue.get()
	        self.logger.info('processing file {0}'.format(f))
                import_file(f)
                self.queue.task_done()
            except Queue.Empty:
                self.logger.info('Queue is empty')
                break
            except:
                self.logger.warn('Unhandled exception')
                break
        self.logger.debug('Worker stopped')

def main():
    set_odin_logging()
    logger = logging.getLogger('test_server')
    logger.info('starting testserver')
    queue = Queue.Queue()
    worker = Worker(queue)
    worker.daemon = True
    worker.start()
    wm = WatchManager()
    handler = EventHandler(queue)
    notifier = ThreadedNotifier(wm, handler)
    directory = '/odindata/odin/level0'
    wdd = wm.add_watch(directory, IN_CREATE | IN_MOVED_TO, rec=True,
            auto_add=True, quiet=False)
    logger.info('watching {0}'.format(directory))
    notifier.start()
    while 1:
        try:
            sleep(60)
            logger.debug('mark - worker[{}] - notifier[{}]'.format(
                    worker.is_alive(),notifier.is_alive()))
        except KeyboardInterrupt:
            logger.warn('C-c pressed exiting')
            break
    logger.info('Waiting for worker to finish')
    queue.join()
    notifier.stop()
    logger.info('all jobs done.  normal exit')

if __name__=='__main__':

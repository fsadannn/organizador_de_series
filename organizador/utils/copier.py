from __future__ import annotations

import time
from queue import Queue

from PyQt5.QtCore import QObject, QThread, pyqtSignal, pyqtSlot

from .qt_utils import reconnect


class _CopyTask(QThread):
    """Worker thread that pulls tasks from a queue."""
    names = pyqtSignal(str, str)
    progress = pyqtSignal(int, int, float)
    finish = pyqtSignal()
    finish2 = pyqtSignal()

    def __init__(self, copier: Copier):
        self.copier: Copier = copier
        super().__init__(copier)

    def run(self):
        queue = self.copier.queue
        while True:
            task = queue.get(block=True)
            try:
                if task is None:
                    break
                src_file, dst_file, total, src_path, dst_path = task
                # print('processing: ' + src_path)
                _chunk_size = 1024 * 1024
                read = src_file.read
                write = dst_file.write
                self.names.emit(src_path, dst_path)
                count = 0
                timeit = time.time()
                timeitold = 0
                speedd = 0
                # The 'or None' is so that it works with binary and text files
                for chunk in iter(lambda: read(_chunk_size) or None, None):
                    write(chunk)
                    lchunk = len(chunk)
                    count += lchunk
                    t1 = timeitold
                    t2 = timeit
                    t1 = t2
                    t2 = time.time()
                    speedd = lchunk / max(t2 - t1, 1e-12)
                    self.progress.emit(total, count, speedd)
                dst_file.close()
                self.finish.emit()
                self.emit.finish2()
            except Exception as error:
                self.copier.add_error(error)
            finally:
                queue.task_done()


class Copier(QObject):
    finish = pyqtSignal()

    def __init__(self):
        super(Copier, self).__init__()
        self.queue = Queue()
        self.errors = []
        self.running = True
        self.worker = _CopyTask(self)
        reconnect(self.worker.finish2, self.watch)
        self.worker.start()

    @pyqtSlot()
    def watch(self):
        if self.queue.empty():
            self.finish.emit()

    def start(self):
        self.queue = Queue()
        reconnect(self.worker.finish2)
        self.worker = _CopyTask(self)
        reconnect(self.worker.finish2, self.watch)
        self.worker.start()
        self.running = True

    def stop(self):
        self.queue.put(None)
        self.worker.wait()
        self.queue.join()
        self.running = False

    def add_error(self, error):
        self.errors.append(error)

    def __enter__(self):
        self.start()
        return self

    def __exit__(
        self,
        exc_type,      # type: Optional[Type[BaseException]]
        exc_value,     # type: Optional[BaseException]
        traceback      # type: Optional[TracebackType]
    ):
        self.stop()

    def copy(self, src_fs, src_path, dst_fs, dst_path):
        src_file = src_fs.openbin(src_path, 'r')
        size = src_fs.getinfo(src_path, namespaces=['details']).size
        try:
            dst_file = dst_fs.openbin(dst_path, 'w')
        except Exception as e:
            # If dst file fails to open, explicitly close src_file
            src_file.close()
            # print(e)
            raise
        self.queue.put((src_file, dst_file, size, src_path, dst_path))

import sys

from PyQt5.QtWidgets import QApplication

from stock import MyLogger
from stock.OpenApi import OpenApi


logger = MyLogger.logger
class Collector():
    def __init__(self):
        logger.info("Collector 시작")
        self.app = QApplication(sys.argv)
        self.openapi = OpenApi()

        self.app.exec_() # 이벤트 루프 실행

if __name__ == "__main__":
    collector = Collector()
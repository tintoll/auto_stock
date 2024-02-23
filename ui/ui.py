from kiwoom.kiwoom import *

import sys
from PyQt5.QtWidgets import *
class UI_class():
    def __init__(self):
        print("실행할 UI 클래스")
        self.app = QApplication(sys.argv)

        # 생성만하면 프로세스가 죽어서 self로 받아줌
        self.kiwoom = Kiwoom()

        self.app.exec_() # 이벤트 루프 실행
from PyQt5.QAxContainer import *
from PyQt5.QtCore import *
from config.errorCode import *
class Kiwoom(QAxWidget):
    def __init__(self):
        super().__init__()
        print("실행할 키움 클래스")

        ## event loop 모음 ##
        self.login_event_loop = None
        ####################

        ## 변수 모음 ##
        self.account_num = None
        ####################



        self.get_ocx_instance()
        self.event_slots()
        self.signal_login_commConnect()
        self.get_account_info()
    def get_ocx_instance(self):
        # 키움 OpenAPI+의 OCX 방식을 사용하기 위해서는 OCX의 인스턴스를 얻어와야 합니다.
        # 윈도우 레지스트리에 등록된 ProgID를 사용하여 인스턴스를 얻어옵니다.
        self.setControl("KHOPENAPI.KHOpenAPICtrl.1")

    def event_slots(self):
        self.OnEventConnect.connect(self.login_slot)

    def login_slot(self, err_code):
        print(errors(err_code))

        # 로그인이 끝났기 때문에 이벤트 루프를 종료시킵니다.
        self.login_event_loop.exit()

    def signal_login_commConnect(self):
        self.dynamicCall("CommConnect()")

        self.login_event_loop = QEventLoop()
        self.login_event_loop.exec_()

    def get_account_info(self):
        account_list = self.dynamicCall("GetLoginInfo(String)", "ACCNO")
        self.account_num = account_list.split(';')[0]
        print("나의 보유 계좌번호 %s" % self.account_num)
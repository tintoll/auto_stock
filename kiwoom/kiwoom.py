from PyQt5.QAxContainer import *
from PyQt5.QtCore import *
from config.errorCode import *
class Kiwoom(QAxWidget):
    def __init__(self):
        super().__init__()
        print("실행할 키움 클래스")

        ## event loop 모음 ##
        self.login_event_loop = None
        self.detail_account_info_event_loop = None
        self.detail_account_info_event_loop_2 = QEventLoop()
        ####################

        ## 변수 모음 ##
        self.account_num = None
        self.account_stock_dict = {}
        ####################

        ## 계좌 관련 변수 ##
        self.use_money = 0
        self.use_money_percent = 0.5
        ####################

        self.get_ocx_instance()
        self.event_slots()
        self.signal_login_commConnect()
        self.get_account_info() # 계좌번호 가져오기
        self.detail_account_info() # 예수금 가져오기
        self.detail_account_mystock() # 계좌평가잔고내역 가져오기
    def get_ocx_instance(self):
        # 키움 OpenAPI+의 OCX 방식을 사용하기 위해서는 OCX의 인스턴스를 얻어와야 합니다.
        # 윈도우 레지스트리에 등록된 ProgID를 사용하여 인스턴스를 얻어옵니다.
        self.setControl("KHOPENAPI.KHOpenAPICtrl.1")

    def event_slots(self):
        # 로그인 이벤트 연결
        self.OnEventConnect.connect(self.login_slot)
        # 예수금 요청 이벤트 연결
        self.OnReceiveTrData.connect(self.trdata_slot)

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

    def detail_account_info(self):
        print("예수금을 요청하는 부분")
        self.dynamicCall("SetInputValue(String, String)", "계좌번호", self.account_num)
        self.dynamicCall("SetInputValue(String, String)", "비밀번호", "0000")
        self.dynamicCall("SetInputValue(String, String)", "비밀번호입력매체구분", "00")
        self.dynamicCall("SetInputValue(String, String)", "조회구분", "2")
        self.dynamicCall("CommRqData(String, String, int, String)", "예수금상세현황요청", "opw00001", "0", "2000")

        self.detail_account_info_event_loop = QEventLoop()
        self.detail_account_info_event_loop.exec_()

    def detail_account_mystock(self, sPrevNext="0"):
        print("계좌평가잔고내역을 요청하는 부분")
        self.dynamicCall("SetInputValue(String, String)", "계좌번호", self.account_num)
        self.dynamicCall("SetInputValue(String, String)", "비밀번호", "0000")
        self.dynamicCall("SetInputValue(String, String)", "비밀번호입력매체구분", "00")
        self.dynamicCall("SetInputValue(String, String)", "조회구분", "2")
        self.dynamicCall("CommRqData(String, String, int, String)", "계좌평가잔고내역요청", "opw00018", sPrevNext, "2000")

        self.detail_account_info_event_loop_2.exec_() # 다시 요청이 오면 중복 경고가 나올수 있으나 큰 문제는 없다.

    def trdata_slot(self, sScrNo, sRQName, sTrCode, sRecordName, sPrevNext):
        '''
        TR 요청을 받는 구역, 슬롯이다.
        :param sScrNo: 스크린번호
        :param sRQName: 내가 요청햇을때 지은 이름
        :param sTrCode: 요청 id, tr코드
        :param sRecordName: 사용안함
        :param sPrevNext: 다음 페이지가 있는지
        :return:
        '''
        if sRQName == "예수금상세현황요청":
            deposit = self.dynamicCall("GetCommData(String, String, int, STring)", sTrCode, sRQName, 0, "예수금")
            print("예수금 %s" % deposit) # "000000010000000"
            print("예수금 형변환 %s" % int(deposit)) # 10000000

            # 현재 예수금에서 실제 사용할 돈을 계산
            self.use_money = int(deposit) * self.use_money_percent
            # 한번에 사용할 금액을 4등분해서 사용
            self.use_money = self.use_money / 4

            ok_deposit = self.dynamicCall("GetCommData(String, String, int, STring)", sTrCode, sRQName, 0, "출금가능금액")
            print("출금가능금액 %s" % ok_deposit)
            print("출금가능금액 형변환 %s" % int(ok_deposit))

            self.detail_account_info_event_loop.exit()
        if sRQName == "계좌평가잔고내역요청":
            total_buy_money = self.dynamicCall("GetCommData(String, String, int, STring)", sTrCode, sRQName, 0, "총매입금액")
            total_buy_money_result = int(total_buy_money)
            print("총매입금액 %s" % total_buy_money_result)

            total_profit_loss_rate = self.dynamicCall("GetCommData(String, String, int, STring)", sTrCode, sRQName, 0, "총수익률(%)")
            total_profit_loss_rate_result = float(total_profit_loss_rate)
            print("총수익률(%%) %s" % total_profit_loss_rate_result)
            
            # 멀티데이터 조회 (내가 매수한 종목들에 대한 정보를 조회)
            # QString으로 통일하자, 원래 아무명이나 사용해도 되는데 안되는경우도 있다고 함.
            rows = self.dynamicCall("GetRepeatCnt(QString, QString)", sTrCode, sRQName)
            cnt = 0 # 종목이 몇개인지 확인
            for i in range(rows):
                # A003322 = 종목번호, A:장내주식,J:ETF,Q:ETN종목
                code = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, "종목번호")
                code = code.strip()[1:] # 앞에 문자 하나 제거, strip()은 양쪽공백제거
                code_nm = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, "종목명")
                stock_quantity = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, "보유수량")
                buy_price = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, "매입가")
                learn_rate = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, "수익률(%)")
                current_price = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, "현재가")
                total_chegyul_price = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, "매입금액")
                possible_quantity = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, "매매가능수량")

                # dict에 종목코드가 없으면 추가
                if code in self.account_stock_dict:
                    pass
                else:
                    self.account_stock_dict.update({code: {}})

                code_nm = code_nm.strip()
                stock_quantity = int(stock_quantity.strip())
                buy_price = int(buy_price.strip())
                learn_rate = float(learn_rate.strip())
                current_price = int(current_price.strip())
                total_chegyul_price = int(total_chegyul_price.strip())
                possible_quantity = int(possible_quantity.strip())

                # dict에 종목코드에 대한 정보를 업데이트
                self.account_stock_dict[code].update({"종목명": code_nm})
                self.account_stock_dict[code].update({"보유수량": stock_quantity})
                self.account_stock_dict[code].update({"매입가": buy_price})
                self.account_stock_dict[code].update({"수익률": learn_rate})
                self.account_stock_dict[code].update({"현재가": current_price})
                self.account_stock_dict[code].update({"매입금액": total_chegyul_price})
                self.account_stock_dict[code].update({"매매가능수량": possible_quantity})
                cnt += 1
            print("계좌에 가지고 있는 종목 %s" % self.account_stock_dict)
            print("계좌에 가지고 있는 종목 수 %s" % cnt)

            if sPrevNext == "2": # 0이면 다음페이지가 없다는 뜻, 2이면 다음페이지가 있다는 뜻
                self.detail_account_mystock(sPrevNext="2")
            else:
                self.detail_account_info_event_loop_2.exit() # 다음페이지가 없으면 이벤트루프를 종료시킨다.

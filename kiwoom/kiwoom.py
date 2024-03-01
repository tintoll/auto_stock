import os

from PyQt5.QAxContainer import *
from PyQt5.QtCore import *
from config.errorCode import *
from PyQt5.QtTest import *
from config.kiwoomType import *

class Kiwoom(QAxWidget):
    def __init__(self):
        super().__init__()
        print("실행할 키움 클래스")

        self.realType = RealType()

        ## event loop 모음 ##
        self.login_event_loop = None
        self.detail_account_info_event_loop = QEventLoop()
        self.calculator_event_loop = QEventLoop()
        ####################

        ## 스크린 번호 모음 ##
        self.screen_my_info = "2000"
        self.screen_calculation_stock = "4000"
        self.screen_real_stock = "5000" # 종목별로 할당할 스크린 번호
        self.screen_meme_stock = "6000" # 종목별 할당할 주문용 스크린 번호
        self.screen_start_stop_real = "1000" # 장 시작/종료 실시간 스크린 번호
        ####################

        ## 변수 모음 ##
        self.account_num = None
        self.account_stock_dict = {}
        self.not_account_stock_dict ={}
        self.portfolio_stock_dict = {}
        ####################

        ### 종목 분석용 ###
        self.calcul_data = []
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
        self.not_concluded_account() # 미체결 요청

        # self.calculator_fnc() # 종목 분석용, 임시용으로 실행


        self.read_code() # 저장된 종목 읽어오기
        self.screen_number_setting() # 스크린 번호를 할당
        self.real_event_slots() # 실시간 이벤트 연결
        
        # 장시작 이냐? 아니냐?를 확인
        self.dynamicCall("SetRealReg(QString, QString, QString, QString)", self.screen_start_stop_real, self.realType.REALTYPE["장시작시간"]["장운영구분"], "0")

        for code in self.portfolio_stock_dict.keys():
            screen_num = self.portfolio_stock_dict[code]["스크린번호"]
            fids = self.realType.REALTYPE["주식체결"]["체결시간"] # 1틱별로 보내줌.
            self.dynamicCall("SetRealReg(QString, QString, QString, QString)", screen_num, code, fids, "1") # 1은 추가 등록이라
            print("실시간 등록 코드: %s, 스크린번호: %s, fid번호: %s" % (code, screen_num, fids))


    def get_ocx_instance(self):
        # 키움 OpenAPI+의 OCX 방식을 사용하기 위해서는 OCX의 인스턴스를 얻어와야 합니다.
        # 윈도우 레지스트리에 등록된 ProgID를 사용하여 인스턴스를 얻어옵니다.
        self.setControl("KHOPENAPI.KHOpenAPICtrl.1")

    def event_slots(self):
        # 로그인 이벤트 연결
        self.OnEventConnect.connect(self.login_slot)
        # 예수금 요청 이벤트 연결
        self.OnReceiveTrData.connect(self.trdata_slot)
    def real_event_slots(self):
        self.OnReceiveRealData.connect(self.realdata_slot)

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
        self.dynamicCall("CommRqData(String, String, int, String)", "예수금상세현황요청", "opw00001", "0", self.screen_my_info)

        self.detail_account_info_event_loop.exec_()

    def detail_account_mystock(self, sPrevNext="0"):
        print("계좌평가잔고내역을 요청하는 부분")
        self.dynamicCall("SetInputValue(String, String)", "계좌번호", self.account_num)
        self.dynamicCall("SetInputValue(String, String)", "비밀번호", "0000")
        self.dynamicCall("SetInputValue(String, String)", "비밀번호입력매체구분", "00")
        self.dynamicCall("SetInputValue(String, String)", "조회구분", "2")
        self.dynamicCall("CommRqData(String, String, int, String)", "계좌평가잔고내역요청", "opw00018", sPrevNext, self.screen_my_info)

        self.detail_account_info_event_loop.exec_() # 다시 요청이 오면 중복 경고가 나올수 있으나 큰 문제는 없다.

    def not_concluded_account(self):
        print("미체결 요청하는 부분")
        self.dynamicCall("SetInputValue(String, String)", "계좌번호", self.account_num)
        self.dynamicCall("SetInputValue(String, String)", "전체종목구분", "0")
        self.dynamicCall("SetInputValue(String, String)", "매매구분", "0")
        self.dynamicCall("SetInputValue(String, String)", "종목코드", "0")
        self.dynamicCall("SetInputValue(String, String)", "체결구분", "1")
        self.dynamicCall("CommRqData(String, String, int, String)", "미체결요청", "opt10075", 0, self.screen_my_info)

        self.detail_account_info_event_loop.exec_()

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
            # print("예수금 %s" % deposit) # "000000010000000"
            print("예수금 형변환 %s" % int(deposit)) # 10000000

            # 현재 예수금에서 실제 사용할 돈을 계산
            self.use_money = int(deposit) * self.use_money_percent
            # 한번에 사용할 금액을 4등분해서 사용
            self.use_money = self.use_money / 4

            ok_deposit = self.dynamicCall("GetCommData(String, String, int, STring)", sTrCode, sRQName, 0, "출금가능금액")
            # print("출금가능금액 %s" % ok_deposit)
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
                account_code_dict = self.account_stock_dict[code]
                account_code_dict.update({"종목명": code_nm})
                account_code_dict.update({"보유수량": stock_quantity})
                account_code_dict.update({"매입가": buy_price})
                account_code_dict.update({"수익률": learn_rate})
                account_code_dict.update({"현재가": current_price})
                account_code_dict.update({"매입금액": total_chegyul_price})
                account_code_dict.update({"매매가능수량": possible_quantity})
                cnt += 1
            print("계좌에 가지고 있는 종목 %s" % self.account_stock_dict)
            print("계좌에 가지고 있는 종목 수 %s" % cnt)

            if sPrevNext == "2": # 0이면 다음페이지가 없다는 뜻, 2이면 다음페이지가 있다는 뜻
                self.detail_account_mystock(sPrevNext="2")
            else:
                self.detail_account_info_event_loop.exit() # 다음페이지가 없으면 이벤트루프를 종료시킨다.
        elif sRQName == "미체결요청":
            rows = self.dynamicCall("GetRepeatCnt(QString, QString)", sTrCode, sRQName)
            for i in range(rows):
                code = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, "종목코드")
                code_nm = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, "종목명")
                order_no = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, "주문번호")
                order_status = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, "주문상태") # 접수, 확인, 체결
                order_quantity = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, "주문수량")
                order_price = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, "주문가격")
                order_gubun = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, "주문구분") # -매도, +매수
                not_quantity = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, "미체결수량")
                ok_quantity = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, "체결량")

                code = code.strip()
                code_nm = code_nm.strip()
                order_no = int(order_no.strip())
                order_status = order_status.strip()
                order_quantity = int(order_quantity.strip())
                order_price = int(order_price.strip())
                order_gubun = order_gubun.strip().lstrip('+').lstrip('-') # 기호가 들어가서 삭제해준다.
                not_quantity = int(not_quantity.strip())
                ok_quantity = int(ok_quantity.strip())

                if order_no in self.not_account_stock_dict:
                    pass
                else:
                    self.not_account_stock_dict[order_no] = {}
                order_dict = self.not_account_stock_dict[order_no]
                order_dict.update({"종목코드": code})
                order_dict.update({"종목명": code_nm})
                order_dict.update({"주문번호": order_no})
                order_dict.update({"주문상태": order_status})
                order_dict.update({"주문수량": order_quantity})
                order_dict.update({"주문가격": order_price})
                order_dict.update({"주문구분": order_gubun})
                order_dict.update({"미체결수량": not_quantity})
                order_dict.update({"체결량": ok_quantity})

                print("미체결 종목 %s" % self.not_account_stock_dict[order_no])

            self.detail_account_info_event_loop.exit()
        elif "주식일봉차트조회" == sRQName:
            code = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, 0, "종목코드")
            code = code.strip() # 앞뒤 공백 제거, 앞에 공백이 엄청많음
            print("%s 일봉 데이터 요청" % code)

            # GetCommDataEx는 한번에 600개까지만 가져올수 있다.
            # data = self.dynamicCall("GetCommDataEx(QString, QString)", sTrCode, sRQName)
            #  [['', '현재가', '거래량', '거래대금', '일자', '시가', '고가', '저가', ''], [], [], ...]
            cnt = self.dynamicCall("GetRepeatCnt(QString, QString)", sTrCode, sRQName)
            print("데이터 일수 %s" % cnt)
            for i in range(cnt):
                data = []
                current_price = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, "현재가")
                value = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, "거래량")
                trading_value = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, "거래대금")
                date = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, "일자")
                start_price = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, "시가")
                high_price = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, "고가")
                low_price = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, "저가")

                # 구조 맞추기 위해서 동일하게 등록
                data.append("")
                data.append(current_price.strip())
                data.append(value.strip())
                data.append(trading_value.strip())
                data.append(date.strip())
                data.append(start_price.strip())
                data.append(high_price.strip())
                data.append(low_price.strip())
                data.append("")

                self.calcul_data.append(data.copy())

            # 일봉의 데이터 한번에 600개까지만 가져올수 있다.
            if sPrevNext == "2":
                self.day_kiwoom_db(code=code, sPrevNext=sPrevNext)
            else:
                # 종목에 대한 데이터가 다 만들어졌으니 실제 그린벨 법칙에 맞는 종목을 찾아서 파일로 만들어 놓는다.
                print("총 일수 %s" % len(self.calcul_data))

                pass_success = False
                # 120일 이평선을 그릴만큼의 데이터가 있는지 확인
                if self.calcul_data == None or len(self.calcul_data) < 120:
                    pass_success = False
                else:
                    total_price = 0
                    for value in self.calcul_data[:120]:
                        total_price += int(value[1])
                    # 120일 이평선
                    moving_average_price = total_price / 120
                    # 오늘 저가가 120일이평보다 작고 고가가 120일이평보다 큰지 확인
                    bottom_stock_price = False
                    check_price = None
                    if int(self.calcul_data[0][7]) <= moving_average_price and moving_average_price <= int(self.calcul_data[0][6]):
                        print("오늘 주가가 120일 이평선에 걸쳐있는지 확인 ")
                        bottom_stock_price = True
                        check_price = int(self.calcul_data[0][6])

                    # 과거 일봉들이 120일 이평선보다 밑에 있는지 확인
                    # 그렇게 확인을 하다가 일봉이 120일 이평선 위에 있으면 계산을 진행
                    prev_price = None # 과거의 일봉 저가
                    if bottom_stock_price == True:
                        moving_average_price_prev = 0
                        price_top_moving = False
                        idx = 1
                        while True:
                            if len(self.calcul_data[idx:]) < 120:
                                print("120일치가 없음!")
                                break
                            total_price = 0
                            for value in self.calcul_data[idx:120+idx]:
                                total_price += int(value[1])
                            moving_average_price_prev = total_price / 120

                            if moving_average_price_prev <= int(self.calcul_data[idx][7]) and idx <= 20:
                                print("20일 동안 주가가 120일 이평선과 같거나 위에 있으면 통과 실패")
                                price_top_moving = False
                                break
                            elif int(self.calcul_data[idx][7]) > moving_average_price_prev and idx > 20:
                                print("120일 이평선 위에 있는 일봉 확인됨")
                                price_top_moving = True
                                prev_price = int(self.calcul_data[idx][7])
                                break
                            idx += 1

                            # 해당 부분 이평선이 가장 최근일자의 이평선 가격보다 낮은지 확인
                            if price_top_moving == True:
                                if moving_average_price > moving_average_price_prev and check_price > prev_price:
                                    print("포착된 이평선의 가격이 오늘자(최근일자) 이평선 가격보다 낮은 것 확인됨")
                                    print("포착된 부분의 일봉 저가가 오늘자 일봉의 고가보다 낮은지 확인됨")
                                    pass_success = True
                if pass_success == True:
                    print("조건부 통과됨")
                    # 코드가지고 이름 가져오기
                    code_nm = self.dynamicCall("GetMasterCodeName(QString)", code)
                    # 파일로 저장 a는 append의 약자
                    f = open("files/condition_stock.txt", "a", encoding="utf8")
                    # 종목코드, 종목명, 오늘 종가
                    f.write("%s\t%s\t%s\n" % (code, code_nm, str(self.calcul_data[0][1]))) # 문자로만 들어가야함.
                    f.close()
                elif pass_success == False:
                    print("조건부 통과 못함")

                self.calcul_data.clear() # 데이터를 다시 초기화
                self.calculator_event_loop.exit()

    def get_code_list_by_market(self, market_code):
        '''
        종목코드들을 반환
        :param market_code:
        :return:
        '''

        code_list = self.dynamicCall("GetCodeListByMarket(QString)", market_code)
        code_list = code_list.split(';')[:-1] # 마지막은 공백이라서 제거
        return code_list

    def calculator_fnc(self):
        '''
        종목 분석 실행용 함수
        :return:
        '''
        code_list = self.get_code_list_by_market("10") # 코스닥
        print("코스닥 갯수 %s" % len(code_list))

        for idx, code in enumerate(code_list):
            # 스크린번호에 대한 연결을 끊어준다.
            # 스크린번호를 한번이라도 요청하면 그룹이 만들어진다.
            self.dynamicCall("DisconnectRealData(QString)", self.screen_calculation_stock)
            print("%s / %s : Kosdaq Stock Code : %s is updating..." % (idx+1, len(code_list), code))
            self.day_kiwoom_db(code=code)


    def day_kiwoom_db(self, code=None, date=None, sPrevNext="0"):
        # 한번에 많은 요청이 들어가면 서버에서 막아버린다. 그래서 지연을 준다. 3.6초 정도 지연을 준다.
        QTest.qWait(3600)

        self.dynamicCall("SetInputValue(QString, QString)", "종목코드", code)
        self.dynamicCall("SetInputValue(QString, QString)", "수정주가구분", "1")
        if date != None:
            self.dynamicCall("SetInputValue(QString, QString)", "기준일자", date)

        self.dynamicCall("CommRqData(QString, QString, int, QString)", "주식일봉차트조회", "opt10081", sPrevNext, self.screen_calculation_stock)
        self.calculator_event_loop.exec_()

    def read_code(self):
        if os.path.exists("files/condition_stock.txt"):
            f = open("files/condition_stock.txt", "r", encoding="utf8")
            lines = f.readlines()
            for line in lines:
                if line != "":
                    ls = line.split("\t")

                    stock_code = ls[0]
                    stock_name = ls[1]
                    stock_price = int(ls[2].split("\n")[0])
                    stock_price = abs(stock_price) # 전날하락했으면 -가 붙는다.

                    self.portfolio_stock_dict.update({stock_code: {"종목명": stock_name, "현재가": stock_price}})
            f.close()
            print(self.portfolio_stock_dict)

    def screen_number_setting(self):
        screen_overwrite = []
        # 계좌평가잔고내역을 있는 종목들
        for code in self.account_stock_dict.keys():
            if code not in screen_overwrite:
                screen_overwrite.append(code)
        # 미체결 요청에 있는 종목들
        for order_number in self.not_account_stock_dict.keys():
            code = self.not_account_stock_dict[order_number]["종목코드"]
            if code not in screen_overwrite:
                screen_overwrite.append(code)
        # 포트폴리오에 있는 종목들
        for code in self.portfolio_stock_dict.keys():
            if code not in screen_overwrite:
                screen_overwrite.append(code)
        # 스크린번호 하나에 요청 개수는 100개까지
        # 스크린번호는 200개까지 생성가능
        cnt = 0
        for code in screen_overwrite:
            temp_screen = int(self.screen_real_stock)
            meme_screen = int(self.screen_meme_stock)
            if (cnt % 50) == 0:
                temp_screen += 1
                meme_screen += 1
                self.screen_real_stock = str(temp_screen)
                self.screen_meme_stock = str(meme_screen)

            if code in self.portfolio_stock_dict.keys():
                self.portfolio_stock_dict[code].update({"스크린번호": str(self.screen_real_stock)})
                self.portfolio_stock_dict[code].update({"주문용스크린번호": str(self.screen_meme_stock)})
            elif code not in self.portfolio_stock_dict.keys():
                self.portfolio_stock_dict.update({code: {"스크린번호": str(self.screen_real_stock), "주문용스크린번호": str(self.screen_meme_stock)}})

            cnt += 1
        print(self.portfolio_stock_dict)

    def realdata_slot(self, sCode, sRealType, sRealData):
        if sRealType == "장시작시간":
            fid = self.realType.REALTYPE[sRealType]['장운영구분']
            value = self.dynamicCall("GetCommRealData(QString, int)", sCode, fid)
            if value == "0":
                print("장 시작 전")
            elif value == "3":
                print("장 시작")
            elif value == "2":
                print("장 종료, 동시호가로 넘어감")
            elif value == "4":
                print("3시30분 장 종료")
        elif sRealType == "주식체결":
            print(sCode)


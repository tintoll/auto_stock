import logging
import sys

from PyQt5.QAxContainer import QAxWidget
from PyQt5.QtCore import QEventLoop

from config.errorCode import errors
from stock import MyLogger
from stock.Crawler import crawling
import pandas as pd
from datetime import datetime

logger = MyLogger.logger

class OpenApi(QAxWidget):
    def __init__(self):
        super().__init__()
        logger.info("OpenAPI 실행")

        ## event loop ##
        self.login_event_loop = None
        ################

        self.set_ocx_instance()
        self.set_signal_slots()

        self.login()
        # 종목 코드 가져오기
        all_code_list = self.getStockCodeList() # [000020,00000, ...]
        stockInfoList = []
        for stockCode in all_code_list[:20]:
            stockInfo = self.makeStockInfo(stockCode)
            # 필터 조건
            if not (stockInfo['codeName'].endswith(('우', '우B')) and
                    stockInfo['construction'] not in ['거래정지', '관리종목', '투자주의환기종목']) :
                # 현재가치
                currentTotalPrice = stockInfo['자본금'] * ((float(stockInfo['자본유보율']) - float(stockInfo['부채비율'])) / 100)
                stockInfo['currentTotalPrice'] = currentTotalPrice
                stockInfoList.append(stockInfo)

        # DataFrame 생성
        df = pd.DataFrame(stockInfoList)
        # Excel 파일로 저장
        excel_file = f'주식종목_{datetime.now().strftime("%Y%m%d")}.xlsx'
        df.to_excel(excel_file, index=False)
        logger.info(f'{excel_file} 파일 저장 완료')

        sys.exit(0)

    def makeStockInfo(self, stockCode):
        stockInfo = {
            "code": stockCode,
        }
        code_name = self.dynamicCall("GetMasterCodeName(QString)", stockCode)
        construction = self.dynamicCall("GetMasterConstruction(QString)", stockCode)
        stockInfo['codeName'] = code_name
        stockInfo['construction'] = construction

        advanceInfo = crawling(stockCode)
        if advanceInfo:
            stockInfo.update(advanceInfo)

        return stockInfo

    def getStockCodeList(self):
        kospi_code_list = self.dynamicCall("GetCodeListByMarket(QString)", "0")
        kospi_code_list = kospi_code_list.split(';')[:-1]  # 마지막은 공백이라서 제거
        kosdaq_code_list = self.dynamicCall("GetCodeListByMarket(QString)", "10")
        kosdaq_code_list = kosdaq_code_list.split(';')[:-1]
        logger.info("코스피 종목 갯수 : %s" % len(kospi_code_list))
        logger.info("코스닥 종목 갯수 : %s" % len(kosdaq_code_list))
        all_code_list = kospi_code_list + kosdaq_code_list
        return all_code_list

    def set_signal_slots(self):
        self.OnEventConnect.connect(self.login_slot)
        self.OnReceiveTrData.connect(self.trdata_slot)
        self.OnReceiveMsg.connect(self.msg_slot)

    def login_slot(self, err_code):
        logger.info(errors(err_code))
        self.login_event_loop.exit()
        logger.info("로그인 완료")

    def trdata_slot(self, sScrNo, sRQName, sTrCode, sRecordName, sPrevNext):
        pass

    # 송수신 메시지 get
    def msg_slot(self, sScrNo, sRQName, sTrCode, msg):
        logger.info("스크린 : %s, 요청이름 : %s, tr코드 : %s --- %s" % (sScrNo, sRQName, sTrCode, msg))

    def login(self):
        self.dynamicCall("CommConnect()")
        self.login_event_loop = QEventLoop()
        self.login_event_loop.exec_()


    def set_ocx_instance(self):
        self.setControl("KHOPENAPI.KHOpenAPICtrl.1")
        logger.info("Ocx Instance 설정 완료")

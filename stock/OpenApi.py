import logging
import sys

import sqlalchemy
from PyQt5.QAxContainer import QAxWidget
from PyQt5.QtCore import QEventLoop
from pandas import DataFrame

from config.errorCode import errors
from stock import MyLogger
from stock.Crawler import crawling
import pandas as pd
from datetime import datetime

from stock.Repository import Repository

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
        all_code_list = self.getStockCodeList()  # [000020,00000, ...]
        stockInfoList = []
        for stockCode in all_code_list:
            stockInfo = self.makeStockInfo(stockCode)
            print(stockInfo)
            if stockInfo and not (stockInfo['자본유보율'] == '' or stockInfo['부채비율'] == ''):
                # 현재가치 구하기
                currentTotalPrice = stockInfo['자본금'] * ((float(stockInfo['자본유보율']) - float(stockInfo['부채비율'])) / 100)
                stockInfo['currentTotalPrice'] = int(currentTotalPrice)
                stockInfoList.append(stockInfo)

        # DB 생성
        repository = Repository()

        # DataFrame 생성
        df = pd.DataFrame(stockInfoList)
        # DB 저장
        df.to_sql(name="stock_info", con=repository.db_engine, if_exists='replace', index=False
                  , dtype={'code': sqlalchemy.types.NVARCHAR(length=255),
                           'codeName': sqlalchemy.types.NVARCHAR(length=255),
                           'construction': sqlalchemy.types.NVARCHAR(length=255),
                           '시가총액': sqlalchemy.types.BIGINT,
                           '결산분기': sqlalchemy.types.NVARCHAR(length=255),
                           '영역이익': sqlalchemy.types.BIGINT,
                           '당기순이익': sqlalchemy.types.BIGINT,
                           '자본금': sqlalchemy.types.BIGINT,
                           '부채비율': sqlalchemy.types.NVARCHAR(length=255),
                           '자본유보율': sqlalchemy.types.NVARCHAR(length=255),
                           'EPS': sqlalchemy.types.NVARCHAR(length=255),
                           'PER': sqlalchemy.types.NVARCHAR(length=255),
                           'BPS': sqlalchemy.types.NVARCHAR(length=255),
                           'PBR': sqlalchemy.types.NVARCHAR(length=255),
                           'currentTotalPrice': sqlalchemy.types.BIGINT,
                           })
        # # Excel 파일로 저장
        # excel_file = f'주식종목_{datetime.now().strftime("%Y%m%d")}.xlsx'
        # df.to_excel(excel_file, index=False)
        # logger.info(f'{excel_file} 파일 저장 완료')

        sys.exit(0)

    def makeStockInfo(self, stockCode):

        code_name = self.dynamicCall("GetMasterCodeName(QString)", stockCode)
        construction = self.dynamicCall("GetMasterConstruction(QString)", stockCode)
        stockInfo = {
            "code": stockCode,
            'codeName': code_name,
            'construction': construction,
            '시가총액': 0,
            '결산분기': '',
            '영역이익': 0,
            '당기순이익': 0,
            '자본금': 0,
            '부채비율': '',
            '자본유보율': '',
            'EPS': '',
            'PER': '',
            'BPS': '',
            'PBR': ''
        }

        etfNetn = ['KODEX ', 'KOSEF ', 'TIGER ', 'KBSTAR ', 'ACE ', 'TREX ', 'ARIRANG ', 'SOL ', 'HANARO ', 'FOCUS ',
                   'TIMEFOLIO ', 'HK ', '마이다스 ', 'MASTER ', '에셋플러스 ', 'WOORI ', 'VITA ', '히어로즈 ', 'UNICORN ', '대신343 ',
                   '마이티 ', 'BNK ', 'KTOP ', 'KoAct ', 'TRUSTON ', 'ITF ', '신한 ', '대신 ', '미래에셋 ', '삼성 ', 'QV ', '한투 ',
                   'KB ', '메리츠 ', '하나 ', '키움 ']

        # 시작하는거 제외 etf, etn
        if stockInfo['codeName'].endswith(('우', '우B')) or stockInfo['codeName'].startswith(tuple(etfNetn)): 
            return None

        if stockInfo['codeName'].includes('스팩'):
            return None
            
        if stockInfo['construction'] in ['거래정지', '관리종목','투자주의환기종목']:    
            return None

        advanceInfo = crawling(stockCode)
        if advanceInfo:
            stockInfo.update(advanceInfo)

        return stockInfo

    def getStockCodeList(self):
        kospi_code_list = self.dynamicCall("GetCodeListByMarket(QString)", "0")
        kospi_code_list = kospi_code_list.split(';')[:-1]  # 마지막은 공백이라서 제거
        kosdaq_code_list = self.dynamicCall("GetCodeListByMarket(QString)", "10")
        kosdaq_code_list = kosdaq_code_list.split(';')[:-1]
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

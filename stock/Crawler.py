import requests
from bs4 import BeautifulSoup
import time
from selenium import webdriver
from stock import MyLogger

logger = MyLogger.logger

chrome_options = webdriver.ChromeOptions()
chrome_options.add_argument("--headless")  # 브라우저가 보이지 않도록 설정
driver = webdriver.Chrome(options=chrome_options)
def crawling(stockCode):
    # url = f"https://finance.naver.com/item/coinfo.naver?code={stockCode}"

    # iframe 안의 주소
    url = f"https://navercomp.wisereport.co.kr/v2/company/c1010001.aspx?cmp_cd={stockCode}"
    driver.get(url)
    time.sleep(1)

    # DOM이 다 로드된다음에 html을 가져오기 위해서 selenium을 사용하였음.
    iframe_soup = BeautifulSoup(driver.page_source, 'html.parser')
    # 종목명 가져오기
    stockInfo = {
       "code": stockCode
    }

    # 시가총액 가겨오기
    summaryElement = iframe_soup.find(id="cTB11")
    try:
        if summaryElement:
            stockInfo['시가총액'] = int(summaryElement.find_all('tr')[4].find('td').get_text().strip().replace(',', '').replace('억원', '')+ '00000000')
        else:
            logger.info("시가총액 파싱 실패")
    except:
        logger.info("시가총액 파싱 실패")
        return None

    tableTargetElement = iframe_soup.find(id="cTB00")
    next_element = tableTargetElement.find_next_sibling()
    if not next_element:
        logger.info("테이블 파싱 실패")
        return None

    tables = next_element.find_all('table')
    if tables:
        last_table = tables[-1]
        trList = last_table.find_all('tr')
        last_column_index = -1
        if '(E)' in trList[1].find_all('th')[-1].get_text():
            last_column_index = -2
        stockInfo['결산분기'] = trList[1].find_all('th')[last_column_index].get_text().strip()[:7];
        stockInfo['영역이익'] = int(
            trList[3].find_all('td')[last_column_index].get_text().strip().replace(',', '') + '00000000')
        stockInfo['당기순이익'] = int(
            trList[6].find_all('td')[last_column_index].get_text().strip().replace(',', '') + '00000000')
        stockInfo['자본금'] = int(
            trList[14].find_all('td')[last_column_index].get_text().strip().replace(',', '') + '00000000')
        stockInfo['부채비율'] = trList[25].find_all('td')[last_column_index].get_text().strip().replace(',', '')
        stockInfo['자본유보율'] = trList[26].find_all('td')[last_column_index].get_text().strip().replace(',', '')
        stockInfo['EPS'] = trList[27].find_all('td')[last_column_index].get_text().strip()
        stockInfo['PER'] = trList[28].find_all('td')[last_column_index].get_text().strip()
        stockInfo['BPS'] = trList[29].find_all('td')[last_column_index].get_text().strip().replace(',', '')
        stockInfo['PBR'] = trList[30].find_all('td')[last_column_index].get_text().strip()

    return stockInfo

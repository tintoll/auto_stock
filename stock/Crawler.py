import requests
from bs4 import BeautifulSoup
import time
from selenium import webdriver


class Crawler:
    def __init__(self):
        pass

    def crawling(self, stockCode):

        # url = f"https://finance.naver.com/item/coinfo.naver?code={stockCode}"
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument("--headless")  # 브라우저가 보이지 않도록 설정
        driver = webdriver.Chrome(options=chrome_options)

        # iframe 안의 주소
        url = f"https://navercomp.wisereport.co.kr/v2/company/c1010001.aspx?cmp_cd={stockCode}"
        driver.get(url)
        time.sleep(2)

        # DOM이 다 로드된다음에 html을 가져오기 위해서 selenium을 사용하였음.
        iframe_soup = BeautifulSoup(driver.page_source, 'html.parser')
        # 종목명 가져오기
        stockInfo = {
            "code" : stockCode
        }
        company_name = iframe_soup.select_one('td.cmp-table-cell.td0101 span.name').text.strip()
        stockInfo['company_name'] = company_name

        basicInfos = iframe_soup.select('td.cmp-table-cell.td0301 > dl > dt')
        for i,info in enumerate(basicInfos):
            if i == 0:
                stockInfo['eps'] = info.select_one('b').text.strip()
            elif i == 1:
                stockInfo['bpx'] = info.select_one('b').text.strip()
            elif i == 2:
                stockInfo['per'] = info.select_one('b').text.strip()
            elif i == 4:
                stockInfo['pbr'] = info.select_one('b').text.strip()
        tableTargetElement  = iframe_soup.find(id="cTB00")
        next_element = tableTargetElement.find_next_sibling()
        if not next_element:
            print("Element with ID QmZIZ20rMn not found")
            return None

        tables = next_element.find_all('table')
        if tables:
            last_table = tables[-1]
            print(last_table)





if __name__ == "__main__":
    stock_code = '005930'  # 삼성전자 종목코드
    crawler = Crawler()
    crawler.crawling(stock_code)

import requests
from bs4 import BeautifulSoup


class Crawler:
    def __init__(self):
        pass

    def crawling(self, stockCode):
        url = f"https://finance.naver.com/item/coinfo.naver?code={stockCode}"
        response = requests.get(url)
        if response.status_code != 200:
            print("Failed to retrieve data")
            return None
        soup = BeautifulSoup(response.content, 'html.parser')
        # 종목명 가져오기
        stockInfo = {
            "code" : stockCode
        }
        # iframe의 src 속성 가져오기
        iframe_src = soup.find(id="coinfo_cp")['src']
        iframe_response = requests.get(iframe_src)
        if iframe_response.status_code != 200:
            print("Failed to retrieve iframe content")
            return None

        iframe_soup = BeautifulSoup(iframe_response.content, 'html.parser')

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

        print(stockInfo)

        # 

        # 분석 데이터 가져오기
        # analysis_data = {}
        # table = soup.find('table', {'class': 'gHead'})
        # if table:
        #     rows = table.find_all('tr')
        #     for row in rows:
        #         cols = row.find_all('td')
        #         if len(cols) == 2:
        #             key = cols[0].text.strip()
        #             value = cols[1].text.strip()
        #             analysis_data[key] = value
        #
        # # 결과 출력
        # for key, value in analysis_data.items():
        #     print(key + ':', value)

if __name__ == "__main__":
    stock_code = '005930'  # 삼성전자 종목코드
    crawler = Crawler()
    crawler.crawling(stock_code)

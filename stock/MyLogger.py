# 로그 생성
import logging

logger = logging.getLogger()

# 로그의 출력 기준 설정
logger.setLevel(logging.INFO)

# log 출력 형식
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# log를 console에 출력
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter)
logger.addHandler(stream_handler)

# log를 파일에 출력
# file_handler = logging.FileHandler('stock_logger.log')
# file_handler.setFormatter(formatter)
# logger.addHandler(file_handler)
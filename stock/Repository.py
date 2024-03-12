from sqlalchemy import create_engine


class Repository:
    def __init__(self):
        dbUser = "stock"
        dbPassword = "Rkwmdk1234!"
        dbIp = "localhost"
        dbPort = "3306"
        dbSchema = "stock_info"

        self.db_engine = create_engine(
            "mysql+pymysql://" + dbUser + ":" + dbPassword + "@" + dbIp + ":" + dbPort + "/" + str(dbSchema),
            encoding='utf-8')

        self.db_connection = self.db_engine.connect()

if __name__ == "__main__":
    repository = Repository()
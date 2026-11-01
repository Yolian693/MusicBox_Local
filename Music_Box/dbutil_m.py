import pymysql
import logging

logger = logging.getLogger(__name__)

class DB_util_m:
    Default_Config = {            #类属性。这个字典直接定义在类里,所有实例共享这一份配置。
        'host':'127.0.0.1',
        'port':3306,
        'user':'root',
        'password':'2026',
        'database':'music_db',
        'charset':'utf8mb4'
    }
    def __init__(self,**kwargs):         #构造方法/初始化方法。__init__ 在每次实例化对象（db = DBUtil()）时自动触发。
        '''
        get connection
        get cursor
        '''
        self.config = {**self.Default_Config,**kwargs}          #双星号 ** 解包,把字典拆成 key=value 的形式
        self.con = None
        self.cursor = None
        self.con = pymysql.connect(**self.config)
        self.cursor = self.con.cursor(pymysql.cursors.DictCursor)

    # 支持 with 语句，保证异常路径也能关闭
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        self.close()

    def close(self) -> None:
        '''
        close connection and cursor
        '''
        if self.cursor:
            self.cursor.close()
            self.cursor = None
        if self.con:
            self.con.close()
            self.con = None

    def execute_dml(self,sql,*args) -> bool:            #*args,可变位置参数
        '''
        execute DML to add, delete, update
        '''
        try:
            self.cursor.execute(sql,args)
            self.con.commit()
            return True
        except Exception as e:
            logger.exception('DML failed: %s, args=%s', sql, args)
            self.con.rollback()             #在出错时撤销事务，防止数据只写了一半。
            return False

    def query_one(self,sql,*args):
        '''
        get one data
        '''
        self.cursor.execute(sql,args)
        return self.cursor.fetchone()

    def query_all(self,sql,*args):
        '''
        get all datas
        '''
        self.cursor.execute(sql,args)
        return self.cursor.fetchall()



# test
if __name__ == '__main__':
    db = DB_util_m()
    sql = 'select * from t_user where sex = %s;'
    print("查询结果：")
    print(db.query_all(sql, 'male'))
    db.close()

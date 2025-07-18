import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


class Config:
    # 格式："mysql+pymysql://<自己电脑的数据库名称>:<自己电脑的数据库密码>@localhost:3306/docmind?charset=utf8mb4"
    SQLALCHEMY_DATABASE_URI = "mysql+pymysql://root:qwertyuiop@localhost:3306/docmind?charset=utf8mb4"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    # 上传与生成文件都放在这里
    UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")

# backend/app.py
from flask import Flask
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from backend.config import Config

db = SQLAlchemy()


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # 1) 跨域配置
    CORS(app, resources={r"/api/*": {"origins": "http://localhost:5173"}})

    # 2) 初始化 ORM
    db.init_app(app)

    # 3) 导入模型，确保 create_all 能建表
    from backend.models.file_record import FileRecord

    # 4) 注册路由
    from backend.routes.files import files_bp
    app.register_blueprint(files_bp, url_prefix="/api/files")

    # 5) 建表
    with app.app_context():
        db.create_all()

    return app


# if __name__ == "__main__":
#     app = create_app()
#     app.run(host="0.0.0.0", port=5000, debug=True)

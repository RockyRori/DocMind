from flask import Flask
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from config import Config

db = SQLAlchemy()


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    CORS(app)
    db.init_app(app)

    # 在这里注册蓝图
    # from routes.pdf import pdf_bp
    # app.register_blueprint(pdf_bp, url_prefix='/api/pdf')

    return app


if __name__ == "__main__":
    App = create_app()
    App.run(host="0.0.0.0", port=5000, debug=True)

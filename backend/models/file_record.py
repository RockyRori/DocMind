import os
from datetime import datetime
from flask import url_for
from backend.app import db


class FileRecord(db.Model):
    __tablename__ = "files"
    file_base = db.Column(db.String(28), primary_key=True)
    pdf_name = db.Column(db.String(255), primary_key=True)
    pdf_size = db.Column(db.String(28), nullable=False)
    pdf_time = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    md_name = db.Column(db.String(255), nullable=False, default="UNKNOWN")
    md_size = db.Column(db.String(28), nullable=False, default="UNKNOWN")
    md_time = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    file_path = db.Column(db.String(511), nullable=False)

    @property
    def name_no_ext(self) -> str:
        """PDF 名称去掉后缀（不改变数据库）"""
        return os.path.splitext(self.pdf_name)[0]

    @property
    def pdf_url(self) -> str:
        """下载或预览 PDF 的 URL"""
        return url_for(
            'files.download_pdf',
            file_base=self.file_base,
            filename=self.pdf_name,
            _external=False
        )

    @property
    def md_url(self) -> str:
        """下载或预览 Markdown 的 URL"""
        return url_for(
            'files.download_md',
            file_base=self.file_base,
            md_name=self.md_name,
            _external=False
        )

    @property
    def img_prefix(self) -> str:
        """动态生成前端访问图片的前缀 URL（不改变数据库）"""
        # send_image 路由需要在 routes/files.py 中定义，如前所述
        return url_for(
            'files.download_image',
            file_base=self.file_base,
            pdf_no_ext=self.name_no_ext,
            filename='',
            _external=False
        )

    def to_dict(self):
        return {
            "file_base": self.file_base,
            "pdf_name": self.pdf_name,
            "pdf_size": self.pdf_size,
            "pdf_time": self.pdf_time.strftime("%Y/%m/%d %H:%M:%S"),
            "md_name": self.md_name,
            "md_size": self.md_size,
            "md_time": self.md_time.strftime("%Y/%m/%d %H:%M:%S"),
            # 前端直接用这个 URL 预览 PDF
            "pdf_url": self.pdf_url,
            # 前端直接用这个 URL 下载 MD
            "md_url": self.md_url,
            "img_prefix": self.img_prefix
        }

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
            "pdf_url": url_for(
                "files.download_pdf",
                file_base=self.file_base,
                filename=self.pdf_name,
                _external=False
            ),
            # 前端直接用这个 URL 下载 MD
            "md_url": url_for(
                "files.download_md",
                file_base=self.file_base,
                md_name=self.md_name,
                _external=False
            )
        }

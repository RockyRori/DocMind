import os
from flask import url_for
from backend.app import db
from datetime import datetime, timezone, timedelta


class FileRecord(db.Model):
    __tablename__ = "files"

    pdf_name = db.Column(db.String(255), primary_key=True)
    pdf_size = db.Column(db.String(28), nullable=False)
    pdf_time = db.Column(db.DateTime, nullable=False, default=datetime.now(timezone(timedelta(hours=8))))

    docx_name = db.Column(db.String(255), nullable=False, default="UNKNOWN")
    docx_size = db.Column(db.String(28), nullable=False, default="UNKNOWN")

    json_name = db.Column(db.String(255), nullable=False, default="UNKNOWN")
    json_size = db.Column(db.String(28), nullable=False, default="UNKNOWN")

    md_name = db.Column(db.String(255), nullable=False, default="UNKNOWN")
    md_size = db.Column(db.String(28), nullable=False, default="UNKNOWN")

    file_base = db.Column(db.String(28), primary_key=True)
    file_path = db.Column(db.String(511), nullable=False)

    @property
    def name_no_ext(self) -> str:
        return os.path.splitext(self.pdf_name)[0]

    @property
    def pdf_url(self) -> str:
        return url_for(
            'files.download_pdf',
            file_base=self.file_base,
            pdf_name=self.pdf_name,
            _external=True
        )

    @property
    def docx_url(self) -> str:
        return url_for(
            'files.download_docx',
            file_base=self.file_base,
            docx_name=self.docx_name,
            _external=True
        )

    @property
    def json_url(self) -> str:
        return url_for(
            'files.download_json',
            file_base=self.file_base,
            json_name=self.json_name,
            _external=True
        )

    @property
    def md_url(self) -> str:
        return url_for(
            'files.download_md',
            file_base=self.file_base,
            pdf_name_no_ext=self.name_no_ext,
            md_name=self.md_name,
            _external=True
        )

    @property
    def img_prefix(self) -> str:
        return url_for(
            'files.download_image',
            file_base=self.file_base,
            pdf_no_ext=self.name_no_ext,
            filename='',
            _external=True
        )

    def to_dict(self):
        return {
            "pdf_name": self.pdf_name,
            "pdf_size": self.pdf_size,
            "pdf_time": self.pdf_time.strftime("%Y/%m/%d %H:%M:%S"),

            "docx_name": self.docx_name,
            "docx_size": self.docx_size,

            "json_name": self.json_name,
            "json_size": self.json_size,

            "md_name": self.md_name,
            "md_size": self.md_size,

            "file_base": self.file_base,
            "file_path": self.file_path,

            "pdf_url": self.pdf_url,
            "docx_url": self.docx_url,
            "json_url": self.json_url,
            "md_url": self.md_url,
            "img_prefix": self.img_prefix
        }

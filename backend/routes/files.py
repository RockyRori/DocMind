import os
from datetime import datetime
from flask import (
    Blueprint, request, jsonify, current_app,
    send_from_directory, abort
)
from backend.app import db
from backend.models.file_record import FileRecord
from backend.services.pdf_service import ensure_upload_folder, async_convert_with_local_mineru

files_bp = Blueprint("files", __name__)


@files_bp.route("", methods=["GET"])
def list_files():
    recs = FileRecord.query.order_by(FileRecord.pdf_time.desc()).all()
    return jsonify([r.to_dict() for r in recs])


@files_bp.route("", methods=["POST"])
def upload_file():
    uploaded = request.files.get("file")
    if not uploaded:
        return jsonify({"error": "缺少 file 字段"}), 400

    file_base = request.form.get("file_base", "server_default")
    folder = ensure_upload_folder(file_base)

    # 1. 保存 PDF
    filename = uploaded.filename
    save_path = os.path.join(folder, filename)
    uploaded.save(save_path)
    pdf_size = f"{os.path.getsize(save_path) / 1024 / 1024:.1f}MB"

    # 2. 创建或更新数据库记录
    rec = FileRecord.query.get((file_base, filename))
    if not rec:
        rec = FileRecord(
            file_base=file_base,
            pdf_name=filename,
            file_path=folder,
            pdf_size=pdf_size
        )
        db.session.add(rec)
    else:
        rec.pdf_size = pdf_size
        rec.pdf_time = datetime.utcnow()
    db.session.commit()

    # 3. 异步调用本地 mineru CLI 生成 Markdown
    async_convert_with_local_mineru(rec, current_app._get_current_object())

    # 4. 返回记录（此时 md_name 仍为 UNKNOWN）
    return jsonify(rec.to_dict()), 201


@files_bp.route("/download/pdf/<file_base>/<path:filename>", methods=["GET"])
def download_pdf(file_base, filename):
    folder = os.path.join(current_app.config["UPLOAD_FOLDER"], file_base)
    file_path = os.path.join(folder, filename)
    if not os.path.exists(file_path):
        abort(404)
    # as_attachment=False 让浏览器内联显示
    return send_from_directory(folder, filename, as_attachment=False)


@files_bp.route("/download/md/<file_base>/<pdf_name_no_ext>/<path:md_name>", methods=["GET"])
def download_md(file_base, pdf_name_no_ext, md_name):
    """
    从本地 mineru CLI 生成的 vlm 子目录下载 Markdown
      uploads/{file_base}/{pdf_name_no_ext}/vlm/{md_name}
    """
    base = current_app.config["UPLOAD_FOLDER"]
    vlm_dir = os.path.join(base, file_base, pdf_name_no_ext, "vlm")
    file_path = os.path.join(vlm_dir, md_name)
    if not os.path.exists(file_path):
        abort(404)
    # as_attachment=True 强制下载
    return send_from_directory(
        vlm_dir, md_name,
        as_attachment=True,
        download_name=md_name,
        mimetype="text/markdown"
    )


@files_bp.route("/<file_base>/<pdf_name>", methods=["DELETE"])
def delete_file(file_base, pdf_name):
    rec = FileRecord.query.get_or_404((file_base, pdf_name))
    # 删除本地文件
    pdf_path = os.path.join(current_app.config["UPLOAD_FOLDER"], file_base, rec.pdf_name)
    md_path = os.path.join(current_app.config["UPLOAD_FOLDER"], file_base, rec.md_name)
    for p in [pdf_path, md_path]:
        if os.path.exists(p):
            os.remove(p)
    db.session.delete(rec)
    db.session.commit()
    return jsonify({"message": "已删除"})

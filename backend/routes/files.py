import os
from datetime import datetime, timezone, timedelta
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


@files_bp.route("/batch", methods=["POST"])
def upload_files_batch():
    """
    批量上传 PDF 文件：
    前端需以 'files' 字段上传多个文件。
    返回所有已接收并入库的记录列表。
    """
    uploaded_list = request.files.getlist("files")
    if not uploaded_list:
        return jsonify({"error": "缺少 files 字段"}), 400

    file_base = request.form.get("file_base", "server_default")
    folder = ensure_upload_folder(file_base)

    results = []
    for uploaded in uploaded_list:
        pdf_name = uploaded.filename
        save_path = os.path.join(folder, pdf_name)
        uploaded.save(save_path)
        pdf_size = f"{os.path.getsize(save_path) / 1024 / 1024:.1f}MB"

        # 创建或更新记录
        rec = FileRecord.query.get((file_base, pdf_name))
        if not rec:
            rec = FileRecord(
                pdf_name=pdf_name,
                pdf_size=pdf_size,
                pdf_time=datetime.now(timezone(timedelta(hours=8))),
                docx_name="UNKNOWN",
                docx_size="UNKNOWN",
                json_name="UNKNOWN",
                json_size="UNKNOWN",
                md_name="UNKNOWN",
                md_size="UNKNOWN",
                file_base=file_base,
                file_path=folder,
            )
            db.session.add(rec)
        else:
            rec.pdf_size = pdf_size
            rec.pdf_time = datetime.now(timezone(timedelta(hours=8)))
        db.session.commit()

        # 异步转换
        async_convert_with_local_mineru(current_app._get_current_object(), rec.file_base, rec.pdf_name)

        results.append(rec.to_dict())

    return jsonify(results), 201


@files_bp.route("/download/pdf/<file_base>/<path:pdf_name>", methods=["GET"])
def download_pdf(file_base, pdf_name):
    folder = os.path.join(current_app.config["UPLOAD_FOLDER"], file_base)
    file_path = os.path.join(folder, pdf_name)
    if not os.path.exists(file_path):
        abort(404)
    # as_attachment=False 让浏览器内联显示
    return send_from_directory(folder, pdf_name, as_attachment=False)


@files_bp.route("/download/docx/<file_base>/<path:docx_name>", methods=["GET"])
def download_docx(file_base, docx_name):
    folder = os.path.join(current_app.config["UPLOAD_FOLDER"], file_base)
    file_path = os.path.join(folder, docx_name)
    if not os.path.exists(file_path):
        abort(404)

    return send_from_directory(folder, docx_name, as_attachment=False)


@files_bp.route("/download/json/<file_base>/<path:json_name>", methods=["GET"])
def download_json(file_base, json_name):
    folder = os.path.join(current_app.config["UPLOAD_FOLDER"], file_base)
    file_path = os.path.join(folder, json_name)
    if not os.path.exists(file_path):
        abort(404)

    return send_from_directory(folder, json_name, as_attachment=False)


@files_bp.route("/download/md/<file_base>/<path:md_name>", methods=["GET"])
def download_md(file_base, md_name):
    """
    从本地 mineru CLI 生成的 vlm 子目录下载 Markdown
      uploads/{file_base}/{name_without_ext}/vlm/{md_name}
    """
    name_without_ext = md_name.rsplit(".", 1)[0]
    base = current_app.config["UPLOAD_FOLDER"]
    vlm_dir = os.path.join(base, file_base, name_without_ext, "vlm")
    file_path = os.path.join(vlm_dir, md_name)
    if not os.path.exists(file_path):
        abort(404)
    # as_attachment=True 强制下载
    return send_from_directory(
        vlm_dir, md_name,
        as_attachment=False,
        download_name=md_name,
        mimetype="text/markdown"
    )


@files_bp.route("/download/images/<file_base>/<pdf_no_ext>/<path:filename>")
def download_image(file_base, pdf_no_ext, filename):
    """
    例如 GET /api/files/download/images/server_default/常州/1f7627...jpg
    """
    base = current_app.config["UPLOAD_FOLDER"]
    folder = os.path.join(base, file_base, pdf_no_ext, "vlm", "images")
    return send_from_directory(folder, filename, as_attachment=False,
                               mimetype="image/jpeg")


@files_bp.route("/<file_base>/<pdf_name>", methods=["DELETE"])
def delete_file(file_base, pdf_name):
    """
    删除指定 PDF 及其生成的 Markdown 和所有关联目录。
    """
    # 查询记录
    rec = FileRecord.query.get_or_404((file_base, pdf_name))
    base_upload = current_app.config["UPLOAD_FOLDER"]

    # 删除 PDF 文件
    pdf_path = os.path.join(base_upload, file_base, rec.pdf_name)
    if os.path.isfile(pdf_path):
        try:
            os.remove(pdf_path)
        except Exception as e:
            current_app.logger.warning(f"删除 PDF 文件失败 {pdf_path}: {e}")

    # 删除 DOCX 文件
    pdf_path = os.path.join(base_upload, file_base, rec.docx_name)
    if os.path.isfile(pdf_path):
        try:
            os.remove(pdf_path)
        except Exception as e:
            current_app.logger.warning(f"删除 PDF 文件失败 {pdf_path}: {e}")

    # 删除 JSON 文件
    pdf_path = os.path.join(base_upload, file_base, rec.json_name)
    if os.path.isfile(pdf_path):
        try:
            os.remove(pdf_path)
        except Exception as e:
            current_app.logger.warning(f"删除 PDF 文件失败 {pdf_path}: {e}")

    # 删除 Markdown 文件
    # 当前在子文件夹当中一并删除

    # 删除 mineru 生成的子目录
    name_without_ext = pdf_name.rsplit(".", 1)[0]
    output_dir = os.path.join(base_upload, file_base, name_without_ext)
    if os.path.isdir(output_dir):
        import shutil
        try:
            shutil.rmtree(output_dir)
        except Exception as e:
            current_app.logger.warning(f"删除输出目录失败 {output_dir}: {e}")

    # 删除数据库记录
    db.session.delete(rec)
    db.session.commit()

    return jsonify({"message": "已删除"})

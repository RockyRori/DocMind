import os
import shutil
import threading
import subprocess
from datetime import datetime
from flask import current_app
from backend.app import db
from backend.models.file_record import FileRecord


def ensure_upload_folder(file_base: str):
    folder = os.path.join(current_app.config["UPLOAD_FOLDER"], file_base)
    os.makedirs(folder, exist_ok=True)
    return folder


def async_convert_with_local_mineru(rec: FileRecord, app):
    """
    异步调用本地 mineru CLI 并搬移生成的 Markdown 和图片文件。
    """

    def task():
        with app.app_context():
            try:
                folder = ensure_upload_folder(rec.file_base)
                pdf_path = os.path.join(folder, rec.pdf_name)
                output_dir = folder

                # 调用 mineru
                cmd = [
                    "mineru",
                    "-p", pdf_path,
                    "-o", output_dir,
                    "-b", "vlm-sglang-client",
                    "-u", "http://172.16.0.176:30000"
                ]
                subprocess.run(cmd, check=True, cwd=folder)
                # 后续的命令应该在subprocess执行结束之后才开始，否则会导致错误。

                name_without_ext = rec.pdf_name.rsplit(".", 1)[0]
                # mineru 生成在 output_dir/<name_without_ext>/vlm
                vlm_dir = os.path.join(output_dir, name_without_ext, "vlm")

                # 1. 移动 .md
                md_name = f"{name_without_ext}.md"
                src_md = os.path.join(vlm_dir, md_name)
                if not os.path.exists(src_md):
                    app.logger.error(f"预期的 Markdown 文件不存在: {src_md}")
                    return
                # dst_md = os.path.join(folder, md_name)
                # os.replace(src_md, dst_md)

                # 2. 移动 images 文件夹
                src_images = os.path.join(vlm_dir, "images")
                if os.path.isdir(src_images):
                    dst_images = os.path.join(folder, "images")
                    # 如果目标已存在，先删除再移动
                    if os.path.exists(dst_images):
                        shutil.rmtree(dst_images)
                    # shutil.move(src_images, dst_images)

                # 更新数据库
                rec.md_name = md_name
                rec.md_time = datetime.utcnow()
                rec.md_size = f"{os.path.getsize(src_md) / 1024:.1f}KB"
                db.session.commit()

                # 可选：清理中间目录
                # shutil.rmtree(os.path.join(output_dir, name_without_ext))

            except Exception as e:
                app.logger.error(f"本地 mineru 异步处理出错: {e}")

    threading.Thread(target=task, daemon=True).start()

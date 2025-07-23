# backend/services/pdf_service.py
import os
import shutil
import threading
import subprocess
import time
import pypandoc
from flask import current_app
from backend.app import db
from backend.models.file_record import FileRecord


def ensure_upload_folder(file_base: str):
    folder = os.path.join(current_app.config["UPLOAD_FOLDER"], file_base)
    os.makedirs(folder, exist_ok=True)
    return folder


def async_convert_with_local_mineru(app, file_base: str, pdf_name: str):
    """
    异步调用本地 mineru CLI。
    只接收主键 (file_base, pdf_name)，在线程内部重新获取 ORM 对象和会话。
    """

    def task():
        # 推入上下文，也新开会话
        with app.app_context():
            # 开启一个新的事务
            with db.session.begin():
                # 1. 重新拿 fresh ORM 对象
                rec = FileRecord.query.get((file_base, pdf_name))
                if not rec:
                    current_app.logger.error(f"记录不存在: {file_base}, {pdf_name}")
                    return

                folder = ensure_upload_folder(rec.file_base)
                pdf_path = os.path.join(folder, rec.pdf_name)
                output_dir = folder

                # 2. 检查文件存在
                if not os.path.isfile(pdf_path):
                    current_app.logger.error(f"PDF 文件不存在: {pdf_path}")
                    return

                # 3. 调用 mineru，同步等待
                cmd = [
                    "mineru",
                    "-p", pdf_path,
                    "-o", output_dir,
                    "-b", "vlm-sglang-client",
                    "-u", "http://172.16.0.176:30000"
                ]
                subprocess.run(cmd, check=True, cwd=folder)

                # 4. 等待 Markdown 生成
                name = rec.pdf_name.rsplit(".", 1)[0]
                vlm_dir = os.path.join(output_dir, name, "vlm")
                src_md = os.path.join(vlm_dir, f"{name}.md")
                src_json = os.path.join(vlm_dir, f"{name}_content_list.json")

                # 轮询等待文件出现
                timeout, interval = 600, 1
                start = time.time()
                while not os.path.exists(src_md) and time.time() - start < timeout:
                    time.sleep(interval)

                if not os.path.exists(src_md):
                    current_app.logger.error(f"Markdown 未生成: {src_md}")
                    return
                if not os.path.exists(src_json):
                    current_app.logger.error(f"JSON 未生成: {src_json}")
                    return
                rec.md_name = f"{name}.md"
                rec.md_size = f"{os.path.getsize(src_md) / 1024:.1f}KB"

                # 5. 复制 JSON 文件
                rec.json_name = f"{name}.json"
                target_json = os.path.join(folder, rec.json_name)
                shutil.copy(src_json, target_json)
                rec.json_size = f"{os.path.getsize(target_json) / 1024:.1f}KB"

                # 6. Markdown 转换为 Word 文档
                docx_name = f"{name}.docx"
                docx_path = os.path.join(folder, docx_name)
                extra_args = [
                    '--resource-path', vlm_dir,
                    '--resource-path', os.path.join(vlm_dir, 'images')
                ]
                pypandoc.convert_file(source_file=src_md, to='docx', extra_args=extra_args, outputfile=docx_path)
                rec.docx_name = docx_name
                rec.docx_size = f"{os.path.getsize(docx_path) / 1024:.1f}KB"
                current_app.logger.info(f"已生成 Word 文档: {docx_path}")

                # db.session.commit() 随 with db.session.begin() 一起自动提交

    threading.Thread(target=task, daemon=True).start()

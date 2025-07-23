-- 创建数据库（如果不存在）并切换
CREATE DATABASE IF NOT EXISTS docmind;
USE docmind;
SET GLOBAL time_zone = '+8:00';

-- 删除表（注意外键依赖顺序）
DROP TABLE IF EXISTS files;

-- 创建文件表
# PDF文件和Markdown文件内容存在外部文件系统
# Markdown文件处理状态存储在应用程序内存
# UNKNOWN表示文件正在处理中
CREATE TABLE IF NOT EXISTS files
(
    pdf_name  VARCHAR(255) NOT NULL COMMENT 'PDF文件名称',
    pdf_size  VARCHAR(28)  NOT NULL COMMENT 'PDF文件大小',
    pdf_time  TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT 'PDF上传/更新文件时间',

    docx_name VARCHAR(255) NOT NULL DEFAULT 'UNKNOWN' COMMENT 'Word（Docx）文件名称',
    docx_size VARCHAR(28)  NOT NULL DEFAULT 'UNKNOWN' COMMENT 'Word（Docx）文件大小',

    json_name VARCHAR(255) NOT NULL DEFAULT 'UNKNOWN' COMMENT 'JSON文件名称',
    json_size VARCHAR(28)  NOT NULL DEFAULT 'UNKNOWN' COMMENT 'JSON文件大小',

    md_name   VARCHAR(255) NOT NULL DEFAULT 'UNKNOWN' COMMENT 'Markdown文件名称',
    md_size   VARCHAR(28)  NOT NULL DEFAULT 'UNKNOWN' COMMENT 'Markdown文件大小',

    file_base VARCHAR(28)  NOT NULL DEFAULT 'server_default' COMMENT '存储文件的服务器',
    file_path VARCHAR(511) NOT NULL COMMENT '文件在存储系统里的路径或URL前缀',

    PRIMARY KEY (file_base, pdf_name)
);

-- 插入初始数据
INSERT INTO docmind.files (pdf_name, pdf_size, pdf_time, docx_name, docx_size, json_name, json_size, md_name, md_size,
                           file_base, file_path)
VALUES ('常州千瓦机组.pdf', '0.3MB', '2025-07-16 10:28:31', '常州千瓦机组.docx', '290.4KB', '常州千瓦机组.json', '3.8KB', 'UNKNOWN',
        'UNKNOWN', 'server_default', '/');

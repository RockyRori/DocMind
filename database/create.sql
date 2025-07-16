-- 创建数据库（如果不存在）并切换
CREATE DATABASE IF NOT EXISTS docmind;
USE docmind;
SET GLOBAL time_zone = '+8:00';

-- 删除表（注意外键依赖顺序）
DROP TABLE IF EXISTS files;

-- 创建文件表
# PDF文件和Markdown文件内容存在外部文件系统
# Markdown文件处理状态存储在应用程序内存
# UNKNOWN表示Markdown文件正在处理中
CREATE TABLE IF NOT EXISTS files
(
    pdf_name  VARCHAR(255) NOT NULL COMMENT 'PDF文件名称',
    pdf_size  VARCHAR(28)  NOT NULL COMMENT 'PDF文件大小',
    pdf_time  TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT 'PDF上传/更新文件时间',
    md_name   VARCHAR(255) NOT NULL DEFAULT 'UNKNOWN' COMMENT 'Markdown文件名称',
    md_size   VARCHAR(28)  NOT NULL DEFAULT 'UNKNOWN' COMMENT 'Markdown文件大小',
    md_time   TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT 'Markdown上传/更新文件时间',
    file_base VARCHAR(28)  NOT NULL DEFAULT 'server_default' COMMENT '存储文件的服务器',
    file_path VARCHAR(511) NOT NULL COMMENT '文件在存储系统里的路径或URL前缀',
    PRIMARY KEY (file_base, pdf_name)
);

-- 插入初始数据
insert into docmind.files (pdf_name, pdf_size, pdf_time, md_name, md_size, md_time, file_base, file_path)
values ('规范.pdf', '3.1MB', '2025-07-16 10:28:31', 'UNKNOWN', 'UNKNOWN', '2025-07-16 03:28:31', 'server_default', '/');


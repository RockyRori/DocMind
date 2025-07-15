use DATABASE abc;
CREATE SCHEMA IF NOT EXISTS pdf_analysis;

USE pdf_analysis;
CREATE TABLE IF NOT EXISTS file_data (
    id INT AUTO_INCREMENT PRIMARY KEY,
    file_name VARCHAR(255) NOT NULL,
    update_time DATE NOT NULL,
    size VARCHAR(20) NOT NULL,
    output_name VARCHAR(255) NOT NULL,
);


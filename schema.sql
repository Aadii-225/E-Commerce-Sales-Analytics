CREATE DATABASE IF NOT EXISTS ecommerce_analytics;
USE ecommerce_analytics;

CREATE TABLE IF NOT EXISTS sales (
    Order_ID VARCHAR(30) PRIMARY KEY,
    Date DATE NOT NULL,
    Product VARCHAR(100) NOT NULL,
    Category VARCHAR(100),
    Region VARCHAR(50),
    Customer VARCHAR(30),
    Quantity INT NOT NULL DEFAULT 1,
    Sales DECIMAL(12, 2) NOT NULL,
    Cost DECIMAL(12, 2) NOT NULL,
    INDEX idx_sales_date (Date),
    INDEX idx_sales_region (Region),
    INDEX idx_sales_product (Product)
);

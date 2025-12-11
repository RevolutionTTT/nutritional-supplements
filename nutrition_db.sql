-- MySQL dump 10.13  Distrib 9.3.0, for Win64 (x86_64)
-- 数据库：nutrition_supplement_db
-- 服务器版本：9.3.0

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8mb4 */;  -- 设置字符集为 utf8mb4
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;  -- 设置时区为 UTC
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;  -- 禁用唯一性检查，导入数据时避免冲突
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;  -- 禁用外键约束
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;  -- 设置 SQL 模式
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;  -- 关闭提示信息

-- =============================================
-- 表结构：cart_items（购物车表）
-- 记录用户购物车中商品及数量
-- =============================================
DROP TABLE IF EXISTS `cart_items`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
CREATE TABLE `cart_items` (
  `id` int NOT NULL AUTO_INCREMENT,  -- 主键，自增
  `user_id` int NOT NULL,            -- 用户ID，外键关联 users.id
  `product_id` int NOT NULL,         -- 商品ID，外键关联 products.id
  `quantity` int NOT NULL,           -- 商品数量
  `added_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,  -- 添加时间，默认当前时间
  PRIMARY KEY (`id`),
  KEY `user_id` (`user_id`),
  KEY `product_id` (`product_id`),
  CONSTRAINT `cart_items_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`),
  CONSTRAINT `cart_items_ibfk_2` FOREIGN KEY (`product_id`) REFERENCES `products` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- 数据导入：cart_items（目前为空）
LOCK TABLES `cart_items` WRITE;
/*!40000 ALTER TABLE `cart_items` DISABLE KEYS */;
/*!40000 ALTER TABLE `cart_items` ENABLE KEYS */;
UNLOCK TABLES;

-- =============================================
-- 表结构：categories（商品分类表）
-- 存储系统中的商品分类信息
-- =============================================
DROP TABLE IF EXISTS `categories`;
CREATE TABLE `categories` (
  `id` int NOT NULL AUTO_INCREMENT,  -- 主键，自增
  `name` varchar(100) NOT NULL,      -- 分类名称
  `description` text,                -- 分类描述
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,  -- 创建时间
  `image_url` varchar(255) DEFAULT NULL,  -- 分类图片URL，可选
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- 示例数据：categories
LOCK TABLES `categories` WRITE;
INSERT INTO `categories` VALUES
(1,'维生素','各种维生素补充剂','2025-11-23 13:51:37',NULL),
(2,'矿物质','钙、铁、锌等矿物质补充','2025-11-23 13:51:37',NULL),
(3,'蛋白粉','健身营养蛋白补充','2025-11-23 13:51:37',NULL),
(4,'氨基酸','必需氨基酸补充剂','2025-11-23 13:51:37',NULL);
UNLOCK TABLES;

-- =============================================
-- 表结构：order_items（订单明细表）
-- 存储订单中每个商品的数量和价格
-- =============================================
DROP TABLE IF EXISTS `order_items`;
CREATE TABLE `order_items` (
  `id` int NOT NULL AUTO_INCREMENT,
  `order_id` int NOT NULL,       -- 关联订单表 orders.id
  `product_id` int NOT NULL,     -- 关联商品表 products.id
  `quantity` int NOT NULL,       -- 商品数量
  `unit_price` decimal(10,2) NOT NULL,  -- 单价
  PRIMARY KEY (`id`),
  KEY `order_id` (`order_id`),
  KEY `product_id` (`product_id`),
  CONSTRAINT `order_items_ibfk_1` FOREIGN KEY (`order_id`) REFERENCES `orders` (`id`),
  CONSTRAINT `order_items_ibfk_2` FOREIGN KEY (`product_id`) REFERENCES `products` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- 数据导入：order_items（目前为空）
LOCK TABLES `order_items` WRITE;
/*!40000 ALTER TABLE `order_items` DISABLE KEYS */;
/*!40000 ALTER TABLE `order_items` ENABLE KEYS */;
UNLOCK TABLES;

-- =============================================
-- 表结构：orders（订单表）
-- 存储用户订单基本信息
-- =============================================
DROP TABLE IF EXISTS `orders`;
CREATE TABLE `orders` (
  `id` int NOT NULL AUTO_INCREMENT,  -- 主键，自增
  `user_id` int NOT NULL,            -- 下单用户ID
  `total_amount` decimal(10,2) NOT NULL, -- 订单总金额
  `status` enum('pending','confirmed','shipped','delivered','cancelled') DEFAULT 'pending',  -- 订单状态
  `shipping_address` text NOT NULL,  -- 收货地址
  `payment_method` varchar(50) DEFAULT NULL,  -- 支付方式
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,  -- 创建时间
  PRIMARY KEY (`id`),
  KEY `idx_orders_user` (`user_id`),
  KEY `idx_orders_status` (`status`),
  CONSTRAINT `orders_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- 数据导入：orders（目前为空）
LOCK TABLES `orders` WRITE;
/*!40000 ALTER TABLE `orders` DISABLE KEYS */;
/*!40000 ALTER TABLE `orders` ENABLE KEYS */;
UNLOCK TABLES;

-- =============================================
-- 表结构：payments（支付表）
-- 记录订单支付信息，包括状态和交易ID
-- =============================================
DROP TABLE IF EXISTS `payments`;
CREATE TABLE `payments` (
  `id` int NOT NULL AUTO_INCREMENT,
  `order_id` int NOT NULL,  -- 关联订单ID
  `payment_method` varchar(50) NOT NULL,  -- 支付方式
  `amount` decimal(10,2) NOT NULL,        -- 支付金额
  `status` enum('pending','success','failed','cancelled') DEFAULT 'pending', -- 支付状态
  `transaction_id` varchar(100) DEFAULT NULL,  -- 支付平台交易ID
  `paid_at` timestamp NULL DEFAULT NULL,      -- 支付时间
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP, -- 创建时间
  PRIMARY KEY (`id`),
  UNIQUE KEY `transaction_id` (`transaction_id`),  -- 交易ID唯一
  KEY `order_id` (`order_id`),
  CONSTRAINT `payments_ibfk_1` FOREIGN KEY (`order_id`) REFERENCES `orders` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- 数据导入：payments（目前为空）
LOCK TABLES `payments` WRITE;
/*!40000 ALTER TABLE `payments` DISABLE KEYS */;
/*!40000 ALTER TABLE `payments` ENABLE KEYS */;
UNLOCK TABLES;

-- =============================================
-- 表结构：products（商品表）
-- 存储系统中所有商品信息
-- =============================================
DROP TABLE IF EXISTS `products`;
CREATE TABLE `products` (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(200) NOT NULL,        -- 商品名称
  `description` text,                  -- 商品描述
  `category_id` int DEFAULT NULL,       -- 分类ID，关联 categories.id
  `price` decimal(10,2) NOT NULL,      -- 价格
  `stock_quantity` int NOT NULL,        -- 库存数量
  `image_url` varchar(500) DEFAULT NULL, -- 图片URL
  `is_active` tinyint(1) DEFAULT '1',  -- 是否上架
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `average_rating` decimal(3,2) DEFAULT '0.00', -- 平均评分
  `review_count` int DEFAULT '0',       -- 评论数量
  PRIMARY KEY (`id`),
  KEY `idx_products_category` (`category_id`),
  KEY `idx_products_active` (`is_active`),
  CONSTRAINT `products_ibfk_1` FOREIGN KEY (`category_id`) REFERENCES `categories` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- 示例数据：products
LOCK TABLES `products` WRITE;
INSERT INTO `products` VALUES
(1,'维生素C 1000mg','高效维生素C补充，增强免疫力',1,89.90,100,NULL,1,'2025-11-23 13:51:37',0.00,0),
(2,'钙镁锌片','复合矿物质补充，强健骨骼',2,129.00,80,NULL,1,'2025-11-23 13:51:37',0.00,0),
(3,'乳清蛋白粉','优质乳清蛋白，健身必备',3,299.00,50,NULL,1,'2025-11-23 13:51:37',0.00,0),
(4,'BCAA氨基酸','支链氨基酸，运动恢复',4,199.00,60,NULL,1,'2025-11-23 13:51:37',0.00,0);
UNLOCK TABLES;

-- =============================================
-- 表结构：reviews（商品评价表）
-- 存储用户对商品的评价及评分
-- =============================================
DROP TABLE IF EXISTS `reviews`;
CREATE TABLE `reviews` (
  `id` int NOT NULL AUTO_INCREMENT,
  `user_id` int NOT NULL,        -- 评价用户ID
  `product_id` int NOT NULL,     -- 评价商品ID
  `order_id` int NOT NULL,       -- 关联订单ID，保证只有购买过的商品可评价
  `rating` int NOT NULL,         -- 评分 1-5
  `title` varchar(200) DEFAULT NULL, -- 评价标题
  `content` text,                -- 评价内容
  `is_verified` tinyint(1) DEFAULT '0', -- 是否验证通过
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `unique_user_product_order` (`user_id`,`product_id`,`order_id`),  -- 同一用户同一订单同一商品唯一
  KEY `order_id` (`order_id`),
  KEY `idx_reviews_product` (`product_id`),
  KEY `idx_reviews_user` (`user_id`),
  CONSTRAINT `reviews_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`),
  CONSTRAINT `reviews_ibfk_2` FOREIGN KEY (`product_id`) REFERENCES `products` (`id`),
  CONSTRAINT `reviews_ibfk_3` FOREIGN KEY (`order_id`) REFERENCES `orders` (`id`),
  CONSTRAINT `reviews_chk_1` CHECK (((`rating` >= 1) and (`rating` <= 5)))  -- 评分范围限制
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- 数据导入：reviews（目前为空）
LOCK TABLES `reviews` WRITE;
/*!40000 ALTER TABLE `reviews` DISABLE KEYS */;
/*!40000 ALTER TABLE `reviews` ENABLE KEYS */;
UNLOCK TABLES;

-- =============================================
-- 表结构：user_addresses（用户收货地址表）
-- 存储用户的多个收货地址
-- =============================================
DROP TABLE IF EXISTS `user_addresses`;
CREATE TABLE `user_addresses` (
  `id` int NOT NULL AUTO_INCREMENT,
  `user_id` int NOT NULL,                -- 用户ID
  `recipient_name` varchar(100) NOT NULL, -- 收件人姓名
  `phone` varchar(20) NOT NULL,           -- 联系电话
  `province` varchar(50) NOT NULL,       -- 省
  `city` varchar(50) NOT NULL,           -- 市
  `district` varchar(50) NOT NULL,       -- 区
  `detail_address` text NOT NULL,        -- 详细地址
  `is_default` tinyint(1) DEFAULT '0',   -- 是否默认地址
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `user_id` (`user_id`),
  CONSTRAINT `user_addresses_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- 数据导入：user_addresses（目前为空）
LOCK TABLES `user_addresses` WRITE;
/*!40000 ALTER TABLE `user_addresses` DISABLE KEYS */;
/*!40000 ALTER TABLE `user_addresses` ENABLE KEYS */;
UNLOCK TABLES;

-- =============================================
-- 表结构：user_favorites（用户收藏表）
-- 存储用户收藏的商品
-- =============================================
DROP TABLE IF EXISTS `user_favorites`;
CREATE TABLE `user_favorites` (
  `id` int NOT NULL AUTO_INCREMENT,
  `user_id` int NOT NULL,        -- 用户ID
  `product_id` int NOT NULL,     -- 收藏商品ID
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `unique_user_product` (`user_id`,`product_id`),  -- 用户同一商品唯一
  KEY `product_id` (`product_id`),
  CONSTRAINT `user_favorites_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`),
  CONSTRAINT `user_favorites_ibfk_2` FOREIGN KEY (`product_id`) REFERENCES `products` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- 数据导入：user_favorites（目前为空）
LOCK TABLES `user_favorites` WRITE;
/*!40000 ALTER TABLE `user_favorites` DISABLE KEYS */;
/*!40000 ALTER TABLE `user_favorites` ENABLE KEYS */;
UNLOCK TABLES;

-- =============================================
-- 表结构：users（用户表）
-- 存储系统注册用户信息
-- =============================================
DROP TABLE IF EXISTS `users`;
CREATE TABLE `users` (
  `id` int NOT NULL AUTO_INCREMENT,
  `username` varchar(50) NOT NULL,       -- 用户名，唯一
  `email` varchar(100) NOT NULL,         -- 邮箱，唯一
  `password_hash` varchar(255) NOT NULL, -- 密码哈希
  `full_name` varchar(100) DEFAULT NULL, -- 真实姓名
  `phone` varchar(20) DEFAULT NULL,      -- 电话
  `address` text,                        -- 默认地址
  `is_admin` tinyint NOT NULL DEFAULT '0' COMMENT '是否为管理员：0-否，1-是',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `username` (`username`),
  UNIQUE KEY `email` (`email`)
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- 示例数据：users
LOCK TABLES `users` WRITE;
INSERT INTO `users` VALUES
(1,'user1','user@qq.com','Aa123456','用户',NULL,NULL,0,'2025-12-07 01:22:29'),
(4,'admin','admin@example.com','Aa123456','管理员',NULL,NULL,1,'2025-12-07 01:15:00');
UNLOCK TABLES;

/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;
/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2025-12-07  9:27:18

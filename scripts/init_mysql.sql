-- ====================================
-- 户外活动规划助手 - MySQL 数据库初始化脚本
-- ====================================
-- 此脚本会在 Docker MySQL 容器首次启动时自动执行
-- ====================================

-- 创建数据库（如果不存在）
CREATE DATABASE IF NOT EXISTS outdoor_planner CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

USE outdoor_planner;

-- 用户表
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE COMMENT '用户名',
    phone VARCHAR(20) UNIQUE COMMENT '手机号',
    password_hash VARCHAR(255) NOT NULL COMMENT '密码哈希',
    role ENUM('user', 'admin') DEFAULT 'user' COMMENT '角色',
    status ENUM('active', 'disabled') DEFAULT 'active' COMMENT '状态',
    last_login_at DATETIME COMMENT '最后登录时间',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    INDEX idx_username (username),
    INDEX idx_phone (phone),
    INDEX idx_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户表';

-- 额度使用表
CREATE TABLE IF NOT EXISTS quota_usage (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    usage_date DATE NOT NULL COMMENT '使用日期',
    usage_count INT NOT NULL DEFAULT 0 COMMENT '使用次数',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    UNIQUE KEY uk_user_date (user_id, usage_date),
    INDEX idx_usage_date (usage_date),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='额度使用表';

-- 短信验证码表
CREATE TABLE IF NOT EXISTS sms_codes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    phone VARCHAR(20) NOT NULL,
    code VARCHAR(10) NOT NULL COMMENT '验证码',
    action ENUM('register', 'login', 'bind', 'unbind', 'reset_password') NOT NULL COMMENT '操作类型',
    is_used BOOLEAN DEFAULT FALSE COMMENT '是否已使用',
    expires_at DATETIME NOT NULL COMMENT '过期时间',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    INDEX idx_phone_code (phone, code),
    INDEX idx_expires_at (expires_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='短信验证码表';

-- 创建默认管理员账户 (密码: admin123，请在生产环境中修改)
-- 密码哈希由 Python PasswordHasher 生成，这里使用占位符
-- INSERT INTO users (username, password_hash, role, status) VALUES
-- ('admin', '$2b$12$placeholder_hash', 'admin', 'active');

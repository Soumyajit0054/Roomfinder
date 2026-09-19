CREATE DATABASE IF NOT EXISTS roomfinder;

USE roomfinder;


CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,

    name VARCHAR(100) NOT NULL,

    email VARCHAR(150) NOT NULL UNIQUE,

    phone VARCHAR(20),

    password VARCHAR(255) NOT NULL,

    role ENUM('tenant', 'owner', 'admin')
        NOT NULL DEFAULT 'tenant',

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);


CREATE TABLE properties (
    id INT AUTO_INCREMENT PRIMARY KEY,

    owner_id INT NOT NULL,

    title VARCHAR(200) NOT NULL,

    description TEXT,

    location VARCHAR(150) NOT NULL,

    address VARCHAR(255),

    rent DECIMAL(10,2) NOT NULL,

    room_type VARCHAR(50) NOT NULL,

    furnished VARCHAR(20) DEFAULT 'No',

    food_available VARCHAR(20) DEFAULT 'No',

    gender_preference VARCHAR(30) DEFAULT 'Any',

    available TINYINT(1) DEFAULT 1,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (owner_id)
        REFERENCES users(id)
        ON DELETE CASCADE
);


CREATE TABLE property_images (
    id INT AUTO_INCREMENT PRIMARY KEY,

    property_id INT NOT NULL,

    image VARCHAR(255) NOT NULL,

    FOREIGN KEY (property_id)
        REFERENCES properties(id)
        ON DELETE CASCADE
);


CREATE TABLE favorites (
    id INT AUTO_INCREMENT PRIMARY KEY,

    tenant_id INT NOT NULL,

    property_id INT NOT NULL,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    UNIQUE KEY unique_favorite (
        tenant_id,
        property_id
    ),

    FOREIGN KEY (tenant_id)
        REFERENCES users(id)
        ON DELETE CASCADE,

    FOREIGN KEY (property_id)
        REFERENCES properties(id)
        ON DELETE CASCADE
);


CREATE TABLE rental_requests (
    id INT AUTO_INCREMENT PRIMARY KEY,

    property_id INT NOT NULL,

    tenant_id INT NOT NULL,

    message TEXT,

    status ENUM(
        'pending',
        'accepted',
        'rejected'
    ) DEFAULT 'pending',

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (property_id)
        REFERENCES properties(id)
        ON DELETE CASCADE,

    FOREIGN KEY (tenant_id)
        REFERENCES users(id)
        ON DELETE CASCADE
);


-- Admin account
--
-- Password: admin123
--
-- This hash is for Werkzeug's password hashing.
INSERT INTO users
(name, email, phone, password, role)
VALUES
(
    'Administrator',
    'admin@roomfinder.com',
    '0000000000',
    'scrypt:32768:8:1$admin$dummy',
    'admin'
);
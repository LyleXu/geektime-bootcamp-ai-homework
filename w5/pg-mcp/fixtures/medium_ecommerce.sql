-- ==========================================
-- 中型电商系统数据库 (Medium E-commerce Database)
-- ==========================================
-- 规模: 18张表, 5个视图, 4个枚举类型, 35个索引
-- 数据量: ~5000条记录
-- 场景: 中小型电商平台
-- ==========================================

-- 清理已存在的对象
DROP DATABASE IF EXISTS ecommerce_medium;
CREATE DATABASE ecommerce_medium;
\c ecommerce_medium;

-- ==========================================
-- 1. 枚举类型
-- ==========================================

CREATE TYPE order_status AS ENUM ('pending', 'paid', 'processing', 'shipped', 'delivered', 'cancelled', 'refunded');
CREATE TYPE payment_method AS ENUM ('credit_card', 'debit_card', 'paypal', 'alipay', 'wechat_pay', 'bank_transfer');
CREATE TYPE payment_status AS ENUM ('pending', 'completed', 'failed', 'refunded');
CREATE TYPE shipment_status AS ENUM ('pending', 'in_transit', 'delivered', 'returned');

-- ==========================================
-- 2. 用户表
-- ==========================================

CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(100),
    phone VARCHAR(20),
    avatar_url VARCHAR(255),
    email_verified BOOLEAN DEFAULT FALSE,
    phone_verified BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login_at TIMESTAMP
);

CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_phone ON users(phone);
COMMENT ON TABLE users IS '用户表 - Users table';
COMMENT ON COLUMN users.email_verified IS '邮箱是否已验证';

-- ==========================================
-- 3. 地址表
-- ==========================================

CREATE TABLE addresses (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    recipient_name VARCHAR(100) NOT NULL,
    phone VARCHAR(20) NOT NULL,
    province VARCHAR(50),
    city VARCHAR(50),
    district VARCHAR(50),
    street_address TEXT NOT NULL,
    postal_code VARCHAR(10),
    is_default BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_addresses_user ON addresses(user_id);
CREATE INDEX idx_addresses_is_default ON addresses(is_default);
COMMENT ON TABLE addresses IS '收货地址表';

-- ==========================================
-- 4. 商品分类表
-- ==========================================

CREATE TABLE categories (
    id SERIAL PRIMARY KEY,
    parent_id INTEGER REFERENCES categories(id) ON DELETE SET NULL,
    name VARCHAR(100) NOT NULL,
    slug VARCHAR(100) UNIQUE NOT NULL,
    description TEXT,
    icon_url VARCHAR(255),
    sort_order INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_categories_parent ON categories(parent_id);
CREATE INDEX idx_categories_slug ON categories(slug);
CREATE INDEX idx_categories_is_active ON categories(is_active);
COMMENT ON TABLE categories IS '商品分类表 - Category hierarchy';

-- ==========================================
-- 5. 品牌表
-- ==========================================

CREATE TABLE brands (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    slug VARCHAR(100) UNIQUE NOT NULL,
    logo_url VARCHAR(255),
    description TEXT,
    website VARCHAR(255),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_brands_slug ON brands(slug);
CREATE INDEX idx_brands_is_active ON brands(is_active);

-- ==========================================
-- 6. 商品表
-- ==========================================

CREATE TABLE products (
    id SERIAL PRIMARY KEY,
    category_id INTEGER NOT NULL REFERENCES categories(id) ON DELETE RESTRICT,
    brand_id INTEGER REFERENCES brands(id) ON DELETE SET NULL,
    sku VARCHAR(50) UNIQUE NOT NULL,
    name VARCHAR(200) NOT NULL,
    slug VARCHAR(200) UNIQUE NOT NULL,
    description TEXT,
    price DECIMAL(10, 2) NOT NULL,
    sale_price DECIMAL(10, 2),
    cost_price DECIMAL(10, 2),
    stock_quantity INTEGER DEFAULT 0,
    weight DECIMAL(8, 2),
    dimensions VARCHAR(50),
    is_active BOOLEAN DEFAULT TRUE,
    is_featured BOOLEAN DEFAULT FALSE,
    view_count INTEGER DEFAULT 0,
    sale_count INTEGER DEFAULT 0,
    rating_avg DECIMAL(3, 2) DEFAULT 0,
    rating_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_products_category ON products(category_id);
CREATE INDEX idx_products_brand ON products(brand_id);
CREATE INDEX idx_products_sku ON products(sku);
CREATE INDEX idx_products_slug ON products(slug);
CREATE INDEX idx_products_is_active ON products(is_active);
CREATE INDEX idx_products_is_featured ON products(is_featured);
CREATE INDEX idx_products_price ON products(price);
CREATE INDEX idx_products_sale_price ON products(sale_price);
COMMENT ON TABLE products IS '商品表 - Products catalog';
COMMENT ON COLUMN products.sale_price IS '促销价格';

-- ==========================================
-- 7. 商品图片表
-- ==========================================

CREATE TABLE product_images (
    id SERIAL PRIMARY KEY,
    product_id INTEGER NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    image_url VARCHAR(255) NOT NULL,
    alt_text VARCHAR(200),
    sort_order INTEGER DEFAULT 0,
    is_primary BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_product_images_product ON product_images(product_id);
CREATE INDEX idx_product_images_is_primary ON product_images(is_primary);

-- ==========================================
-- 8. 订单表
-- ==========================================

CREATE TABLE orders (
    id SERIAL PRIMARY KEY,
    order_no VARCHAR(50) UNIQUE NOT NULL,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    address_id INTEGER REFERENCES addresses(id) ON DELETE SET NULL,
    status order_status DEFAULT 'pending',
    subtotal DECIMAL(10, 2) NOT NULL,
    shipping_fee DECIMAL(10, 2) DEFAULT 0,
    tax DECIMAL(10, 2) DEFAULT 0,
    discount DECIMAL(10, 2) DEFAULT 0,
    total DECIMAL(10, 2) NOT NULL,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    paid_at TIMESTAMP,
    shipped_at TIMESTAMP,
    delivered_at TIMESTAMP,
    cancelled_at TIMESTAMP
);

CREATE INDEX idx_orders_order_no ON orders(order_no);
CREATE INDEX idx_orders_user ON orders(user_id);
CREATE INDEX idx_orders_status ON orders(status);
CREATE INDEX idx_orders_created_at ON orders(created_at);
COMMENT ON TABLE orders IS '订单表';

-- ==========================================
-- 9. 订单明细表
-- ==========================================

CREATE TABLE order_items (
    id SERIAL PRIMARY KEY,
    order_id INTEGER NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
    product_id INTEGER NOT NULL REFERENCES products(id) ON DELETE RESTRICT,
    product_name VARCHAR(200) NOT NULL,
    product_sku VARCHAR(50) NOT NULL,
    quantity INTEGER NOT NULL,
    unit_price DECIMAL(10, 2) NOT NULL,
    subtotal DECIMAL(10, 2) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_order_items_order ON order_items(order_id);
CREATE INDEX idx_order_items_product ON order_items(product_id);

-- ==========================================
-- 10. 支付记录表
-- ==========================================

CREATE TABLE payments (
    id SERIAL PRIMARY KEY,
    order_id INTEGER NOT NULL REFERENCES orders(id) ON DELETE RESTRICT,
    payment_no VARCHAR(50) UNIQUE NOT NULL,
    method payment_method NOT NULL,
    status payment_status DEFAULT 'pending',
    amount DECIMAL(10, 2) NOT NULL,
    transaction_id VARCHAR(100),
    paid_at TIMESTAMP,
    refunded_at TIMESTAMP,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_payments_order ON payments(order_id);
CREATE INDEX idx_payments_payment_no ON payments(payment_no);
CREATE INDEX idx_payments_status ON payments(status);
CREATE INDEX idx_payments_method ON payments(method);

-- ==========================================
-- 11. 物流表
-- ==========================================

CREATE TABLE shipments (
    id SERIAL PRIMARY KEY,
    order_id INTEGER NOT NULL REFERENCES orders(id) ON DELETE RESTRICT,
    tracking_no VARCHAR(100) UNIQUE NOT NULL,
    carrier VARCHAR(100),
    status shipment_status DEFAULT 'pending',
    shipped_at TIMESTAMP,
    delivered_at TIMESTAMP,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_shipments_order ON shipments(order_id);
CREATE INDEX idx_shipments_tracking_no ON shipments(tracking_no);
CREATE INDEX idx_shipments_status ON shipments(status);

-- ==========================================
-- 12. 购物车表
-- ==========================================

CREATE TABLE cart_items (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    product_id INTEGER NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    quantity INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, product_id)
);

CREATE INDEX idx_cart_items_user ON cart_items(user_id);
CREATE INDEX idx_cart_items_product ON cart_items(product_id);

-- ==========================================
-- 13. 收藏表
-- ==========================================

CREATE TABLE wishlists (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    product_id INTEGER NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, product_id)
);

CREATE INDEX idx_wishlists_user ON wishlists(user_id);
CREATE INDEX idx_wishlists_product ON wishlists(product_id);

-- ==========================================
-- 14. 商品评价表
-- ==========================================

CREATE TABLE reviews (
    id SERIAL PRIMARY KEY,
    product_id INTEGER NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE SET NULL,
    order_id INTEGER REFERENCES orders(id) ON DELETE SET NULL,
    rating INTEGER NOT NULL CHECK (rating >= 1 AND rating <= 5),
    title VARCHAR(200),
    content TEXT,
    images TEXT[],
    is_verified_purchase BOOLEAN DEFAULT FALSE,
    helpful_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_reviews_product ON reviews(product_id);
CREATE INDEX idx_reviews_user ON reviews(user_id);
CREATE INDEX idx_reviews_rating ON reviews(rating);
CREATE INDEX idx_reviews_is_verified ON reviews(is_verified_purchase);
COMMENT ON TABLE reviews IS '商品评价表';

-- ==========================================
-- 15. 优惠券表
-- ==========================================

CREATE TABLE coupons (
    id SERIAL PRIMARY KEY,
    code VARCHAR(50) UNIQUE NOT NULL,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    discount_type VARCHAR(20) NOT NULL, -- 'percentage' or 'fixed'
    discount_value DECIMAL(10, 2) NOT NULL,
    min_purchase DECIMAL(10, 2) DEFAULT 0,
    max_discount DECIMAL(10, 2),
    usage_limit INTEGER,
    used_count INTEGER DEFAULT 0,
    start_date TIMESTAMP NOT NULL,
    end_date TIMESTAMP NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_coupons_code ON coupons(code);
CREATE INDEX idx_coupons_is_active ON coupons(is_active);

-- ==========================================
-- 16. 用户优惠券表
-- ==========================================

CREATE TABLE user_coupons (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    coupon_id INTEGER NOT NULL REFERENCES coupons(id) ON DELETE CASCADE,
    order_id INTEGER REFERENCES orders(id) ON DELETE SET NULL,
    used_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, coupon_id)
);

CREATE INDEX idx_user_coupons_user ON user_coupons(user_id);
CREATE INDEX idx_user_coupons_coupon ON user_coupons(coupon_id);

-- ==========================================
-- 17. 库存日志表
-- ==========================================

CREATE TABLE inventory_logs (
    id SERIAL PRIMARY KEY,
    product_id INTEGER NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    order_id INTEGER REFERENCES orders(id) ON DELETE SET NULL,
    change_type VARCHAR(20) NOT NULL, -- 'restock', 'sale', 'return', 'adjust'
    quantity_change INTEGER NOT NULL,
    quantity_before INTEGER NOT NULL,
    quantity_after INTEGER NOT NULL,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_inventory_logs_product ON inventory_logs(product_id);
CREATE INDEX idx_inventory_logs_order ON inventory_logs(order_id);
CREATE INDEX idx_inventory_logs_created_at ON inventory_logs(created_at);

-- ==========================================
-- 18. 搜索历史表
-- ==========================================

CREATE TABLE search_history (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    keyword VARCHAR(200) NOT NULL,
    result_count INTEGER DEFAULT 0,
    searched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_search_history_user ON search_history(user_id);
CREATE INDEX idx_search_history_keyword ON search_history(keyword);
CREATE INDEX idx_search_history_searched_at ON search_history(searched_at);

-- ==========================================
-- 19. 视图
-- ==========================================

-- 商品详情视图
CREATE VIEW product_details AS
SELECT 
    p.id,
    p.sku,
    p.name,
    p.slug,
    p.description,
    p.price,
    p.sale_price,
    COALESCE(p.sale_price, p.price) AS current_price,
    p.stock_quantity,
    p.is_active,
    p.is_featured,
    p.view_count,
    p.sale_count,
    p.rating_avg,
    p.rating_count,
    c.name AS category_name,
    c.slug AS category_slug,
    b.name AS brand_name,
    b.slug AS brand_slug,
    p.created_at,
    p.updated_at
FROM products p
LEFT JOIN categories c ON p.category_id = c.id
LEFT JOIN brands b ON p.brand_id = b.id;

COMMENT ON VIEW product_details IS '商品详情视图';

-- 订单统计视图
CREATE VIEW order_statistics AS
SELECT 
    o.id,
    o.order_no,
    u.username,
    u.full_name,
    o.status,
    o.total,
    o.created_at,
    o.paid_at,
    o.delivered_at,
    COUNT(oi.id) AS item_count,
    SUM(oi.quantity) AS total_quantity
FROM orders o
JOIN users u ON o.user_id = u.id
LEFT JOIN order_items oi ON o.id = oi.order_id
GROUP BY o.id, u.username, u.full_name;

COMMENT ON VIEW order_statistics IS '订单统计视图';

-- 用户购买统计视图
CREATE VIEW user_purchase_stats AS
SELECT 
    u.id AS user_id,
    u.username,
    u.full_name,
    COUNT(DISTINCT o.id) AS order_count,
    SUM(CASE WHEN o.status = 'delivered' THEN o.total ELSE 0 END) AS total_spent,
    AVG(CASE WHEN o.status = 'delivered' THEN o.total ELSE NULL END) AS avg_order_value,
    MAX(o.created_at) AS last_order_date
FROM users u
LEFT JOIN orders o ON u.id = o.user_id
GROUP BY u.id, u.username, u.full_name;

COMMENT ON VIEW user_purchase_stats IS '用户购买统计视图';

-- 畅销商品视图
CREATE VIEW bestselling_products AS
SELECT 
    p.id,
    p.sku,
    p.name,
    p.price,
    p.stock_quantity,
    p.sale_count,
    p.rating_avg,
    p.rating_count,
    c.name AS category,
    b.name AS brand
FROM products p
LEFT JOIN categories c ON p.category_id = c.id
LEFT JOIN brands b ON p.brand_id = b.id
WHERE p.is_active = TRUE
ORDER BY p.sale_count DESC, p.rating_avg DESC
LIMIT 50;

COMMENT ON VIEW bestselling_products IS '畅销商品TOP50';

-- 库存预警视图
CREATE VIEW low_stock_products AS
SELECT 
    p.id,
    p.sku,
    p.name,
    p.stock_quantity,
    p.sale_count,
    c.name AS category,
    b.name AS brand
FROM products p
LEFT JOIN categories c ON p.category_id = c.id
LEFT JOIN brands b ON p.brand_id = b.id
WHERE p.is_active = TRUE AND p.stock_quantity < 20
ORDER BY p.stock_quantity ASC, p.sale_count DESC;

COMMENT ON VIEW low_stock_products IS '低库存商品预警';

-- ==========================================
-- 20. 测试数据
-- ==========================================

-- 插入用户 (100个)
DO $$
DECLARE
    i INTEGER;
    surnames TEXT[] := ARRAY['王', '李', '张', '刘', '陈', '杨', '赵', '黄', 'Wang', 'Li', 'Zhang', 'Liu', 'Chen'];
    names TEXT[] := ARRAY['小明', '小红', '伟', '芳', '强', '丽', 'Ming', 'Hong', 'Wei', 'Fang'];
BEGIN
    FOR i IN 1..100 LOOP
        INSERT INTO users (username, email, password_hash, full_name, phone, email_verified, phone_verified)
        VALUES (
            'user' || i,
            'user' || i || '@shop.com',
            '$2b$12$hash' || i,
            surnames[1 + (RANDOM() * (array_length(surnames, 1) - 1))::INTEGER] || names[1 + (RANDOM() * (array_length(names, 1) - 1))::INTEGER],
            '138' || LPAD((10000000 + RANDOM() * 89999999)::INTEGER::TEXT, 8, '0'),
            RANDOM() < 0.8,
            RANDOM() < 0.6
        );
    END LOOP;
END $$;

-- 插入地址 (150个)
DO $$
DECLARE
    i INTEGER;
    user_id INTEGER;
    provinces TEXT[] := ARRAY['北京', '上海', '广东', '浙江', '江苏', 'Beijing', 'Shanghai'];
    cities TEXT[] := ARRAY['北京市', '上海市', '广州市', '深圳市', '杭州市', '南京市'];
BEGIN
    FOR i IN 1..150 LOOP
        user_id := 1 + (RANDOM() * 99)::INTEGER;
        INSERT INTO addresses (user_id, recipient_name, phone, province, city, street_address, postal_code, is_default)
        VALUES (
            user_id,
            '收货人' || i,
            '138' || LPAD((10000000 + RANDOM() * 89999999)::INTEGER::TEXT, 8, '0'),
            provinces[1 + (RANDOM() * (array_length(provinces, 1) - 1))::INTEGER],
            cities[1 + (RANDOM() * (array_length(cities, 1) - 1))::INTEGER],
            '街道地址 ' || i || ' Street Address',
            LPAD((100000 + RANDOM() * 99999)::INTEGER::TEXT, 6, '0'),
            RANDOM() < 0.2
        );
    END LOOP;
END $$;

-- 插入分类 (20个，含层级)
INSERT INTO categories (id, parent_id, name, slug, description, is_active) VALUES
(1, NULL, '电子产品', 'electronics', 'Electronics', TRUE),
(2, 1, '手机', 'phones', 'Mobile Phones', TRUE),
(3, 1, '电脑', 'computers', 'Computers', TRUE),
(4, 1, '相机', 'cameras', 'Cameras', TRUE),
(5, NULL, '服装', 'clothing', 'Clothing & Fashion', TRUE),
(6, 5, '男装', 'mens-clothing', 'Men''s Clothing', TRUE),
(7, 5, '女装', 'womens-clothing', 'Women''s Clothing', TRUE),
(8, 5, '童装', 'kids-clothing', 'Kids Clothing', TRUE),
(9, NULL, '图书', 'books', 'Books', TRUE),
(10, 9, '技术书籍', 'tech-books', 'Technical Books', TRUE),
(11, 9, '文学', 'literature', 'Literature', TRUE),
(12, NULL, '家居', 'home', 'Home & Living', TRUE),
(13, 12, '家具', 'furniture', 'Furniture', TRUE),
(14, 12, '厨具', 'kitchenware', 'Kitchenware', TRUE),
(15, NULL, '运动', 'sports', 'Sports & Outdoors', TRUE),
(16, 15, '健身', 'fitness', 'Fitness', TRUE),
(17, 15, '户外', 'outdoor', 'Outdoor', TRUE),
(18, NULL, '美妆', 'beauty', 'Beauty & Personal Care', TRUE),
(19, 18, '护肤', 'skincare', 'Skincare', TRUE),
(20, 18, '彩妆', 'makeup', 'Makeup', TRUE);

-- 插入品牌 (30个)
DO $$
DECLARE
    brands_data TEXT[][] := ARRAY[
        ARRAY['Apple', 'apple'],
        ARRAY['Samsung', 'samsung'],
        ARRAY['Huawei', 'huawei'],
        ARRAY['Xiaomi', 'xiaomi'],
        ARRAY['Dell', 'dell'],
        ARRAY['Lenovo', 'lenovo'],
        ARRAY['Sony', 'sony'],
        ARRAY['Canon', 'canon'],
        ARRAY['Nike', 'nike'],
        ARRAY['Adidas', 'adidas'],
        ARRAY['Zara', 'zara'],
        ARRAY['H&M', 'hm'],
        ARRAY['Uniqlo', 'uniqlo'],
        ARRAY['优衣库', 'youyiku'],
        ARRAY['李宁', 'lining'],
        ARRAY['安踏', 'anta'],
        ARRAY['海尔', 'haier'],
        ARRAY['美的', 'midea'],
        ARRAY['格力', 'gree'],
        ARRAY['华为', 'huawei-cn']
    ];
    i INTEGER;
BEGIN
    FOR i IN 1..array_length(brands_data, 1) LOOP
        INSERT INTO brands (name, slug, is_active)
        VALUES (brands_data[i][1], brands_data[i][2], TRUE);
    END LOOP;
END $$;

-- 插入商品 (500个)
DO $$
DECLARE
    i INTEGER;
    cat_id INTEGER;
    brand_id INTEGER;
    base_price DECIMAL;
BEGIN
    FOR i IN 1..500 LOOP
        cat_id := 2 + (RANDOM() * 18)::INTEGER;
        brand_id := CASE WHEN RANDOM() < 0.8 THEN 1 + (RANDOM() * 19)::INTEGER ELSE NULL END;
        base_price := (20 + RANDOM() * 1980)::NUMERIC(10,2);
        
        INSERT INTO products (category_id, brand_id, sku, name, slug, description, price, sale_price, cost_price, stock_quantity, is_active, is_featured, view_count, sale_count, rating_avg, rating_count)
        VALUES (
            cat_id,
            brand_id,
            'SKU' || LPAD(i::TEXT, 6, '0'),
            'Product ' || i || ' - 商品' || i,
            'product-' || i,
            'This is a detailed description for product ' || i || '. 这是商品' || i || '的详细描述。',
            base_price,
            CASE WHEN RANDOM() < 0.3 THEN (base_price * (0.7 + RANDOM() * 0.2))::NUMERIC(10,2) ELSE NULL END,
            (base_price * 0.6)::NUMERIC(10,2),
            (10 + RANDOM() * 190)::INTEGER,
            RANDOM() < 0.95,
            RANDOM() < 0.1,
            (RANDOM() * 5000)::INTEGER,
            (RANDOM() * 500)::INTEGER,
            (3 + RANDOM() * 2)::NUMERIC(3,2),
            (RANDOM() * 200)::INTEGER
        );
    END LOOP;
END $$;

-- 插入商品图片 (1500个)
DO $$
DECLARE
    i INTEGER;
    prod_id INTEGER;
BEGIN
    FOR i IN 1..1500 LOOP
        prod_id := 1 + (RANDOM() * 499)::INTEGER;
        INSERT INTO product_images (product_id, image_url, alt_text, sort_order, is_primary)
        VALUES (
            prod_id,
            'https://cdn.shop.com/products/' || prod_id || '/img' || i || '.jpg',
            'Product image ' || i,
            i % 5,
            (i % 5 = 0)
        );
    END LOOP;
END $$;

-- 插入订单 (800个)
DO $$
DECLARE
    i INTEGER;
    user_id INTEGER;
    addr_id INTEGER;
    stat order_status;
    statuses order_status[] := ARRAY['pending', 'paid', 'processing', 'shipped', 'delivered', 'cancelled'];
    subtotal DECIMAL;
    total DECIMAL;
BEGIN
    FOR i IN 1..800 LOOP
        user_id := 1 + (RANDOM() * 99)::INTEGER;
        addr_id := 1 + (RANDOM() * 149)::INTEGER;
        stat := statuses[1 + (RANDOM() * 5)::INTEGER];
        subtotal := (50 + RANDOM() * 2950)::NUMERIC(10,2);
        total := (subtotal + 10 + subtotal * 0.06)::NUMERIC(10,2);
        
        INSERT INTO orders (order_no, user_id, address_id, status, subtotal, shipping_fee, tax, total, created_at, paid_at, delivered_at)
        VALUES (
            'ORD' || TO_CHAR(CURRENT_DATE, 'YYYYMMDD') || LPAD(i::TEXT, 6, '0'),
            user_id,
            addr_id,
            stat,
            subtotal,
            10.00,
            (subtotal * 0.06)::NUMERIC(10,2),
            total,
            CURRENT_TIMESTAMP - (RANDOM() * 90 || ' days')::INTERVAL,
            CASE WHEN stat != 'pending' THEN CURRENT_TIMESTAMP - (RANDOM() * 85 || ' days')::INTERVAL ELSE NULL END,
            CASE WHEN stat = 'delivered' THEN CURRENT_TIMESTAMP - (RANDOM() * 70 || ' days')::INTERVAL ELSE NULL END
        );
    END LOOP;
END $$;

-- 插入订单明细 (2000个)
DO $$
DECLARE
    i INTEGER;
    ord_id INTEGER;
    prod_id INTEGER;
    qty INTEGER;
    price DECIMAL;
BEGIN
    FOR i IN 1..2000 LOOP
        ord_id := 1 + (RANDOM() * 799)::INTEGER;
        prod_id := 1 + (RANDOM() * 499)::INTEGER;
        qty := 1 + (RANDOM() * 4)::INTEGER;
        price := (20 + RANDOM() * 980)::NUMERIC(10,2);
        
        INSERT INTO order_items (order_id, product_id, product_name, product_sku, quantity, unit_price, subtotal)
        SELECT 
            ord_id,
            prod_id,
            p.name,
            p.sku,
            qty,
            price,
            (price * qty)::NUMERIC(10,2)
        FROM products p
        WHERE p.id = prod_id;
    END LOOP;
END $$;

-- 插入支付记录 (700个)
DO $$
DECLARE
    i INTEGER;
    ord_id INTEGER;
    methods payment_method[] := ARRAY['credit_card', 'alipay', 'wechat_pay', 'paypal'];
    statuses payment_status[] := ARRAY['completed', 'pending', 'failed'];
BEGIN
    FOR i IN 1..700 LOOP
        ord_id := 1 + (RANDOM() * 799)::INTEGER;
        INSERT INTO payments (order_id, payment_no, method, status, amount, transaction_id, paid_at)
        SELECT 
            ord_id,
            'PAY' || TO_CHAR(CURRENT_DATE, 'YYYYMMDD') || LPAD(i::TEXT, 6, '0'),
            methods[1 + (RANDOM() * 3)::INTEGER],
            statuses[1 + (RANDOM() * 2)::INTEGER],
            o.total,
            'TXN' || LPAD(i::TEXT, 10, '0'),
            CASE WHEN RANDOM() < 0.8 THEN CURRENT_TIMESTAMP - (RANDOM() * 80 || ' days')::INTERVAL ELSE NULL END
        FROM orders o
        WHERE o.id = ord_id
        ON CONFLICT DO NOTHING;
    END LOOP;
END $$;

-- 插入物流记录 (600个)
DO $$
DECLARE
    i INTEGER;
    ord_id INTEGER;
    carriers TEXT[] := ARRAY['顺丰速运', '中通快递', '圆通速递', 'EMS', 'DHL'];
BEGIN
    FOR i IN 1..600 LOOP
        ord_id := 1 + (RANDOM() * 799)::INTEGER;
        INSERT INTO shipments (order_id, tracking_no, carrier, status, shipped_at, delivered_at)
        VALUES (
            ord_id,
            'SHIP' || LPAD(i::TEXT, 12, '0'),
            carriers[1 + (RANDOM() * 4)::INTEGER],
            'delivered',
            CURRENT_TIMESTAMP - (RANDOM() * 70 || ' days')::INTERVAL,
            CURRENT_TIMESTAMP - (RANDOM() * 60 || ' days')::INTERVAL
        )
        ON CONFLICT DO NOTHING;
    END LOOP;
END $$;

-- 插入购物车 (200个)
DO $$
DECLARE
    i INTEGER;
    user_id INTEGER;
    prod_id INTEGER;
BEGIN
    FOR i IN 1..200 LOOP
        user_id := 1 + (RANDOM() * 99)::INTEGER;
        prod_id := 1 + (RANDOM() * 499)::INTEGER;
        INSERT INTO cart_items (user_id, product_id, quantity)
        VALUES (user_id, prod_id, 1 + (RANDOM() * 3)::INTEGER)
        ON CONFLICT DO NOTHING;
    END LOOP;
END $$;

-- 插入收藏 (300个)
DO $$
DECLARE
    i INTEGER;
    user_id INTEGER;
    prod_id INTEGER;
BEGIN
    FOR i IN 1..300 LOOP
        user_id := 1 + (RANDOM() * 99)::INTEGER;
        prod_id := 1 + (RANDOM() * 499)::INTEGER;
        INSERT INTO wishlists (user_id, product_id)
        VALUES (user_id, prod_id)
        ON CONFLICT DO NOTHING;
    END LOOP;
END $$;

-- 插入评价 (1000个)
DO $$
DECLARE
    i INTEGER;
    prod_id INTEGER;
    user_id INTEGER;
    ord_id INTEGER;
    reviews TEXT[] := ARRAY[
        '非常好的商品！Very good!',
        '物超所值，推荐购买',
        'Excellent quality',
        '质量不错，值得购买',
        'Good value for money',
        '还可以，符合预期',
        'Fast delivery, good product',
        '包装精美，商品满意',
        'Perfect!',
        '五星好评！'
    ];
BEGIN
    FOR i IN 1..1000 LOOP
        prod_id := 1 + (RANDOM() * 499)::INTEGER;
        user_id := 1 + (RANDOM() * 99)::INTEGER;
        ord_id := CASE WHEN RANDOM() < 0.7 THEN 1 + (RANDOM() * 799)::INTEGER ELSE NULL END;
        
        INSERT INTO reviews (product_id, user_id, order_id, rating, title, content, is_verified_purchase, helpful_count)
        VALUES (
            prod_id,
            user_id,
            ord_id,
            1 + (RANDOM() * 4)::INTEGER,
            'Review ' || i,
            reviews[1 + (RANDOM() * 9)::INTEGER],
            ord_id IS NOT NULL,
            (RANDOM() * 50)::INTEGER
        );
    END LOOP;
END $$;

-- 插入优惠券 (20个)
DO $$
DECLARE
    i INTEGER;
BEGIN
    FOR i IN 1..20 LOOP
        INSERT INTO coupons (code, name, description, discount_type, discount_value, min_purchase, usage_limit, start_date, end_date, is_active)
        VALUES (
            'COUPON' || LPAD(i::TEXT, 4, '0'),
            '优惠券 ' || i || ' Coupon',
            'Special discount coupon',
            CASE WHEN RANDOM() < 0.5 THEN 'percentage' ELSE 'fixed' END,
            CASE WHEN RANDOM() < 0.5 THEN (5 + RANDOM() * 25)::NUMERIC(10,2) ELSE (10 + RANDOM() * 90)::NUMERIC(10,2) END,
            (50 + RANDOM() * 450)::NUMERIC(10,2),
            100 + (RANDOM() * 900)::INTEGER,
            CURRENT_TIMESTAMP - (30 || ' days')::INTERVAL,
            CURRENT_TIMESTAMP + (60 || ' days')::INTERVAL,
            RANDOM() < 0.8
        );
    END LOOP;
END $$;

-- ==========================================
-- 21. 权限配置
-- ==========================================

CREATE USER shop_readonly WITH PASSWORD 'readonly_pass';
GRANT CONNECT ON DATABASE ecommerce_medium TO shop_readonly;
GRANT USAGE ON SCHEMA public TO shop_readonly;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO shop_readonly;
GRANT SELECT ON ALL SEQUENCES IN SCHEMA public TO shop_readonly;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO shop_readonly;

-- ==========================================
-- 22. 数据库统计
-- ==========================================

ANALYZE;

DO $$
BEGIN
    RAISE NOTICE '========================================';
    RAISE NOTICE '中型电商数据库创建完成！';
    RAISE NOTICE 'Medium E-commerce Database Created!';
    RAISE NOTICE '========================================';
    RAISE NOTICE '表数量: 18';
    RAISE NOTICE '视图数量: 5';
    RAISE NOTICE '枚举类型: 4';
    RAISE NOTICE '索引数量: ~40';
    RAISE NOTICE '----------------------------------------';
    RAISE NOTICE '数据统计:';
    RAISE NOTICE '用户: 100';
    RAISE NOTICE '地址: 150';
    RAISE NOTICE '分类: 20';
    RAISE NOTICE '品牌: 20';
    RAISE NOTICE '商品: 500';
    RAISE NOTICE '商品图片: 1500';
    RAISE NOTICE '订单: 800';
    RAISE NOTICE '订单明细: 2000';
    RAISE NOTICE '支付记录: 700';
    RAISE NOTICE '物流记录: 600';
    RAISE NOTICE '购物车: 200';
    RAISE NOTICE '收藏: 300';
    RAISE NOTICE '评价: 1000';
    RAISE NOTICE '优惠券: 20';
    RAISE NOTICE '========================================';
END $$;

-- ==========================================
-- 小型博客系统数据库 (Small Blog Database)
-- ==========================================
-- 规模: 8张表, 2个视图, 1个枚举类型, 10个索引
-- 数据量: ~500条记录
-- 场景: 个人博客系统
-- ==========================================

-- 清理已存在的对象
DROP DATABASE IF EXISTS blog_small;
CREATE DATABASE blog_small;
\c blog_small;

-- ==========================================
-- 1. 枚举类型
-- ==========================================

CREATE TYPE post_status AS ENUM ('draft', 'published', 'archived');
CREATE TYPE comment_status AS ENUM ('pending', 'approved', 'spam');

-- ==========================================
-- 2. 用户表
-- ==========================================

CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(100),
    bio TEXT,
    avatar_url VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login_at TIMESTAMP
);

CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_email ON users(email);
COMMENT ON TABLE users IS '博客用户表';
COMMENT ON COLUMN users.bio IS '用户简介';

-- ==========================================
-- 3. 分类表
-- ==========================================

CREATE TABLE categories (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) UNIQUE NOT NULL,
    slug VARCHAR(50) UNIQUE NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_categories_slug ON categories(slug);
COMMENT ON TABLE categories IS '文章分类表';

-- ==========================================
-- 4. 标签表
-- ==========================================

CREATE TABLE tags (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) UNIQUE NOT NULL,
    slug VARCHAR(50) UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_tags_slug ON tags(slug);

-- ==========================================
-- 5. 文章表
-- ==========================================

CREATE TABLE posts (
    id SERIAL PRIMARY KEY,
    title VARCHAR(200) NOT NULL,
    slug VARCHAR(200) UNIQUE NOT NULL,
    content TEXT NOT NULL,
    excerpt TEXT,
    author_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    category_id INTEGER REFERENCES categories(id) ON DELETE SET NULL,
    status post_status DEFAULT 'draft',
    view_count INTEGER DEFAULT 0,
    published_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_posts_author ON posts(author_id);
CREATE INDEX idx_posts_category ON posts(category_id);
CREATE INDEX idx_posts_status ON posts(status);
CREATE INDEX idx_posts_published_at ON posts(published_at);
COMMENT ON TABLE posts IS '博客文章表';
COMMENT ON COLUMN posts.excerpt IS '文章摘要';

-- ==========================================
-- 6. 文章标签关联表
-- ==========================================

CREATE TABLE post_tags (
    post_id INTEGER NOT NULL REFERENCES posts(id) ON DELETE CASCADE,
    tag_id INTEGER NOT NULL REFERENCES tags(id) ON DELETE CASCADE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (post_id, tag_id)
);

CREATE INDEX idx_post_tags_post ON post_tags(post_id);
CREATE INDEX idx_post_tags_tag ON post_tags(tag_id);

-- ==========================================
-- 7. 评论表
-- ==========================================

CREATE TABLE comments (
    id SERIAL PRIMARY KEY,
    post_id INTEGER NOT NULL REFERENCES posts(id) ON DELETE CASCADE,
    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    parent_id INTEGER REFERENCES comments(id) ON DELETE CASCADE,
    content TEXT NOT NULL,
    status comment_status DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_comments_post ON comments(post_id);
CREATE INDEX idx_comments_user ON comments(user_id);
CREATE INDEX idx_comments_parent ON comments(parent_id);
CREATE INDEX idx_comments_status ON comments(status);

-- ==========================================
-- 8. 页面浏览记录表
-- ==========================================

CREATE TABLE page_views (
    id SERIAL PRIMARY KEY,
    post_id INTEGER NOT NULL REFERENCES posts(id) ON DELETE CASCADE,
    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    ip_address INET,
    user_agent TEXT,
    viewed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_page_views_post ON page_views(post_id);
CREATE INDEX idx_page_views_viewed_at ON page_views(viewed_at);

-- ==========================================
-- 9. 视图
-- ==========================================

-- 文章统计视图
CREATE VIEW post_stats AS
SELECT 
    p.id,
    p.title,
    p.slug,
    p.status,
    u.username AS author,
    c.name AS category,
    p.view_count,
    COUNT(DISTINCT cm.id) AS comment_count,
    COUNT(DISTINCT pt.tag_id) AS tag_count,
    p.published_at,
    p.created_at
FROM posts p
LEFT JOIN users u ON p.author_id = u.id
LEFT JOIN categories c ON p.category_id = c.id
LEFT JOIN comments cm ON p.id = cm.post_id AND cm.status = 'approved'
LEFT JOIN post_tags pt ON p.id = pt.post_id
GROUP BY p.id, u.username, c.name;

COMMENT ON VIEW post_stats IS '文章统计视图，包含评论数、标签数等';

-- 热门文章视图
CREATE VIEW popular_posts AS
SELECT 
    p.id,
    p.title,
    p.slug,
    u.username AS author,
    p.view_count,
    COUNT(cm.id) AS comment_count,
    p.published_at
FROM posts p
JOIN users u ON p.author_id = u.id
LEFT JOIN comments cm ON p.id = cm.post_id AND cm.status = 'approved'
WHERE p.status = 'published'
GROUP BY p.id, u.username
ORDER BY p.view_count DESC, comment_count DESC
LIMIT 10;

COMMENT ON VIEW popular_posts IS '热门文章TOP10';

-- ==========================================
-- 10. 测试数据
-- ==========================================

-- 插入用户 (20个)
INSERT INTO users (username, email, password_hash, full_name, bio) VALUES
('alice_wang', 'alice@blog.com', '$2b$12$hash1', '王小明', '热爱编程的技术博主'),
('bob_lee', 'bob@blog.com', '$2b$12$hash2', '李国强', 'Java开发工程师'),
('charlie_zhang', 'charlie@blog.com', '$2b$12$hash3', 'Zhang San', 'Full-stack developer'),
('david_liu', 'david@blog.com', '$2b$12$hash4', '刘德华', 'Python爱好者'),
('emma_chen', 'emma@blog.com', '$2b$12$hash5', '陈小红', 'AI researcher'),
('frank_wu', 'frank@blog.com', '$2b$12$hash6', '吴大伟', '数据分析师'),
('grace_huang', 'grace@blog.com', '$2b$12$hash7', 'Grace Huang', 'Frontend developer'),
('henry_zhou', 'henry@blog.com', '$2b$12$hash8', '周杰伦', '音乐与代码'),
('iris_sun', 'iris@blog.com', '$2b$12$hash9', '孙燕姿', 'Tech writer'),
('jack_ma', 'jack@blog.com', '$2b$12$hash10', 'Jack Ma', 'Entrepreneur'),
('kevin_lin', 'kevin@blog.com', '$2b$12$hash11', '林俊杰', 'DevOps engineer'),
('lisa_tang', 'lisa@blog.com', '$2b$12$hash12', '唐小丽', 'Mobile developer'),
('mike_wang', 'mike@blog.com', '$2b$12$hash13', 'Mike Wang', 'Cloud architect'),
('nancy_zhao', 'nancy@blog.com', '$2b$12$hash14', '赵敏', 'Security expert'),
('oliver_xu', 'oliver@blog.com', '$2b$12$hash15', '徐志摩', 'Poet & coder'),
('peter_qian', 'peter@blog.com', '$2b$12$hash16', 'Peter Qian', 'Blockchain dev'),
('queen_song', 'queen@blog.com', '$2b$12$hash17', '宋美龄', 'Tech leader'),
('ryan_feng', 'ryan@blog.com', '$2b$12$hash18', '冯小刚', 'Film & tech'),
('susan_jiang', 'susan@blog.com', '$2b$12$hash19', '姜文', 'Director'),
('tom_yu', 'tom@blog.com', '$2b$12$hash20', '于谦', 'Comedian');

-- 插入分类 (5个)
INSERT INTO categories (name, slug, description) VALUES
('技术', 'tech', '技术相关文章'),
('生活', 'life', '生活感悟'),
('旅行', 'travel', '旅行游记'),
('读书', 'reading', '读书笔记'),
('思考', 'thinking', '随笔与思考');

-- 插入标签 (15个)
INSERT INTO tags (name, slug) VALUES
('Python', 'python'),
('JavaScript', 'javascript'),
('AI', 'ai'),
('Database', 'database'),
('Web', 'web'),
('云计算', 'cloud'),
('摄影', 'photography'),
('美食', 'food'),
('历史', 'history'),
('哲学', 'philosophy'),
('音乐', 'music'),
('电影', 'movie'),
('运动', 'sports'),
('健康', 'health'),
('创业', 'startup');

-- 插入文章 (100个)
DO $$
DECLARE
    i INTEGER;
    user_id INTEGER;
    cat_id INTEGER;
    stat post_status;
    pub_date TIMESTAMP;
BEGIN
    FOR i IN 1..100 LOOP
        user_id := (RANDOM() * 19 + 1)::INTEGER;
        cat_id := (RANDOM() * 4 + 1)::INTEGER;
        
        IF i % 3 = 0 THEN
            stat := 'draft';
            pub_date := NULL;
        ELSIF i % 5 = 0 THEN
            stat := 'archived';
            pub_date := CURRENT_TIMESTAMP - (RANDOM() * 365 || ' days')::INTERVAL;
        ELSE
            stat := 'published';
            pub_date := CURRENT_TIMESTAMP - (RANDOM() * 180 || ' days')::INTERVAL;
        END IF;
        
        INSERT INTO posts (title, slug, content, excerpt, author_id, category_id, status, view_count, published_at)
        VALUES (
            'Article Title ' || i || ' - ' || (CASE WHEN i % 2 = 0 THEN '技术分享' ELSE 'Tech Sharing' END),
            'article-' || i,
            'This is the full content of article ' || i || '. It contains detailed information and examples.',
            'This is the excerpt of article ' || i,
            user_id,
            cat_id,
            stat,
            (RANDOM() * 10000)::INTEGER,
            pub_date
        );
    END LOOP;
END $$;

-- 为文章添加标签 (200个关联)
DO $$
DECLARE
    i INTEGER;
    post_id INTEGER;
    tag_id INTEGER;
BEGIN
    FOR i IN 1..200 LOOP
        post_id := (RANDOM() * 99 + 1)::INTEGER;
        tag_id := (RANDOM() * 14 + 1)::INTEGER;
        
        INSERT INTO post_tags (post_id, tag_id)
        VALUES (post_id, tag_id)
        ON CONFLICT DO NOTHING;
    END LOOP;
END $$;

-- 插入评论 (300个)
DO $$
DECLARE
    i INTEGER;
    post_id INTEGER;
    user_id INTEGER;
    stat comment_status;
BEGIN
    FOR i IN 1..300 LOOP
        post_id := (RANDOM() * 99 + 1)::INTEGER;
        user_id := (RANDOM() * 19 + 1)::INTEGER;
        
        IF i % 4 = 0 THEN
            stat := 'pending';
        ELSIF i % 10 = 0 THEN
            stat := 'spam';
        ELSE
            stat := 'approved';
        END IF;
        
        INSERT INTO comments (post_id, user_id, content, status)
        VALUES (
            post_id,
            user_id,
            'This is comment ' || i || '. Great article!',
            stat
        );
    END LOOP;
END $$;

-- 插入页面浏览记录 (1000个)
DO $$
DECLARE
    i INTEGER;
    post_id INTEGER;
    user_id INTEGER;
BEGIN
    FOR i IN 1..1000 LOOP
        post_id := (RANDOM() * 99 + 1)::INTEGER;
        user_id := CASE WHEN RANDOM() < 0.7 THEN (RANDOM() * 19 + 1)::INTEGER ELSE NULL END;
        
        INSERT INTO page_views (post_id, user_id, ip_address, user_agent, viewed_at)
        VALUES (
            post_id,
            user_id,
            ('192.168.' || (RANDOM() * 255)::INTEGER || '.' || (RANDOM() * 255)::INTEGER)::INET,
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            CURRENT_TIMESTAMP - (RANDOM() * 90 || ' days')::INTERVAL
        );
    END LOOP;
END $$;

-- ==========================================
-- 11. 权限配置
-- ==========================================

CREATE USER blog_readonly WITH PASSWORD 'readonly_pass';
GRANT CONNECT ON DATABASE blog_small TO blog_readonly;
GRANT USAGE ON SCHEMA public TO blog_readonly;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO blog_readonly;
GRANT SELECT ON ALL SEQUENCES IN SCHEMA public TO blog_readonly;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO blog_readonly;

-- ==========================================
-- 12. 数据库统计
-- ==========================================

-- 更新统计信息
ANALYZE;

-- 显示数据库基本信息
DO $$
BEGIN
    RAISE NOTICE '========================================';
    RAISE NOTICE '小型博客数据库创建完成！';
    RAISE NOTICE '========================================';
    RAISE NOTICE '表数量: 8';
    RAISE NOTICE '视图数量: 2';
    RAISE NOTICE '枚举类型: 2';
    RAISE NOTICE '索引数量: ~20';
    RAISE NOTICE '----------------------------------------';
    RAISE NOTICE '数据统计:';
    RAISE NOTICE '用户: 20';
    RAISE NOTICE '分类: 5';
    RAISE NOTICE '标签: 15';
    RAISE NOTICE '文章: 100';
    RAISE NOTICE '评论: 300';
    RAISE NOTICE '浏览记录: 1000';
    RAISE NOTICE '========================================';
END $$;

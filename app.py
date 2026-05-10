"""
ShopForge - Online Shopping Platform Management System
Demonstrates advanced SQL concepts: JOINs, CTEs, Window Functions,
Subqueries, Triggers, Views, Indexes, Transactions, Aggregations
"""

import sqlite3
import json
import os
from datetime import datetime, timedelta
from flask import Flask, render_template, request, jsonify, g
import random

app = Flask(__name__)
DB_PATH = "shopforge.db"

# ─────────────────────────────────────────
#  DATABASE LAYER
# ─────────────────────────────────────────

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DB_PATH)
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA foreign_keys = ON")
        db.execute("PRAGMA journal_mode = WAL")
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def query_db(query, args=(), one=False):
    cur = get_db().execute(query, args)
    rv = cur.fetchall()
    return (rv[0] if rv else None) if one else rv

def modify_db(query, args=()):
    db = get_db()
    cur = db.execute(query, args)
    db.commit()
    return cur.lastrowid


# ─────────────────────────────────────────
#  SCHEMA — Advanced SQL Concepts
# ─────────────────────────────────────────

SCHEMA = """
-- TABLES with proper constraints & foreign keys
CREATE TABLE IF NOT EXISTS categories (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    name      TEXT NOT NULL UNIQUE,
    icon      TEXT DEFAULT '📦',
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS products (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT NOT NULL,
    description TEXT,
    price       REAL NOT NULL CHECK(price >= 0),
    stock       INTEGER NOT NULL DEFAULT 0 CHECK(stock >= 0),
    category_id INTEGER REFERENCES categories(id) ON DELETE SET NULL,
    sku         TEXT UNIQUE,
    rating      REAL DEFAULT 0 CHECK(rating BETWEEN 0 AND 5),
    image_seed  INTEGER,
    created_at  TEXT DEFAULT (datetime('now')),
    updated_at  TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS customers (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    name       TEXT NOT NULL,
    email      TEXT NOT NULL UNIQUE,
    city       TEXT,
    tier       TEXT DEFAULT 'Bronze' CHECK(tier IN ('Bronze','Silver','Gold','Platinum')),
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS orders (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id INTEGER NOT NULL REFERENCES customers(id) ON DELETE CASCADE,
    status      TEXT DEFAULT 'Pending' CHECK(status IN ('Pending','Processing','Shipped','Delivered','Cancelled')),
    total       REAL DEFAULT 0,
    discount    REAL DEFAULT 0,
    created_at  TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS order_items (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id   INTEGER NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
    product_id INTEGER NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    quantity   INTEGER NOT NULL CHECK(quantity > 0),
    unit_price REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS reviews (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id  INTEGER NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    customer_id INTEGER NOT NULL REFERENCES customers(id) ON DELETE CASCADE,
    rating      INTEGER CHECK(rating BETWEEN 1 AND 5),
    body        TEXT,
    created_at  TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS audit_log (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    event     TEXT NOT NULL,
    detail    TEXT,
    logged_at TEXT DEFAULT (datetime('now'))
);

-- INDEXES for query performance
CREATE INDEX IF NOT EXISTS idx_products_category ON products(category_id);
CREATE INDEX IF NOT EXISTS idx_orders_customer   ON orders(customer_id);
CREATE INDEX IF NOT EXISTS idx_orders_status     ON orders(status);
CREATE INDEX IF NOT EXISTS idx_order_items_order ON order_items(order_id);
CREATE INDEX IF NOT EXISTS idx_reviews_product   ON reviews(product_id);

-- VIEW: enriched order summary (JOIN + aggregation)
CREATE VIEW IF NOT EXISTS vw_order_summary AS
SELECT
    o.id,
    c.name  AS customer_name,
    c.email AS customer_email,
    c.tier,
    o.status,
    o.total,
    o.discount,
    COUNT(oi.id)       AS item_count,
    SUM(oi.quantity)   AS total_qty,
    o.created_at
FROM orders o
JOIN customers c      ON c.id = o.customer_id
LEFT JOIN order_items oi ON oi.order_id = o.id
GROUP BY o.id;

-- VIEW: product performance (multi-JOIN + aggregation)
CREATE VIEW IF NOT EXISTS vw_product_performance AS
SELECT
    p.id,
    p.name,
    p.price,
    p.stock,
    cat.name          AS category,
    p.rating,
    COUNT(oi.id)      AS times_ordered,
    COALESCE(SUM(oi.quantity), 0) AS units_sold,
    COALESCE(SUM(oi.quantity * oi.unit_price), 0) AS revenue
FROM products p
LEFT JOIN categories  cat ON cat.id = p.category_id
LEFT JOIN order_items oi  ON oi.product_id = p.id
GROUP BY p.id;

-- TRIGGER: auto-update product rating after review insert
CREATE TRIGGER IF NOT EXISTS trg_update_product_rating
AFTER INSERT ON reviews
BEGIN
    UPDATE products
    SET rating = (
        SELECT ROUND(AVG(rating), 1) FROM reviews WHERE product_id = NEW.product_id
    ),
    updated_at = datetime('now')
    WHERE id = NEW.product_id;

    INSERT INTO audit_log(event, detail)
    VALUES('REVIEW_ADDED', 'Product #' || NEW.product_id || ' got rating ' || NEW.rating);
END;

-- TRIGGER: log order status changes
CREATE TRIGGER IF NOT EXISTS trg_log_order_status
AFTER UPDATE OF status ON orders
BEGIN
    INSERT INTO audit_log(event, detail)
    VALUES('ORDER_STATUS_CHANGE',
           'Order #' || NEW.id || ': ' || OLD.status || ' → ' || NEW.status);
END;
"""


def seed_data(db):
    cats = [
        ("Electronics","⚡"), ("Clothing","👕"), ("Books","📚"),
        ("Home & Garden","🏡"), ("Sports","⚽"), ("Beauty","💄"), ("Toys","🧸")
    ]
    for name, icon in cats:
        db.execute("INSERT OR IGNORE INTO categories(name,icon) VALUES(?,?)", (name, icon))

    products_data = [
        ("Wireless Noise-Cancelling Headphones","Premium audio, 30hr battery",18999,45,1,"WNC-001",4.7),
        ("4K Ultra HD Smart TV 55\"","HDR, Dolby Atmos, 4 HDMI",54999,12,1,"TV-4K-55",4.5),
        ("Mechanical Gaming Keyboard","RGB, Cherry MX Red switches",7499,80,1,"KBD-MX1",4.6),
        ("Slim Fit Oxford Shirt","100% cotton, wrinkle-free",1299,150,2,"SHT-OX1",4.2),
        ("Running Shoes Pro","Lightweight, breathable mesh",4999,60,5,"SHO-RUN1",4.8),
        ("The Pragmatic Programmer","20th Anniversary Edition",2499,35,3,"BK-PP20",4.9),
        ("Clean Code","A Handbook of Agile Software",1999,40,3,"BK-CC01",4.8),
        ("Air Fryer 5.5L","Digital display, 8 presets",5999,25,4,"KIT-AF55",4.6),
        ("Yoga Mat Premium","Non-slip, 6mm thick",1799,90,5,"YOG-PM6",4.4),
        ("Vitamin C Serum","30ml, 20% concentration",2299,200,6,"BEA-VC30",4.5),
        ("LEGO Creator Set","500 pieces, 3-in-1 build",3499,30,7,"TOY-LG01",4.7),
        ("Bluetooth Speaker","Waterproof IPX7, 360° sound",3999,55,1,"SPK-BT1",4.3),
        ("Denim Jacket","Classic wash, regular fit",2799,70,2,"JKT-DN1",4.1),
        ("Succulent Plant Set","Set of 6, low-maintenance",899,120,4,"PLT-SC6",4.6),
        ("Protein Powder 1kg","Whey isolate, chocolate",2999,85,5,"SPT-WP1",4.4),
    ]
    for i,(name,desc,price,stock,cat,sku,rating) in enumerate(products_data, 1):
        db.execute("""
            INSERT OR IGNORE INTO products(name,description,price,stock,category_id,sku,rating,image_seed)
            VALUES(?,?,?,?,?,?,?,?)
        """, (name, desc, price, stock, cat, sku, rating, i*7+13))

    customers_data = [
        ("Priya Sharma","priya@example.com","Mumbai","Platinum"),
        ("Rahul Mehta","rahul@example.com","Delhi","Gold"),
        ("Ananya Iyer","ananya@example.com","Bangalore","Silver"),
        ("Karthik Nair","karthik@example.com","Chennai","Gold"),
        ("Sneha Patel","sneha@example.com","Ahmedabad","Bronze"),
        ("Vikram Singh","vikram@example.com","Jaipur","Silver"),
        ("Deepika Rao","deepika@example.com","Hyderabad","Platinum"),
        ("Arjun Reddy","arjun@example.com","Pune","Bronze"),
        ("Meera Joshi","meera@example.com","Kolkata","Gold"),
        ("Aditya Kumar","aditya@example.com","Chandigarh","Silver"),
    ]
    for name,email,city,tier in customers_data:
        db.execute("INSERT OR IGNORE INTO customers(name,email,city,tier) VALUES(?,?,?,?)",
                   (name,email,city,tier))

    statuses = ["Delivered","Delivered","Delivered","Shipped","Processing","Pending","Cancelled"]
    random.seed(42)
    for o in range(30):
        cid = random.randint(1,10)
        status = random.choice(statuses)
        days_ago = random.randint(0,90)
        created = (datetime.now() - timedelta(days=days_ago)).strftime("%Y-%m-%d %H:%M:%S")
        oid = db.execute(
            "INSERT INTO orders(customer_id,status,created_at) VALUES(?,?,?)",
            (cid, status, created)
        ).lastrowid
        total = 0
        n_items = random.randint(1,4)
        for _ in range(n_items):
            pid = random.randint(1,15)
            row = db.execute("SELECT price FROM products WHERE id=?", (pid,)).fetchone()
            if not row: continue
            qty = random.randint(1,3)
            price = row[0]
            total += qty * price
            db.execute(
                "INSERT INTO order_items(order_id,product_id,quantity,unit_price) VALUES(?,?,?,?)",
                (oid, pid, qty, price)
            )
        discount = round(total * random.choice([0,0,0,0.05,0.10]), 2)
        db.execute("UPDATE orders SET total=?, discount=? WHERE id=?",
                   (round(total,2), discount, oid))

    for r in range(40):
        pid = random.randint(1,15)
        cid = random.randint(1,10)
        rating = random.randint(3,5)
        db.execute(
            "INSERT OR IGNORE INTO reviews(product_id,customer_id,rating) VALUES(?,?,?)",
            (pid, cid, rating)
        )
    db.commit()


def init_db():
    if os.path.exists(DB_PATH):
        return
    conn = sqlite3.connect(DB_PATH)
    conn.executescript(SCHEMA)
    seed_data(conn)
    conn.close()


# ─────────────────────────────────────────
#  API ROUTES
# ─────────────────────────────────────────

@app.route("/")
def index():
    return render_template("index.html")


# ── DASHBOARD ──────────────────────────
@app.route("/api/dashboard")
def dashboard():
    db = get_db()

    # KPIs with subqueries
    kpis = db.execute("""
        SELECT
            (SELECT COUNT(*) FROM orders)                           AS total_orders,
            (SELECT ROUND(SUM(total),2) FROM orders
                WHERE status != 'Cancelled')                        AS total_revenue,
            (SELECT COUNT(*) FROM customers)                        AS total_customers,
            (SELECT COUNT(*) FROM products WHERE stock < 20)        AS low_stock,
            (SELECT ROUND(AVG(total),2) FROM orders
                WHERE status='Delivered')                           AS avg_order_value,
            (SELECT COUNT(*) FROM orders WHERE status='Pending')    AS pending_orders
    """).fetchone()

    # Revenue by month — GROUP BY + strftime
    monthly = db.execute("""
        SELECT strftime('%Y-%m', created_at) AS month,
               ROUND(SUM(total),2)           AS revenue,
               COUNT(*)                      AS order_count
        FROM orders
        WHERE status != 'Cancelled'
        GROUP BY month
        ORDER BY month DESC
        LIMIT 6
    """).fetchall()

    # Top categories by revenue — multi-JOIN + GROUP BY
    cat_revenue = db.execute("""
        SELECT c.name AS category, c.icon,
               ROUND(SUM(oi.quantity * oi.unit_price),2) AS revenue,
               SUM(oi.quantity)                           AS units
        FROM order_items oi
        JOIN products p    ON p.id = oi.product_id
        JOIN categories c  ON c.id = p.category_id
        JOIN orders o      ON o.id = oi.order_id
        WHERE o.status != 'Cancelled'
        GROUP BY c.id
        ORDER BY revenue DESC
        LIMIT 6
    """).fetchall()

    # Order status distribution
    status_dist = db.execute("""
        SELECT status, COUNT(*) AS cnt
        FROM orders
        GROUP BY status
        ORDER BY cnt DESC
    """).fetchall()

    # Customer tier distribution
    tier_dist = db.execute("""
        SELECT tier, COUNT(*) AS cnt FROM customers GROUP BY tier
    """).fetchall()

    return jsonify({
        "kpis": dict(kpis),
        "monthly": [dict(r) for r in monthly],
        "cat_revenue": [dict(r) for r in cat_revenue],
        "status_dist": [dict(r) for r in status_dist],
        "tier_dist": [dict(r) for r in tier_dist],
    })


# ── PRODUCTS ───────────────────────────
@app.route("/api/products")
def products():
    search = request.args.get("search","")
    cat    = request.args.get("category","")
    sort   = request.args.get("sort","revenue")
    rows   = query_db(f"""
        SELECT * FROM vw_product_performance
        WHERE (name LIKE ? OR category LIKE ?)
          AND (? = '' OR category = ?)
        ORDER BY {sort if sort in ('revenue','units_sold','price','rating','stock') else 'revenue'} DESC
    """, (f"%{search}%", f"%{search}%", cat, cat))
    return jsonify([dict(r) for r in rows])


@app.route("/api/products/<int:pid>")
def product_detail(pid):
    db = get_db()
    p = db.execute("""
        SELECT p.*, c.name AS category, c.icon
        FROM products p
        LEFT JOIN categories c ON c.id = p.category_id
        WHERE p.id = ?
    """, (pid,)).fetchone()
    if not p:
        return jsonify({"error":"Not found"}), 404

    # Reviews with customer info — JOIN
    reviews = db.execute("""
        SELECT r.rating, r.body, r.created_at, cu.name AS reviewer
        FROM reviews r
        JOIN customers cu ON cu.id = r.customer_id
        WHERE r.product_id = ?
        ORDER BY r.created_at DESC
        LIMIT 5
    """, (pid,)).fetchall()

    # Related products — subquery + LIMIT
    related = db.execute("""
        SELECT id, name, price, rating FROM products
        WHERE category_id = (SELECT category_id FROM products WHERE id = ?)
          AND id != ?
        ORDER BY rating DESC
        LIMIT 4
    """, (pid, pid)).fetchall()

    return jsonify({
        "product": dict(p),
        "reviews": [dict(r) for r in reviews],
        "related": [dict(r) for r in related],
    })


@app.route("/api/products", methods=["POST"])
def add_product():
    d = request.json
    pid = modify_db("""
        INSERT INTO products(name,description,price,stock,category_id,sku,image_seed)
        VALUES(?,?,?,?,?,?,?)
    """, (d["name"], d.get("description",""), d["price"], d.get("stock",0),
          d.get("category_id"), d.get("sku",""), random.randint(10,999)))
    modify_db("INSERT INTO audit_log(event,detail) VALUES('PRODUCT_ADDED','Product #' || ?)", (pid,))
    return jsonify({"id": pid, "message": "Product added"})


@app.route("/api/products/<int:pid>", methods=["PUT"])
def update_product(pid):
    d = request.json
    modify_db("""
        UPDATE products SET name=?, price=?, stock=?, updated_at=datetime('now')
        WHERE id=?
    """, (d["name"], d["price"], d["stock"], pid))
    return jsonify({"message": "Updated"})


@app.route("/api/products/<int:pid>", methods=["DELETE"])
def delete_product(pid):
    modify_db("DELETE FROM products WHERE id=?", (pid,))
    return jsonify({"message": "Deleted"})


# ── ORDERS ────────────────────────────
@app.route("/api/orders")
def orders():
    status = request.args.get("status","")
    rows = query_db("""
        SELECT * FROM vw_order_summary
        WHERE (? = '' OR status = ?)
        ORDER BY created_at DESC
        LIMIT 50
    """, (status, status))
    return jsonify([dict(r) for r in rows])


@app.route("/api/orders/<int:oid>")
def order_detail(oid):
    db = get_db()
    o = db.execute("SELECT * FROM vw_order_summary WHERE id=?", (oid,)).fetchone()
    if not o:
        return jsonify({"error":"Not found"}), 404
    items = db.execute("""
        SELECT oi.quantity, oi.unit_price,
               p.name AS product_name, p.sku,
               (oi.quantity * oi.unit_price) AS subtotal
        FROM order_items oi
        JOIN products p ON p.id = oi.product_id
        WHERE oi.order_id = ?
    """, (oid,)).fetchall()
    return jsonify({"order": dict(o), "items": [dict(i) for i in items]})


@app.route("/api/orders/<int:oid>/status", methods=["PUT"])
def update_order_status(oid):
    new_status = request.json.get("status")
    modify_db("UPDATE orders SET status=? WHERE id=?", (new_status, oid))
    return jsonify({"message": "Status updated"})


@app.route("/api/orders", methods=["POST"])
def create_order():
    d = request.json
    db = get_db()
    # TRANSACTION: atomic order creation
    try:
        oid = db.execute(
            "INSERT INTO orders(customer_id,status) VALUES(?,?)",
            (d["customer_id"], "Pending")
        ).lastrowid
        total = 0
        for item in d["items"]:
            row = db.execute("SELECT price,stock FROM products WHERE id=?",
                             (item["product_id"],)).fetchone()
            if not row or row["stock"] < item["quantity"]:
                db.rollback()
                return jsonify({"error": f"Insufficient stock for product {item['product_id']}"}), 400
            db.execute("""
                INSERT INTO order_items(order_id,product_id,quantity,unit_price)
                VALUES(?,?,?,?)
            """, (oid, item["product_id"], item["quantity"], row["price"]))
            db.execute("UPDATE products SET stock=stock-? WHERE id=?",
                       (item["quantity"], item["product_id"]))
            total += item["quantity"] * row["price"]
        db.execute("UPDATE orders SET total=? WHERE id=?", (round(total,2), oid))
        db.commit()
        return jsonify({"id": oid, "total": total, "message": "Order created"})
    except Exception as e:
        db.rollback()
        return jsonify({"error": str(e)}), 500


# ── CUSTOMERS ─────────────────────────
@app.route("/api/customers")
def customers():
    search = request.args.get("search","")
    # CTE: customer stats with window function for rank
    rows = query_db("""
        WITH customer_stats AS (
            SELECT
                c.id, c.name, c.email, c.city, c.tier, c.created_at,
                COUNT(o.id)                      AS order_count,
                COALESCE(ROUND(SUM(o.total),2),0) AS lifetime_value,
                COALESCE(ROUND(AVG(o.total),2),0) AS avg_order
            FROM customers c
            LEFT JOIN orders o ON o.customer_id = c.id AND o.status != 'Cancelled'
            WHERE c.name LIKE ? OR c.email LIKE ?
            GROUP BY c.id
        )
        SELECT *,
               RANK() OVER (ORDER BY lifetime_value DESC) AS revenue_rank
        FROM customer_stats
        ORDER BY lifetime_value DESC
    """, (f"%{search}%", f"%{search}%"))
    return jsonify([dict(r) for r in rows])


@app.route("/api/customers", methods=["POST"])
def add_customer():
    d = request.json
    cid = modify_db(
        "INSERT INTO customers(name,email,city,tier) VALUES(?,?,?,?)",
        (d["name"], d["email"], d.get("city",""), d.get("tier","Bronze"))
    )
    return jsonify({"id": cid, "message": "Customer added"})


# ── ANALYTICS ─────────────────────────
@app.route("/api/analytics")
def analytics():
    db = get_db()

    # Window function: running revenue total
    running = db.execute("""
        SELECT
            strftime('%Y-%m-%d', created_at) AS day,
            SUM(total) AS daily_rev,
            SUM(SUM(total)) OVER (ORDER BY strftime('%Y-%m-%d', created_at)) AS running_total
        FROM orders
        WHERE status != 'Cancelled'
        GROUP BY day
        ORDER BY day DESC
        LIMIT 30
    """).fetchall()

    # CTE: top customers by revenue with percentile
    top_customers = db.execute("""
        WITH ranked AS (
            SELECT
                c.name, c.tier,
                ROUND(SUM(o.total),2) AS spent,
                COUNT(o.id)           AS orders,
                NTILE(4) OVER (ORDER BY SUM(o.total)) AS quartile
            FROM customers c
            JOIN orders o ON o.customer_id = c.id AND o.status='Delivered'
            GROUP BY c.id
        )
        SELECT * FROM ranked ORDER BY spent DESC LIMIT 10
    """).fetchall()

    # Product ranking with DENSE_RANK window function
    product_rank = db.execute("""
        SELECT
            p.name,
            cat.name AS category,
            COALESCE(SUM(oi.quantity * oi.unit_price),0) AS revenue,
            DENSE_RANK() OVER (PARTITION BY cat.name ORDER BY
                COALESCE(SUM(oi.quantity * oi.unit_price),0) DESC
            ) AS category_rank
        FROM products p
        LEFT JOIN categories cat ON cat.id = p.category_id
        LEFT JOIN order_items oi ON oi.product_id = p.id
        GROUP BY p.id
        ORDER BY revenue DESC
        LIMIT 15
    """).fetchall()

    # Cohort: orders per weekday
    weekday = db.execute("""
        SELECT
            CASE CAST(strftime('%w', created_at) AS INT)
                WHEN 0 THEN 'Sun' WHEN 1 THEN 'Mon' WHEN 2 THEN 'Tue'
                WHEN 3 THEN 'Wed' WHEN 4 THEN 'Thu' WHEN 5 THEN 'Fri'
                ELSE 'Sat' END AS day_name,
            COUNT(*) AS orders,
            ROUND(AVG(total),2) AS avg_total
        FROM orders
        GROUP BY strftime('%w', created_at)
        ORDER BY CAST(strftime('%w', created_at) AS INT)
    """).fetchall()

    # Audit log
    logs = db.execute("""
        SELECT event, detail, logged_at FROM audit_log
        ORDER BY logged_at DESC LIMIT 20
    """).fetchall()

    return jsonify({
        "running": [dict(r) for r in running],
        "top_customers": [dict(r) for r in top_customers],
        "product_rank": [dict(r) for r in product_rank],
        "weekday": [dict(r) for r in weekday],
        "logs": [dict(r) for r in logs],
    })


# ── CATEGORIES & MISC ─────────────────
@app.route("/api/categories")
def categories():
    rows = query_db("SELECT * FROM categories ORDER BY name")
    return jsonify([dict(r) for r in rows])


@app.route("/api/sql", methods=["POST"])
def run_sql():
    """Custom SQL query runner — demonstrates raw SQL power"""
    sql = request.json.get("sql","").strip()
    if not sql:
        return jsonify({"error": "No SQL provided"}), 400
    forbidden = ["DROP","DELETE","UPDATE","INSERT","ALTER","CREATE","ATTACH"]
    if any(kw in sql.upper() for kw in forbidden):
        return jsonify({"error": "Only SELECT queries allowed in explorer"}), 403
    try:
        rows = query_db(sql)
        if not rows:
            return jsonify({"columns": [], "rows": [], "count": 0})
        cols = list(rows[0].keys())
        data = [list(r) for r in rows]
        return jsonify({"columns": cols, "rows": data, "count": len(data)})
    except Exception as e:
        return jsonify({"error": str(e)}), 400


if __name__ == "__main__":
    init_db()
    app.run(debug=True, port=5000)

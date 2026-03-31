-- Database setup and sample data for AI Data Analyst
-- Run this script to create tables and populate with sample data

-- Create cafes table
CREATE TABLE IF NOT EXISTS cafes (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    location VARCHAR(255) NOT NULL,
    manager_name VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create vendors table
CREATE TABLE IF NOT EXISTS vendors (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    category VARCHAR(100) NOT NULL,
    contact_email VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create orders table
CREATE TABLE IF NOT EXISTS orders (
    id SERIAL PRIMARY KEY,
    cafe_id INTEGER NOT NULL REFERENCES cafes(id),
    vendor_id INTEGER NOT NULL REFERENCES vendors(id),
    order_date TIMESTAMP NOT NULL,
    total_amount DECIMAL(10, 2) NOT NULL,
    status VARCHAR(50) NOT NULL,
    items JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insert sample cafes
INSERT INTO cafes (name, location, manager_name, created_at) VALUES
('Downtown Coffee House', '123 Main St, Downtown', 'Sarah Johnson', '2023-01-15 08:00:00'),
('Riverside Café', '456 River Rd, Riverside', 'Michael Chen', '2023-02-20 09:30:00'),
('Central Perk', '789 Central Ave, Midtown', 'Emily Davis', '2023-03-10 10:00:00'),
('Beans & Brew', '321 Oak St, Uptown', 'David Wilson', '2023-04-05 11:00:00'),
('Morning Glory Café', '654 Pine St, Eastside', 'Lisa Anderson', '2023-05-12 08:30:00'),
('The Daily Grind', '987 Elm St, Westside', 'Robert Martinez', '2023-06-18 09:00:00'),
('Café Luna', '147 Maple Ave, Northside', 'Jennifer Brown', '2023-07-22 10:30:00'),
('Espresso Express', '258 Cedar Blvd, Southside', 'James Taylor', '2023-08-14 11:30:00')
ON CONFLICT DO NOTHING;

-- Insert sample vendors
INSERT INTO vendors (name, category, contact_email, created_at) VALUES
('Premium Coffee Co.', 'Coffee Beans', 'sales@premiumcoffee.com', '2023-01-01 00:00:00'),
('Fresh Pastries Ltd.', 'Bakery', 'orders@freshpastries.com', '2023-01-05 00:00:00'),
('Organic Tea House', 'Tea', 'info@organictea.com', '2023-01-10 00:00:00'),
('Sweet Treats Inc.', 'Desserts', 'contact@sweettreats.com', '2023-01-15 00:00:00'),
('Dairy Delights', 'Dairy Products', 'sales@dairydelights.com', '2023-01-20 00:00:00'),
('Fresh Fruits Co.', 'Fruits', 'orders@freshfruits.com', '2023-02-01 00:00:00'),
('Gourmet Sandwiches', 'Food', 'info@gourmetsandwiches.com', '2023-02-05 00:00:00'),
('Artisan Breads', 'Bakery', 'contact@artisanbreads.com', '2023-02-10 00:00:00')
ON CONFLICT DO NOTHING;

-- Insert sample orders (last 3 months of data)
INSERT INTO orders (cafe_id, vendor_id, order_date, total_amount, status, items) VALUES
-- January 2024 orders
(1, 1, '2024-01-05 09:00:00', 1250.50, 'completed', '{"coffee_beans_kg": 25, "price_per_kg": 50.02}'),
(1, 2, '2024-01-08 10:30:00', 450.75, 'completed', '{"croissants": 50, "muffins": 30, "price_per_item": 5.625}'),
(2, 1, '2024-01-10 08:15:00', 980.25, 'completed', '{"coffee_beans_kg": 20, "price_per_kg": 49.01}'),
(2, 3, '2024-01-12 11:00:00', 320.00, 'completed', '{"tea_packets": 80, "price_per_packet": 4.00}'),
(3, 1, '2024-01-15 09:45:00', 1500.00, 'completed', '{"coffee_beans_kg": 30, "price_per_kg": 50.00}'),
(3, 4, '2024-01-18 10:00:00', 675.50, 'completed', '{"cakes": 5, "cookies": 100, "price_per_cake": 75.00, "price_per_cookie": 3.005}'),
(4, 2, '2024-01-20 08:30:00', 525.25, 'completed', '{"bagels": 60, "donuts": 40, "price_per_item": 5.2525}'),
(4, 5, '2024-01-22 11:15:00', 890.00, 'completed', '{"milk_liters": 200, "cream_liters": 50, "price_per_liter": 3.56}'),
(5, 1, '2024-01-25 09:00:00', 1125.75, 'completed', '{"coffee_beans_kg": 22, "price_per_kg": 51.17}'),
(5, 6, '2024-01-28 10:45:00', 425.50, 'completed', '{"apples_kg": 50, "bananas_kg": 30, "price_per_kg": 5.32}'),

-- February 2024 orders
(1, 1, '2024-02-02 09:00:00', 1300.00, 'completed', '{"coffee_beans_kg": 26, "price_per_kg": 50.00}'),
(1, 2, '2024-02-05 10:30:00', 480.25, 'completed', '{"croissants": 55, "muffins": 30, "price_per_item": 5.65}'),
(2, 1, '2024-02-08 08:15:00', 1025.50, 'completed', '{"coffee_beans_kg": 20, "price_per_kg": 51.28}'),
(2, 3, '2024-02-10 11:00:00', 350.00, 'completed', '{"tea_packets": 85, "price_per_packet": 4.12}'),
(3, 1, '2024-02-12 09:45:00', 1550.75, 'completed', '{"coffee_beans_kg": 31, "price_per_kg": 50.02}'),
(3, 4, '2024-02-15 10:00:00', 720.50, 'completed', '{"cakes": 6, "cookies": 110, "price_per_cake": 75.00, "price_per_cookie": 2.50}'),
(4, 2, '2024-02-18 08:30:00', 550.00, 'completed', '{"bagels": 65, "donuts": 45, "price_per_item": 5.00}'),
(4, 5, '2024-02-20 11:15:00', 925.25, 'completed', '{"milk_liters": 210, "cream_liters": 55, "price_per_liter": 3.48}'),
(5, 1, '2024-02-22 09:00:00', 1180.50, 'completed', '{"coffee_beans_kg": 23, "price_per_kg": 51.33}'),
(6, 1, '2024-02-25 08:45:00', 1425.00, 'completed', '{"coffee_beans_kg": 28, "price_per_kg": 50.89}'),
(6, 7, '2024-02-28 10:30:00', 675.75, 'completed', '{"sandwiches": 90, "price_per_sandwich": 7.51}'),
(7, 1, '2024-02-28 11:00:00', 1100.25, 'completed', '{"coffee_beans_kg": 22, "price_per_kg": 50.01}'),

-- March 2024 orders
(1, 1, '2024-03-01 09:00:00', 1350.50, 'completed', '{"coffee_beans_kg": 27, "price_per_kg": 50.02}'),
(1, 2, '2024-03-04 10:30:00', 495.75, 'completed', '{"croissants": 60, "muffins": 35, "price_per_item": 5.22}'),
(2, 1, '2024-03-07 08:15:00', 1050.00, 'completed', '{"coffee_beans_kg": 21, "price_per_kg": 50.00}'),
(2, 3, '2024-03-10 11:00:00', 375.25, 'completed', '{"tea_packets": 90, "price_per_packet": 4.17}'),
(3, 1, '2024-03-12 09:45:00', 1600.00, 'completed', '{"coffee_beans_kg": 32, "price_per_kg": 50.00}'),
(3, 4, '2024-03-15 10:00:00', 750.50, 'completed', '{"cakes": 7, "cookies": 120, "price_per_cake": 75.00, "price_per_cookie": 1.88}'),
(4, 2, '2024-03-18 08:30:00', 575.25, 'completed', '{"bagels": 70, "donuts": 50, "price_per_item": 4.79}'),
(4, 5, '2024-03-20 11:15:00', 950.00, 'completed', '{"milk_liters": 220, "cream_liters": 60, "price_per_liter": 3.39}'),
(5, 1, '2024-03-22 09:00:00', 1200.75, 'completed', '{"coffee_beans_kg": 24, "price_per_kg": 50.03}'),
(5, 6, '2024-03-25 10:45:00', 450.50, 'completed', '{"apples_kg": 55, "bananas_kg": 35, "price_per_kg": 5.01}'),
(6, 1, '2024-03-27 08:45:00', 1475.25, 'completed', '{"coffee_beans_kg": 29, "price_per_kg": 50.87}'),
(6, 7, '2024-03-28 10:30:00', 700.00, 'completed', '{"sandwiches": 95, "price_per_sandwich": 7.37}'),
(7, 1, '2024-03-29 11:00:00', 1150.50, 'completed', '{"coffee_beans_kg": 23, "price_per_kg": 50.02}'),
(7, 8, '2024-03-30 09:30:00', 425.75, 'completed', '{"bread_loaves": 85, "price_per_loaf": 5.01}'),
(8, 1, '2024-03-31 08:00:00', 1325.00, 'completed', '{"coffee_beans_kg": 26, "price_per_kg": 50.96}'),
(8, 3, '2024-03-31 10:00:00', 340.25, 'completed', '{"tea_packets": 75, "price_per_packet": 4.54}'),

-- Some pending/cancelled orders for variety
(1, 1, '2024-04-01 09:00:00', 1400.00, 'pending', '{"coffee_beans_kg": 28, "price_per_kg": 50.00}'),
(2, 2, '2024-04-02 10:00:00', 500.00, 'cancelled', '{"croissants": 50, "muffins": 40, "price_per_item": 5.56}'),
(3, 1, '2024-04-03 08:00:00', 1100.00, 'pending', '{"coffee_beans_kg": 22, "price_per_kg": 50.00}'),
(4, 4, '2024-04-04 11:00:00', 800.00, 'completed', '{"cakes": 8, "cookies": 130, "price_per_cake": 75.00, "price_per_cookie": 1.54}'),
(5, 1, '2024-04-05 09:00:00', 1250.00, 'completed', '{"coffee_beans_kg": 25, "price_per_kg": 50.00}')
ON CONFLICT DO NOTHING;

-- Create indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_orders_cafe_id ON orders(cafe_id);
CREATE INDEX IF NOT EXISTS idx_orders_vendor_id ON orders(vendor_id);
CREATE INDEX IF NOT EXISTS idx_orders_order_date ON orders(order_date);
CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(status);
CREATE INDEX IF NOT EXISTS idx_cafes_location ON cafes(location);
CREATE INDEX IF NOT EXISTS idx_vendors_category ON vendors(category);

-- Display summary
SELECT 'Database setup complete!' as message;
SELECT COUNT(*) as total_cafes FROM cafes;
SELECT COUNT(*) as total_vendors FROM vendors;
SELECT COUNT(*) as total_orders FROM orders;
SELECT 
    status,
    COUNT(*) as count,
    SUM(total_amount) as total_revenue
FROM orders
GROUP BY status;


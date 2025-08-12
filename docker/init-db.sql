-- Initialize property management database with sample data (quickstart example)

-- Create users table
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    phone VARCHAR(50),
    role VARCHAR(50) NOT NULL DEFAULT 'user',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create landlords table
CREATE TABLE landlords (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    properties_owned INTEGER DEFAULT 0,
    monthly_income DECIMAL(12, 2),
    tax_id VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create tenants table
CREATE TABLE tenants (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    lease_id UUID,
    monthly_rent DECIMAL(10, 2),
    move_in_date DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create properties table
CREATE TABLE properties (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    address VARCHAR(500) NOT NULL,
    owner_id UUID NOT NULL REFERENCES landlords(id) ON DELETE CASCADE,
    bedrooms INTEGER,
    bathrooms DECIMAL(3, 1),
    rent_amount DECIMAL(10, 2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create leases table
CREATE TABLE leases (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    property_id UUID NOT NULL REFERENCES properties(id) ON DELETE CASCADE,
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    landlord_id UUID NOT NULL REFERENCES landlords(id) ON DELETE CASCADE,
    lease_start DATE NOT NULL,
    lease_end DATE NOT NULL,
    monthly_rent DECIMAL(10, 2) NOT NULL,
    security_deposit DECIMAL(10, 2),
    status VARCHAR(50) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insert sample users
INSERT INTO users (name, email, phone, role) VALUES
('James Smith', 'james.smith@example.com', '+1-555-0101', 'landlord'),
('Sarah Johnson', 'sarah.johnson@example.com', '+1-555-0102', 'landlord'),
('John Doe', 'john.doe@example.com', '+1-555-0201', 'tenant'),
('Emily Davis', 'emily.davis@example.com', '+1-555-0202', 'tenant'),
('Michael Brown', 'michael.brown@example.com', '+1-555-0203', 'tenant'),
('Jessica Wilson', 'jessica.wilson@example.com', '+1-555-0301', 'admin');

-- Insert landlords
INSERT INTO landlords (user_id, properties_owned, monthly_income, tax_id)
SELECT 
    u.id,
    CASE u.name 
        WHEN 'James Smith' THEN 3
        WHEN 'Sarah Johnson' THEN 2
    END,
    CASE u.name 
        WHEN 'James Smith' THEN 4500.00
        WHEN 'Sarah Johnson' THEN 3200.00
    END,
    CASE u.name 
        WHEN 'James Smith' THEN 'TAX-001-JS'
        WHEN 'Sarah Johnson' THEN 'TAX-002-SJ'
    END
FROM users u 
WHERE u.role = 'landlord';

-- Insert tenants
INSERT INTO tenants (user_id, monthly_rent, move_in_date)
SELECT 
    u.id,
    CASE u.name 
        WHEN 'John Doe' THEN 1500.00
        WHEN 'Emily Davis' THEN 1200.00
        WHEN 'Michael Brown' THEN 1800.00
    END,
    CASE u.name 
        WHEN 'John Doe' THEN '2023-06-01'::date
        WHEN 'Emily Davis' THEN '2023-08-15'::date
        WHEN 'Michael Brown' THEN '2023-09-01'::date
    END
FROM users u 
WHERE u.role = 'tenant';

-- Insert properties
INSERT INTO properties (address, owner_id, bedrooms, bathrooms, rent_amount)
SELECT 
    addr.address,
    l.id,
    addr.bedrooms,
    addr.bathrooms,
    addr.rent
FROM landlords l
JOIN users u ON l.user_id = u.id
CROSS JOIN (
    SELECT '123 Main Street, Downtown' as address, 2 as bedrooms, 1.5 as bathrooms, 1500.00 as rent
    UNION ALL SELECT '456 Oak Avenue, Midtown', 1, 1.0, 1200.00
    UNION ALL SELECT '789 Pine Road, Uptown', 3, 2.0, 1800.00
    UNION ALL SELECT '321 Elm Street, Downtown', 2, 2.0, 1600.00
    UNION ALL SELECT '654 Maple Drive, Suburbs', 4, 3.0, 2200.00
) addr
WHERE 
    (u.name = 'James Smith' AND addr.address IN ('123 Main Street, Downtown', '456 Oak Avenue, Midtown', '789 Pine Road, Uptown'))
    OR (u.name = 'Sarah Johnson' AND addr.address IN ('321 Elm Street, Downtown', '654 Maple Drive, Suburbs'));

-- Insert leases
INSERT INTO leases (property_id, tenant_id, landlord_id, lease_start, lease_end, monthly_rent, security_deposit)
SELECT 
    p.id,
    t.id,
    l.id,
    lease_data.start_date,
    lease_data.end_date,
    p.rent_amount,
    p.rent_amount * 1.5
FROM properties p
JOIN landlords l ON p.owner_id = l.id
JOIN users lu ON l.user_id = lu.id
CROSS JOIN tenants t
JOIN users tu ON t.user_id = tu.id
CROSS JOIN (
    SELECT '2023-06-01'::date as start_date, '2024-05-31'::date as end_date, 'John Doe' as tenant_name, '123 Main Street, Downtown' as property_addr
    UNION ALL SELECT '2023-08-15'::date, '2024-08-14'::date, 'Emily Davis', '456 Oak Avenue, Midtown'
    UNION ALL SELECT '2023-09-01'::date, '2024-08-31'::date, 'Michael Brown', '789 Pine Road, Uptown'
) lease_data
WHERE tu.name = lease_data.tenant_name 
AND p.address = lease_data.property_addr;

-- Update tenant lease_id references
UPDATE tenants 
SET lease_id = l.id
FROM leases l
WHERE tenants.id = l.tenant_id;

-- Create indexes for better performance
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_name ON users(name);
CREATE INDEX idx_landlords_user_id ON landlords(user_id);
CREATE INDEX idx_tenants_user_id ON tenants(user_id);
CREATE INDEX idx_properties_owner_id ON properties(owner_id);
CREATE INDEX idx_properties_address ON properties(address);
CREATE INDEX idx_leases_property_id ON leases(property_id);
CREATE INDEX idx_leases_tenant_id ON leases(tenant_id);

-- Grant permissions
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO fantastic_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO fantastic_user; 
ALTER TABLE garment_types
    ADD COLUMN IF NOT EXISTS category VARCHAR(50) NOT NULL DEFAULT 'CLOTHING' AFTER is_frequent,
    ADD COLUMN IF NOT EXISTS active TINYINT(1) NOT NULL DEFAULT 1 AFTER category,
    ADD COLUMN IF NOT EXISTS default_unit_type VARCHAR(20) NOT NULL DEFAULT 'UNIT' AFTER active,
    ADD COLUMN IF NOT EXISTS default_unit_price DECIMAL(10,2) NULL AFTER default_unit_type,
    ADD COLUMN IF NOT EXISTS display_order INT NULL AFTER default_unit_price,
    ADD COLUMN IF NOT EXISTS created_at DATETIME NULL DEFAULT current_timestamp() AFTER display_order,
    ADD COLUMN IF NOT EXISTS updated_at DATETIME NULL DEFAULT current_timestamp() ON UPDATE current_timestamp() AFTER created_at;

ALTER TABLE laundry_services
    ADD COLUMN IF NOT EXISTS weight_lb DECIMAL(10,2) NULL AFTER transaction_id,
    ADD COLUMN IF NOT EXISTS notes TEXT NULL AFTER weight_lb;

CREATE TABLE IF NOT EXISTS service_extra_types (
    id INT NOT NULL AUTO_INCREMENT,
    code VARCHAR(50) NOT NULL,
    name VARCHAR(100) NOT NULL,
    unit_label VARCHAR(30) NOT NULL DEFAULT 'unidad',
    default_unit_price DECIMAL(10,2) NULL,
    active TINYINT(1) NOT NULL DEFAULT 1,
    display_order INT NULL,
    created_at DATETIME NULL DEFAULT current_timestamp(),
    updated_at DATETIME NULL DEFAULT current_timestamp() ON UPDATE current_timestamp(),
    PRIMARY KEY (id),
    UNIQUE KEY uq_service_extra_types_code (code),
    UNIQUE KEY uq_service_extra_types_name (name)
);

CREATE TABLE IF NOT EXISTS laundry_service_items (
    id INT NOT NULL AUTO_INCREMENT,
    laundry_service_id INT NOT NULL,
    garment_type_id INT NOT NULL,
    quantity DECIMAL(10,2) NOT NULL DEFAULT 1.00,
    unit_type VARCHAR(20) NOT NULL DEFAULT 'UNIT',
    unit_price DECIMAL(10,2) NULL,
    subtotal DECIMAL(10,2) NULL,
    notes TEXT NULL,
    created_at DATETIME NULL DEFAULT current_timestamp(),
    updated_at DATETIME NULL DEFAULT current_timestamp() ON UPDATE current_timestamp(),
    PRIMARY KEY (id),
    KEY idx_laundry_service_items_service (laundry_service_id),
    KEY idx_laundry_service_items_garment (garment_type_id),
    CONSTRAINT fk_laundry_service_items_service
        FOREIGN KEY (laundry_service_id) REFERENCES laundry_services (id)
        ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_laundry_service_items_garment
        FOREIGN KEY (garment_type_id) REFERENCES garment_types (id)
        ON UPDATE CASCADE
);

CREATE TABLE IF NOT EXISTS laundry_service_extras (
    id INT NOT NULL AUTO_INCREMENT,
    laundry_service_id INT NOT NULL,
    service_extra_type_id INT NOT NULL,
    quantity DECIMAL(10,2) NOT NULL DEFAULT 1.00,
    unit_price DECIMAL(10,2) NULL,
    subtotal DECIMAL(10,2) NULL,
    notes TEXT NULL,
    created_at DATETIME NULL DEFAULT current_timestamp(),
    updated_at DATETIME NULL DEFAULT current_timestamp() ON UPDATE current_timestamp(),
    PRIMARY KEY (id),
    KEY idx_laundry_service_extras_service (laundry_service_id),
    KEY idx_laundry_service_extras_type (service_extra_type_id),
    CONSTRAINT fk_laundry_service_extras_service
        FOREIGN KEY (laundry_service_id) REFERENCES laundry_services (id)
        ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_laundry_service_extras_type
        FOREIGN KEY (service_extra_type_id) REFERENCES service_extra_types (id)
        ON UPDATE CASCADE
);

UPDATE garment_types
SET category = 'CLOTHING',
    active = 1,
    default_unit_type = 'UNIT'
WHERE name IN (
    'Camisas',
    'Pantalones',
    'Faldas',
    'Chores',
    'Ropa Interior',
    'Boxers',
    'Brazieres',
    'Calcetines (Impares)',
    'Sueters',
    'Vestidos'
);

UPDATE garment_types
SET category = 'CLOTHING',
    active = 1,
    default_unit_type = 'PAIR'
WHERE name IN ('Calcetines (Pares)');

UPDATE garment_types
SET category = 'BEDDING',
    active = 1,
    default_unit_type = 'UNIT'
WHERE name IN (
    'Toallas',
    'Sobrefundas',
    'Fundas Almohada',
    'Sabanas',
    'Edredones',
    'Forros Elásticos'
);

INSERT INTO garment_types (name, icon, is_frequent, category, active, default_unit_type, default_unit_price, display_order)
SELECT 'Edredon Grande', NULL, 1, 'BEDDING', 1, 'UNIT', 5.00, 100
WHERE NOT EXISTS (SELECT 1 FROM garment_types WHERE name = 'Edredon Grande');

INSERT INTO garment_types (name, icon, is_frequent, category, active, default_unit_type, default_unit_price, display_order)
SELECT 'Edredon Mediano', NULL, 1, 'BEDDING', 1, 'UNIT', 3.00, 101
WHERE NOT EXISTS (SELECT 1 FROM garment_types WHERE name = 'Edredon Mediano');

INSERT INTO garment_types (name, icon, is_frequent, category, active, default_unit_type, default_unit_price, display_order)
SELECT 'Cobija Gruesa', NULL, 1, 'BEDDING', 1, 'UNIT', 2.00, 102
WHERE NOT EXISTS (SELECT 1 FROM garment_types WHERE name = 'Cobija Gruesa');

INSERT INTO garment_types (name, icon, is_frequent, category, active, default_unit_type, default_unit_price, display_order)
SELECT 'Cobija Delgada', NULL, 1, 'BEDDING', 1, 'UNIT', 1.00, 103
WHERE NOT EXISTS (SELECT 1 FROM garment_types WHERE name = 'Cobija Delgada');

INSERT INTO garment_types (name, icon, is_frequent, category, active, default_unit_type, default_unit_price, display_order)
SELECT 'Zapatos', NULL, 1, 'FOOTWEAR', 1, 'UNIT', NULL, 104
WHERE NOT EXISTS (SELECT 1 FROM garment_types WHERE name = 'Zapatos');

INSERT INTO garment_types (name, icon, is_frequent, category, active, default_unit_type, default_unit_price, display_order)
SELECT 'Peluches', NULL, 1, 'PLUSH', 1, 'UNIT', NULL, 105
WHERE NOT EXISTS (SELECT 1 FROM garment_types WHERE name = 'Peluches');

INSERT INTO garment_types (name, icon, is_frequent, category, active, default_unit_type, default_unit_price, display_order)
SELECT 'Alfombras', NULL, 1, 'RUG', 1, 'UNIT', NULL, 106
WHERE NOT EXISTS (SELECT 1 FROM garment_types WHERE name = 'Alfombras');

INSERT INTO service_extra_types (code, name, unit_label, default_unit_price, active, display_order)
SELECT 'IRONING', 'Planchado', 'prenda', NULL, 1, 1
WHERE NOT EXISTS (SELECT 1 FROM service_extra_types WHERE code = 'IRONING');

INSERT INTO service_extra_types (code, name, unit_label, default_unit_price, active, display_order)
SELECT 'SCENT_BEADS', 'Perlitas de olor', 'unidad', NULL, 1, 2
WHERE NOT EXISTS (SELECT 1 FROM service_extra_types WHERE code = 'SCENT_BEADS');

INSERT INTO service_extra_types (code, name, unit_label, default_unit_price, active, display_order)
SELECT 'SOAK', 'Remojo', 'aplicacion', NULL, 1, 3
WHERE NOT EXISTS (SELECT 1 FROM service_extra_types WHERE code = 'SOAK');

INSERT INTO service_extra_types (code, name, unit_label, default_unit_price, active, display_order)
SELECT 'VINEGAR', 'Vinagre', 'unidad', NULL, 1, 4
WHERE NOT EXISTS (SELECT 1 FROM service_extra_types WHERE code = 'VINEGAR');

INSERT INTO service_extra_types (code, name, unit_label, default_unit_price, active, display_order)
SELECT 'SALT', 'Sal', 'unidad', NULL, 1, 5
WHERE NOT EXISTS (SELECT 1 FROM service_extra_types WHERE code = 'SALT');

INSERT INTO service_extra_types (code, name, unit_label, default_unit_price, active, display_order)
SELECT 'VANISH', 'Vanish', 'unidad', NULL, 1, 6
WHERE NOT EXISTS (SELECT 1 FROM service_extra_types WHERE code = 'VANISH');

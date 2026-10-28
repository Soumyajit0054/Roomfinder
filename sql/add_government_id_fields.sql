USE roomfinder;

ALTER TABLE users
    ADD COLUMN country VARCHAR(100) NOT NULL DEFAULT 'India'
        AFTER phone,
    ADD COLUMN government_id_file VARCHAR(255) NOT NULL DEFAULT ''
        AFTER country,
    ADD COLUMN government_id_verified TINYINT(1) NOT NULL DEFAULT 0
        AFTER government_id_file,
    ADD COLUMN government_id_status ENUM(
        'pending',
        'auto_verified',
        'rejected'
    ) NOT NULL DEFAULT 'pending'
        AFTER government_id_verified,
    ADD COLUMN government_id_validation_method VARCHAR(30)
        AFTER government_id_status,
    ADD COLUMN government_id_validation_notes TEXT
        AFTER government_id_validation_method;

USE roomfinder;

ALTER TABLE users
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

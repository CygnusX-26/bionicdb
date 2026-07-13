PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS libs (
    id INTEGER PRIMARY KEY,
    build_id TEXT NOT NULL UNIQUE,
    sha256 TEXT NOT NULL UNIQUE,
    file_path TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS releases (
    id INTEGER PRIMARY KEY,
    lib_id INTEGER NOT NULL REFERENCES libs(id) ON DELETE CASCADE,
    device TEXT NOT NULL,
    firmware_build_id TEXT NOT NULL,
    android_version TEXT NOT NULL,
    android_api INTEGER NOT NULL,
    security_patch TEXT NOT NULL,
    UNIQUE (lib_id, device, firmware_build_id)
);

CREATE INDEX IF NOT EXISTS releases_device_idx ON releases(device);
CREATE INDEX IF NOT EXISTS releases_firmware_build_id_idx ON releases(firmware_build_id);
CREATE INDEX IF NOT EXISTS releases_android_api_idx ON releases(android_api);
CREATE INDEX IF NOT EXISTS releases_security_patch_idx ON releases(security_patch);

CREATE TABLE IF NOT EXISTS symbols (
    lib_id INTEGER NOT NULL REFERENCES libs(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    offset INTEGER NOT NULL CHECK (offset >= 0),
    PRIMARY KEY (lib_id, name, offset)
);

CREATE INDEX IF NOT EXISTS symbols_name_idx ON symbols(name);
CREATE INDEX IF NOT EXISTS symbols_offset_idx ON symbols(offset);

CREATE VIEW IF NOT EXISTS symbols_with_build_id AS
SELECT
    symbols.name,
    symbols.offset,
    libs.build_id
FROM symbols
JOIN libs ON libs.id = symbols.lib_id;

CREATE VIEW IF NOT EXISTS lib_releases AS
SELECT
    libs.build_id,
    libs.sha256,
    libs.file_path,
    releases.device,
    releases.firmware_build_id,
    releases.android_version,
    releases.android_api,
    releases.security_patch
FROM libs
JOIN releases ON releases.lib_id = libs.id;

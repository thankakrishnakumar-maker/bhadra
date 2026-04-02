import os
import json
import secrets
from datetime import datetime, timedelta, date
from functools import wraps
from io import BytesIO
import base64

from flask import (Flask, render_template_string, request, redirect, url_for,
                   flash, session, jsonify, send_file, make_response)
from flask_sqlalchemy import SQLAlchemy
from flask_login import (LoginManager, UserMixin, login_user, logout_user,
                         login_required, current_user)
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename


-- ============================================================
-- 1. ASSET CATEGORIES TABLE
-- ============================================================
CREATE TABLE IF NOT EXISTS asset_category (
    id BIGSERIAL PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    code_prefix VARCHAR(3) NOT NULL,
    description TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Enable RLS
ALTER TABLE asset_category ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Allow all for authenticated" ON asset_category FOR ALL USING (true) WITH CHECK (true);

-- ============================================================
-- 2. ASSETS TABLE
-- ============================================================
CREATE TABLE IF NOT EXISTS asset (
    id BIGSERIAL PRIMARY KEY,
    asset_code VARCHAR(20) NOT NULL UNIQUE,
    name TEXT NOT NULL,
    description TEXT,
    category_id BIGINT REFERENCES asset_category(id),
    location TEXT,
    condition VARCHAR(20) DEFAULT 'New',
    quantity INTEGER DEFAULT 1,
    purchase_value NUMERIC(12,2) DEFAULT 0,
    purchase_date DATE,
    supplier_donor TEXT,
    warranty_expiry DATE,
    serial_number TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_by BIGINT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for fast lookups
CREATE INDEX IF NOT EXISTS idx_asset_code ON asset(asset_code);
CREATE INDEX IF NOT EXISTS idx_asset_category ON asset(category_id);
CREATE INDEX IF NOT EXISTS idx_asset_location ON asset(location);
CREATE INDEX IF NOT EXISTS idx_asset_condition ON asset(condition);
CREATE INDEX IF NOT EXISTS idx_asset_active ON asset(is_active);

-- Enable RLS
ALTER TABLE asset ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Allow all for authenticated" ON asset FOR ALL USING (true) WITH CHECK (true);

-- ============================================================
-- 3. ASSET AUDIT LOG TABLE
-- ============================================================
CREATE TABLE IF NOT EXISTS asset_audit_log (
    id BIGSERIAL PRIMARY KEY,
    asset_id BIGINT REFERENCES asset(id) ON DELETE CASCADE,
    action VARCHAR(30) NOT NULL,
    details TEXT,
    performed_by BIGINT,
    performed_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_audit_asset ON asset_audit_log(asset_id);
CREATE INDEX IF NOT EXISTS idx_audit_date ON asset_audit_log(performed_at);

-- Enable RLS
ALTER TABLE asset_audit_log ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Allow all for authenticated" ON asset_audit_log FOR ALL USING (true) WITH CHECK (true);

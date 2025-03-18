-- Start a transaction
ROLLBACK;
BEGIN;

-- 1. Create Extensions and Roles
CREATE EXTENSION IF NOT EXISTS pgcrypto; -- For password hashing
CREATE EXTENSION IF NOT EXISTS postgis;  -- For geographic data

DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'user') THEN
        CREATE ROLE "user";
    END IF;
END $$;

DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'admin') THEN
        CREATE ROLE "admin";
    END IF;
END $$;

-- 2. Drop Existing Tables
DROP TABLE IF EXISTS real_time_status CASCADE;
DROP TABLE IF EXISTS transactions CASCADE;
DROP TABLE IF EXISTS trips CASCADE;
DROP TABLE IF EXISTS peak_times CASCADE;
DROP TABLE IF EXISTS transfer_times CASCADE;
DROP TABLE IF EXISTS trains CASCADE;
DROP TABLE IF EXISTS routes CASCADE;
DROP TABLE IF EXISTS holidays CASCADE;
DROP TABLE IF EXISTS users CASCADE;
DROP TABLE IF EXISTS stations CASCADE;
DROP TABLE IF EXISTS lines CASCADE;
DROP TABLE IF EXISTS schedule_templates CASCADE;
DROP TABLE IF EXISTS service_patterns CASCADE;
DROP TABLE IF EXISTS service_pattern_details CASCADE;
DROP TABLE IF EXISTS frequency_rules CASCADE;
DROP TABLE IF EXISTS annual_calendar CASCADE;
DROP TABLE IF EXISTS schedule_adjustments CASCADE;
DROP TABLE IF EXISTS schedules CASCADE;

-- 3. Create Tables
CREATE TABLE users (
    user_id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(20) DEFAULT 'user',
    balance DECIMAL(10, 2) DEFAULT 0.00,
    card_type VARCHAR(50),
    billing_address TEXT,
    notification_preferences JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP
);

CREATE TABLE stations (
    station_id VARCHAR(10) PRIMARY KEY,
    station_name VARCHAR(100) UNIQUE NOT NULL,
    location GEOGRAPHY(POINT),
    station_type TEXT[]
);

CREATE TABLE lines (
    line_id SERIAL PRIMARY KEY,
    line_name VARCHAR(50) UNIQUE NOT NULL,
    start_time TIME,
    end_time TIME
);

CREATE TABLE routes (
    route_id SERIAL PRIMARY KEY,
    line_id INTEGER REFERENCES lines(line_id),
    from_station_id VARCHAR(10) REFERENCES stations(station_id),
    to_station_id VARCHAR(10) REFERENCES stations(station_id),
    travel_time INTEGER
);

CREATE TABLE transfer_times (
    station_id VARCHAR(10) REFERENCES stations(station_id),
    from_line_id INTEGER REFERENCES lines(line_id),
    to_line_id INTEGER REFERENCES lines(line_id),
    transfer_time_peak INTEGER DEFAULT 2,
    transfer_time_offpeak INTEGER DEFAULT 1,
    PRIMARY KEY (station_id, from_line_id, to_line_id)
);

CREATE TABLE schedule_templates (
    template_id SERIAL PRIMARY KEY,
    template_name VARCHAR(50) NOT NULL,
    description TEXT
);

CREATE TABLE service_patterns (
    pattern_id SERIAL PRIMARY KEY,
    pattern_name VARCHAR(50) NOT NULL,
    description TEXT,
    line_id INTEGER REFERENCES lines(line_id)
);

CREATE TABLE service_pattern_details (
    pattern_detail_id SERIAL PRIMARY KEY,
    pattern_id INTEGER REFERENCES service_patterns(pattern_id),
    station_sequence INTEGER,
    station_id VARCHAR(10) REFERENCES stations(station_id),
    dwell_time INTEGER DEFAULT 30,
    UNIQUE(pattern_id, station_sequence)
);

CREATE TABLE frequency_rules (
    rule_id SERIAL PRIMARY KEY,
    template_id INTEGER REFERENCES schedule_templates(template_id),
    line_id INTEGER REFERENCES lines(line_id),
    pattern_id INTEGER REFERENCES service_patterns(pattern_id),
    start_time TIME,
    end_time TIME,
    headway_minutes INTEGER,
    min_trains INTEGER,
    max_trains INTEGER
);

CREATE TABLE annual_calendar (
    date_id DATE PRIMARY KEY,
    template_id INTEGER REFERENCES schedule_templates(template_id)
);

CREATE TABLE schedule_adjustments (
    adjustment_id SERIAL PRIMARY KEY,
    date_id DATE REFERENCES annual_calendar(date_id),
    line_id INTEGER REFERENCES lines(line_id),
    pattern_id INTEGER REFERENCES service_patterns(pattern_id),
    start_time TIME,
    end_time TIME,
    headway_minutes INTEGER,
    notes TEXT
);

CREATE TABLE trains (
    train_id VARCHAR(50) PRIMARY KEY,
    line_id INTEGER REFERENCES lines(line_id),
    current_route_id INTEGER REFERENCES routes(route_id),
    current_station_id VARCHAR(10) REFERENCES stations(station_id),
    status VARCHAR(20) DEFAULT 'at_station',
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    next_station_id VARCHAR(10) REFERENCES stations(station_id),
    schedule_adherence INTEGER DEFAULT 0
);

CREATE TABLE holidays (
    holiday_date DATE PRIMARY KEY
);

CREATE TABLE schedules (
    schedule_id SERIAL PRIMARY KEY,
    line_id INTEGER REFERENCES lines(line_id),
    station_id VARCHAR(10) REFERENCES stations(station_id),
    departure_time TIME,
    day_type VARCHAR(20),
    next_station_id VARCHAR(10) REFERENCES stations(station_id),
    UNIQUE (line_id, station_id, departure_time, day_type)
);

CREATE TABLE trips (
    trip_id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(user_id),
    start_station_id VARCHAR(10) REFERENCES stations(station_id),
    end_station_id VARCHAR(10) REFERENCES stations(station_id),
    start_time TIMESTAMP,
    end_time TIMESTAMP,
    fare DECIMAL(10, 2),
    stations_visited TEXT[],
    description TEXT
);

CREATE TABLE transactions (
    transaction_id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(user_id),
    station_id VARCHAR(10) REFERENCES stations(station_id),
    amount DECIMAL(10, 2),
    payment_method VARCHAR(50),
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(20)
);

CREATE TABLE real_time_status (
    status_id SERIAL PRIMARY KEY,
    train_id VARCHAR(50) REFERENCES trains(train_id),
    line_id INTEGER REFERENCES lines(line_id),
    route_id INTEGER REFERENCES routes(route_id),
    current_station_id VARCHAR(10) REFERENCES stations(station_id),
    status VARCHAR(20),
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 4. Grant Privileges
GRANT USAGE ON SCHEMA public TO "user", "admin";
GRANT SELECT ON ALL TABLES IN SCHEMA public TO "user", "admin";
GRANT INSERT, UPDATE, DELETE ON TABLE users, trips, transactions TO "user";
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO "admin";
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO "admin";
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO "user";

-- 5. Add Indexes
CREATE INDEX IF NOT EXISTS idx_schedules_line_station ON schedules(line_id, station_id, next_station_id);
CREATE INDEX IF NOT EXISTS idx_trips_user_start ON trips(user_id, start_time);
CREATE INDEX IF NOT EXISTS idx_annual_calendar_template ON annual_calendar(template_id);
CREATE INDEX IF NOT EXISTS idx_frequency_rules_template_line ON frequency_rules(template_id, line_id);
CREATE INDEX IF NOT EXISTS idx_schedule_adjustments_date_line ON schedule_adjustments(date_id, line_id);

-- 6. Insert Data
-- Insert lines
INSERT INTO lines (line_name, start_time, end_time) VALUES
('Line 1', '06:00', '23:00'),
('Line 2', '06:00', '23:00'),
('Line 3A', '06:00', '23:00'),
('Line 3B', '06:00', '23:00'),
('Line 4', '06:00', '23:00'),
('Line 4B', '06:00', '23:00'),
('Line 4B1', '06:00', '23:00'),
('Line 5', '06:00', '23:00'),
('Line 6', '06:00', '23:00'),
('MR2', '06:00', '23:00'),
('MR3', '06:00', '23:00');

-- Insert stations
INSERT INTO stations (station_id, station_name, station_type) VALUES
('S101MD', 'Mien Dong', ARRAY['metro']),
('S102STAP', 'Suoi Tien Amusement Park', ARRAY['metro']),
('S103SHTP', 'Saigon Hi-tech Park', ARRAY['metro']),
('S104TD', 'Thu Duc', ARRAY['metro']),
('S105BT', 'Binh Thai', ARRAY['metro']),
('S106PL', 'Phuoc Long', ARRAY['metro']),
('S107RC', 'Rach Chiec', ARRAY['metro']),
('S108AP', 'Anphu', ARRAY['metro']),
('S109TD', 'Thao Dien', ARRAY['metro', 'monorail']),
('S110SB', 'Saigon Bridge', ARRAY['metro']),
('S111VT', 'Van Thanh', ARRAY['metro']),
('S112BS', 'Ba Son', ARRAY['metro']),
('S113OH', 'Opera House', ARRAY['metro']),
('S114BT', 'Ben Thanh', ARRAY['metro']),
('S201CC', 'Cu Chi', ARRAY['metro']),
('S202AS', 'An Suong', ARRAY['metro']),
('S203TTN', 'Tan Thoi Nhat', ARRAY['metro']),
('S204TB', 'Tan Binh', ARRAY['metro']),
('S205PVB', 'Pham Van Bach', ARRAY['metro']),
('S206BQ', 'Ba Queo', ARRAY['metro']),
('S207NHD', 'Nguyen Hong Dao', ARRAY['metro']),
('S208BH', 'Bay Hien', ARRAY['metro']),
('S209PVH', 'Pham Van Hai', ARRAY['metro']),
('S210LTR', 'Le Thi Rieng Park', ARRAY['metro']),
('S211HH', 'Hoa Hung', ARRAY['metro']),
('S212DC', 'Dan Chu', ARRAY['metro']),
('S213TD', 'Tao Dan', ARRAY['metro']),
('S214HMN', 'Ham Nghi', ARRAY['metro']),
('S215TTS', 'Thu Thiem Square', ARRAY['metro']),
('S216MCT', 'Mai Chi Tho', ARRAY['metro']),
('S217TN', 'Tran Nao', ARRAY['metro', 'monorail']),
('S218BK', 'Binh Khanh', ARRAY['metro']),
('S219TT', 'Thu Thiem', ARRAY['metro']),
('S301TK', 'Tan Kien', ARRAY['metro']),
('S302EBS', 'Eastern Bus Station', ARRAY['metro']),
('S303PLP', 'Phu Lam Park', ARRAY['metro']),
('S304PL', 'Phu Lam', ARRAY['metro']),
('S305CG', 'Cay Go', ARRAY['metro']),
('S306CL', 'Cho Lon', ARRAY['metro']),
('S307TKP', 'Thuan Kieu Plaza', ARRAY['metro']),
('S308UMP', 'University of Meds and Pharma', ARRAY['metro']),
('S309HBP', 'Hoa Binh Park', ARRAY['metro']),
('S310CH', 'Cong Hoa', ARRAY['metro']),
('S311TB', 'Thai Binh', ARRAY['metro']),
('S401TX', 'Thanh Xuan', ARRAY['metro']),
('S402NTG', 'Nga Tu Ga', ARRAY['metro']),
('S403ALB', 'An Loc Bridge', ARRAY['metro']),
('S404AN', 'An Nhon', ARRAY['metro']),
('S405NVL', 'Nguyen Van Luong', ARRAY['metro']),
('S406GV', 'Go Vap', ARRAY['metro', 'monorail']),
('S407175', '175 Hospital', ARRAY['metro']),
('S408GDP', 'Gia Dinh Park', ARRAY['metro']),
('S409PN', 'Phu Nhuan', ARRAY['metro']),
('S410KB', 'Kieu Bridge', ARRAY['metro']),
('S411LVTP', 'Le Van Tam Park', ARRAY['metro']),
('S511TL', 'Turtle Lake', ARRAY['metro']),
('S412OLB', 'Ong Lanh Bridge', ARRAY['metro']),
('S413Y', 'Yersin', ARRAY['metro']),
('S414KH', 'Khanh Hoa', ARRAY['metro']),
('S415TH', 'Tan Hung', ARRAY['metro']),
('S416NHT', 'Nguyen Huu Tho', ARRAY['metro']),
('S417NVL', 'Nguyen Van Linh', ARRAY['metro', 'monorail']),
('S418PK', 'Phuoc Kien', ARRAY['metro']),
('S419PHL', 'Pham Huu Lau', ARRAY['metro']),
('S420BC', 'Ba Chiem', ARRAY['metro']),
('S421LT', 'Long Thoi', ARRAY['metro']),
('S422HP', 'Hiep Phuoc', ARRAY['metro']),
('S423TSN', 'Tan Son Nhat', ARRAY['metro']),
('S424LCC', 'Lang Cha Ca', ARRAY['metro']),
('S425HVTP', 'Hoang Van Thu Park', ARRAY['metro']),
('S426BC', 'Ba Chieu', ARRAY['metro']),
('S427NVD', 'Nguyen Van Dau', ARRAY['metro']),
('S428TBM', 'Tan Binh Market', ARRAY['metro']),
('S429BH', 'Bac Hai', ARRAY['metro']),
('S430HCMUT', 'HCMC Uni of Tech', ARRAY['metro']),
('S431PT', 'Phu Tho', ARRAY['metro']),
('S432XC', 'Xom Cui', ARRAY['metro']),
('S433D8BS', 'District 8 Bus Station', ARRAY['metro']),
('S434BH', 'Binh Hung', ARRAY['metro', 'monorail']),
('S435CG', 'Can Giuoc', ARRAY['metro']),
('S436AC', 'Au Co', ARRAY['metro']),
('S437VL', 'Vuon Lai', ARRAY['metro']),
('S438TP', 'Tan Phu', ARRAY['metro']),
('S439LBB', 'Luy Ban Bich', ARRAY['metro']),
('S501DA', 'Di An', ARRAY['metro']),
('S502GAB', 'Ga An Binh', ARRAY['metro']),
('S503TB', 'Tam Binh', ARRAY['metro']),
('S504HBP', 'Hiep Binh Phuoc', ARRAY['metro']),
('S505BT', 'Binh Trieu', ARRAY['metro']),
('S506XVNT', 'Xo Viet Nghe Tinh', ARRAY['metro']),
('S507HX', 'Hang Xanh', ARRAY['metro']),
('S508NCV', 'Nguyen Cuu Van', ARRAY['metro']),
('S509SZ', 'Saigon Zoo', ARRAY['metro']),
('S510HL', 'Hoa Lu', ARRAY['metro']),
('S512IP', 'Independence Palace', ARRAY['metro']),
('S602TCH', 'Tan Chanh Hiep', ARRAY['metro', 'monorail']),
('S603QSC', 'Quang Trung Software City', ARRAY['monorail']),
('S604PHI', 'Phan Huy Ich', ARRAY['monorail']),
('S605TS', 'Tan Son', ARRAY['monorail']),
('S606HTT', 'Hanh Thong Tay', ARRAY['monorail']),
('S607TN', 'Thong Nhat', ARRAY['monorail']),
('S608XT', 'Xom Thuoc', ARRAY['monorail']),
('MR201TD', 'Thanh Da', ARRAY['monorail']),
('MR203BA', 'Binh An', ARRAY['monorail']),
('MR204LDC', 'Luong Dinh Cua', ARRAY['monorail']),
('MR205STT', 'South Thu Thiem', ARRAY['monorail']),
('MR206HTP', 'Huynh Tan Phat', ARRAY['monorail']),
('MR207TT', 'Tan Thuan Tay', ARRAY['monorail']),
('MR208NTT', 'Nguyen Thi Thap', ARRAY['monorail']),
('MR209PMH', 'Phu My Hung', ARRAY['monorail']),
('MR210NDC', 'Nguyen Duc Canh', ARRAY['monorail']),
('MR211RMIT', 'RMIT', ARRAY['monorail']),
('MR212COB', 'Cau Ong Be', ARRAY['monorail']),
('MR213PH', 'Pham Hung', ARRAY['monorail']),
('MR214RHA', 'Rach Hiep An', ARRAY['monorail']);

-- Insert routes
INSERT INTO routes (line_id, from_station_id, to_station_id, travel_time)
SELECT r.line_id, r.from_station_id, r.to_station_id, r.travel_time
FROM (
    VALUES 
    -- Line 1
    (1, 'S101MD', 'S102STAP', 3), (1, 'S102STAP', 'S101MD', 3),
    (1, 'S102STAP', 'S103SHTP', 4), (1, 'S103SHTP', 'S102STAP', 4),
    (1, 'S103SHTP', 'S104TD', 5), (1, 'S104TD', 'S103SHTP', 5),
    (1, 'S104TD', 'S105BT', 3), (1, 'S105BT', 'S104TD', 3),
    (1, 'S105BT', 'S106PL', 4), (1, 'S106PL', 'S105BT', 4),
    (1, 'S106PL', 'S107RC', 5), (1, 'S107RC', 'S106PL', 5),
    (1, 'S107RC', 'S108AP', 3), (1, 'S108AP', 'S107RC', 3),
    (1, 'S108AP', 'S109TD', 4), (1, 'S109TD', 'S108AP', 4),
    (1, 'S109TD', 'S110SB', 5), (1, 'S110SB', 'S109TD', 5),
    (1, 'S110SB', 'S111VT', 3), (1, 'S111VT', 'S110SB', 3),
    (1, 'S111VT', 'S112BS', 4), (1, 'S112BS', 'S111VT', 4),
    (1, 'S112BS', 'S113OH', 5), (1, 'S113OH', 'S112BS', 5),
    (1, 'S113OH', 'S114BT', 3), (1, 'S114BT', 'S113OH', 3),
    -- Line 2
    (2, 'S201CC', 'S202AS', 4), (2, 'S202AS', 'S201CC', 4),
    (2, 'S202AS', 'S203TTN', 3), (2, 'S203TTN', 'S202AS', 3),
    (2, 'S203TTN', 'S204TB', 4), (2, 'S204TB', 'S203TTN', 4),
    (2, 'S204TB', 'S205PVB', 3), (2, 'S205PVB', 'S204TB', 3),
    (2, 'S205PVB', 'S206BQ', 4), (2, 'S206BQ', 'S205PVB', 4),
    (2, 'S206BQ', 'S207NHD', 5), (2, 'S207NHD', 'S206BQ', 5),
    (2, 'S207NHD', 'S208BH', 3), (2, 'S208BH', 'S207NHD', 3),
    (2, 'S209PVH', 'S210LTR', 5), (2, 'S210LTR', 'S209PVH', 5),
    (2, 'S210LTR', 'S211HH', 3), (2, 'S211HH', 'S210LTR', 3),
    (2, 'S211HH', 'S212DC', 4), (2, 'S212DC', 'S211HH', 4),
    (2, 'S212DC', 'S213TD', 5), (2, 'S213TD', 'S212DC', 5),
    (2, 'S213TD', 'S214HMN', 3), (2, 'S214HMN', 'S213TD', 3),
    (2, 'S214HMN', 'S215TTS', 4), (2, 'S215TTS', 'S214HMN', 4),
    (2, 'S215TTS', 'S216MCT', 5), (2, 'S216MCT', 'S215TTS', 5),
    (2, 'S216MCT', 'S217TN', 3), (2, 'S217TN', 'S216MCT', 3),
    (2, 'S217TN', 'S218BK', 4), (2, 'S218BK', 'S217TN', 4),
    (2, 'S218BK', 'S219TT', 5), (2, 'S219TT', 'S218BK', 5),
    (2, 'S114BT', 'S214HMN', 3), (2, 'S214HMN', 'S114BT', 3),
    -- Line 3A
    (3, 'S301TK', 'S302EBS', 4), (3, 'S302EBS', 'S301TK', 4),
    (3, 'S302EBS', 'S303PLP', 3), (3, 'S303PLP', 'S302EBS', 3),
    (3, 'S303PLP', 'S304PL', 4), (3, 'S304PL', 'S303PLP', 4),
    (3, 'S304PL', 'S305CG', 5), (3, 'S305CG', 'S304PL', 5),
    (3, 'S305CG', 'S306CL', 3), (3, 'S306CL', 'S305CG', 3),
    (3, 'S306CL', 'S307TKP', 4), (3, 'S307TKP', 'S306CL', 4),
    (3, 'S307TKP', 'S308UMP', 5), (3, 'S308UMP', 'S307TKP', 5),
    (3, 'S308UMP', 'S309HBP', 3), (3, 'S309HBP', 'S308UMP', 3),
    (3, 'S309HBP', 'S310CH', 4), (3, 'S310CH', 'S309HBP', 4),
    (3, 'S310CH', 'S311TB', 5), (3, 'S311TB', 'S310CH', 5),
    (3, 'S311TB', 'S114BT', 3), (3, 'S114BT', 'S311TB', 3),
    -- Line 3B
    (4, 'S501DA', 'S502GAB', 4), (4, 'S502GAB', 'S501DA', 4),
    (4, 'S502GAB', 'S503TB', 3), (4, 'S503TB', 'S502GAB', 3),
    (4, 'S503TB', 'S504HBP', 4), (4, 'S504HBP', 'S503TB', 4),
    (4, 'S504HBP', 'S505BT', 5), (4, 'S505BT', 'S504HBP', 5),
    (4, 'S505BT', 'S506XVNT', 3), (4, 'S506XVNT', 'S505BT', 3),
    (4, 'S506XVNT', 'S507HX', 4), (4, 'S507HX', 'S506XVNT', 4),
    (4, 'S507HX', 'S508NCV', 5), (4, 'S508NCV', 'S507HX', 5),
    (4, 'S508NCV', 'S509SZ', 3), (4, 'S509SZ', 'S508NCV', 3),
    (4, 'S509SZ', 'S510HL', 4), (4, 'S510HL', 'S509SZ', 4),
    (4, 'S510HL', 'S511TL', 5), (4, 'S511TL', 'S510HL', 5),
    (4, 'S511TL', 'S512IP', 3), (4, 'S512IP', 'S511TL', 3),
    (4, 'S512IP', 'S213TD', 4), (4, 'S213TD', 'S512IP', 4),
    (4, 'S213TD', 'S310CH', 5), (4, 'S310CH', 'S213TD', 5),
    (4, 'S114BT', 'S310CH', 3),
    -- Line 4
    (5, 'S401TX', 'S402NTG', 4), (5, 'S402NTG', 'S401TX', 4),
    (5, 'S402NTG', 'S403ALB', 3), (5, 'S403ALB', 'S402NTG', 3),
    (5, 'S403ALB', 'S404AN', 4), (5, 'S404AN', 'S403ALB', 4),
    (5, 'S404AN', 'S405NVL', 5), (5, 'S405NVL', 'S404AN', 5),
    (5, 'S405NVL', 'S406GV', 3), (5, 'S406GV', 'S405NVL', 3),
    (5, 'S406GV', 'S407175', 4), (5, 'S407175', 'S406GV', 4),
    (5, 'S407175', 'S408GDP', 5), (5, 'S408GDP', 'S407175', 5),
    (5, 'S408GDP', 'S409PN', 3), (5, 'S409PN', 'S408GDP', 3),
    (5, 'S409PN', 'S410KB', 4), (5, 'S410KB', 'S409PN', 4),
    (5, 'S410KB', 'S411LVTP', 5), (5, 'S411LVTP', 'S410KB', 5),
    (5, 'S411LVTP', 'S511TL', 3), (5, 'S511TL', 'S411LVTP', 3),
    (5, 'S511TL', 'S114BT', 4), (5, 'S114BT', 'S511TL', 4),
    (5, 'S114BT', 'S412OLB', 5), (5, 'S412OLB', 'S114BT', 5),
    (5, 'S412OLB', 'S413Y', 3), (5, 'S413Y', 'S412OLB', 3),
    (5, 'S413Y', 'S414KH', 4), (5, 'S414KH', 'S413Y', 4),
    (5, 'S414KH', 'S415TH', 5), (5, 'S415TH', 'S414KH', 5),
    (5, 'S415TH', 'S416NHT', 3), (5, 'S416NHT', 'S415TH', 3),
    (5, 'S416NHT', 'S417NVL', 4), (5, 'S417NVL', 'S416NHT', 4),
    (5, 'S417NVL', 'S418PK', 5), (5, 'S418PK', 'S417NVL', 5),
    (5, 'S418PK', 'S419PHL', 3), (5, 'S419PHL', 'S418PK', 3),
    (5, 'S419PHL', 'S420BC', 4), (5, 'S420BC', 'S419PHL', 4),
    (5, 'S420BC', 'S421LT', 5), (5, 'S421LT', 'S420BC', 5),
    (5, 'S421LT', 'S422HP', 3), (5, 'S422HP', 'S421LT', 3),
    -- Line 4B
    (6, 'S408GDP', 'S423TSN', 4), (6, 'S423TSN', 'S408GDP', 4),
    (6, 'S423TSN', 'S424LCC', 5), (6, 'S424LCC', 'S423TSN', 5),
    -- Line 4B1
    (7, 'S423TSN', 'S425HVTP', 4), (7, 'S425HVTP', 'S423TSN', 4),
    -- Line 5
    (8, 'S110SB', 'S507HX', 4), (8, 'S507HX', 'S110SB', 4),
    (8, 'S507HX', 'S426BC', 5), (8, 'S426BC', 'S507HX', 5),
    (8, 'S426BC', 'S427NVD', 3), (8, 'S427NVD', 'S426BC', 3),
    (8, 'S427NVD', 'S409PN', 4), (8, 'S409PN', 'S427NVD', 4),
    (8, 'S409PN', 'S425HVTP', 5), (8, 'S425HVTP', 'S409PN', 5),
    (8, 'S425HVTP', 'S424LCC', 3), (8, 'S424LCC', 'S425HVTP', 3),
    (8, 'S424LCC', 'S208BH', 4), (8, 'S208BH', 'S424LCC', 4),
    (8, 'S208BH', 'S428TBM', 5), (8, 'S428TBM', 'S208BH', 5),
    (8, 'S428TBM', 'S429BH', 3), (8, 'S429BH', 'S428TBM', 3),
    (8, 'S429BH', 'S430HCMUT', 4), (8, 'S430HCMUT', 'S429BH', 4),
    (8, 'S430HCMUT', 'S431PT', 5), (8, 'S431PT', 'S430HCMUT', 5),
    (8, 'S431PT', 'S308UMP', 3), (8, 'S308UMP', 'S431PT', 3),
    (8, 'S308UMP', 'S432XC', 4), (8, 'S432XC', 'S308UMP', 4),
    (8, 'S432XC', 'S433D8BS', 5), (8, 'S433D8BS', 'S432XC', 5),
    (8, 'S433D8BS', 'S434BH', 3), (8, 'S434BH', 'S433D8BS', 3),
    (8, 'S434BH', 'S435CG', 4), (8, 'S435CG', 'S434BH', 4),
    -- Line 6
    (9, 'S206BQ', 'S436AC', 4), (9, 'S436AC', 'S206BQ', 4),
    (9, 'S436AC', 'S437VL', 5), (9, 'S437VL', 'S436AC', 5),
    (9, 'S437VL', 'S438TP', 3), (9, 'S438TP', 'S437VL', 3),
    (9, 'S438TP', 'S309HBP', 4), (9, 'S309HBP', 'S438TP', 4),
    (9, 'S309HBP', 'S439LBB', 5), (9, 'S439LBB', 'S309HBP', 5),
    (9, 'S439LBB', 'S304PL', 3), (9, 'S304PL', 'S439LBB', 3),
    -- MR2
    (10, 'S109TD', 'MR201TD', 4), (10, 'MR201TD', 'S109TD', 4),
    (10, 'MR201TD', 'MR203BA', 5), (10, 'MR203BA', 'MR201TD', 5),
    (10, 'MR203BA', 'MR204LDC', 3), (10, 'MR204LDC', 'MR203BA', 3),
    (10, 'MR204LDC', 'S217TN', 4), (10, 'S217TN', 'MR204LDC', 4),
    (10, 'S217TN', 'MR205STT', 5), (10, 'MR205STT', 'S217TN', 5),
    (10, 'MR205STT', 'MR206HTP', 3), (10, 'MR206HTP', 'MR205STT', 3),
    (10, 'MR206HTP', 'MR207TT', 4), (10, 'MR207TT', 'MR206HTP', 4),
    (10, 'MR207TT', 'MR208NTT', 5), (10, 'MR208NTT', 'MR207TT', 5),
    (10, 'MR208NTT', 'MR209PMH', 3), (10, 'MR209PMH', 'MR208NTT', 3),
    (10, 'MR209PMH', 'MR210NDC', 4), (10, 'MR210NDC', 'MR209PMH', 4),
    (10, 'MR210NDC', 'S417NVL', 5), (10, 'S417NVL', 'MR210NDC', 5),
    (10, 'S417NVL', 'MR211RMIT', 3), (10, 'MR211RMIT', 'S417NVL', 3),
    (10, 'MR211RMIT', 'MR212COB', 4), (10, 'MR212COB', 'MR211RMIT', 4),
    (10, 'MR212COB', 'MR213PH', 5), (10, 'MR213PH', 'MR212COB', 5),
    (10, 'MR213PH', 'MR214RHA', 3), (10, 'MR214RHA', 'MR213PH', 3),
    (10, 'MR214RHA', 'S434BH', 4), (10, 'S434BH', 'MR214RHA', 4),
    -- MR3
    (11, 'S602TCH', 'S603QSC', 4), (11, 'S603QSC', 'S602TCH', 4),
    (11, 'S603QSC', 'S604PHI', 5), (11, 'S604PHI', 'S603QSC', 5),
    (11, 'S604PHI', 'S605TS', 3), (11, 'S605TS', 'S604PHI', 3),
    (11, 'S605TS', 'S606HTT', 4), (11, 'S606HTT', 'S605TS', 4),
    (11, 'S606HTT', 'S607TN', 5), (11, 'S607TN', 'S606HTT', 5),
    (11, 'S607TN', 'S608XT', 3), (11, 'S608XT', 'S607TN', 3),
    (11, 'S608XT', 'S406GV', 4), (11, 'S406GV', 'S608XT', 4)
) r (line_id, from_station_id, to_station_id, travel_time);

-- Insert trains
INSERT INTO trains (train_id, line_id, current_route_id, current_station_id, next_station_id)
SELECT 
    t.train_id,
    t.line_id,
    r.route_id AS current_route_id,
    t.current_station_id,
    t.next_station_id
FROM (
    VALUES 
    ('T1-001', 1, 'S101MD', 'S102STAP'),
    ('T1-002', 1, 'S103SHTP', 'S104TD'),
    ('T1-003', 1, 'S106PL', 'S107RC'),
    ('T2-001', 2, 'S214HMN', 'S215TTS'),
    ('T2-002', 2, 'S217TN', 'S218BK')
) t (train_id, line_id, current_station_id, next_station_id)
JOIN routes r ON r.from_station_id = t.current_station_id 
    AND r.to_station_id = t.next_station_id 
    AND r.line_id = t.line_id;

-- Insert admin user
DO $$
BEGIN
    INSERT INTO users (username, email, password_hash, role)
    VALUES (
        'admin',
        'admin@example.com',
        crypt('securepassword123', gen_salt('bf')),
        'admin'
    )
    ON CONFLICT (username) DO NOTHING;
END $$;

-- Insert sample data for new tables
INSERT INTO schedule_templates (template_name, description) VALUES
('Weekday', 'Standard weekday schedule'),
('Weekend', 'Weekend schedule'),
('Holiday', 'Holiday schedule');

INSERT INTO service_patterns (pattern_name, description, line_id) VALUES
('Line 1 Full', 'Full route for Line 1', 1);

INSERT INTO service_pattern_details (pattern_id, station_sequence, station_id, dwell_time) VALUES
(1, 1, 'S101MD', 30),
(1, 2, 'S102STAP', 30),
(1, 3, 'S103SHTP', 30);

INSERT INTO frequency_rules (template_id, line_id, pattern_id, start_time, end_time, headway_minutes) VALUES
(1, 1, 1, '06:00', '09:00', 10),
(1, 1, 1, '09:00', '17:00', 15),
(1, 1, 1, '17:00', '23:00', 20);

INSERT INTO annual_calendar (date_id, template_id) VALUES
('2025-03-18', 1),
('2025-12-25', 3);
-- Insert transfer times
INSERT INTO transfer_times (station_id, from_line_id, to_line_id, transfer_time_peak, transfer_time_offpeak)
SELECT DISTINCT s.station_id, l1.line_id, l2.line_id, 2, 1
FROM stations s
CROSS JOIN lines l1
CROSS JOIN lines l2
WHERE s.station_id IN ('S109TD', 'S217TN', 'S406GV', 'S417NVL', 'S434BH')
AND l1.line_id < l2.line_id
ON CONFLICT DO NOTHING;

-- Update specific transfer times
UPDATE transfer_times 
SET transfer_time_peak = 3, transfer_time_offpeak = 2
WHERE station_id = 'S101MD' AND from_line_id = 1 AND to_line_id IN (SELECT line_id FROM lines WHERE line_id != 1);

-- Commit the transaction
COMMIT;
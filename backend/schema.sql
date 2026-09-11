CREATE TABLE farmers (
    id SERIAL PRIMARY KEY,
    phone VARCHAR(15) UNIQUE NOT NULL,
    name VARCHAR(100),
    village VARCHAR(100)
);

CREATE TABLE slots (
    id SERIAL PRIMARY KEY,
    slot_date DATE NOT NULL,
    start_time TIME NOT NULL,
    capacity INT NOT NULL DEFAULT 5,
    booked INT NOT NULL DEFAULT 0,
    CONSTRAINT no_overbooking CHECK (booked <= capacity),
    UNIQUE (slot_date, start_time)
);

CREATE TABLE bookings (
    id SERIAL PRIMARY KEY,
    farmer_id INT NOT NULL REFERENCES farmers(id),
    slot_id INT NOT NULL REFERENCES slots(id),
    token_number INT NOT NULL,
    crop VARCHAR(50),
    status VARCHAR(20) NOT NULL DEFAULT 'BOOKED',
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE notifications (
    id SERIAL PRIMARY KEY,
    farmer_id INT NOT NULL REFERENCES farmers(id),
    phone VARCHAR(15) NOT NULL,
    channel VARCHAR(10) NOT NULL,
    body TEXT NOT NULL,
    reason VARCHAR(40) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'QUEUED',
    attempts INT NOT NULL DEFAULT 0,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    delivered_at TIMESTAMP
);

CREATE INDEX idx_bookings_slot ON bookings(slot_id);
CREATE INDEX idx_notif_phone ON notifications(phone);
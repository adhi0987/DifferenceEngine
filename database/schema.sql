-- AttendIQ COA — PostgreSQL reference schema (design section 8).
-- The backend uses SQLAlchemy and can target this schema in production
-- (set DATABASE_URL=postgresql+psycopg://...). SQLite is used for local runs.

CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    institutional_id VARCHAR(50) UNIQUE NOT NULL,
    full_name VARCHAR(150) NOT NULL,
    email VARCHAR(150) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(20) NOT NULL,
    phone_hash VARCHAR(255),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE departments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(150) NOT NULL,
    code VARCHAR(20) UNIQUE,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE courses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    department_id UUID REFERENCES departments(id),
    course_code VARCHAR(30) NOT NULL,
    course_name VARCHAR(150) NOT NULL,
    syllabus_summary TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE course_sections (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    course_id UUID NOT NULL REFERENCES courses(id),
    faculty_id UUID REFERENCES users(id),
    section_name VARCHAR(100) NOT NULL,
    academic_term VARCHAR(50) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE enrollments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id UUID NOT NULL REFERENCES users(id),
    section_id UUID NOT NULL REFERENCES course_sections(id),
    enrollment_status VARCHAR(30) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE (student_id, section_id)
);

CREATE TABLE classrooms (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    room_code VARCHAR(50) UNIQUE NOT NULL,
    room_name VARCHAR(150) NOT NULL,
    building_name VARCHAR(150),
    wifi_ssid_hash VARCHAR(255),
    beacon_id_hash VARCHAR(255),
    latitude DECIMAL(10,7),
    longitude DECIMAL(10,7),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE class_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    section_id UUID NOT NULL REFERENCES course_sections(id),
    classroom_id UUID REFERENCES classrooms(id),
    topic_title VARCHAR(200) NOT NULL,
    session_date DATE NOT NULL,
    start_time TIMESTAMP NOT NULL,
    end_time TIMESTAMP,
    status VARCHAR(30) DEFAULT 'scheduled',
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE qr_tokens (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL REFERENCES class_sessions(id),
    token_hash VARCHAR(255) NOT NULL,
    valid_from TIMESTAMP NOT NULL,
    valid_until TIMESTAMP NOT NULL,
    is_revoked BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE attendance_records (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL REFERENCES class_sessions(id),
    student_id UUID NOT NULL REFERENCES users(id),
    enrollment_id UUID REFERENCES enrollments(id),
    check_in_time TIMESTAMP NOT NULL,
    verification_status VARCHAR(30) NOT NULL,
    qr_verified BOOLEAN DEFAULT FALSE,
    device_verified BOOLEAN DEFAULT FALSE,
    proximity_verified BOOLEAN DEFAULT FALSE,
    risk_score INTEGER DEFAULT 0,
    remarks TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE (session_id, student_id)
);

CREATE TABLE device_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id),
    device_hash VARCHAR(255) NOT NULL,
    login_ip_hash VARCHAR(255),
    user_agent_hash VARCHAR(255),
    session_started_at TIMESTAMP DEFAULT NOW(),
    session_expires_at TIMESTAMP NOT NULL,
    is_active BOOLEAN DEFAULT TRUE
);

CREATE TABLE quiz_questions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    course_id UUID NOT NULL REFERENCES courses(id),
    topic VARCHAR(150) NOT NULL,
    question_text TEXT NOT NULL,
    option_a TEXT,
    option_b TEXT,
    option_c TEXT,
    option_d TEXT,
    correct_option VARCHAR(10),
    difficulty VARCHAR(20) DEFAULT 'medium',
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE session_quizzes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL REFERENCES class_sessions(id),
    question_id UUID NOT NULL REFERENCES quiz_questions(id),
    launched_at TIMESTAMP NOT NULL,
    closes_at TIMESTAMP NOT NULL,
    status VARCHAR(30) DEFAULT 'active'
);

CREATE TABLE quiz_responses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_quiz_id UUID NOT NULL REFERENCES session_quizzes(id),
    student_id UUID NOT NULL REFERENCES users(id),
    selected_option VARCHAR(10),
    free_text_answer TEXT,
    is_correct BOOLEAN,
    response_time TIMESTAMP DEFAULT NOW(),
    UNIQUE (session_quiz_id, student_id)
);

CREATE TABLE resources (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    course_id UUID NOT NULL REFERENCES courses(id),
    uploaded_by UUID REFERENCES users(id),
    title VARCHAR(200) NOT NULL,
    resource_type VARCHAR(50) NOT NULL,
    topic VARCHAR(150),
    file_url TEXT NOT NULL,
    required_tier VARCHAR(30) DEFAULT 'bronze',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE reward_policies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    course_id UUID NOT NULL REFERENCES courses(id),
    tier_name VARCHAR(30) NOT NULL,
    min_attendance_percentage DECIMAL(5,2) NOT NULL,
    min_participation_score DECIMAL(5,2) DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE student_reward_status (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id UUID NOT NULL REFERENCES users(id),
    course_id UUID NOT NULL REFERENCES courses(id),
    attendance_percentage DECIMAL(5,2) DEFAULT 0,
    participation_score DECIMAL(8,2) DEFAULT 0,
    current_tier VARCHAR(30) DEFAULT 'none',
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE (student_id, course_id)
);

CREATE TABLE resource_access_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id UUID NOT NULL REFERENCES users(id),
    resource_id UUID NOT NULL REFERENCES resources(id),
    access_time TIMESTAMP DEFAULT NOW(),
    access_allowed BOOLEAN NOT NULL,
    denial_reason TEXT
);

CREATE TABLE audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    actor_user_id UUID REFERENCES users(id),
    action VARCHAR(100) NOT NULL,
    entity_type VARCHAR(100) NOT NULL,
    entity_id UUID,
    meta JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_attendance_session ON attendance_records(session_id);
CREATE INDEX idx_attendance_student ON attendance_records(student_id);
CREATE INDEX idx_sessions_section ON class_sessions(section_id);
CREATE INDEX idx_enrollments_section ON enrollments(section_id);
CREATE INDEX idx_audit_entity ON audit_logs(entity_type);

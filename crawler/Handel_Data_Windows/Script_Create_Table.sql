USE Big_Data;
GO

-- 1. Bảng nhóm kỹ năng (skill_groups)
CREATE TABLE dbo.skill_groups (
    id   INT IDENTITY(1,1) PRIMARY KEY,
    name NVARCHAR(100) NOT NULL UNIQUE
);
GO

-- 2. Bảng kỹ năng (skills)
CREATE TABLE dbo.skills (
    id   INT IDENTITY(1,1) PRIMARY KEY,
    name NVARCHAR(100) NOT NULL UNIQUE
);
GO

-- 3. Bảng chi tiết gán kỹ năng vào nhóm (skill_details)
CREATE TABLE dbo.skill_details (
    skill_id INT NOT NULL,
    group_id INT NOT NULL,
    CONSTRAINT PK_skill_details PRIMARY KEY CLUSTERED (skill_id, group_id),
    CONSTRAINT FK_skill_details_skill FOREIGN KEY (skill_id)
        REFERENCES dbo.skills(id)
        ON DELETE CASCADE,
    CONSTRAINT FK_skill_details_group FOREIGN KEY (group_id)
        REFERENCES dbo.skill_groups(id)
        ON DELETE CASCADE
);
GO

-- 4. Bảng công việc chính (jobs)
CREATE TABLE dbo.jobs (
    id                   INT IDENTITY(1,1) PRIMARY KEY,
    group_id             INT NOT NULL,            -- category của job
    title                NVARCHAR(255) NOT NULL,
    link                 NVARCHAR(MAX),
    location             NVARCHAR(255),
    experience           NVARCHAR(100),
    work_location_detail NVARCHAR(MAX),
    working_time         NVARCHAR(255),
    deadline             DATE,
    salary_raw           NVARCHAR(100),
    salary_normalized    BIGINT,
    currency_unit        NVARCHAR(10),
    CONSTRAINT FK_jobs_group FOREIGN KEY (group_id)
        REFERENCES dbo.skill_groups(id)
        ON DELETE NO ACTION
);
GO

-- 5. Bảng mô tả chi tiết công việc (job_details)
CREATE TABLE dbo.job_details (
    id           INT IDENTITY(1,1) PRIMARY KEY,
    job_id       INT NOT NULL,
    description  NVARCHAR(MAX),
    requirements NVARCHAR(MAX),
    benefits     NVARCHAR(MAX),
    CONSTRAINT FK_job_details_job FOREIGN KEY (job_id)
        REFERENCES dbo.jobs(id)
        ON DELETE CASCADE
);
GO

-- 6. Bảng gán kỹ năng vào công việc (job_skills)
CREATE TABLE dbo.job_skills (
    job_id   INT NOT NULL,
    skill_id INT NOT NULL,
    CONSTRAINT PK_job_skills PRIMARY KEY CLUSTERED (job_id, skill_id),
    CONSTRAINT FK_job_skills_job FOREIGN KEY (job_id)
        REFERENCES dbo.jobs(id)
        ON DELETE CASCADE,
    CONSTRAINT FK_job_skills_skill FOREIGN KEY (skill_id)
        REFERENCES dbo.skills(id)
        ON DELETE CASCADE
);
GO

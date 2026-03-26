-- Connect to the database
\c metadata_db

--- schema (eva_submissions)
CREATE SCHEMA eva_submissions AUTHORIZATION metadata_db_user;

--- table (submission_account)
CREATE TABLE eva_submissions.submission_account (
	id varchar(255) NOT NULL,
	first_name varchar(255) NULL,
	last_name varchar(255) NULL,
	login_type varchar(255) NOT NULL,
	primary_email varchar(255) NOT NULL,
	user_id varchar(255) NOT NULL,
	CONSTRAINT submission_account_pkey PRIMARY KEY (id),
	CONSTRAINT uk_submission_account_user_id_login_type UNIQUE (user_id, login_type)
);

ALTER TABLE eva_submissions.submission_account OWNER to metadata_db_user;
GRANT ALL ON TABLE eva_submissions.submission_account to metadata_db_user;


--- table (submission_account_secondary_emails)
CREATE TABLE eva_submissions.submission_account_secondary_emails (
	submission_account_id varchar(255) NOT NULL,
	secondary_emails varchar(255) NULL
);

ALTER TABLE eva_submissions.submission_account_secondary_emails OWNER to metadata_db_user;
GRANT ALL ON TABLE eva_submissions.submission_account_secondary_emails to metadata_db_user;

ALTER TABLE eva_submissions.submission_account_secondary_emails ADD CONSTRAINT fk_submission_account_secondary_emails_submission_account_id FOREIGN KEY (submission_account_id) REFERENCES eva_submissions.submission_account(id);


--- table (submission)
CREATE TABLE eva_submissions.submission (
	submission_id varchar(255) NOT NULL,
	completion_time timestamp NULL,
	initiation_time timestamp NOT NULL,
	"status" varchar(255) NOT NULL,
	upload_url varchar(255) NULL,
	uploaded_time timestamp NULL,
	submission_account_id varchar(255) NOT NULL,
	CONSTRAINT submission_pkey PRIMARY KEY (submission_id)
);

ALTER TABLE eva_submissions.submission OWNER to metadata_db_user;
GRANT ALL ON TABLE eva_submissions.submission to metadata_db_user;

ALTER TABLE eva_submissions.submission ADD CONSTRAINT fk_submission_submission_account_id FOREIGN KEY (submission_account_id) REFERENCES eva_submissions.submission_account(id);


--- table (submission_details)
CREATE TABLE eva_submissions.submission_details (
	submission_id varchar(255) NOT NULL,
	metadata_json jsonb NOT NULL,
	project_description varchar(5000) NOT NULL,
	project_title varchar(500) NOT NULL,
	CONSTRAINT submission_details_pkey PRIMARY KEY (submission_id)
);

ALTER TABLE eva_submissions.submission_details OWNER to metadata_db_user;
GRANT ALL ON TABLE eva_submissions.submission_details to metadata_db_user;


--- table (submission_processing_status)
CREATE TABLE eva_submissions.submission_processing_status (
	submission_id varchar(255) NOT NULL,
	last_update_time timestamp NOT NULL,
	priority int4 DEFAULT 5 NOT NULL,
	"status" varchar(255) NOT NULL,
	step varchar(255) NOT NULL,
	CONSTRAINT submission_processing_status_pkey PRIMARY KEY (submission_id)
);

ALTER TABLE eva_submissions.submission_processing_status OWNER to metadata_db_user;
GRANT ALL ON TABLE eva_submissions.submission_processing_status to metadata_db_user;


--- table (revinfo)
CREATE TABLE eva_submissions.revinfo (
	rev int4 NOT NULL,
	revtstmp int8 NULL,
	CONSTRAINT revinfo_pkey PRIMARY KEY (rev)
);

ALTER TABLE eva_submissions.revinfo OWNER to metadata_db_user;
GRANT ALL ON TABLE eva_submissions.revinfo to metadata_db_user;


--- table (submission_processing_status_aud)
CREATE TABLE eva_submissions.submission_processing_status_aud (
	submission_id varchar(255) NOT NULL,
	rev int4 NOT NULL,
	revtype int2 NULL,
	last_update_time timestamp NULL,
	priority int4 DEFAULT 5 NULL,
	"status" varchar(255) NULL,
	step varchar(255) NULL,
	CONSTRAINT submission_processing_status_aud_pkey PRIMARY KEY (submission_id, rev)
);

ALTER TABLE eva_submissions.submission_processing_status_aud OWNER to metadata_db_user;
GRANT ALL ON TABLE eva_submissions.submission_processing_status_aud to metadata_db_user;

ALTER TABLE eva_submissions.submission_processing_status_aud ADD CONSTRAINT fk_submission_processing_status_aud_rev FOREIGN KEY (rev) REFERENCES eva_submissions.revinfo(rev);

--- table (call_home_event)
CREATE TABLE eva_submissions.call_home_event (
	id bigserial NOT NULL,
	cli_version varchar(255) NULL,
	created_at timestamp NULL,
	deployment_id varchar(255) NULL,
	event_type varchar(255) NULL,
	executor varchar(255) NULL,
	raw_payload jsonb NOT NULL,
	run_id varchar(255) NULL,
	runtime_seconds int4 NULL,
	tasks varchar(255) NULL,
	CONSTRAINT call_home_event_pkey PRIMARY KEY (id)
);

ALTER TABLE eva_submissions.call_home_event OWNER to metadata_db_user;
GRANT ALL ON TABLE eva_submissions.call_home_event to metadata_db_user;

--- Insert the test eva submission account
INSERT INTO eva_submissions.submission_account (id,first_name,last_name,login_type,primary_email,user_id) VALUES
	 ('eva_webin','Test','User','webin','test@ebi.ac.uk','Webin-123');
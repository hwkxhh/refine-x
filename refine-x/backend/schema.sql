--
-- PostgreSQL database dump
--

\restrict 7nDUFrQjNSJwa4JUEltHd7dw2zsbWLRxb1jd2u5HXlFqkcsZtVBEtbYFldwlHxg

-- Dumped from database version 18.2
-- Dumped by pg_dump version 18.2

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET transaction_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: alembic_version; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.alembic_version (
    version_num character varying(32) NOT NULL
);


--
-- Name: annotations; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.annotations (
    id integer NOT NULL,
    chart_id integer NOT NULL,
    user_id integer NOT NULL,
    data_point_index integer NOT NULL,
    text character varying NOT NULL,
    created_at timestamp without time zone
);


--
-- Name: annotations_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.annotations_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: annotations_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.annotations_id_seq OWNED BY public.annotations.id;


--
-- Name: charts; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.charts (
    id integer NOT NULL,
    job_id integer NOT NULL,
    chart_type character varying NOT NULL,
    x_header character varying NOT NULL,
    y_header character varying,
    title character varying NOT NULL,
    config json,
    data json NOT NULL,
    is_recommended boolean,
    created_at timestamp without time zone
);


--
-- Name: charts_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.charts_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: charts_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.charts_id_seq OWNED BY public.charts.id;


--
-- Name: cleaned_datasets; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.cleaned_datasets (
    id integer NOT NULL,
    job_id integer NOT NULL,
    column_metadata json,
    row_count_original integer,
    row_count_cleaned integer,
    quality_score double precision,
    cleaning_summary json,
    created_at timestamp without time zone,
    global_flags json,
    htype_map json,
    pii_tags json,
    struct_flags json,
    personal_identity_flags json,
    date_time_flags json,
    contact_location_flags json,
    numeric_financial_flags json,
    boolean_category_flags json,
    org_product_flags json,
    text_technical_flags json,
    missing_value_flags json,
    duplicate_flags json,
    analytical_results json,
    conditional_flags json,
    medical_flags json
);


--
-- Name: COLUMN cleaned_datasets.boolean_category_flags; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.cleaned_datasets.boolean_category_flags IS 'Flags from Boolean, Category, Status, Survey & Multi-Value cleaning (Session 8)';


--
-- Name: cleaned_datasets_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.cleaned_datasets_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: cleaned_datasets_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.cleaned_datasets_id_seq OWNED BY public.cleaned_datasets.id;


--
-- Name: cleaning_logs; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.cleaning_logs (
    id integer NOT NULL,
    job_id integer NOT NULL,
    row_index integer,
    column_name character varying,
    action character varying NOT NULL,
    original_value character varying,
    new_value character varying,
    reason character varying NOT NULL,
    "timestamp" timestamp without time zone,
    formula_id character varying,
    was_auto_applied boolean DEFAULT true
);


--
-- Name: cleaning_logs_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.cleaning_logs_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: cleaning_logs_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.cleaning_logs_id_seq OWNED BY public.cleaning_logs.id;


--
-- Name: comparison_jobs; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.comparison_jobs (
    id integer NOT NULL,
    user_id integer NOT NULL,
    job_id_1 integer NOT NULL,
    job_id_2 integer NOT NULL,
    header_mapping json,
    deltas json,
    significant_changes json,
    status character varying,
    ai_insight character varying,
    created_at timestamp without time zone
);


--
-- Name: comparison_jobs_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.comparison_jobs_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: comparison_jobs_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.comparison_jobs_id_seq OWNED BY public.comparison_jobs.id;


--
-- Name: insights; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.insights (
    id integer NOT NULL,
    chart_id integer,
    job_id integer NOT NULL,
    content text NOT NULL,
    confidence character varying NOT NULL,
    confidence_score double precision NOT NULL,
    recommendations json,
    created_at timestamp without time zone
);


--
-- Name: insights_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.insights_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: insights_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.insights_id_seq OWNED BY public.insights.id;


--
-- Name: upload_jobs; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.upload_jobs (
    id integer NOT NULL,
    user_id integer NOT NULL,
    filename character varying NOT NULL,
    file_path character varying NOT NULL,
    file_size integer NOT NULL,
    file_type character varying NOT NULL,
    status character varying,
    error_message character varying,
    row_count integer,
    column_count integer,
    quality_score double precision,
    created_at timestamp without time zone,
    processed_at timestamp without time zone,
    column_relevance_result json,
    confirmed_columns json
);


--
-- Name: upload_jobs_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.upload_jobs_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: upload_jobs_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.upload_jobs_id_seq OWNED BY public.upload_jobs.id;


--
-- Name: user_goals; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.user_goals (
    id integer NOT NULL,
    job_id integer NOT NULL,
    goal_text character varying NOT NULL,
    goal_category character varying,
    created_at timestamp without time zone
);


--
-- Name: user_goals_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.user_goals_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: user_goals_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.user_goals_id_seq OWNED BY public.user_goals.id;


--
-- Name: users; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.users (
    id integer NOT NULL,
    email character varying NOT NULL,
    password_hash character varying NOT NULL,
    name character varying,
    created_at timestamp with time zone DEFAULT now()
);


--
-- Name: users_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.users_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: users_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.users_id_seq OWNED BY public.users.id;


--
-- Name: annotations id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.annotations ALTER COLUMN id SET DEFAULT nextval('public.annotations_id_seq'::regclass);


--
-- Name: charts id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.charts ALTER COLUMN id SET DEFAULT nextval('public.charts_id_seq'::regclass);


--
-- Name: cleaned_datasets id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cleaned_datasets ALTER COLUMN id SET DEFAULT nextval('public.cleaned_datasets_id_seq'::regclass);


--
-- Name: cleaning_logs id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cleaning_logs ALTER COLUMN id SET DEFAULT nextval('public.cleaning_logs_id_seq'::regclass);


--
-- Name: comparison_jobs id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.comparison_jobs ALTER COLUMN id SET DEFAULT nextval('public.comparison_jobs_id_seq'::regclass);


--
-- Name: insights id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.insights ALTER COLUMN id SET DEFAULT nextval('public.insights_id_seq'::regclass);


--
-- Name: upload_jobs id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.upload_jobs ALTER COLUMN id SET DEFAULT nextval('public.upload_jobs_id_seq'::regclass);


--
-- Name: user_goals id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_goals ALTER COLUMN id SET DEFAULT nextval('public.user_goals_id_seq'::regclass);


--
-- Name: users id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.users ALTER COLUMN id SET DEFAULT nextval('public.users_id_seq'::regclass);


--
-- Name: alembic_version alembic_version_pkc; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.alembic_version
    ADD CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num);


--
-- Name: annotations annotations_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.annotations
    ADD CONSTRAINT annotations_pkey PRIMARY KEY (id);


--
-- Name: charts charts_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.charts
    ADD CONSTRAINT charts_pkey PRIMARY KEY (id);


--
-- Name: cleaned_datasets cleaned_datasets_job_id_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cleaned_datasets
    ADD CONSTRAINT cleaned_datasets_job_id_key UNIQUE (job_id);


--
-- Name: cleaned_datasets cleaned_datasets_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cleaned_datasets
    ADD CONSTRAINT cleaned_datasets_pkey PRIMARY KEY (id);


--
-- Name: cleaning_logs cleaning_logs_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cleaning_logs
    ADD CONSTRAINT cleaning_logs_pkey PRIMARY KEY (id);


--
-- Name: comparison_jobs comparison_jobs_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.comparison_jobs
    ADD CONSTRAINT comparison_jobs_pkey PRIMARY KEY (id);


--
-- Name: insights insights_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.insights
    ADD CONSTRAINT insights_pkey PRIMARY KEY (id);


--
-- Name: upload_jobs upload_jobs_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.upload_jobs
    ADD CONSTRAINT upload_jobs_pkey PRIMARY KEY (id);


--
-- Name: user_goals user_goals_job_id_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_goals
    ADD CONSTRAINT user_goals_job_id_key UNIQUE (job_id);


--
-- Name: user_goals user_goals_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_goals
    ADD CONSTRAINT user_goals_pkey PRIMARY KEY (id);


--
-- Name: users users_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (id);


--
-- Name: ix_annotations_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_annotations_id ON public.annotations USING btree (id);


--
-- Name: ix_charts_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_charts_id ON public.charts USING btree (id);


--
-- Name: ix_cleaned_datasets_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_cleaned_datasets_id ON public.cleaned_datasets USING btree (id);


--
-- Name: ix_cleaning_logs_formula_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_cleaning_logs_formula_id ON public.cleaning_logs USING btree (formula_id);


--
-- Name: ix_cleaning_logs_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_cleaning_logs_id ON public.cleaning_logs USING btree (id);


--
-- Name: ix_comparison_jobs_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_comparison_jobs_id ON public.comparison_jobs USING btree (id);


--
-- Name: ix_insights_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_insights_id ON public.insights USING btree (id);


--
-- Name: ix_upload_jobs_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_upload_jobs_id ON public.upload_jobs USING btree (id);


--
-- Name: ix_user_goals_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_user_goals_id ON public.user_goals USING btree (id);


--
-- Name: ix_users_email; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX ix_users_email ON public.users USING btree (email);


--
-- Name: ix_users_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_users_id ON public.users USING btree (id);


--
-- Name: annotations annotations_chart_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.annotations
    ADD CONSTRAINT annotations_chart_id_fkey FOREIGN KEY (chart_id) REFERENCES public.charts(id);


--
-- Name: annotations annotations_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.annotations
    ADD CONSTRAINT annotations_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- Name: charts charts_job_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.charts
    ADD CONSTRAINT charts_job_id_fkey FOREIGN KEY (job_id) REFERENCES public.upload_jobs(id);


--
-- Name: cleaned_datasets cleaned_datasets_job_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cleaned_datasets
    ADD CONSTRAINT cleaned_datasets_job_id_fkey FOREIGN KEY (job_id) REFERENCES public.upload_jobs(id);


--
-- Name: cleaning_logs cleaning_logs_job_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cleaning_logs
    ADD CONSTRAINT cleaning_logs_job_id_fkey FOREIGN KEY (job_id) REFERENCES public.upload_jobs(id);


--
-- Name: comparison_jobs comparison_jobs_job_id_1_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.comparison_jobs
    ADD CONSTRAINT comparison_jobs_job_id_1_fkey FOREIGN KEY (job_id_1) REFERENCES public.upload_jobs(id);


--
-- Name: comparison_jobs comparison_jobs_job_id_2_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.comparison_jobs
    ADD CONSTRAINT comparison_jobs_job_id_2_fkey FOREIGN KEY (job_id_2) REFERENCES public.upload_jobs(id);


--
-- Name: comparison_jobs comparison_jobs_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.comparison_jobs
    ADD CONSTRAINT comparison_jobs_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- Name: insights insights_chart_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.insights
    ADD CONSTRAINT insights_chart_id_fkey FOREIGN KEY (chart_id) REFERENCES public.charts(id);


--
-- Name: insights insights_job_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.insights
    ADD CONSTRAINT insights_job_id_fkey FOREIGN KEY (job_id) REFERENCES public.upload_jobs(id);


--
-- Name: upload_jobs upload_jobs_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.upload_jobs
    ADD CONSTRAINT upload_jobs_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- Name: user_goals user_goals_job_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_goals
    ADD CONSTRAINT user_goals_job_id_fkey FOREIGN KEY (job_id) REFERENCES public.upload_jobs(id);


--
-- PostgreSQL database dump complete
--

\unrestrict 7nDUFrQjNSJwa4JUEltHd7dw2zsbWLRxb1jd2u5HXlFqkcsZtVBEtbYFldwlHxg


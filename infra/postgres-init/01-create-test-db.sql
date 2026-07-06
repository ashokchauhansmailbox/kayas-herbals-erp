-- Initial cluster bootstrap: create the test database alongside the dev DB
-- so pytest can run without extra steps in docker compose environments.
CREATE DATABASE kaya_bos_test OWNER kaya;

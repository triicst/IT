--
-- Create Example Tables 
--


-- Add serial ID to existing
-- ALTER TABLE container ADD COLUMN id SERIAL PRIMARY KEY;
--
-- jsonb contains docker inspect AND 'info' object
-- Key fields: 'Config'->'Labels'->'DBaaS'
--
CREATE TABLE company (
    id             SERIAL NOT NULL PRIMARY KEY,
    name           TEXT    NOT NULL,
    age            INT     NOT NULL,
    address        CHAR(50),
    salary         REAL
    )


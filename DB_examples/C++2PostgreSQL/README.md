Title:  Postgres C++ programming example 
Author: John Dey  jfdey@fredhutch.org 
Date:   June 1, 2017 
# PostgreSQL C++

## Environment 
This tutorial will use the Fred Hutch Gizmo cluster. There are three
head nodes for the Gizmo cluster are rhino1, 2 and 3. Gizmo's programming
environment is managed with **Modules**. Setup your environment by loading
the Postgres C++ libraries; libpqxx. 

    module load libpqxx/5.0.1-foss-2016b

The libpqxx is linked to PostgreSQL 9.6.0 libraries. The psql command line
interface is included with the environment.

### PostgreSQL Environment

Create a Postgres DB using MyDB.  (http://mydb.fredhutch.org). Follow
the instructions on the Create screen and place the database credentials 
in ~/.pgpass.  After creating the database instance with MyDB, create
a table for the example script to use.

Create a table for the examples:

    psql -h mydb -d database-name -p 32061 --file=create.sql


### Compiler

The foss-2016b toolkit is built with GCC-5.4.0-2.26. If your project requires
other modules they should be selected from the foss-2016b modules. Libpqxx and
libpq need to specified in the order listed in this example:

    g++ postgres_example.cpp -std=c++11 -lpqxx -lpq -lpthread

#### postgres_example.cpp

The example connects, inserts and queries from Postgres 9.6.x

-- -----------------------------------------------------------------------------------
-- File Name    : https://oracle-base.com/dba/ords/user_ords_schemas.sql
-- Author       : Tim Hall
-- Description  : Displays all ORDS enabled schemas.
-- Call Syntax  : @user_ords_schemas
-- Last Modified: 23/06/2025
-- -----------------------------------------------------------------------------------
set linesize 100
column parsing_schema format a20
column pattern format a30
column status format a10

select id,
       parsing_schema,
       pattern,
       status
from   user_ords_schemas
order by parsing_schema;
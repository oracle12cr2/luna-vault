-- -----------------------------------------------------------------------------------
-- File Name    : https://oracle-base.com/dba/ords/dba_ords_roles.sql
-- Author       : Tim Hall
-- Description  : Displays all ORDS roles.
-- Call Syntax  : @dba_ords_roles
-- Last Modified: 23/06/2025
-- -----------------------------------------------------------------------------------
column name format a60

select id, name
from   dba_ords_roles
order by 1;
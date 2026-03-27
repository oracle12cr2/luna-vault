-- -----------------------------------------------------------------------------------
-- File Name    : https://oracle-base.com/dba/ords/dba_ords_privileges.sql
-- Author       : Tim Hall
-- Description  : Displays all ORDS privileges.
-- Call Syntax  : @dba_ords_privileges
-- Last Modified: 23/06/2025
-- -----------------------------------------------------------------------------------
column name format a60
column description format a60

select id, name
from   dba_ords_privileges
order by 1;
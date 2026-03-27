-- -----------------------------------------------------------------------------------
-- File Name    : https://oracle-base.com/dba/ords/dba_ords_client_roles.sql
-- Author       : Tim Hall
-- Description  : Displays all ORDS client roles.
-- Call Syntax  : @dba_ords_client_roles
-- Last Modified: 23/06/2025
-- -----------------------------------------------------------------------------------
column client_name format a30
column role_name format a20

select client_id, client_name, role_id, role_name
from   dba_ords_client_roles
order by client_name, role_name;
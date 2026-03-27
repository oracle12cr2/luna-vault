-- -----------------------------------------------------------------------------------
-- File Name    : https://oracle-base.com/dba/ords/dba_ords_privilege_roles.sql
-- Author       : Tim Hall
-- Description  : Displays all ORDS privilege and role associations.
-- Call Syntax  : @dba_ords_privilege_roles
-- Last Modified: 23/06/2025
-- -----------------------------------------------------------------------------------
column privilege_name format a60
column role_name format a60

select privilege_id, privilege_name, role_id, role_name
from   dba_ords_privilege_roles
order by privilege_name, role_name;
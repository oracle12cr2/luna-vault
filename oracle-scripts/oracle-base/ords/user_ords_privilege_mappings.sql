-- -----------------------------------------------------------------------------------
-- File Name    : https://oracle-base.com/dba/ords/user_ords_privilege_mappings.sql
-- Author       : Tim Hall
-- Description  : Displays all ORDS privilege mappings.
-- Call Syntax  : @user_ords_privilege_mappings
-- Last Modified: 23/06/2025
-- -----------------------------------------------------------------------------------
column privilege_name format a60
column pattern format a60

select pm.name as privilege_name, pm.pattern
from   user_ords_privilege_mappings pm
order by pm.name, pm.pattern;

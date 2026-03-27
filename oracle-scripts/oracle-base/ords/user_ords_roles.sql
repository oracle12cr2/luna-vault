-- -----------------------------------------------------------------------------------
-- File Name    : https://oracle-base.com/dba/ords/user_ords_roles.sql
-- Author       : Tim Hall
-- Description  : Displays all ORDS roles.
-- Call Syntax  : @user_ords_roles
-- Last Modified: 23/06/2025
-- -----------------------------------------------------------------------------------
column name format a60

select id, name
from   user_ords_roles
order by 1;
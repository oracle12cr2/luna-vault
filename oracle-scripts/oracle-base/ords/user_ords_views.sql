-- -----------------------------------------------------------------------------------
-- File Name    : https://oracle-base.com/dba/ords/user_ords_views.sql
-- Author       : Tim Hall
-- Description  : Displays all ORDS DBA views.
-- Call Syntax  : @user_ords_views
-- Last Modified: 23/06/2025
-- -----------------------------------------------------------------------------------
column object_name format a30

select object_name
from   all_objects
where  object_name like 'USER_ORDS%'
and    object_type = 'VIEW'
order by 1;
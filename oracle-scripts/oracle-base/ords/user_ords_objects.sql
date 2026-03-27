-- -----------------------------------------------------------------------------------
-- File Name    : https://oracle-base.com/dba/ords/user_ords_objects.sql
-- Author       : Tim Hall
-- Description  : Displays all ORDS AutoRest objects.
-- Call Syntax  : @user_ords_objects
-- Last Modified: 23/06/2025
-- -----------------------------------------------------------------------------------
set linesize 150 

column parsing_schema format a20
column parsing_object format a30
column object_alias format a40

select parsing_schema,
       parsing_object,
       object_alias,
       type,
       status
from   user_ords_enabled_objects
order by 1, 2;
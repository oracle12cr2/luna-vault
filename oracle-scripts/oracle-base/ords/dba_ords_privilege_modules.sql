-- -----------------------------------------------------------------------------------
-- File Name    : https://oracle-base.com/dba/ords/dba_ords_privilege_modules.sql
-- Author       : Tim Hall
-- Description  : Displays all ORDS privilege and associated modules.
-- Call Syntax  : @dba_ords_privilege_modules
-- Last Modified: 23/06/2025
-- -----------------------------------------------------------------------------------
column name format a60
column pattern format a60

select s.parsing_schema, p.module_id, p.module_name, p.privilege_id, p.privilege_name
from   dba_ords_privilege_modules p
       join dba_ords_schemas s on s.id = p.schema_id
order by s.parsing_schema, p.module_name, p.privilege_name;
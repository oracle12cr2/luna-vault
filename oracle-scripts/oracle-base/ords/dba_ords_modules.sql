-- -----------------------------------------------------------------------------------
-- File Name    : https://oracle-base.com/dba/ords/dba_ords_modules.sql
-- Author       : Tim Hall
-- Description  : Displays all ORDS modules.
-- Call Syntax  : @dba_ords_modules
-- Last Modified: 23/06/2025
-- -----------------------------------------------------------------------------------
column parsing_schema format a20
column module_name format a20
column uri_prefix format a20

select s.parsing_schema,
       m.id as module_id,
       m.name as module_name,
       m.uri_prefix,
       m.status
from   dba_ords_modules m
       join dba_ords_schemas s on s.id = schema_id
order by s.parsing_schema, m.name;

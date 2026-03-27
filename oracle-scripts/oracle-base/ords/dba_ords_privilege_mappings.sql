-- -----------------------------------------------------------------------------------
-- File Name    : https://oracle-base.com/dba/ords/dba_ords_privilege_mappings.sql
-- Author       : Tim Hall
-- Description  : Displays all ORDS privilege mappings.
-- Call Syntax  : @dba_ords_privilege_mappings
-- Last Modified: 23/06/2025
-- -----------------------------------------------------------------------------------
column privilege_name format a60
column pattern format a60

select s.parsing_schema, p.name as privilege_name, p.pattern
from   dba_ords_privilege_mappings p
       join dba_ords_schemas s on s.id = p.schema_id
order by s.parsing_schema, p.name;
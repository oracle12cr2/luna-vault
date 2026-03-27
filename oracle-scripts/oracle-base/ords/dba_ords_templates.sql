-- -----------------------------------------------------------------------------------
-- File Name    : https://oracle-base.com/dba/ords/dba_ords_templates.sql
-- Author       : Tim Hall
-- Description  : Displays all ORDS templates.
-- Call Syntax  : @dba_ords_templates
-- Last Modified: 23/06/2025
-- -----------------------------------------------------------------------------------
column parsing_schema format a20
column name format a20
column uri_template format a40

select s.parsing_schema,
       m.name as module_name,
       t.id as template_id,
       t.uri_template
from   dba_ords_templates t
       join dba_ords_modules m on m.id = t.module_id
       join dba_ords_schemas s on s.id = m.schema_id
order by s.parsing_schema, m.name, t.uri_template;
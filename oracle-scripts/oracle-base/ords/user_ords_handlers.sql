-- -----------------------------------------------------------------------------------
-- File Name    : https://oracle-base.com/dba/ords/user_ords_handlers.sql
-- Author       : Tim Hall
-- Description  : Displays all ORDS enabled handlers.
-- Call Syntax  : @user_ords_handlers
-- Last Modified: 23/06/2025
-- -----------------------------------------------------------------------------------
set linesize 200
column parsing_schema format a20
column source_type format a20
column source format a50

select s.parsing_schema,
       m.name as module_name,
       t.uri_template,
       h.id as handler_id,
       h.source_type,
       h.method
from   user_ords_handlers h
       join user_ords_templates t on t.id = h.template_id
       join user_ords_modules m on m.id = t.module_id
       join user_ords_schemas s on s.id = m.schema_id
order by s.parsing_schema, m.name, t.uri_template;
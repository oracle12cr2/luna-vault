-- -----------------------------------------------------------------------------------
-- File Name    : https://oracle-base.com/dba/ords/dba_ords_handler_content.sql
-- Author       : Tim Hall
-- Description  : Displays handler content.
-- Call Syntax  : @dba_ords_handler_content (handler-id)
-- Last Modified: 23/06/2025
-- -----------------------------------------------------------------------------------
set linesize 200 lone 1000000 verify off pagesize 100
column source format a100

select h.method,
       h.source
from   dba_ords_handlers h
where  h.id = &1
order by h.method;
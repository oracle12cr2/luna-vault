-- -----------------------------------------------------------------------------------
-- File Name    : https://oracle-base.com/dba/ords/dba_ords_clients.sql
-- Author       : Tim Hall
-- Description  : Displays all ORDS clients.
-- Call Syntax  : @dba_ords_clients
-- Last Modified: 23/06/2025
-- -----------------------------------------------------------------------------------
column name format a30
column client_secret format a30

select id, name, client_id, client_secret
from   dba_ords_clients
order by 1;
CREATE MATERIALIZED VIEW dbadmin.mv_source as          
select 'list_source' as rang, array_agg(distinct split_part(t_sources.desc_source, ' '::text, 1)) AS list_source 
from gn_synthese.t_sources
where t_sources.desc_source ilike '%[%]%'
group by 1 ;

-- View indexes:
CREATE INDEX mv_source_source_idx ON dbadmin.mv_source USING btree (list_source);
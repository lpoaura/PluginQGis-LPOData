
CREATE materialized VIEW dbadmin.mv_source AS (
select split_part(desc_source,' ',1) source, array_agg(id_source) 
FROM gn_synthese.t_sources
group by split_part(desc_source,' ',1));
create index on dbadmin.mv_source(source);
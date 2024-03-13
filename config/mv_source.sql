/**********************************************************************************************************************
 * 		Création de la vue permettant la récupération des sources de données
 **********************************************************************************************************************/
CREATE MATERIALIZED VIEW dbadmin.mv_source AS
SELECT 'list_source' AS rang, array_agg(DISTINCT split_part(t_sources.desc_source, ' '::text, 1)) AS list_source
FROM gn_synthese.t_sources
WHERE t_sources.desc_source ILIKE '%[%]%'
GROUP BY 1;

-- View indexes:
CREATE INDEX mv_source_source_idx ON dbadmin.mv_source USING btree (list_source);

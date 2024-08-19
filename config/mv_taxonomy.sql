/*****************************************************
 * 	   vue matérialisée permettant la consultation   *
 *     des listes de taxons par QGIS                 *
 *****************************************************/
CREATE MATERIALIZED VIEW dbadmin.mv_taxonomy
AS WITH taxa AS (
         SELECT DISTINCT tcse.taxo_group AS groupe_taxo,
            t.regne,
            t.phylum,
            t.classe,
            t.ordre,
            t.famille,
            t.group1_inpn,
            t.group2_inpn,
            t.cd_nom,
            t.cd_ref,
            t.lb_nom AS nom_sci,
            COALESCE(tcse.common_name, split_part(t.nom_vern::text, ','::text, 1)::character varying)::character varying(250) AS nom_vern
           FROM gn_synthese.synthese s
             LEFT JOIN src_lpodatas.t_c_synthese_extended tcse ON s.id_synthese = tcse.id_synthese
             JOIN taxonomie.taxref t ON s.cd_nom = t.cd_nom
        )
 SELECT 'groupe_taxo'::text AS rang,
    array_agg(DISTINCT taxa.groupe_taxo ORDER BY taxa.groupe_taxo) AS liste,
    NULL::json[] AS liste_object
   FROM taxa
UNION ALL
 SELECT 'regne'::text AS rang,
    array_agg(DISTINCT taxa.regne ORDER BY taxa.regne) AS liste,
    NULL::json[] AS liste_object
   FROM taxa
UNION ALL
 SELECT 'phylum'::text AS rang,
    array_agg(DISTINCT taxa.phylum ORDER BY taxa.phylum) AS liste,
    NULL::json[] AS liste_object
   FROM taxa
UNION ALL
 SELECT 'classe'::text AS rang,
    array_agg(DISTINCT taxa.classe ORDER BY taxa.classe) AS liste,
    NULL::json[] AS liste_object
   FROM taxa
UNION ALL
 SELECT 'ordre'::text AS rang,
    array_agg(DISTINCT taxa.ordre ORDER BY taxa.ordre) AS liste,
    NULL::json[] AS liste_object
   FROM taxa
UNION ALL
 SELECT 'famille'::text AS rang,
    array_agg(DISTINCT taxa.famille ORDER BY taxa.famille) AS liste,
    NULL::json[] AS liste_object
   FROM taxa
UNION ALL
 SELECT 'group1_inpn'::text AS rang,
    array_agg(DISTINCT taxa.group1_inpn ORDER BY taxa.group1_inpn) AS liste,
    NULL::json[] AS liste_object
   FROM taxa
UNION ALL
 SELECT 'group2_inpn'::text AS rang,
    array_agg(DISTINCT taxa.group2_inpn ORDER BY taxa.group2_inpn) AS liste,
    NULL::json[] AS liste_object
   FROM taxa
UNION ALL
 SELECT 'species'::text AS rang,
    NULL::text[] AS liste,
    array_agg(json_build_object('cd_ref', taxa.cd_ref, 'nom_vern', taxa.nom_vern, 'nom_sci', taxa.nom_sci)) AS liste_object
   FROM taxa
WITH DATA;

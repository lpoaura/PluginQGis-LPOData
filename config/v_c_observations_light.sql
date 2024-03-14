/**************************************************************************
 * 		vue permettant l'exécution des requêtes de synthèse du plugin     *
 **************************************************************************/
CREATE OR REPLACE VIEW src_lpodatas.v_c_observations_light AS
SELECT
    s.id_synthese,
    s.unique_id_sinp AS uuid,
    ts.name_source AS source,
    ts.desc_source,
    s.entity_source_pk_value AS
    source_id_data,
    se.id_sp_source AS source_id_sp,
    s.cd_nom,
    cor.cd_ref,
    cor.vn_id,
    cor.groupe_taxo_fr::character varying(50) AS groupe_taxo,
    cor.tx_group1_inpn::character varying(255) AS group1_inpn,
    cor.tx_group2_inpn::character varying(255) AS
    group2_inpn,
    cor.tx_classe::character varying(50) AS classe,
    cor.tx_id_rang::character varying(10) AS id_rang,
    se.taxo_real AS taxon_vrai,
    s.observers AS observateur,
    se.pseudo_observer_uid,
    se.bird_breed_code AS oiso_code_nidif,
    se.breed_status AS
    statut_repro, se.bat_breed_colo AS cs_colo_repro,
    se.bat_is_gite AS cs_is_gite,
    se.bat_period AS cs_periode,
    s.count_max AS nombre_total,
    se.estimation_code AS
    code_estimation, s.date_min AS date,
    s.date_min::date AS date_jour,
    s.date_min::time without time zone AS heure,
    EXTRACT(YEAR FROM s.date_min)::integer
    AS date_an,
    s.altitude_max AS altitude,
    se.mortality AS mortalite,
    se.mortality_cause AS mortalite_cause,
    s.the_geom_local AS geom,
    se.export_excluded AS exp_excl,
    se.project_code AS code_etude,
    s.comment_description AS comment,
    se.private_comment
    AS comment_priv, se.juridical_person AS pers_morale,
    se.behaviour::text AS comportement,
    se.geo_accuracy AS "precision",
    se.details::text AS details,
    se.place,
    se.id_form
    AS id_formulaire,
    s.meta_update_date AS derniere_maj,
    se.is_hidden AS donnee_cachee,
    s.reference_biblio,
    COALESCE(
        cor.vn_nom_fr,
        cor.tx_nom_fr
    ) AS nom_vern, COALESCE(cor.vn_nom_sci, cor.tx_nom_sci
    ) AS nom_sci,
    ST_GEOMETRYTYPE(s.the_geom_local) AS type_geom,
    s.id_nomenclature_valid_status
    = ANY(ARRAY[ref_nomenclatures.get_id_nomenclature(
        'STATUT_VALID'::character varying, '2'::character
        varying
    ),
    ref_nomenclatures.get_id_nomenclature(
        'STATUT_VALID'::character varying, '1'::character
        varying
    )]) AS is_valid,
    s.id_nomenclature_observation_status
    = ref_nomenclatures.get_id_nomenclature(
        'STATUT_OBS'::character varying, 'Pr'::character varying
    ) AS is_present,
    ST_ASEWKT(s.the_geom_local) AS geom_ekt
FROM gn_synthese.synthese AS s
LEFT JOIN
    src_lpodatas.t_c_synthese_extended AS se
    ON s.id_synthese = se.id_synthese
INNER JOIN gn_synthese.t_sources AS ts ON s.id_source = ts.id_source
LEFT JOIN taxonomie.taxref AS t ON s.cd_nom = t.cd_nom
LEFT JOIN taxonomie.mv_c_cor_vn_taxref AS cor ON
    cor.cd_nom = t.cd_ref
    AND cor.cd_nom IS NOT NULL;

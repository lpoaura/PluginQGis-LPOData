/***************************************************************************
*       Creation de la vue v_c_observations                                *
***************************************************************************/

/* objectif : vue structurant les données pour faciliter le requetage*/

-- src_lpodatas.v_c_observations source

-- src_lpodatas.v_c_observations source

drop view if exists src_lpodatas.v_c_observations;
CREATE OR REPLACE VIEW src_lpodatas.v_c_observations
AS SELECT DISTINCT s.id_synthese,
    s.unique_id_sinp AS uuid,
    ts.name_source AS source,
    ts.desc_source,
    s.entity_source_pk_value AS source_id_data,
    se.id_sp_source AS source_id_sp,
    s.cd_nom AS taxref_cdnom,
    s.cd_nom,
    t.cd_ref,
    se.taxo_group AS groupe_taxo,
    t.group1_inpn,
    t.group2_inpn,
    se.taxo_real AS taxon_vrai,
    cor.vn_nom_fr AS nom_vern,
    t.lb_nom AS nom_sci,
    s.observers AS observateur,
    se.pseudo_observer_uid,
    se.bird_breed_code AS oiso_code_nidif,
    se.bird_breed_status AS oiso_statut_nidif,
    se.bat_breed_colo AS cs_colo_repro,
    se.bat_is_gite AS cs_is_gite,
    se.bat_period AS cs_periode,
    s.count_max AS nombre_total,
    se.estimation_code AS code_estimation,
    s.date_min AS date,
	s.date_min::date AS date_jour,
    s.date_min::time AS heure,
    EXTRACT(year FROM s.date_min)::integer AS date_an,
    s.altitude_max AS altitude,
    se.mortality AS mortalite,
    se.mortality_cause AS mortalite_cause,
    s.the_geom_local AS geom,
    se.export_excluded AS exp_excl,
    se.project_code AS code_etude,
    s.comment_description AS comment,
    se.private_comment AS comment_priv,
    fj.item ->> 'comment'::text AS comment_forms,
    se.juridical_person AS pers_morale,
    se.behaviour::text AS comportement,
    se.geo_accuracy AS "precision",
    se.details::text AS details,
    se.place,
    se.id_form AS id_formulaire,
    s.meta_update_date AS derniere_maj,
    s.id_nomenclature_valid_status = ANY (ARRAY[ref_nomenclatures.get_id_nomenclature('STATUT_VALID'::character varying, '2'::character varying), ref_nomenclatures.get_id_nomenclature('STATUT_VALID'::character varying, '1'::character varying)]) AS is_valid,
    se.is_hidden AS donnee_cachee,
    s.id_nomenclature_observation_status = ref_nomenclatures.get_id_nomenclature('STATUT_OBS'::character varying, 'Pr'::character varying) AS is_present,
    s.reference_biblio,
    st_asewkt(s.the_geom_local) AS geom_ekt
   FROM gn_synthese.synthese s
     LEFT JOIN src_lpodatas.t_c_synthese_extended se ON s.id_synthese = se.id_synthese
     JOIN gn_synthese.t_sources ts ON s.id_source = ts.id_source
     JOIN taxonomie.taxref t ON s.cd_nom = t.cd_nom
     LEFT JOIN src_vn_json.forms_json fj ON (fj.item ->> 'id_form_universal'::text) = se.id_form::text AND fj.site::text = ts.name_source::text
     LEFT JOIN taxonomie.mv_c_cor_vn_taxref cor ON cor.cd_nom = s.cd_nom;

-- Permissions

ALTER TABLE src_lpodatas.v_c_observations OWNER TO dbadmin;
GRANT ALL ON TABLE src_lpodatas.v_c_observations TO postgres;
GRANT ALL ON TABLE src_lpodatas.v_c_observations TO dbadmin;
GRANT SELECT ON TABLE src_lpodatas.v_c_observations TO dt;
GRANT ALL ON TABLE src_lpodatas.v_c_observations TO advanced_user;
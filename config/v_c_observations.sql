/***************************************************************************
*       Creation de la vue v_c_observations                                *
***************************************************************************/

/* objectif : vue structurant les données pour faciliter le requetage*/


CREATE OR REPLACE VIEW src_lpodatas.v_c_observations
AS SELECT s.id_synthese,
    s.unique_id_sinp AS uuid,
    ts.name_source AS source,
    ts.desc_source,
    s.entity_source_pk_value AS source_id_data,
    se.id_sp_source AS source_id_sp,
    s.cd_nom AS taxref_cdnom,
    s.cd_nom,
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
    split_part(s.date_min::text, ' '::text, 1)::date AS date,
    split_part(s.date_min::text, ' '::text, 2)::time without time zone AS heure,
    se.date_year AS date_an,
    s.altitude_max AS altitude,
    se.mortality AS mortalite,
    se.mortality_cause AS mortalite_cause,
    s.the_geom_local AS geom,
    se.export_excluded AS exp_excl,
    se.project_code AS code_etude,
    s.comment_description AS commentaires,
    se.private_comment AS commentaires_prives,
    fj.item ->> 'comment'::text AS commentaires_formulaire,
    se.juridical_person AS pers_morale,
    se.behaviour AS comportement,
    se.geo_accuracy AS "precision",
    se.details,
    se.place,
    se.id_form AS id_formulaire,
    s.meta_update_date AS derniere_maj,
    (s.id_nomenclature_valid_status IN ( SELECT t_nomenclatures.id_nomenclature
           FROM ref_nomenclatures.t_nomenclatures
          WHERE t_nomenclatures.id_type = ref_nomenclatures.get_id_nomenclature_type('STATUT_VALID'::character varying) AND (t_nomenclatures.cd_nomenclature::text = ANY (ARRAY['1'::character varying::text, '2'::character varying::text])))) AS is_valid,
    se.is_hidden AS donnee_cachee,
    s.id_nomenclature_observation_status = ref_nomenclatures.get_id_nomenclature('STATUT_OBS'::character varying, 'Pr'::character varying) AS is_present,
    s.reference_biblio,
    st_x(s.the_geom_local) AS x_l93,
    st_y(s.the_geom_local) AS y_l93
   FROM gn_synthese.synthese s
     LEFT JOIN src_lpodatas.t_c_synthese_extended se ON s.id_synthese = se.id_synthese
     JOIN gn_synthese.t_sources ts ON s.id_source = ts.id_source
     JOIN taxonomie.taxref t ON s.cd_nom = t.cd_nom
     JOIN import_vn.forms_json fj ON (fj.item ->> 'id_form_universal'::character varying::text) = se.id_form::text AND fj.site::text = ts.name_source::text
     LEFT JOIN taxonomie.v_cor_vn_taxref cor ON s.cd_nom = cor.cd_nom;
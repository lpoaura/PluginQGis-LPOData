/***************************************************************************
*       Creation de la vue v_c_observations                                *
***************************************************************************/

/* objectif : vue structurant les données pour faciliter le requetage*/

DROP VIEW src_lpodatas.v_c_observations_dev;
CREATE OR REPLACE VIEW src_lpodatas.v_c_observations_dev
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
    se.behaviour::text AS comportement,
    se.geo_accuracy AS "precision",
    se.details::text,
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

-- Permissions

ALTER TABLE src_lpodatas.v_c_observations_dev OWNER TO geonature;
GRANT ALL ON TABLE src_lpodatas.v_c_observations_dev TO geonature;
GRANT ALL ON TABLE src_lpodatas.v_c_observations_dev TO advanced_user;
GRANT ALL ON TABLE src_lpodatas.v_c_observations_dev TO postgres;
GRANT DELETE, SELECT, INSERT, UPDATE ON TABLE src_lpodatas.v_c_observations_dev TO readonly;
GRANT SELECT ON TABLE src_lpodatas.v_c_observations_dev TO common_user;
GRANT REFERENCES(id_synthese) ON src_lpodatas.v_c_observations_dev TO postgres WITH GRANT OPTION;
GRANT UPDATE(id_synthese) ON src_lpodatas.v_c_observations_dev TO readonly;
GRANT REFERENCES(id_synthese) ON src_lpodatas.v_c_observations_dev TO advanced_user;
GRANT REFERENCES(id_synthese) ON src_lpodatas.v_c_observations_dev TO geonature WITH GRANT OPTION;
GRANT SELECT(id_synthese) ON src_lpodatas.v_c_observations_dev TO common_user;
GRANT REFERENCES(uuid) ON src_lpodatas.v_c_observations_dev TO postgres WITH GRANT OPTION;
GRANT SELECT(uuid) ON src_lpodatas.v_c_observations_dev TO common_user;
GRANT REFERENCES(uuid) ON src_lpodatas.v_c_observations_dev TO advanced_user;
GRANT REFERENCES(uuid) ON src_lpodatas.v_c_observations_dev TO geonature WITH GRANT OPTION;
GRANT UPDATE(uuid) ON src_lpodatas.v_c_observations_dev TO readonly;
GRANT REFERENCES("source") ON src_lpodatas.v_c_observations_dev TO postgres WITH GRANT OPTION;
GRANT REFERENCES("source") ON src_lpodatas.v_c_observations_dev TO advanced_user;
GRANT UPDATE("source") ON src_lpodatas.v_c_observations_dev TO readonly;
GRANT REFERENCES("source") ON src_lpodatas.v_c_observations_dev TO geonature WITH GRANT OPTION;
GRANT SELECT("source") ON src_lpodatas.v_c_observations_dev TO common_user;
GRANT REFERENCES(source_id_data) ON src_lpodatas.v_c_observations_dev TO geonature WITH GRANT OPTION;
GRANT UPDATE(source_id_data) ON src_lpodatas.v_c_observations_dev TO readonly;
GRANT REFERENCES(source_id_data) ON src_lpodatas.v_c_observations_dev TO postgres WITH GRANT OPTION;
GRANT REFERENCES(source_id_data) ON src_lpodatas.v_c_observations_dev TO advanced_user;
GRANT SELECT(source_id_data) ON src_lpodatas.v_c_observations_dev TO common_user;
GRANT REFERENCES(source_id_sp) ON src_lpodatas.v_c_observations_dev TO postgres WITH GRANT OPTION;
GRANT REFERENCES(source_id_sp) ON src_lpodatas.v_c_observations_dev TO advanced_user;
GRANT SELECT(source_id_sp) ON src_lpodatas.v_c_observations_dev TO common_user;
GRANT UPDATE(source_id_sp) ON src_lpodatas.v_c_observations_dev TO readonly;
GRANT REFERENCES(source_id_sp) ON src_lpodatas.v_c_observations_dev TO geonature WITH GRANT OPTION;
GRANT REFERENCES(taxref_cdnom) ON src_lpodatas.v_c_observations_dev TO postgres WITH GRANT OPTION;
GRANT UPDATE(taxref_cdnom) ON src_lpodatas.v_c_observations_dev TO readonly;
GRANT REFERENCES(taxref_cdnom) ON src_lpodatas.v_c_observations_dev TO advanced_user;
GRANT SELECT(taxref_cdnom) ON src_lpodatas.v_c_observations_dev TO common_user;
GRANT REFERENCES(taxref_cdnom) ON src_lpodatas.v_c_observations_dev TO geonature WITH GRANT OPTION;
GRANT UPDATE(groupe_taxo) ON src_lpodatas.v_c_observations_dev TO readonly;
GRANT REFERENCES(groupe_taxo) ON src_lpodatas.v_c_observations_dev TO postgres WITH GRANT OPTION;
GRANT REFERENCES(groupe_taxo) ON src_lpodatas.v_c_observations_dev TO geonature WITH GRANT OPTION;
GRANT REFERENCES(groupe_taxo) ON src_lpodatas.v_c_observations_dev TO advanced_user;
GRANT SELECT(groupe_taxo) ON src_lpodatas.v_c_observations_dev TO common_user;
GRANT REFERENCES(group1_inpn) ON src_lpodatas.v_c_observations_dev TO advanced_user;
GRANT REFERENCES(group1_inpn) ON src_lpodatas.v_c_observations_dev TO postgres WITH GRANT OPTION;
GRANT REFERENCES(group1_inpn) ON src_lpodatas.v_c_observations_dev TO geonature WITH GRANT OPTION;
GRANT SELECT(group1_inpn) ON src_lpodatas.v_c_observations_dev TO common_user;
GRANT UPDATE(group1_inpn) ON src_lpodatas.v_c_observations_dev TO readonly;
GRANT REFERENCES(group2_inpn) ON src_lpodatas.v_c_observations_dev TO geonature WITH GRANT OPTION;
GRANT REFERENCES(group2_inpn) ON src_lpodatas.v_c_observations_dev TO advanced_user;
GRANT REFERENCES(group2_inpn) ON src_lpodatas.v_c_observations_dev TO postgres WITH GRANT OPTION;
GRANT UPDATE(group2_inpn) ON src_lpodatas.v_c_observations_dev TO readonly;
GRANT SELECT(group2_inpn) ON src_lpodatas.v_c_observations_dev TO common_user;
GRANT REFERENCES(taxon_vrai) ON src_lpodatas.v_c_observations_dev TO advanced_user;
GRANT UPDATE(taxon_vrai) ON src_lpodatas.v_c_observations_dev TO readonly;
GRANT REFERENCES(taxon_vrai) ON src_lpodatas.v_c_observations_dev TO geonature WITH GRANT OPTION;
GRANT REFERENCES(taxon_vrai) ON src_lpodatas.v_c_observations_dev TO postgres WITH GRANT OPTION;
GRANT SELECT(taxon_vrai) ON src_lpodatas.v_c_observations_dev TO common_user;
GRANT REFERENCES(nom_vern) ON src_lpodatas.v_c_observations_dev TO geonature WITH GRANT OPTION;
GRANT UPDATE(nom_vern) ON src_lpodatas.v_c_observations_dev TO readonly;
GRANT REFERENCES(nom_vern) ON src_lpodatas.v_c_observations_dev TO advanced_user;
GRANT SELECT(nom_vern) ON src_lpodatas.v_c_observations_dev TO common_user;
GRANT REFERENCES(nom_vern) ON src_lpodatas.v_c_observations_dev TO postgres WITH GRANT OPTION;
GRANT SELECT(nom_sci) ON src_lpodatas.v_c_observations_dev TO common_user;
GRANT REFERENCES(nom_sci) ON src_lpodatas.v_c_observations_dev TO postgres WITH GRANT OPTION;
GRANT REFERENCES(nom_sci) ON src_lpodatas.v_c_observations_dev TO advanced_user;
GRANT UPDATE(nom_sci) ON src_lpodatas.v_c_observations_dev TO readonly;
GRANT REFERENCES(nom_sci) ON src_lpodatas.v_c_observations_dev TO geonature WITH GRANT OPTION;
GRANT UPDATE(observateur) ON src_lpodatas.v_c_observations_dev TO readonly;
GRANT SELECT(observateur) ON src_lpodatas.v_c_observations_dev TO common_user;
GRANT REFERENCES(observateur) ON src_lpodatas.v_c_observations_dev TO advanced_user;
GRANT REFERENCES(observateur) ON src_lpodatas.v_c_observations_dev TO postgres WITH GRANT OPTION;
GRANT REFERENCES(observateur) ON src_lpodatas.v_c_observations_dev TO geonature WITH GRANT OPTION;
GRANT UPDATE(pseudo_observer_uid) ON src_lpodatas.v_c_observations_dev TO readonly;
GRANT REFERENCES(pseudo_observer_uid) ON src_lpodatas.v_c_observations_dev TO advanced_user;
GRANT REFERENCES(pseudo_observer_uid) ON src_lpodatas.v_c_observations_dev TO geonature WITH GRANT OPTION;
GRANT REFERENCES(pseudo_observer_uid) ON src_lpodatas.v_c_observations_dev TO postgres WITH GRANT OPTION;
GRANT SELECT(pseudo_observer_uid) ON src_lpodatas.v_c_observations_dev TO common_user;
GRANT REFERENCES(oiso_code_nidif) ON src_lpodatas.v_c_observations_dev TO geonature WITH GRANT OPTION;
GRANT REFERENCES(oiso_code_nidif) ON src_lpodatas.v_c_observations_dev TO postgres WITH GRANT OPTION;
GRANT REFERENCES(oiso_code_nidif) ON src_lpodatas.v_c_observations_dev TO advanced_user;
GRANT UPDATE(oiso_code_nidif) ON src_lpodatas.v_c_observations_dev TO readonly;
GRANT SELECT(oiso_code_nidif) ON src_lpodatas.v_c_observations_dev TO common_user;
GRANT REFERENCES(oiso_statut_nidif) ON src_lpodatas.v_c_observations_dev TO geonature WITH GRANT OPTION;
GRANT REFERENCES(oiso_statut_nidif) ON src_lpodatas.v_c_observations_dev TO advanced_user;
GRANT UPDATE(oiso_statut_nidif) ON src_lpodatas.v_c_observations_dev TO readonly;
GRANT SELECT(oiso_statut_nidif) ON src_lpodatas.v_c_observations_dev TO common_user;
GRANT REFERENCES(oiso_statut_nidif) ON src_lpodatas.v_c_observations_dev TO postgres WITH GRANT OPTION;
GRANT UPDATE(cs_colo_repro) ON src_lpodatas.v_c_observations_dev TO readonly;
GRANT REFERENCES(cs_colo_repro) ON src_lpodatas.v_c_observations_dev TO advanced_user;
GRANT REFERENCES(cs_colo_repro) ON src_lpodatas.v_c_observations_dev TO postgres WITH GRANT OPTION;
GRANT REFERENCES(cs_colo_repro) ON src_lpodatas.v_c_observations_dev TO geonature WITH GRANT OPTION;
GRANT SELECT(cs_colo_repro) ON src_lpodatas.v_c_observations_dev TO common_user;
GRANT REFERENCES(cs_is_gite) ON src_lpodatas.v_c_observations_dev TO advanced_user;
GRANT UPDATE(cs_is_gite) ON src_lpodatas.v_c_observations_dev TO readonly;
GRANT REFERENCES(cs_is_gite) ON src_lpodatas.v_c_observations_dev TO postgres WITH GRANT OPTION;
GRANT REFERENCES(cs_is_gite) ON src_lpodatas.v_c_observations_dev TO geonature WITH GRANT OPTION;
GRANT SELECT(cs_is_gite) ON src_lpodatas.v_c_observations_dev TO common_user;
GRANT REFERENCES(cs_periode) ON src_lpodatas.v_c_observations_dev TO postgres WITH GRANT OPTION;
GRANT REFERENCES(cs_periode) ON src_lpodatas.v_c_observations_dev TO advanced_user;
GRANT REFERENCES(cs_periode) ON src_lpodatas.v_c_observations_dev TO geonature WITH GRANT OPTION;
GRANT UPDATE(cs_periode) ON src_lpodatas.v_c_observations_dev TO readonly;
GRANT SELECT(cs_periode) ON src_lpodatas.v_c_observations_dev TO common_user;
GRANT REFERENCES(nombre_total) ON src_lpodatas.v_c_observations_dev TO advanced_user;
GRANT UPDATE(nombre_total) ON src_lpodatas.v_c_observations_dev TO readonly;
GRANT REFERENCES(nombre_total) ON src_lpodatas.v_c_observations_dev TO geonature WITH GRANT OPTION;
GRANT REFERENCES(nombre_total) ON src_lpodatas.v_c_observations_dev TO postgres WITH GRANT OPTION;
GRANT SELECT(nombre_total) ON src_lpodatas.v_c_observations_dev TO common_user;
GRANT UPDATE(code_estimation) ON src_lpodatas.v_c_observations_dev TO readonly;
GRANT REFERENCES(code_estimation) ON src_lpodatas.v_c_observations_dev TO postgres WITH GRANT OPTION;
GRANT REFERENCES(code_estimation) ON src_lpodatas.vCREATE OR REPLACE VIEW src_lpodatas.v_c_observations_dev
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
    se.behaviour::text AS comportement,
    se.geo_accuracy AS "precision",
    se.details::text,
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

-- Permissions

ALTER TABLE src_lpodatas.v_c_observations_dev OWNER TO geonature;
GRANT ALL ON TABLE src_lpodatas.v_c_observations_dev TO geonature;
GRANT ALL ON TABLE src_lpodatas.v_c_observations_dev TO advanced_user;
GRANT ALL ON TABLE src_lpodatas.v_c_observations_dev TO postgres;
GRANT DELETE, SELECT, INSERT, UPDATE ON TABLE src_lpodatas.v_c_observations_dev TO readonly;
GRANT SELECT ON TABLE src_lpodatas.v_c_observations_dev TO common_user;
GRANT REFERENCES(id_synthese) ON src_lpodatas.v_c_observations_dev TO postgres WITH GRANT OPTION;
GRANT UPDATE(id_synthese) ON src_lpodatas.v_c_observations_dev TO readonly;
GRANT REFERENCES(id_synthese) ON src_lpodatas.v_c_observations_dev TO advanced_user;
GRANT REFERENCES(id_synthese) ON src_lpodatas.v_c_observations_dev TO geonature WITH GRANT OPTION;
GRANT SELECT(id_synthese) ON src_lpodatas.v_c_observations_dev TO common_user;
GRANT REFERENCES(uuid) ON src_lpodatas.v_c_observations_dev TO postgres WITH GRANT OPTION;
GRANT SELECT(uuid) ON src_lpodatas.v_c_observations_dev TO common_user;
GRANT REFERENCES(uuid) ON src_lpodatas.v_c_observations_dev TO advanced_user;
GRANT REFERENCES(uuid) ON src_lpodatas.v_c_observations_dev TO geonature WITH GRANT OPTION;
GRANT UPDATE(uuid) ON src_lpodatas.v_c_observations_dev TO readonly;
GRANT REFERENCES("source") ON src_lpodatas.v_c_observations_dev TO postgres WITH GRANT OPTION;
GRANT REFERENCES("source") ON src_lpodatas.v_c_observations_dev TO advanced_user;
GRANT UPDATE("source") ON src_lpodatas.v_c_observations_dev TO readonly;
GRANT REFERENCES("source") ON src_lpodatas.v_c_observations_dev TO geonature WITH GRANT OPTION;
GRANT SELECT("source") ON src_lpodatas.v_c_observations_dev TO common_user;
GRANT REFERENCES(source_id_data) ON src_lpodatas.v_c_observations_dev TO geonature WITH GRANT OPTION;
GRANT UPDATE(source_id_data) ON src_lpodatas.v_c_observations_dev TO readonly;
GRANT REFERENCES(source_id_data) ON src_lpodatas.v_c_observations_dev TO postgres WITH GRANT OPTION;
GRANT REFERENCES(source_id_data) ON src_lpodatas.v_c_observations_dev TO advanced_user;
GRANT SELECT(source_id_data) ON src_lpodatas.v_c_observations_dev TO common_user;
GRANT REFERENCES(source_id_sp) ON src_lpodatas.v_c_observations_dev TO postgres WITH GRANT OPTION;
GRANT REFERENCES(source_id_sp) ON src_lpodatas.v_c_observations_dev TO advanced_user;
GRANT SELECT(source_id_sp) ON src_lpodatas.v_c_observations_dev TO common_user;
GRANT UPDATE(source_id_sp) ON src_lpodatas.v_c_observations_dev TO readonly;
GRANT REFERENCES(source_id_sp) ON src_lpodatas.v_c_observations_dev TO geonature WITH GRANT OPTION;
GRANT REFERENCES(taxref_cdnom) ON src_lpodatas.v_c_observations_dev TO postgres WITH GRANT OPTION;
GRANT UPDATE(taxref_cdnom) ON src_lpodatas.v_c_observations_dev TO readonly;
GRANT REFERENCES(taxref_cdnom) ON src_lpodatas.v_c_observations_dev TO advanced_user;
GRANT SELECT(taxref_cdnom) ON src_lpodatas.v_c_observations_dev TO common_user;
GRANT REFERENCES(taxref_cdnom) ON src_lpodatas.v_c_observations_dev TO geonature WITH GRANT OPTION;
GRANT UPDATE(groupe_taxo) ON src_lpodatas.v_c_observations_dev TO readonly;
GRANT REFERENCES(groupe_taxo) ON src_lpodatas.v_c_observations_dev TO postgres WITH GRANT OPTION;
GRANT REFERENCES(groupe_taxo) ON src_lpodatas.v_c_observations_dev TO geonature WITH GRANT OPTION;
GRANT REFERENCES(groupe_taxo) ON src_lpodatas.v_c_observations_dev TO advanced_user;
GRANT SELECT(groupe_taxo) ON src_lpodatas.v_c_observations_dev TO common_user;
GRANT REFERENCES(group1_inpn) ON src_lpodatas.v_c_observations_dev TO advanced_user;
GRANT REFERENCES(group1_inpn) ON src_lpodatas.v_c_observations_dev TO postgres WITH GRANT OPTION;
GRANT REFERENCES(group1_inpn) ON src_lpodatas.v_c_observations_dev TO geonature WITH GRANT OPTION;
GRANT SELECT(group1_inpn) ON src_lpodatas.v_c_observations_dev TO common_user;
GRANT UPDATE(group1_inpn) ON src_lpodatas.v_c_observations_dev TO readonly;
GRANT REFERENCES(group2_inpn) ON src_lpodatas.v_c_observations_dev TO geonature WITH GRANT OPTION;
GRANT REFERENCES(group2_inpn) ON src_lpodatas.v_c_observations_dev TO advanced_user;
GRANT REFERENCES(group2_inpn) ON src_lpodatas.v_c_observations_dev TO postgres WITH GRANT OPTION;
GRANT UPDATE(group2_inpn) ON src_lpodatas.v_c_observations_dev TO readonly;
GRANT SELECT(group2_inpn) ON src_lpodatas.v_c_observations_dev TO common_user;
GRANT REFERENCES(taxon_vrai) ON src_lpodatas.v_c_observations_dev TO advanced_user;
GRANT UPDATE(taxon_vrai) ON src_lpodatas.v_c_observations_dev TO readonly;
GRANT REFERENCES(taxon_vrai) ON src_lpodatas.v_c_observations_dev TO geonature WITH GRANT OPTION;
GRANT REFERENCES(taxon_vrai) ON src_lpodatas.v_c_observations_dev TO postgres WITH GRANT OPTION;
GRANT SELECT(taxon_vrai) ON src_lpodatas.v_c_observations_dev TO common_user;
GRANT REFERENCES(nom_vern) ON src_lpodatas.v_c_observations_dev TO geonature WITH GRANT OPTION;
GRANT UPDATE(nom_vern) ON src_lpodatas.v_c_observations_dev TO readonly;
GRANT REFERENCES(nom_vern) ON src_lpodatas.v_c_observations_dev TO advanced_user;
GRANT SELECT(nom_vern) ON src_lpodatas.v_c_observations_dev TO common_user;
GRANT REFERENCES(nom_vern) ON src_lpodatas.v_c_observations_dev TO postgres WITH GRANT OPTION;
GRANT SELECT(nom_sci) ON src_lpodatas.v_c_observations_dev TO common_user;
GRANT REFERENCES(nom_sci) ON src_lpodatas.v_c_observations_dev TO postgres WITH GRANT OPTION;
GRANT REFERENCES(nom_sci) ON src_lpodatas.v_c_observations_dev TO advanced_user;
GRANT UPDATE(nom_sci) ON src_lpodatas.v_c_observations_dev TO readonly;
GRANT REFERENCES(nom_sci) ON src_lpodatas.v_c_observations_dev TO geonature WITH GRANT OPTION;
GRANT UPDATE(observateur) ON src_lpodatas.v_c_observations_dev TO readonly;
GRANT SELECT(observateur) ON src_lpodatas.v_c_observations_dev TO common_user;
GRANT REFERENCES(observateur) ON src_lpodatas.v_c_observations_dev TO advanced_user;
GRANT REFERENCES(observateur) ON src_lpodatas.v_c_observations_dev TO postgres WITH GRANT OPTION;
GRANT REFERENCES(observateur) ON src_lpodatas.v_c_observations_dev TO geonature WITH GRANT OPTION;
GRANT UPDATE(pseudo_observer_uid) ON src_lpodatas.v_c_observations_dev TO readonly;
GRANT REFERENCES(pseudo_observer_uid) ON src_lpodatas.v_c_observations_dev TO advanced_user;
GRANT REFERENCES(pseudo_observer_uid) ON src_lpodatas.v_c_observations_dev TO geonature WITH GRANT OPTION;
GRANT REFERENCES(pseudo_observer_uid) ON src_lpodatas.v_c_observations_dev TO postgres WITH GRANT OPTION;
GRANT SELECT(pseudo_observer_uid) ON src_lpodatas.v_c_observations_dev TO common_user;
GRANT REFERENCES(oiso_code_nidif) ON src_lpodatas.v_c_observations_dev TO geonature WITH GRANT OPTION;
GRANT REFERENCES(oiso_code_nidif) ON src_lpodatas.v_c_observations_dev TO postgres WITH GRANT OPTION;
GRANT REFERENCES(oiso_code_nidif) ON src_lpodatas.v_c_observations_dev TO advanced_user;
GRANT UPDATE(oiso_code_nidif) ON src_lpodatas.v_c_observations_dev TO readonly;
GRANT SELECT(oiso_code_nidif) ON src_lpodatas.v_c_observations_dev TO common_user;
GRANT REFERENCES(oiso_statut_nidif) ON src_lpodatas.v_c_observations_dev TO geonature WITH GRANT OPTION;
GRANT REFERENCES(oiso_statut_nidif) ON src_lpodatas.v_c_observations_dev TO advanced_user;
GRANT UPDATE(oiso_statut_nidif) ON src_lpodatas.v_c_observations_dev TO readonly;
GRANT SELECT(oiso_statut_nidif) ON src_lpodatas.v_c_observations_dev TO common_user;
GRANT REFERENCES(oiso_statut_nidif) ON src_lpodatas.v_c_observations_dev TO postgres WITH GRANT OPTION;
GRANT UPDATE(cs_colo_repro) ON src_lpodatas.v_c_observations_dev TO readonly;
GRANT REFERENCES(cs_colo_repro) ON src_lpodatas.v_c_observations_dev TO advanced_user;
GRANT REFERENCES(cs_colo_repro) ON src_lpodatas.v_c_observations_dev TO postgres WITH GRANT OPTION;
GRANT REFERENCES(cs_colo_repro) ON src_lpodatas.v_c_observations_dev TO geonature WITH GRANT OPTION;
GRANT SELECT(cs_colo_repro) ON src_lpodatas.v_c_observations_dev TO common_user;
GRANT REFERENCES(cs_is_gite) ON src_lpodatas.v_c_observations_dev TO advanced_user;
GRANT UPDATE(cs_is_gite) ON src_lpodatas.v_c_observations_dev TO readonly;
GRANT REFERENCES(cs_is_gite) ON src_lpodatas.v_c_observations_dev TO postgres WITH GRANT OPTION;
GRANT REFERENCES(cs_is_gite) ON src_lpodatas.v_c_observations_dev TO geonature WITH GRANT OPTION;
GRANT SELECT(cs_is_gite) ON src_lpodatas.v_c_observations_dev TO common_user;
GRANT REFERENCES(cs_periode) ON src_lpodatas.v_c_observations_dev TO postgres WITH GRANT OPTION;
GRANT REFERENCES(cs_periode) ON src_lpodatas.v_c_observations_dev TO advanced_user;
GRANT REFERENCES(cs_periode) ON src_lpodatas.v_c_observations_dev TO geonature WITH GRANT OPTION;
GRANT UPDATE(cs_periode) ON src_lpodatas.v_c_observations_dev TO readonly;
GRANT SELECT(cs_periode) ON src_lpodatas.v_c_observations_dev TO common_user;
GRANT REFERENCES(nombre_total) ON src_lpodatas.v_c_observations_dev TO advanced_user;
GRANT UPDATE(nombre_total) ON src_lpodatas.v_c_observations_dev TO readonly;
GRANT REFERENCES(nombre_total) ON src_lpodatas.v_c_observations_dev TO geonature WITH GRANT OPTION;
GRANT REFERENCES(nombre_total) ON src_lpodatas.v_c_observations_dev TO postgres WITH GRANT OPTION;
GRANT SELECT(nombre_total) ON src_lpodatas.v_c_observations_dev TO common_user;
GRANT UPDATE(code_estimation) ON src_lpodatas.v_c_observations_dev TO readonly;
GRANT REFERENCES(code_estimation) ON src_lpodatas.v_c_observations_dev TO postgres WITH GRANT OPTION;
GRANT REFERENCES(code_estimation) ON src_lpodatas.v_c_observations_dev TO geonature WITH GRANT OPTION;
GRANT REFERENCES(code_estimation) ON src_lpodatas.v_c_observations_dev TO advanced_user;
GRANT SELECT(code_estimation) ON src_lpodatas.v_c_observations_dev TO common_user;
GRANT SELECT("date") ON src_lpodatas.v_c_observations_dev TO common_user;
GRANT REFERENCES("date") ON src_lpodatas.v_c_observations_dev TO geonature WITH GRANT OPTION;
GRANT REFERENCES("date") ON src_lpodatas.v_c_observations_dev TO postgres WITH GRANT OPTION;
GRANT UPDATE("date") ON src_lpodatas.v_c_observations_dev TO readonly;
GRANT REFERENCES("date") ON src_lpodatas.v_c_observations_dev TO advanced_user;
GRANT REFERENCES(date_an) ON src_lpodatas.v_c_observations_dev TO advanced_user;
GRANT REFERENCES(date_an) ON src_lpodatas.v_c_observations_dev TO postgres WITH GRANT OPTION;
GRANT UPDATE(date_an) ON src_lpodatas.v_c_observations_dev TO readonly;
GRANT REFERENCES(date_an) ON src_lpodatas.v_c_observations_dev TO geonature WITH GRANT OPTION;
GRANT SELECT(date_an) ON src_lpodatas.v_c_observations_dev TO common_user;
GRANT UPDATE(altitude) ON src_lpodatas.v_c_observations_dev TO readonly;
GRANT REFERENCES(altitude) ON src_lpodatas.v_c_observations_dev TO postgres WITH GRANT OPTION;
GRANT REFERENCES(altitude) ON src_lpodatas.v_c_observations_dev TO geonature WITH GRANT OPTION;
GRANT REFERENCES(altitude) ON src_lpodatas.v_c_observations_dev TO advanced_user;
GRANT SELECT(altitude) ON src_lpodatas.v_c_observations_dev TO common_user;
GRANT REFERENCES(mortalite) ON src_lpodatas.v_c_observations_dev TO advanced_user;
GRANT REFERENCES(mortalite) ON src_lpodatas.v_c_observations_dev TO postgres WITH GRANT OPTION;
GRANT UPDATE(mortalite) ON src_lpodatas.v_c_observations_dev TO readonly;
GRANT SELECT(mortalite) ON src_lpodatas.v_c_observations_dev TO common_user;
GRANT REFERENCES(mortalite) ON src_lpodatas.v_c_observations_dev TO geonature WITH GRANT OPTION;
GRANT REFERENCES(mortalite_cause) ON src_lpodatas.v_c_observations_dev TO advanced_user;
GRANT REFERENCES(mortalite_cause) ON src_lpodatas.v_c_observations_dev TO geonature WITH GRANT OPTION;
GRANT REFERENCES(mortalite_cause) ON src_lpodatas.v_c_observations_dev TO postgres WITH GRANT OPTION;
GRANT UPDATE(mortalite_cause) ON src_lpodatas.v_c_observations_dev TO readonly;
GRANT SELECT(mortalite_cause) ON src_lpodatas.v_c_observations_dev TO common_user;
GRANT REFERENCES(geom) ON src_lpodatas.v_c_observations_dev TO postgres WITH GRANT OPTION;
GRANT UPDATE(geom) ON src_lpodatas.v_c_observations_dev TO readonly;
GRANT SELECT(geom) ON src_lpodatas.v_c_observations_dev TO common_user;
GRANT REFERENCES(geom) ON src_lpodatas.v_c_observations_dev TO geonature WITH GRANT OPTION;
GRANT REFERENCES(geom) ON src_lpodatas.v_c_observations_dev TO advanced_user;
GRANT REFERENCES(exp_excl) ON src_lpodatas.v_c_observations_dev TO geonature WITH GRANT OPTION;
GRANT REFERENCES(exp_excl) ON src_lpodatas.v_c_observations_dev TO advanced_user;
GRANT UPDATE(exp_excl) ON src_lpodatas.v_c_observations_dev TO readonly;
GRANT REFERENCES(exp_excl) ON src_lpodatas.v_c_observations_dev TO postgres WITH GRANT OPTION;
GRANT SELECT(exp_excl) ON src_lpodatas.v_c_observations_dev TO common_user;
GRANT REFERENCES(code_etude) ON src_lpodatas.v_c_observations_dev TO geonature WITH GRANT OPTION;
GRANT SELECT(code_etude) ON src_lpodatas.v_c_observations_dev TO common_user;
GRANT UPDATE(code_etude) ON src_lpodatas.v_c_observations_dev TO readonly;
GRANT REFERENCES(code_etude) ON src_lpodatas.v_c_observations_dev TO advanced_user;
GRANT REFERENCES(code_etude) ON src_lpodatas.v_c_observations_dev TO postgres WITH GRANT OPTION;
GRANT REFERENCES(commentaires) ON src_lpodatas.v_c_observations_dev TO postgres WITH GRANT OPTION;
GRANT REFERENCES(commentaires) ON src_lpodatas.v_c_observations_dev TO advanced_user;
GRANT UPDATE(commentaires) ON src_lpodatas.v_c_observations_dev TO readonly;
GRANT REFERENCES(commentaires) ON src_lpodatas.v_c_observations_dev TO geonature WITH GRANT OPTION;
GRANT SELECT(commentaires) ON src_lpodatas.v_c_observations_dev TO common_user;
GRANT REFERENCES(pers_morale) ON src_lpodatas.v_c_observations_dev TO postgres WITH GRANT OPTION;
GRANT REFERENCES(pers_morale) ON src_lpodatas.v_c_observations_dev TO advanced_user;
GRANT SELECT(pers_morale) ON src_lpodatas.v_c_observations_dev TO common_user;
GRANT REFERENCES(pers_morale) ON src_lpodatas.v_c_observations_dev TO geonature WITH GRANT OPTION;
GRANT UPDATE(pers_morale) ON src_lpodatas.v_c_observations_dev TO readonly;
GRANT REFERENCES(comportement) ON src_lpodatas.v_c_observations_dev TO advanced_user;
GRANT REFERENCES(comportement) ON src_lpodatas.v_c_observations_dev TO postgres WITH GRANT OPTION;
GRANT REFERENCES(comportement) ON src_lpodatas.v_c_observations_dev TO geonature WITH GRANT OPTION;
GRANT UPDATE(comportement) ON src_lpodatas.v_c_observations_dev TO readonly;
GRANT SELECT(comportement) ON src_lpodatas.v_c_observations_dev TO common_user;
GRANT REFERENCES("precision") ON src_lpodatas.v_c_observations_dev TO geonature WITH GRANT OPTION;
GRANT REFERENCES("precision") ON src_lpodatas.v_c_observations_dev TO postgres WITH GRANT OPTION;
GRANT UPDATE("precision") ON src_lpodatas.v_c_observations_dev TO readonly;
GRANT REFERENCES("precision") ON src_lpodatas.v_c_observations_dev TO advanced_user;
GRANT SELECT("precision") ON src_lpodatas.v_c_observations_dev TO common_user;
GRANT REFERENCES(details) ON src_lpodatas.v_c_observations_dev TO geonature WITH GRANT OPTION;
GRANT REFERENCES(details) ON src_lpodatas.v_c_observations_dev TO postgres WITH GRANT OPTION;
GRANT UPDATE(details) ON src_lpodatas.v_c_observations_dev TO readonly;
GRANT REFERENCES(details) ON src_lpodatas.v_c_observations_dev TO advanced_user;
GRANT SELECT(details) ON src_lpodatas.v_c_observations_dev TO common_user;
GRANT REFERENCES(place) ON src_lpodatas.v_c_observations_dev TO postgres WITH GRANT OPTION;
GRANT REFERENCES(place) ON src_lpodatas.v_c_observations_dev TO geonature WITH GRANT OPTION;
GRANT UPDATE(place) ON src_lpodatas.v_c_observationCREATE OR REPLACE VIEW src_lpodatas.v_c_observations_dev
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
    se.behaviour::text AS comportement,
    se.geo_accuracy AS "precision",
    se.details::text,
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

-- Permissions

ALTER TABLE src_lpodatas.v_c_observations_dev OWNER TO geonature;
GRANT ALL ON TABLE src_lpodatas.v_c_observations_dev TO geonature;
GRANT ALL ON TABLE src_lpodatas.v_c_observations_dev TO advanced_user;
GRANT ALL ON TABLE src_lpodatas.v_c_observations_dev TO postgres;
GRANT DELETE, SELECT, INSERT, UPDATE ON TABLE src_lpodatas.v_c_observations_dev TO readonly;
GRANT SELECT ON TABLE src_lpodatas.v_c_observations_dev TO common_user;
GRANT REFERENCES(id_synthese) ON src_lpodatas.v_c_observations_dev TO postgres WITH GRANT OPTION;
GRANT UPDATE(id_synthese) ON src_lpodatas.v_c_observations_dev TO readonly;
GRANT REFERENCES(id_synthese) ON src_lpodatas.v_c_observations_dev TO advanced_user;
GRANT REFERENCES(id_synthese) ON src_lpodatas.v_c_observations_dev TO geonature WITH GRANT OPTION;
GRANT SELECT(id_synthese) ON src_lpodatas.v_c_observations_dev TO common_user;
GRANT REFERENCES(uuid) ON src_lpodatas.v_c_observations_dev TO postgres WITH GRANT OPTION;
GRANT SELECT(uuid) ON src_lpodatas.v_c_observations_dev TO common_user;
GRANT REFERENCES(uuid) ON src_lpodatas.v_c_observations_dev TO advanced_user;
GRANT REFERENCES(uuid) ON src_lpodatas.v_c_observations_dev TO geonature WITH GRANT OPTION;
GRANT UPDATE(uuid) ON src_lpodatas.v_c_observations_dev TO readonly;
GRANT REFERENCES("source") ON src_lpodatas.v_c_observations_dev TO postgres WITH GRANT OPTION;
GRANT REFERENCES("source") ON src_lpodatas.v_c_observations_dev TO advanced_user;
GRANT UPDATE("source") ON src_lpodatas.v_c_observations_dev TO readonly;
GRANT REFERENCES("source") ON src_lpodatas.v_c_observations_dev TO geonature WITH GRANT OPTION;
GRANT SELECT("source") ON src_lpodatas.v_c_observations_dev TO common_user;
GRANT REFERENCES(source_id_data) ON src_lpodatas.v_c_observations_dev TO geonature WITH GRANT OPTION;
GRANT UPDATE(source_id_data) ON src_lpodatas.v_c_observations_dev TO readonly;
GRANT REFERENCES(source_id_data) ON src_lpodatas.v_c_observations_dev TO postgres WITH GRANT OPTION;
GRANT REFERENCES(source_id_data) ON src_lpodatas.v_c_observations_dev TO advanced_user;
GRANT SELECT(source_id_data) ON src_lpodatas.v_c_observations_dev TO common_user;
GRANT REFERENCES(source_id_sp) ON src_lpodatas.v_c_observations_dev TO postgres WITH GRANT OPTION;
GRANT REFERENCES(source_id_sp) ON src_lpodatas.v_c_observations_dev TO advanced_user;
GRANT SELECT(source_id_sp) ON src_lpodatas.v_c_observations_dev TO common_user;
GRANT UPDATE(source_id_sp) ON src_lpodatas.v_c_observations_dev TO readonly;
GRANT REFERENCES(source_id_sp) ON src_lpodatas.v_c_observations_dev TO geonature WITH GRANT OPTION;
GRANT REFERENCES(taxref_cdnom) ON src_lpodatas.v_c_observations_dev TO postgres WITH GRANT OPTION;
GRANT UPDATE(taxref_cdnom) ON src_lpodatas.v_c_observations_dev TO readonly;
GRANT REFERENCES(taxref_cdnom) ON src_lpodatas.v_c_observations_dev TO advanced_user;
GRANT SELECT(taxref_cdnom) ON src_lpodatas.v_c_observations_dev TO common_user;
GRANT REFERENCES(taxref_cdnom) ON src_lpodatas.v_c_observations_dev TO geonature WITH GRANT OPTION;
GRANT UPDATE(groupe_taxo) ON src_lpodatas.v_c_observations_dev TO readonly;
GRANT REFERENCES(groupe_taxo) ON src_lpodatas.v_c_observations_dev TO postgres WITH GRANT OPTION;
GRANT REFERENCES(groupe_taxo) ON src_lpodatas.v_c_observations_dev TO geonature WITH GRANT OPTION;
GRANT REFERENCES(groupe_taxo) ON src_lpodatas.v_c_observations_dev TO advanced_user;
GRANT SELECT(groupe_taxo) ON src_lpodatas.v_c_observations_dev TO common_user;
GRANT REFERENCES(group1_inpn) ON src_lpodatas.v_c_observations_dev TO advanced_user;
GRANT REFERENCES(group1_inpn) ON src_lpodatas.v_c_observations_dev TO postgres WITH GRANT OPTION;
GRANT REFERENCES(group1_inpn) ON src_lpodatas.v_c_observations_dev TO geonature WITH GRANT OPTION;
GRANT SELECT(group1_inpn) ON src_lpodatas.v_c_observations_dev TO common_user;
GRANT UPDATE(group1_inpn) ON src_lpodatas.v_c_observations_dev TO readonly;
GRANT REFERENCES(group2_inpn) ON src_lpodatas.v_c_observations_dev TO geonature WITH GRANT OPTION;
GRANT REFERENCES(group2_inpn) ON src_lpodatas.v_c_observations_dev TO advanced_user;
GRANT REFERENCES(group2_inpn) ON src_lpodatas.v_c_observations_dev TO postgres WITH GRANT OPTION;
GRANT UPDATE(group2_inpn) ON src_lpodatas.v_c_observations_dev TO readonly;
GRANT SELECT(group2_inpn) ON src_lpodatas.v_c_observations_dev TO common_user;
GRANT REFERENCES(taxon_vrai) ON src_lpodatas.v_c_observations_dev TO advanced_user;
GRANT UPDATE(taxon_vrai) ON src_lpodatas.v_c_observations_dev TO readonly;
GRANT REFERENCES(taxon_vrai) ON src_lpodatas.v_c_observations_dev TO geonature WITH GRANT OPTION;
GRANT REFERENCES(taxon_vrai) ON src_lpodatas.v_c_observations_dev TO postgres WITH GRANT OPTION;
GRANT SELECT(taxon_vrai) ON src_lpodatas.v_c_observations_dev TO common_user;
GRANT REFERENCES(nom_vern) ON src_lpodatas.v_c_observations_dev TO geonature WITH GRANT OPTION;
GRANT UPDATE(nom_vern) ON src_lpodatas.v_c_observations_dev TO readonly;
GRANT REFERENCES(nom_vern) ON src_lpodatas.v_c_observations_dev TO advanced_user;
GRANT SELECT(nom_vern) ON src_lpodatas.v_c_observations_dev TO common_user;
GRANT REFERENCES(nom_vern) ON src_lpodatas.v_c_observations_dev TO postgres WITH GRANT OPTION;
GRANT SELECT(nom_sci) ON src_lpodatas.v_c_observations_dev TO common_user;
GRANT REFERENCES(nom_sci) ON src_lpodatas.v_c_observations_dev TO postgres WITH GRANT OPTION;
GRANT REFERENCES(nom_sci) ON src_lpodatas.v_c_observations_dev TO advanced_user;
GRANT UPDATE(nom_sci) ON src_lpodatas.v_c_observations_dev TO readonly;
GRANT REFERENCES(nom_sci) ON src_lpodatas.v_c_observations_dev TO geonature WITH GRANT OPTION;
GRANT UPDATE(observateur) ON src_lpodatas.v_c_observations_dev TO readonly;
GRANT SELECT(observateur) ON src_lpodatas.v_c_observations_dev TO common_user;
GRANT REFERENCES(observateur) ON src_lpodatas.v_c_observations_dev TO advanced_user;
GRANT REFERENCES(observateur) ON src_lpodatas.v_c_observations_dev TO postgres WITH GRANT OPTION;
GRANT REFERENCES(observateur) ON src_lpodatas.v_c_observations_dev TO geonature WITH GRANT OPTION;
GRANT UPDATE(pseudo_observer_uid) ON src_lpodatas.v_c_observations_dev TO readonly;
GRANT REFERENCES(pseudo_observer_uid) ON src_lpodatas.v_c_observations_dev TO advanced_user;
GRANT REFERENCES(pseudo_observer_uid) ON src_lpodatas.v_c_observations_dev TO geonature WITH GRANT OPTION;
GRANT REFERENCES(pseudo_observer_uid) ON src_lpodatas.v_c_observations_dev TO postgres WITH GRANT OPTION;
GRANT SELECT(pseudo_observer_uid) ON src_lpodatas.v_c_observations_dev TO common_user;
GRANT REFERENCES(oiso_code_nidif) ON src_lpodatas.v_c_observations_dev TO geonature WITH GRANT OPTION;
GRANT REFERENCES(oiso_code_nidif) ON src_lpodatas.v_c_observations_dev TO postgres WITH GRANT OPTION;
GRANT REFERENCES(oiso_code_nidif) ON src_lpodatas.v_c_observations_dev TO advanced_user;
GRANT UPDATE(oiso_code_nidif) ON src_lpodatas.v_c_observations_dev TO readonly;
GRANT SELECT(oiso_code_nidif) ON src_lpodatas.v_c_observations_dev TO common_user;
GRANT REFERENCES(oiso_statut_nidif) ON src_lpodatas.v_c_observations_dev TO geonature WITH GRANT OPTION;
GRANT REFERENCES(oiso_statut_nidif) ON src_lpodatas.v_c_observations_dev TO advanced_user;
GRANT UPDATE(oiso_statut_nidif) ON src_lpodatas.v_c_observations_dev TO readonly;
GRANT SELECT(oiso_statut_nidif) ON src_lpodatas.v_c_observations_dev TO common_user;
GRANT REFERENCES(oiso_statut_nidif) ON src_lpodatas.v_c_observations_dev TO postgres WITH GRANT OPTION;
GRANT UPDATE(cs_colo_repro) ON src_lpodatas.v_c_observations_dev TO readonly;
GRANT REFERENCES(cs_colo_repro) ON src_lpodatas.v_c_observations_dev TO advanced_user;
GRANT REFERENCES(cs_colo_repro) ON src_lpodatas.v_c_observations_dev TO postgres WITH GRANT OPTION;
GRANT REFERENCES(cs_colo_repro) ON src_lpodatas.v_c_observations_dev TO geonature WITH GRANT OPTION;
GRANT SELECT(cs_colo_repro) ON src_lpodatas.v_c_observations_dev TO common_user;
GRANT REFERENCES(cs_is_gite) ON src_lpodatas.v_c_observations_dev TO advanced_user;
GRANT UPDATE(cs_is_gite) ON src_lpodatas.v_c_observations_dev TO readonly;
GRANT REFERENCES(cs_is_gite) ON src_lpodatas.v_c_observations_dev TO postgres WITH GRANT OPTION;
GRANT REFERENCES(cs_is_gite) ON src_lpodatas.v_c_observations_dev TO geonature WITH GRANT OPTION;
GRANT SELECT(cs_is_gite) ON src_lpodatas.v_c_observations_dev TO common_user;
GRANT REFERENCES(cs_periode) ON src_lpodatas.v_c_observations_dev TO postgres WITH GRANT OPTION;
GRANT REFERENCES(cs_periode) ON src_lpodatas.v_c_observations_dev TO advanced_user;
GRANT REFERENCES(cs_periode) ON src_lpodatas.v_c_observations_dev TO geonature WITH GRANT OPTION;
GRANT UPDATE(cs_periode) ON src_lpodatas.v_c_observations_dev TO readonly;
GRANT SELECT(cs_periode) ON src_lpodatas.v_c_observations_dev TO common_user;
GRANT REFERENCES(nombre_total) ON src_lpodatas.v_c_CREATE OR REPLACE VIEW src_lpodatas.v_c_observations_dev
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
    se.behaviour::text AS comportement,
    se.geo_accuracy AS "precision",
    se.details::text,
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
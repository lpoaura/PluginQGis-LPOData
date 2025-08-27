DROP VIEW src_lpodatas.v_c_observations;
CREATE VIEW src_lpodatas.v_c_observations AS
SELECT s.id_synthese
     , s.unique_id_sinp                                                                                  AS uuid
     , ts.name_source                                                                                    AS source
     , ts.desc_source
     , s.entity_source_pk_value                                                                          AS source_id_data
     , se.id_sp_source                                                                                   AS source_id_sp
     , s.cd_nom
     , cor.cd_ref
     , (cor.groupe_taxo_fr)::CHARACTER VARYING(50)                                                       AS groupe_taxo
     , (cor.tx_group1_inpn)::CHARACTER VARYING(255)                                                      AS group1_inpn
     , (cor.tx_group2_inpn)::CHARACTER VARYING(255)                                                      AS group2_inpn
     , se.taxo_real                                                                                      AS taxon_vrai
     , COALESCE(cor.vn_nom_fr, cor.tx_nom_fr)                                                            AS nom_vern
     , COALESCE(cor.vn_nom_sci, cor.tx_nom_sci)                                                          AS nom_sci
     , s.observers                                                                                       AS observateur
     , se.pseudo_observer_uid
     , se.bird_breed_code                                                                                AS oiso_code_nidif
     , se.breed_status                                                                                   AS statut_repro
     , se.bat_breed_colo                                                                                 AS cs_colo_repro
     , se.bat_is_gite                                                                                    AS cs_is_gite
     , se.bat_period                                                                                     AS cs_periode
     , s.count_max                                                                                       AS nombre_total
     , se.estimation_code                                                                                AS code_estimation
     , s.date_min                                                                                        AS date
     , (s.date_min)::DATE                                                                                AS date_jour
     , (s.date_min)::TIME WITHOUT TIME ZONE                                                              AS heure
     , (EXTRACT(YEAR FROM s.date_min))::INTEGER                                                          AS date_an
     , s.altitude_max                                                                                    AS altitude
     , se.mortality                                                                                      AS mortalite
     , se.mortality_cause                                                                                AS mortalite_cause
     , public.st_geometrytype(s.the_geom_local)                                                          AS type_geom
     , s.the_geom_local                                                                                  AS geom
     , se.export_excluded                                                                                AS exp_excl
     , se.project_code                                                                                   AS code_etude
     , s.comment_description                                                                             AS comment
     , se.private_comment                                                                                AS comment_priv
     , (fj.item ->> 'comment'::TEXT)                                                                     AS comment_forms
     , se.juridical_person                                                                               AS pers_morale
     , (se.behaviour)::TEXT                                                                              AS comportement
     , se.geo_accuracy                                                                                   AS "precision"
     , (se.details)::TEXT                                                                                AS details
     , se.place
     , se.id_form                                                                                        AS id_formulaire
     , s.meta_update_date                                                                                AS derniere_maj
     , (s.id_nomenclature_valid_status = ANY
        (ARRAY [ref_nomenclatures.get_id_nomenclature('STATUT_VALID'::CHARACTER VARYING,
                                                      '2'::CHARACTER VARYING), ref_nomenclatures.get_id_nomenclature(
                'STATUT_VALID'::CHARACTER VARYING, '1'::CHARACTER VARYING)]))                            AS is_valid
     , se.is_hidden                                                                                      AS donnee_cachee
     , (s.id_nomenclature_observation_status =
        ref_nomenclatures.get_id_nomenclature('STATUT_OBS'::CHARACTER VARYING, 'Pr'::CHARACTER VARYING)) AS is_present
     , s.reference_biblio
     , public.st_asewkt(s.the_geom_local)                                                                AS geom_ekt
FROM (((((gn_synthese.synthese s
    LEFT JOIN src_lpodatas.t_c_synthese_extended se ON ((s.id_synthese = se.id_synthese)))

    JOIN gn_synthese.t_sources ts ON ((s.id_source = ts.id_source)))
    LEFT JOIN src_vn_json.forms_json fj ON ((((fj.item ->> 'id_form_universal'::TEXT) = (se.id_form)::TEXT) AND
                                             ((fj.site)::TEXT = (ts.name_source)::TEXT))))
    LEFT JOIN taxonomie.taxref t ON ((s.cd_nom = t.cd_nom)))
    LEFT JOIN taxonomie.mv_c_cor_vn_taxref cor ON (((cor.cd_nom = t.cd_ref) AND (cor.cd_nom IS NOT NULL))));


ALTER VIEW src_lpodatas.v_c_observations OWNER TO dbadmin;

GRANT ALL ON TABLE src_lpodatas.v_c_observations TO postgres;
GRANT SELECT ON TABLE src_lpodatas.v_c_observations TO dt;
GRANT ALL ON TABLE src_lpodatas.v_c_observations TO advanced_user;
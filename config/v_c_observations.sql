BEGIN;
DROP VIEW IF EXISTS src_lpodatas.v_c_observations;
CREATE VIEW src_lpodatas.v_c_observations AS
WITH synthese_data AS (SELECT s.id_synthese
                            , s.id_source
                            , s.id_dataset
                            , s.unique_id_sinp
                            , s.entity_source_pk_value
                            , s.cd_nom
                            , s.count_max
                            , s.date_min
                            , s.altitude_max
                            , s.comment_description
                            , s.meta_update_date
                            , s.id_nomenclature_valid_status
                            , s.id_nomenclature_observation_status
                            , s.reference_biblio
                            , s.observers
                            , s.the_geom_local AS geom
                       FROM gn_synthese.synthese s)
   , synthese_extended AS (SELECT se.id_synthese
                                , se.id_sp_source
                                , se.taxo_real
                                , se.mortality
                                , se.mortality_cause
                                , se.export_excluded
                                , se.project_code
                                , se.private_comment
                                , se.juridical_person
                                , se.behaviour
                                , se.geo_accuracy
                                , se.details
                                , se.place
                                , se.id_form
                                , se.is_hidden
                                , se.pseudo_observer_uid
                                , se.bird_breed_code
                                , se.breed_status
                                , se.bat_breed_colo
                                , se.bat_is_gite
                                , se.bat_period
                                , se.estimation_code
                           FROM src_lpodatas.t_c_synthese_extended se)
   , sources AS (SELECT ts.id_source
                      , ts.name_source AS source
                      , ts.desc_source
                 FROM gn_synthese.t_sources ts)
   , datasets AS (SELECT id_dataset
                       , dataset_name
                       , unique_dataset_id
                  FROM gn_meta.t_datasets)
   , valid_status AS (SELECT label_default
                           , id_nomenclature
                           , cd_nomenclature
                      FROM ref_nomenclatures.t_nomenclatures
                      WHERE id_type = ref_nomenclatures.get_id_nomenclature_type('STATUT_VALID'))
   , forms AS (SELECT (item ->> 'id_form_universal')::VARCHAR AS id_form
                    , item ->> 'comment'                      AS comment_forms
               FROM src_vn_json.forms_json)
   , taxref_data AS (SELECT t.cd_nom
                          , t.cd_ref
                          , t.id_rang
                          , t.group1_inpn::CHARACTER VARYING(255) AS group1_inpn
                          , t.group2_inpn::CHARACTER VARYING(255) AS group2_inpn
                     FROM taxonomie.taxref t)
   , cor_vn_taxref AS (SELECT cor.cd_nom
                            , cor.cd_ref
                            , cor.vn_nom_fr
                            , cor.tx_nom_fr
                            , cor.vn_nom_sci
                            , cor.tx_nom_sci
                            , cor.groupe_taxo_fr::VARCHAR(50)
                       FROM taxonomie.mv_c_cor_vn_taxref cor)

SELECT sd.id_synthese
     , sd.unique_id_sinp                                                                                 AS uuid
     , s.source
     , s.desc_source
     , ds.dataset_name                                                                                   AS jdd
     , ds.unique_dataset_id                                                                              AS jdd_uuid
     , sd.entity_source_pk_value                                                                         AS source_id_data
     , se.id_sp_source                                                                                   AS source_id_sp
     , t.cd_ref                                                                                          AS cd_nom
     , cor.groupe_taxo_fr                                                                                AS groupe_taxo
     , t.group1_inpn
     , t.group2_inpn
     , t.id_rang
     , se.taxo_real                                                                                      AS taxon_vrai
     , COALESCE(cor.vn_nom_fr, cor.tx_nom_fr)                                                            AS nom_vern
     , COALESCE(cor.vn_nom_sci, cor.tx_nom_sci)                                                          AS nom_sci
     , valid_status.label_default                                                                        AS statut_validation
     , sd.observers                                                                                      AS observateur
     , se.pseudo_observer_uid
     , se.bird_breed_code                                                                                AS oiso_code_nidif
     , se.breed_status                                                                                   AS statut_repro
     , se.bat_breed_colo                                                                                 AS cs_colo_repro
     , se.bat_is_gite                                                                                    AS cs_is_gite
     , se.bat_period                                                                                     AS cs_periode
     , sd.count_max                                                                                      AS nombre_total
     , se.estimation_code                                                                                AS code_estimation
     , sd.date_min                                                                                       AS date
     , (sd.date_min)::DATE                                                                               AS date_jour
     , (sd.date_min)::TIME WITHOUT TIME ZONE                                                             AS heure
     , (EXTRACT(YEAR FROM sd.date_min))::INTEGER                                                         AS date_an
     , sd.altitude_max                                                                                   AS altitude
     , se.mortality                                                                                      AS mortalite
     , se.mortality_cause                                                                                AS mortalite_cause
     , public.st_geometrytype(sd.geom)                                                                   AS type_geom
     , sd.geom
     , se.export_excluded                                                                                AS exp_excl
     , se.project_code                                                                                   AS code_etude
     , sd.comment_description                                                                            AS comment
     , se.private_comment                                                                                AS comment_priv
     , f.comment_forms
     , se.juridical_person                                                                               AS pers_morale
     , (se.behaviour)::TEXT                                                                              AS comportement
     , se.geo_accuracy                                                                                   AS precision
     , (se.details)::TEXT                                                                                AS details
     , se.place
     , se.id_form                                                                                        AS id_formulaire
     , sd.meta_update_date                                                                               AS derniere_maj
     , (sd.id_nomenclature_valid_status = ANY (
    ARRAY [
        ref_nomenclatures.get_id_nomenclature('STATUT_VALID'::CHARACTER VARYING, '2'::CHARACTER VARYING),
        ref_nomenclatures.get_id_nomenclature('STATUT_VALID'::CHARACTER VARYING, '1'::CHARACTER VARYING)
        ]
    ))                                                                                                   AS is_valid
     , se.is_hidden                                                                                      AS donnee_cachee
     , (sd.id_nomenclature_observation_status =
        ref_nomenclatures.get_id_nomenclature('STATUT_OBS'::CHARACTER VARYING, 'Pr'::CHARACTER VARYING)) AS is_present
     , sd.reference_biblio
     , public.st_asewkt(sd.geom)                                                                         AS geom_ekt
FROM synthese_data sd
         LEFT JOIN
     synthese_extended se ON sd.id_synthese = se.id_synthese
         LEFT JOIN
     sources s ON sd.id_source = s.id_source
         LEFT JOIN
     datasets ds ON sd.id_dataset = ds.id_dataset
         LEFT JOIN
     valid_status ON sd.id_nomenclature_valid_status = valid_status.id_nomenclature
         LEFT JOIN
     forms f ON (f.id_form = se.id_form::VARCHAR)
         LEFT JOIN
     taxref_data t ON (sd.cd_nom = t.cd_nom)
         LEFT JOIN
     cor_vn_taxref cor ON (cor.cd_nom = t.cd_ref AND cor.cd_nom IS NOT NULL);
COMMIT;
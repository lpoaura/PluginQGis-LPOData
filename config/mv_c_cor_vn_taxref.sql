/**********************************************************************************************************************
 * 		Création de la vue permettant la récupération des noms d'espèces dans scr_lpo_datas.v_c_observations
 **********************************************************************************************************************/



CREATE MATERIALIZED VIEW taxonomie.mv_c_cor_vn_taxref
TABLESPACE pg_default
AS WITH prep AS (
         SELECT DISTINCT sp.id AS vn_id,
            tg.item ->> 'name'::text AS groupe_taxo_fr,
            tg.item ->> 'latin_name'::text AS groupe_taxo_sci,
            sp.item ->> 'french_name'::text AS french_name,
            sp.item ->> 'latin_name'::text AS latin_name
           FROM src_vn_json.species_json sp
             LEFT JOIN src_vn_json.taxo_groups_json tg ON ((sp.item ->> 'id_taxo_group'::text)::integer) = tg.id AND sp.site::text = tg.site::text
           GROUP BY sp.id, (tg.item ->> 'name'::text), (tg.item ->> 'latin_name'::text), (sp.item ->> 'french_name'::text), (sp.item ->> 'latin_name'::text)
        )
 SELECT vn.vn_id,
    vn.groupe_taxo_fr,
    vn.groupe_taxo_sci,
    vn.french_name AS vn_nom_fr,
    vn.latin_name AS vn_nom_sci,
    tx.cd_nom,
    tx.cd_ref,
    tx.group1_inpn AS tx_group1_inpn,
    tx.group2_inpn AS tx_group2_inpn,
    tx.classe AS tx_classe,
    tx.famille AS tx_famille,
    tx.nom_vern AS tx_nom_fr,
    tx.lb_nom AS tx_nom_sci,
        CASE
            WHEN id_sp_vn.id_sp_source IS NOT NULL THEN true
            ELSE false
        END AS vn_utilisation
   FROM prep vn
     LEFT JOIN taxonomie.cor_c_vn_taxref corr ON vn.vn_id = corr.vn_id
     LEFT JOIN taxonomie.taxref tx ON corr.cd_nom = tx.cd_nom
     LEFT JOIN ( SELECT DISTINCT tcse.id_sp_source
           FROM src_lpodatas.t_c_synthese_extended tcse
             JOIN gn_synthese.synthese s ON s.id_synthese = tcse.id_synthese
          WHERE (s.id_source IN ( SELECT ts.id_source
                   FROM gn_synthese.t_sources ts
                  WHERE ts.name_source::text = 'faune-aura'::text))) id_sp_vn ON id_sp_vn.id_sp_source = vn.vn_id
WITH DATA;

-- View indexes:
CREATE INDEX mv_c_cor_vn_taxref_cd_nom_idx1 ON taxonomie.mv_c_cor_vn_taxref USING btree (cd_nom);
CREATE INDEX mv_c_cor_vn_taxref_groupe_taxo_fr_idx1 ON taxonomie.mv_c_cor_vn_taxref USING btree (groupe_taxo_fr);
CREATE INDEX mv_c_cor_vn_taxref_tx_group2_inpn_idx1 ON taxonomie.mv_c_cor_vn_taxref USING btree (tx_group2_inpn);
CREATE INDEX mv_c_cor_vn_taxref_tx_nom_fr_idx1 ON taxonomie.mv_c_cor_vn_taxref USING btree (tx_nom_fr);
CREATE INDEX mv_c_cor_vn_taxref_tx_nom_sci_idx1 ON taxonomie.mv_c_cor_vn_taxref USING btree (tx_nom_sci);
CREATE INDEX mv_c_cor_vn_taxref_vn_nom_fr_idx1 ON taxonomie.mv_c_cor_vn_taxref USING btree (vn_nom_fr);
CREATE INDEX mv_c_cor_vn_taxref_vn_nom_sci_idx1 ON taxonomie.mv_c_cor_vn_taxref USING btree (vn_nom_sci);
CREATE INDEX mv_c_cor_vn_taxref_vn_utilisation_idx1 ON taxonomie.mv_c_cor_vn_taxref USING btree (vn_utilisation);


-- Permissions

ALTER TABLE taxonomie.mv_c_cor_vn_taxref OWNER TO dbadmin;
GRANT ALL ON TABLE taxonomie.mv_c_cor_vn_taxref TO postgres;
GRANT ALL ON TABLE taxonomie.mv_c_cor_vn_taxref TO dbadmin;
GRANT SELECT ON TABLE taxonomie.mv_c_cor_vn_taxref TO dt;
GRANT ALL ON TABLE taxonomie.mv_c_cor_vn_taxref TO advanced_user;
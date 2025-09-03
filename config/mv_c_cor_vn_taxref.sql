/******************************************************************
 * 		Création de la vue permettant la récupération des noms    *
 *      d'espèces dans scr_lpo_datas.v_c_observations_new             *
 ******************************************************************/
CREATE MATERIALIZED VIEW taxonomie.mv_c_cor_vn_taxref
AS WITH prep_vn AS (
         SELECT DISTINCT sp.id AS vn_id,
            tg.item ->> 'name'::text AS groupe_taxo_fr,
            tg.item ->> 'latin_name'::text AS groupe_taxo_sci,
            sp.item ->> 'french_name'::text AS french_name,
            sp.item ->> 'latin_name'::text AS latin_name
           FROM src_vn_json.species_json sp
             LEFT JOIN src_vn_json.taxo_groups_json tg ON ((sp.item ->> 'id_taxo_group'::text)::integer) = tg.id AND sp.site::text = tg.site::text
          GROUP BY sp.id, (tg.item ->> 'name'::text), (tg.item ->> 'latin_name'::text), (sp.item ->> 'french_name'::text), (sp.item ->> 'latin_name'::text)
        ), prep_tx AS (
         SELECT tx.cd_nom,
            tx.cd_ref,
            tx.group1_inpn AS tx_group1_inpn,
            tx.group2_inpn AS tx_group2_inpn,
            tx.id_rang AS tx_id_rang,
            tx.ordre AS tx_ordre,
            tx.classe AS tx_classe,
            tx.famille AS tx_famille,
            tx.nom_vern AS tx_nom_fr,
            tx.lb_nom AS tx_nom_sci
           FROM taxonomie.taxref tx
          WHERE tx.cd_nom = tx.cd_ref
        ), prep_synth AS (
         SELECT prep_vn.vn_id,
            string_agg(DISTINCT prep_vn.groupe_taxo_fr, ', '::text) AS groupe_taxo_fr,
            string_agg(DISTINCT prep_vn.groupe_taxo_sci, ', '::text) AS groupe_taxo_sci,
            COALESCE(string_agg(DISTINCT prep_vn.french_name, ','::text), string_agg(DISTINCT prep_tx.tx_nom_fr::text, ','::text)) AS vn_nom_fr,
            COALESCE(string_agg(DISTINCT prep_vn.latin_name, ','::text), string_agg(DISTINCT prep_tx.tx_nom_sci::text, ', '::text)) AS vn_nom_sci,
            prep_tx.cd_nom,
            prep_tx.cd_ref,
            string_agg(DISTINCT prep_tx.tx_group1_inpn::text, ', '::text) AS tx_group1_inpn,
            string_agg(DISTINCT prep_tx.tx_group2_inpn::text, ', '::text) AS tx_group2_inpn,
            string_agg(DISTINCT prep_tx.tx_id_rang::text, ', '::text) AS tx_id_rang,
            string_agg(DISTINCT prep_tx.tx_ordre::text, ', '::text) AS tx_ordre,
            string_agg(DISTINCT prep_tx.tx_classe::text, ', '::text) AS tx_classe,
            string_agg(DISTINCT prep_tx.tx_famille::text, ', '::text) AS tx_famille,
            string_agg(DISTINCT prep_tx.tx_nom_fr::text, ', '::text) AS tx_nom_fr,
            string_agg(DISTINCT prep_tx.tx_nom_sci::text, ', '::text) AS tx_nom_sci
           FROM prep_tx
             LEFT JOIN taxonomie.cor_c_vn_taxref cor ON cor.cd_nom = prep_tx.cd_nom
             LEFT JOIN prep_vn ON prep_vn.vn_id = cor.vn_id
          GROUP BY prep_vn.vn_id, prep_tx.cd_nom, prep_tx.cd_ref
        )
 SELECT array_agg(DISTINCT ps1.vn_id) AS vn_id,
    ps1.groupe_taxo_fr,
    ps1.groupe_taxo_sci,
        CASE
            WHEN ps1.cd_nom = ps1.cd_ref THEN ps1.vn_nom_fr
            WHEN ps2.cd_nom = ps1.cd_ref THEN ps2.vn_nom_fr
            ELSE ps1.vn_nom_fr
        END AS vn_nom_fr,
        CASE
            WHEN ps1.cd_nom = ps1.cd_ref THEN ps1.vn_nom_sci
            WHEN ps2.cd_nom = ps1.cd_ref THEN ps2.vn_nom_sci
            ELSE ps1.vn_nom_fr
        END AS vn_nom_sci,
    ps1.cd_ref AS cd_nom,
    ps1.cd_ref,
    ps1.tx_group1_inpn,
    ps1.tx_group2_inpn,
    ps1.tx_id_rang,
    ps1.tx_ordre,
    ps1.tx_classe,
    ps1.tx_famille,
    ps1.tx_nom_fr,
    ps1.tx_nom_sci
   FROM prep_synth ps1
     LEFT JOIN prep_synth ps2 ON ps1.cd_ref = ps2.cd_ref
  GROUP BY ps1.groupe_taxo_fr, ps1.groupe_taxo_sci, (
        CASE
            WHEN ps1.cd_nom = ps1.cd_ref THEN ps1.vn_nom_fr
            WHEN ps2.cd_nom = ps1.cd_ref THEN ps2.vn_nom_fr
            ELSE ps1.vn_nom_fr
        END), (
        CASE
            WHEN ps1.cd_nom = ps1.cd_ref THEN ps1.vn_nom_sci
            WHEN ps2.cd_nom = ps1.cd_ref THEN ps2.vn_nom_sci
            ELSE ps1.vn_nom_fr
        END), ps1.cd_ref, ps1.tx_group1_inpn, ps1.tx_group2_inpn, ps1.tx_id_rang, ps1.tx_ordre, ps1.tx_classe, ps1.tx_famille, ps1.tx_nom_fr, ps1.tx_nom_sci
WITH DATA;

-- View indexes:
CREATE INDEX mv_c_cor_vn_taxref_cd_nom_idx1 ON taxonomie.mv_c_cor_vn_taxref USING btree (cd_nom);
CREATE INDEX mv_c_cor_vn_taxref_cd_ref_idx1 ON taxonomie.mv_c_cor_vn_taxref USING btree (cd_ref);
CREATE INDEX mv_c_cor_vn_taxref_groupe_taxo_fr_idx1 ON taxonomie.mv_c_cor_vn_taxref USING btree (groupe_taxo_fr);
CREATE INDEX mv_c_cor_vn_taxref_tx_group2_inpn_idx1 ON taxonomie.mv_c_cor_vn_taxref USING btree (tx_group2_inpn);
CREATE INDEX mv_c_cor_vn_taxref_tx_nom_fr_idx1 ON taxonomie.mv_c_cor_vn_taxref USING btree (tx_nom_fr);
CREATE INDEX mv_c_cor_vn_taxref_tx_nom_sci_idx1 ON taxonomie.mv_c_cor_vn_taxref USING btree (tx_nom_sci);
CREATE INDEX mv_c_cor_vn_taxref_vn_nom_fr_idx1 ON taxonomie.mv_c_cor_vn_taxref USING btree (vn_nom_fr);
CREATE INDEX mv_c_cor_vn_taxref_vn_nom_sci_idx1 ON taxonomie.mv_c_cor_vn_taxref USING btree (vn_nom_sci);


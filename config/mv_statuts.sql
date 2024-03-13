/*****************************************************************
 * 			Préparation d'une vue avec les statuts
 *****************************************************************/
/*
 * Objectif de la vue :
 * - centraliser dans une seule VM les statuts de menace et de protection en s'adossant exclusivement sur la BDC statuts
 *
 * Contraintes :
 * - les anciennes listes rouges de Rhône-Alpes ne figurent pas dans la bdc statut
 * - il n'est pas possible dans la bdc statut de distinguer les périodes biologiques pour une même LR (mail envoyé à l'INPN pour comprendre)
 * - intégrer les données des statuts isérois
 *
 * Solutions :
 * - pour contourner ces 2 premiers problèmes la VM s'appuie sur les tables t_redlist, ces données sont préparées dans des CTE via des unions
 * - la VM s'appuie également sur une table dans un schéma perso
 *
 * Evolutions :
 * - quand le pb de la BDC statut sera réglé il faudra corriger la requête
 * - quand les nouvelles LR d'AuRA seront publiées et prises en compte dans BDC statut, il faudra également corriger
 * - tester le fonctionnement avec des LR sur la grande région (AuRA), il n'en existe pas actuellement
 * - voir comment traiter les statuts isérois
 * - intégrer les déterminances znieff
 *
 * Pense-bête :
 * - requête à personnaliser en fonction de la région concernée
 *
 */
CREATE MATERIALIZED VIEW taxonomie.mv_c_statut TABLESPACE pg_default AS
WITH prep_lrra AS (
    SELECT DISTINCT tx.classe, sp.id_redlist, sp.status_order, tx.cd_ref, sp.category,
        sp.criteria, sp.id_source
    FROM taxonomie.t_c_redlist sp
        LEFT JOIN taxonomie.taxref tx ON sp.cd_nom = tx.cd_nom
        JOIN taxonomie.bib_c_redlist_source art ON sp.id_source = art.id_source
    WHERE (tx.classe::text = 'Aves'::text
        OR tx.classe::text = 'Mammalia'::text
        AND tx.ordre::text <> 'Chiroptera'::text)
    AND art.area_name::text = 'Rhône-Alpes'::text
), prep_statut_lrra AS (
    SELECT DISTINCT sp.cd_ref, CASE WHEN sp.classe::text !~~ * 'Aves'::text
            AND (sp.id_source <> ALL (ARRAY[18, 19, 20])) THEN
            sp.category
        WHEN sp.classe::text = 'Aves'::text
            AND sp.id_source = 18 THEN
            sp.category
        WHEN sp.classe::text = 'Aves'::text
            AND sp.id_source = 19 THEN
            (sp.category::text || 'w'::text)::character varying
        WHEN sp.classe::text = 'Aves'::text
            AND sp.id_source = 20 THEN
            (sp.category::text || 'm'::text)::character varying
        ELSE
            NULL::character varying
        END AS lrra,
        CASE WHEN sp.id_source = 18 THEN
            sp.category
        ELSE
            NULL::character varying
        END AS lrra_nich, CASE WHEN sp.id_source = 19 THEN
            sp.category
        ELSE
            NULL::character varying
        END AS lrra_hiv, CASE WHEN sp.id_source = 20 THEN
            sp.category
        ELSE
            NULL::character varying
        END AS lrra_migr
    FROM prep_lrra sp
), prep_lrra_ok AS (
    SELECT prep_statut_lrra.cd_ref, string_agg(DISTINCT prep_statut_lrra.lrra::text, ', '::text) AS lrra,
	string_agg(DISTINCT prep_statut_lrra.lrra_nich::text, ', '::text) AS lrra_nich, string_agg(DISTINCT
	prep_statut_lrra.lrra_hiv::text, ', '::text) AS lrra_hiv,
    string_agg(DISTINCT prep_statut_lrra.lrra_migr::text, ', '::text) AS lrra_migr
FROM prep_statut_lrra
GROUP BY prep_statut_lrra.cd_ref
), prep_t_redlist_fr AS ( SELECT DISTINCT sp.id_redlist, sp.status_order, tx.cd_ref, sp.category,
    sp.criteria, sp.id_source, ctx.groupe_taxo_fr, ctx.vn_nom_fr, ctx.vn_nom_sci
FROM taxonomie.t_c_redlist sp
    JOIN taxonomie.taxref tx ON sp.cd_nom = tx.cd_nom
    JOIN taxonomie.mv_c_cor_vn_taxref_bkp ctx ON sp.cd_ref = ctx.cd_ref
    WHERE ctx.groupe_taxo_fr = 'Oiseaux'::text
), prep2 AS (
    SELECT DISTINCT ptlr.cd_ref, ptlr.groupe_taxo_fr, ptlr.vn_nom_fr, ptlr.vn_nom_sci,
        CASE WHEN ptlr.groupe_taxo_fr ~~* 'Oiseaux'::text
            AND ptlr.id_source = 5 THEN
            ptlr.category
        WHEN ptlr.groupe_taxo_fr ~~* 'Oiseaux'::text
            AND ptlr.id_source = 4 THEN
            (ptlr.category::text || 'w'::text)::character varying
        WHEN ptlr.groupe_taxo_fr ~~* 'Oiseaux'::text
            AND ptlr.id_source = 3 THEN
            (ptlr.category::text || 'm'::text)::character varying
        ELSE
            NULL::character varying
        END AS lr_france, CASE WHEN ptlr.id_source = 5 THEN
            ptlr.category
        ELSE
            NULL::character varying
        END AS lr_fr_nich, CASE WHEN ptlr.id_source = 4 THEN
            ptlr.category
        ELSE
            NULL::character varying
        END AS lr_fr_hiv, CASE WHEN ptlr.id_source = 3 THEN
            ptlr.category
        ELSE
            NULL::character varying
        END AS lr_fr_migr
    FROM prep_t_redlist_fr ptlr
        LEFT JOIN taxonomie.taxref tr ON ptlr.cd_ref = tr.cd_nom
        LEFT JOIN taxonomie.bib_c_redlist_source art ON ptlr.id_source = art.id_source
), prep_lrf_ok AS (
    SELECT prep2.cd_ref, prep2.groupe_taxo_fr, prep2.vn_nom_fr, prep2.vn_nom_sci,
	string_agg(DISTINCT prep2.lr_france::text, ', '::text) AS lr_france, string_agg(DISTINCT
	    prep2.lr_fr_nich::text, ', '::text) AS lr_fr_nich, string_agg(DISTINCT prep2.lr_fr_hiv::text,
	    ', '::text) AS lr_fr_hiv, string_agg(DISTINCT prep2.lr_fr_migr::text, ', '::text) AS
	    lr_fr_migr
FROM prep2
GROUP BY prep2.groupe_taxo_fr, prep2.vn_nom_fr, prep2.vn_nom_sci, prep2.cd_ref
), lr_auv AS (
SELECT bs.cd_ref,
    bs.code_statut, bs.label_statut
FROM taxonomie.bdc_statut bs
    WHERE bs.cd_type_statut::text = 'LRR'::text
        AND bs.lb_adm_tr::text = 'Auvergne'::text
), lr_ra AS (
    SELECT bs.cd_ref, bs.code_statut, NULL::text AS lrra_nich, NULL::text AS lrra_hiv,
        NULL::text AS lrra_migr
    FROM taxonomie.bdc_statut bs
    WHERE bs.cd_type_statut::text = 'LRR'::text
        AND bs.lb_adm_tr::text = 'Rhône-Alpes'::text
    UNION
    SELECT prep_lrra_ok.cd_ref, prep_lrra_ok.lrra, prep_lrra_ok.lrra_nich, prep_lrra_ok.lrra_hiv, prep_lrra_ok.lrra_migr
    FROM prep_lrra_ok
), lr_aura AS (
    SELECT bs.cd_ref, bs.code_statut, bs.label_statut
    FROM taxonomie.bdc_statut bs
    WHERE bs.cd_type_statut::text = 'LRR'::text
        AND bs.lb_adm_tr::text = 'Auvergne-Rhône-Alpes'::text
), lr_fr AS (
    SELECT bs.cd_ref, bs.code_statut AS lr_france, NULL::text AS lr_fr_nich, NULL::text AS lr_fr_hiv,
        NULL::text AS lr_fr_migr
    FROM taxonomie.bdc_statut bs
        JOIN taxonomie.taxref ON bs.cd_nom = taxref.cd_nom
    WHERE bs.cd_type_statut::text = 'LRN'::text
        AND bs.lb_adm_tr::text = 'France métropolitaine'::text
        AND (taxref.classe IS NULL
            OR taxref.classe::text <> 'Aves'::text)
    UNION
    SELECT prep_lrf_ok.cd_ref, prep_lrf_ok.lr_france, prep_lrf_ok.lr_fr_nich, prep_lrf_ok.lr_fr_hiv, prep_lrf_ok.lr_fr_migr
    FROM prep_lrf_ok
), lr_euro AS (
    SELECT bs.cd_ref, bs.cd_nom, bs.code_statut, bs.label_statut
    FROM taxonomie.bdc_statut bs
    WHERE bs.cd_type_statut::text = 'LRE'::text
), lr_monde AS (
    SELECT bs.cd_ref, bs.cd_nom, bs.code_statut, bs.label_statut
    FROM taxonomie.bdc_statut bs
    WHERE bs.cd_type_statut::text = 'LRM'::text
), prot_nat AS (
    SELECT bs.cd_ref, CASE WHEN bs.code_statut::text ~~* 'FRAR%'::text THEN
            string_agg(DISTINCT split_part(bs.code_statut::text, 'FRAR'::text, 2), ', '::text)
        ELSE
            string_agg(DISTINCT split_part(bs.label_statut::text, ' : '::text, 2), ', '::text)
	END AS article, string_agg(DISTINCT bs.code_statut::text, ', '::text) AS code_statut,
	    string_agg(DISTINCT bs.label_statut::text, ', '::text) AS label_statut
FROM taxonomie.bdc_statut bs
    WHERE bs.cd_type_statut::text = 'PN'::text
        AND bs.lb_adm_tr::text = 'France métropolitaine'::text
    GROUP BY bs.cd_ref, bs.code_statut
), n2k AS (
SELECT bs.cd_ref, string_agg(DISTINCT split_part(bs.label_statut::text, ' : '::text, 2), ', '::text) AS annexe
FROM taxonomie.bdc_statut bs
    WHERE (bs.cd_type_statut::text = ANY (ARRAY['DH'::character varying::text, 'DO'::character varying::text]))
    AND bs.lb_adm_tr::text = 'France métropolitaine'::text
GROUP BY bs.cd_ref
), berne AS (
SELECT bs.cd_ref, split_part(bs.label_statut::text, ' : '::text, 2) AS annexe, bs.code_statut, bs.label_statut
FROM taxonomie.bdc_statut bs
    WHERE bs.cd_type_statut::text = 'BERN'::text
        AND bs.lb_adm_tr::text = 'France métropolitaine'::text
), bonn AS (
    SELECT bs.cd_ref, string_agg(DISTINCT split_part(bs.label_statut::text, ' : '::text, 2), ', '::text) AS annexe
FROM taxonomie.bdc_statut bs
    WHERE bs.cd_type_statut::text = 'BONN'::text
    GROUP BY bs.cd_ref
), pna_en_cours AS (
SELECT bs.cd_ref, CASE WHEN bs.code_statut::text = 'true'::text THEN
        'Oui'::text
    ELSE
        NULL::text
    END AS statut, bs.label_statut
FROM taxonomie.bdc_statut bs
    WHERE bs.cd_type_statut::text = 'PNA'::text
), pna_ex AS (
    SELECT bs.cd_ref, CASE WHEN bs.code_statut::text = 'true'::text THEN
            'Oui'::text
        ELSE
            NULL::text
        END AS statut, bs.code_statut, bs.label_statut
    FROM taxonomie.bdc_statut bs
    WHERE bs.cd_type_statut::text = 'exPNA'::text
), sc38 AS (
    SELECT tb.cdnom_taxref AS cd_ref, tb.sc38_2015
    FROM partage.lpo38_tabesp1806 tb
        LEFT JOIN taxonomie.mv_c_cor_vn_taxref_bkp ccvt ON ccvt.cd_nom = tb.cdnom_taxref::integer
    WHERE tb.sc38_2015 IS NOT NULL
)
SELECT DISTINCT row_number() OVER () AS id, cor.groupe_taxo_fr, cor.vn_nom_fr, cor.vn_nom_sci, cor.cd_ref,
	string_agg(DISTINCT lr_auv.code_statut::text, ', '::text) AS lr_auv, lr_ra.code_statut AS lr_ra,
	    lr_ra.lrra_nich, lr_ra.lrra_hiv, lr_ra.lrra_migr,
    lr_aura.code_statut AS lr_aura, string_agg(DISTINCT lr_fr.lr_france::text, ', '::text) AS lr_france,
	lr_fr.lr_fr_nich, lr_fr.lr_fr_hiv, lr_fr.lr_fr_migr,
    lr_euro.code_statut AS lr_euro, lr_monde.code_statut AS lr_monde, string_agg(DISTINCT 'Article '::text ||
	prot_nat.article, ', '::text) AS prot_nat, CASE WHEN n2k.annexe = ANY (ARRAY['Annexe II, Annexe IV'::text,
	'Annexe IV, Annexe II'::text]) THEN
        'Annexes II, IV'::text
    ELSE
        n2k.annexe
    END AS n2k,
    berne.annexe AS conv_berne, bonn.annexe AS conv_bonn, pna_en_cours.statut AS pna_en_cours, pna_ex.statut AS pna_ex, sc38.sc38_2015
FROM taxonomie.taxref t
    LEFT JOIN taxonomie.mv_c_cor_vn_taxref_bkp cor ON cor.cd_ref = t.cd_nom
    LEFT JOIN lr_auv ON lr_auv.cd_ref = cor.cd_ref
    LEFT JOIN lr_ra ON lr_ra.cd_ref = cor.cd_ref
    LEFT JOIN lr_aura ON lr_aura.cd_ref = cor.cd_ref
    LEFT JOIN lr_fr ON lr_fr.cd_ref = cor.cd_ref
    LEFT JOIN lr_euro ON lr_euro.cd_nom = cor.cd_ref
    LEFT JOIN lr_monde ON lr_monde.cd_nom = cor.cd_ref
    LEFT JOIN prot_nat ON prot_nat.cd_ref = cor.cd_ref
    LEFT JOIN n2k ON n2k.cd_ref = cor.cd_ref
    LEFT JOIN berne ON berne.cd_ref = cor.cd_ref
    LEFT JOIN bonn ON bonn.cd_ref = cor.cd_ref
    LEFT JOIN pna_en_cours ON pna_en_cours.cd_ref = cor.cd_ref
    LEFT JOIN pna_ex ON pna_ex.cd_ref = cor.cd_ref
    LEFT JOIN sc38 ON sc38.cd_ref::integer = cor.cd_ref
WHERE t.cd_nom = t.cd_ref
GROUP BY cor.vn_nom_fr, cor.vn_nom_sci, cor.cd_ref, lr_ra.code_statut, lr_ra.lrra_nich, lr_ra.lrra_hiv,
    lr_ra.lrra_migr, lr_aura.code_statut, lr_fr.lr_fr_nich, lr_fr.lr_fr_hiv, lr_fr.lr_fr_migr, lr_euro.code_statut,
    lr_monde.code_statut, n2k.annexe, berne.annexe, bonn.annexe, pna_en_cours.statut, pna_ex.statut, sc38.sc38_2015,
    cor.groupe_taxo_fr
ORDER BY cor.groupe_taxo_fr, cor.vn_nom_fr WITH DATA;

-- View indexes:
CREATE INDEX mv_c_statut_cd_ref_idx ON taxonomie.mv_c_statut USING btree (cd_ref);

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
CREATE MATERIALIZED VIEW taxonomie.mv_c_statut AS
WITH prep_t_redlist_fr AS (
    SELECT DISTINCT
        t_1.cd_ref,
        bsv.code_statut,
        stat_tax.rq_statut,
        ctx.groupe_taxo_fr,
        ctx.vn_nom_fr,
        ctx.vn_nom_sci,
        bst.cd_doc
    FROM (((((
        taxonomie.bdc_statut_taxons stat_tax
        LEFT JOIN
            taxonomie.bdc_statut_cor_text_values AS bsctv
            ON ((stat_tax.id_value_text = bsctv.id_value_text))
    )
    LEFT JOIN
        taxonomie.bdc_statut_text AS bst
        ON ((bsctv.id_text = bst.id_text))
    )
    LEFT JOIN
        taxonomie.bdc_statut_values AS bsv
        ON ((bsctv.id_value = bsv.id_value))
    )
    INNER JOIN taxonomie.taxref AS t_1 ON ((stat_tax.cd_nom = t_1.cd_nom))
    )
    INNER JOIN
        taxonomie.mv_c_cor_vn_taxref AS ctx
        ON ((t_1.cd_ref = ctx.cd_ref))
    )
    WHERE
        (
            ((bst.cd_type_statut)::text = 'LRN'::text)
            AND ((t_1.classe)::text = 'Aves'::text)
            AND (bst.cd_doc = ANY(ARRAY[165208, 31343]))
        )
),

prep2 AS (
    SELECT DISTINCT
        ptlr.cd_ref,
        ptlr.groupe_taxo_fr,
        ptlr.vn_nom_fr,
        ptlr.vn_nom_sci,
        ptlr.cd_doc,
        CASE
            WHEN
                (
                    (ptlr.groupe_taxo_fr ~~* 'Oiseaux'::text)
                    AND (ptlr.cd_doc = 165208)
                )
                THEN ptlr.code_statut
            WHEN
                (
                    (ptlr.groupe_taxo_fr ~~* 'Oiseaux'::text)
                    AND (ptlr.cd_doc = 31343)
                    AND ((ptlr.rq_statut)::text ~~* '%hivernant%'::text)
                )
                THEN
                    (((ptlr.code_statut)::text || 'w'::text))::character varying
            WHEN
                (
                    (ptlr.groupe_taxo_fr ~~* 'Oiseaux'::text)
                    AND (ptlr.cd_doc = 31343)
                    AND ((ptlr.rq_statut)::text ~~* '%visiteur%'::text)
                )
                THEN
                    (((ptlr.code_statut)::text || 'm'::text))::character varying
            ELSE NULL::character varying
        END AS lr_france,
        CASE
            WHEN (ptlr.cd_doc = 165208) THEN ptlr.code_statut
            ELSE NULL::character varying
        END AS lr_fr_nich,
        CASE
            WHEN
                (
                    (ptlr.cd_doc = 31343)
                    AND ((ptlr.rq_statut)::text ~~* '%hivernant%'::text)
                )
                THEN ptlr.code_statut
            ELSE NULL::character varying
        END AS lr_fr_hiv,
        CASE
            WHEN
                (
                    (ptlr.cd_doc = 31343)
                    AND ((ptlr.rq_statut)::text ~~* '%visiteur%'::text)
                )
                THEN ptlr.code_statut
            ELSE NULL::character varying
        END AS lr_fr_migr,
        ROW_NUMBER() OVER (ORDER BY ptlr.cd_doc DESC) AS id_order
    FROM prep_t_redlist_fr AS ptlr
    ORDER BY ptlr.cd_doc DESC
),

prep_lrf_ok AS (
    SELECT
        prep2.cd_ref,
        prep2.groupe_taxo_fr,
        prep2.vn_nom_fr,
        prep2.vn_nom_sci,
        STRING_AGG(
            (prep2.lr_france)::text,
            ', '::text ORDER BY (LENGTH((prep2.lr_france)::text))
        ) AS lr_france,
        STRING_AGG(DISTINCT (prep2.lr_fr_nich)::text, ', '::text) AS lr_fr_nich,
        STRING_AGG(DISTINCT (prep2.lr_fr_hiv)::text, ', '::text) AS lr_fr_hiv,
        STRING_AGG(DISTINCT (prep2.lr_fr_migr)::text, ', '::text) AS lr_fr_migr
    FROM prep2
    GROUP BY
        prep2.groupe_taxo_fr, prep2.vn_nom_fr, prep2.vn_nom_sci, prep2.cd_ref
),

lr_auv AS (
    SELECT
        stat_tax.cd_ref,
        bsv.code_statut,
        bsv.label_statut
    FROM (((
        taxonomie.bdc_statut_taxons stat_tax
        LEFT JOIN
            taxonomie.bdc_statut_cor_text_values AS bsctv
            ON ((stat_tax.id_value_text = bsctv.id_value_text))
    )
    LEFT JOIN
        taxonomie.bdc_statut_text AS bst
        ON ((bsctv.id_text = bst.id_text))
    )
    LEFT JOIN
        taxonomie.bdc_statut_values AS bsv
        ON ((bsctv.id_value = bsv.id_value))
    )
    WHERE
        (
            ((bst.cd_type_statut)::text = 'LRR'::text)
            AND ((bst.lb_adm_tr)::text = 'Auvergne'::text)
        )
),

lr_ra AS (
    SELECT
        stat_tax.cd_ref,
        bsv.code_statut,
        NULL::text AS lrra_nich,
        NULL::text AS lrra_hiv,
        NULL::text AS lrra_migr
    FROM (((
        taxonomie.bdc_statut_taxons stat_tax
        LEFT JOIN
            taxonomie.bdc_statut_cor_text_values AS bsctv
            ON ((stat_tax.id_value_text = bsctv.id_value_text))
    )
    LEFT JOIN
        taxonomie.bdc_statut_text AS bst
        ON ((bsctv.id_text = bst.id_text))
    )
    LEFT JOIN
        taxonomie.bdc_statut_values AS bsv
        ON ((bsctv.id_value = bsv.id_value))
    )
    WHERE
        (
            ((bst.cd_type_statut)::text = 'LRR'::text)
            AND ((bst.lb_adm_tr)::text = 'Rhône-Alpes'::text)
        )
),

lr_aura AS (
    SELECT
        stat_tax.cd_ref,
        bsv.code_statut,
        bsv.label_statut
    FROM (((
        taxonomie.bdc_statut_taxons stat_tax
        LEFT JOIN
            taxonomie.bdc_statut_cor_text_values AS bsctv
            ON ((stat_tax.id_value_text = bsctv.id_value_text))
    )
    LEFT JOIN
        taxonomie.bdc_statut_text AS bst
        ON ((bsctv.id_text = bst.id_text))
    )
    LEFT JOIN
        taxonomie.bdc_statut_values AS bsv
        ON ((bsctv.id_value = bsv.id_value))
    )
    WHERE
        (
            ((bst.cd_type_statut)::text = 'LRR'::text)
            AND ((bst.lb_adm_tr)::text = 'Auvergne-Rhône-Alpes'::text)
        )
),

lr_fr AS (
    SELECT
        stat_tax.cd_ref,
        bsv.code_statut AS lr_france,
        NULL::text AS lr_fr_nich,
        NULL::text AS lr_fr_hiv,
        NULL::text AS lr_fr_migr
    FROM ((((
        taxonomie.bdc_statut_taxons stat_tax
        LEFT JOIN
            taxonomie.bdc_statut_cor_text_values AS bsctv
            ON ((stat_tax.id_value_text = bsctv.id_value_text))
    )
    LEFT JOIN
        taxonomie.bdc_statut_text AS bst
        ON ((bsctv.id_text = bst.id_text))
    )
    LEFT JOIN
        taxonomie.bdc_statut_values AS bsv
        ON ((bsctv.id_value = bsv.id_value))
    )
    INNER JOIN taxonomie.taxref ON ((stat_tax.cd_nom = taxref.cd_nom)))
    WHERE
        (
            ((bst.cd_type_statut)::text = 'LRN'::text)
            AND ((bst.lb_adm_tr)::text = 'France métropolitaine'::text)
            AND (
                (taxref.classe IS NULL)
                OR ((taxref.classe)::text <> 'Aves'::text)
            )
        )
    UNION
    SELECT
        prep_lrf_ok.cd_ref,
        prep_lrf_ok.lr_france,
        prep_lrf_ok.lr_fr_nich,
        prep_lrf_ok.lr_fr_hiv,
        prep_lrf_ok.lr_fr_migr
    FROM prep_lrf_ok
),

lr_euro AS (
    SELECT
        stat_tax.cd_ref,
        stat_tax.cd_nom,
        bsv.code_statut
    FROM (((
        taxonomie.bdc_statut_taxons stat_tax
        LEFT JOIN
            taxonomie.bdc_statut_cor_text_values AS bsctv
            ON ((stat_tax.id_value_text = bsctv.id_value_text))
    )
    LEFT JOIN
        taxonomie.bdc_statut_text AS bst
        ON ((bsctv.id_text = bst.id_text))
    )
    LEFT JOIN
        taxonomie.bdc_statut_values AS bsv
        ON ((bsctv.id_value = bsv.id_value))
    )
    WHERE ((bst.cd_type_statut)::text = 'LRE'::text)
),

lr_monde AS (
    SELECT
        stat_tax.cd_ref,
        stat_tax.cd_nom,
        bsv.code_statut
    FROM (((
        taxonomie.bdc_statut_taxons stat_tax
        LEFT JOIN
            taxonomie.bdc_statut_cor_text_values AS bsctv
            ON ((stat_tax.id_value_text = bsctv.id_value_text))
    )
    LEFT JOIN
        taxonomie.bdc_statut_text AS bst
        ON ((bsctv.id_text = bst.id_text))
    )
    LEFT JOIN
        taxonomie.bdc_statut_values AS bsv
        ON ((bsctv.id_value = bsv.id_value))
    )
    WHERE ((bst.cd_type_statut)::text = 'LRM'::text)
),

prot_nat AS (
    SELECT
        stat_tax.cd_ref,
        CASE
            WHEN
                ((bsv.code_statut)::text ~~* 'FRAR%'::text)
                THEN
                    STRING_AGG(
                        DISTINCT SPLIT_PART(
                            (bsv.code_statut)::text, 'FRAR'::text, 2
                        ),
                        ', '::text
                    )
            ELSE
                STRING_AGG(
                    DISTINCT SPLIT_PART(
                        (bsv.label_statut)::text, ' : '::text, 2
                    ),
                    ', '::text
                )
        END AS article,
        STRING_AGG(DISTINCT (bsv.code_statut)::text, ', '::text) AS code_statut,
        STRING_AGG(DISTINCT (bsv.label_statut)::text, ', '::text)
            AS label_statut
    FROM (((
        taxonomie.bdc_statut_taxons stat_tax
        LEFT JOIN
            taxonomie.bdc_statut_cor_text_values AS bsctv
            ON ((stat_tax.id_value_text = bsctv.id_value_text))
    )
    LEFT JOIN
        taxonomie.bdc_statut_text AS bst
        ON ((bsctv.id_text = bst.id_text))
    )
    LEFT JOIN
        taxonomie.bdc_statut_values AS bsv
        ON ((bsctv.id_value = bsv.id_value))
    )
    WHERE
        (
            ((bst.cd_type_statut)::text = 'PN'::text)
            AND ((bst.lb_adm_tr)::text = 'France métropolitaine'::text)
        )
    GROUP BY stat_tax.cd_ref, bsv.code_statut
),

n2k AS (
    SELECT
        stat_tax.cd_ref,
        STRING_AGG(
            DISTINCT SPLIT_PART((bsv.label_statut)::text, ' : '::text, 2),
            ', '::text
        ) AS annexe
    FROM (((
        taxonomie.bdc_statut_taxons stat_tax
        LEFT JOIN
            taxonomie.bdc_statut_cor_text_values AS bsctv
            ON ((stat_tax.id_value_text = bsctv.id_value_text))
    )
    LEFT JOIN
        taxonomie.bdc_statut_text AS bst
        ON ((bsctv.id_text = bst.id_text))
    )
    LEFT JOIN
        taxonomie.bdc_statut_values AS bsv
        ON ((bsctv.id_value = bsv.id_value))
    )
    WHERE
        (
            (
                (bst.cd_type_statut)::text
                = ANY(
                    ARRAY[
                        ('DH'::character varying)::text,
                        ('DO'::character varying)::text
                    ]
                )
            )
            AND ((bst.lb_adm_tr)::text = 'France métropolitaine'::text)
        )
    GROUP BY stat_tax.cd_ref
),

berne AS (
    SELECT
        stat_tax.cd_ref,
        bsv.code_statut,
        bsv.label_statut,
        SPLIT_PART((bsv.label_statut)::text, ' : '::text, 2) AS annexe
    FROM (((
        taxonomie.bdc_statut_taxons stat_tax
        LEFT JOIN
            taxonomie.bdc_statut_cor_text_values AS bsctv
            ON ((stat_tax.id_value_text = bsctv.id_value_text))
    )
    LEFT JOIN
        taxonomie.bdc_statut_text AS bst
        ON ((bsctv.id_text = bst.id_text))
    )
    LEFT JOIN
        taxonomie.bdc_statut_values AS bsv
        ON ((bsctv.id_value = bsv.id_value))
    )
    WHERE
        (
            ((bst.cd_type_statut)::text = 'BERN'::text)
            AND ((bst.lb_adm_tr)::text = 'France métropolitaine'::text)
        )
),

bonn AS (
    SELECT
        stat_tax.cd_ref,
        bsv.code_statut,
        bsv.label_statut,
        SPLIT_PART((bsv.label_statut)::text, ' : '::text, 2) AS annexe
    FROM (((
        taxonomie.bdc_statut_taxons stat_tax
        LEFT JOIN
            taxonomie.bdc_statut_cor_text_values AS bsctv
            ON ((stat_tax.id_value_text = bsctv.id_value_text))
    )
    LEFT JOIN
        taxonomie.bdc_statut_text AS bst
        ON ((bsctv.id_text = bst.id_text))
    )
    LEFT JOIN
        taxonomie.bdc_statut_values AS bsv
        ON ((bsctv.id_value = bsv.id_value))
    )
    WHERE ((bst.cd_type_statut)::text = 'BONN'::text)
),

pna_en_cours AS (
    SELECT
        stat_tax.cd_ref,
        bsv.label_statut,
        CASE
            WHEN ((bsv.code_statut)::text = 'true'::text) THEN 'Oui'::text
            ELSE NULL::text
        END AS statut
    FROM (((
        taxonomie.bdc_statut_taxons stat_tax
        LEFT JOIN
            taxonomie.bdc_statut_cor_text_values AS bsctv
            ON ((stat_tax.id_value_text = bsctv.id_value_text))
    )
    LEFT JOIN
        taxonomie.bdc_statut_text AS bst
        ON ((bsctv.id_text = bst.id_text))
    )
    LEFT JOIN
        taxonomie.bdc_statut_values AS bsv
        ON ((bsctv.id_value = bsv.id_value))
    )
    WHERE ((bst.cd_type_statut)::text = 'PNA'::text)
),

pna_ex AS (
    SELECT
        stat_tax.cd_ref,
        bsv.code_statut,
        bsv.label_statut,
        CASE
            WHEN ((bsv.code_statut)::text = 'true'::text) THEN 'Oui'::text
            ELSE NULL::text
        END AS statut
    FROM (((
        taxonomie.bdc_statut_taxons stat_tax
        LEFT JOIN
            taxonomie.bdc_statut_cor_text_values AS bsctv
            ON ((stat_tax.id_value_text = bsctv.id_value_text))
    )
    LEFT JOIN
        taxonomie.bdc_statut_text AS bst
        ON ((bsctv.id_text = bst.id_text))
    )
    LEFT JOIN
        taxonomie.bdc_statut_values AS bsv
        ON ((bsctv.id_value = bsv.id_value))
    )
    WHERE ((bst.cd_type_statut)::text = 'exPNA'::text)
)

SELECT DISTINCT
    cor.groupe_taxo_fr,
    cor.vn_nom_fr,
    cor.vn_nom_sci,
    cor.cd_ref,
    lr_ra.code_statut AS lr_ra,
    lr_aura.code_statut AS lr_aura,
    lr_fr.lr_fr_nich,
    lr_fr.lr_fr_hiv,
    lr_fr.lr_fr_migr,
    lr_euro.code_statut AS lr_euro,
    lr_monde.code_statut AS lr_monde,
    berne.annexe AS conv_berne,
    pna_en_cours.statut AS pna_en_cours,
    pna_ex.statut AS pna_ex,
    ROW_NUMBER() OVER () AS id,
    STRING_AGG(DISTINCT (lr_auv.code_statut)::text, ', '::text) AS lr_auv,
    STRING_AGG(DISTINCT (lr_fr.lr_france)::text, ', '::text) AS lr_france,
    STRING_AGG(DISTINCT (
        CASE
            WHEN (prot_nat.article ~~* '%article%'::text) THEN ''::text
            ELSE 'Article '::text
        END || prot_nat.article
    ), ', '::text) AS prot_nat,
    CASE
        WHEN
            (
                n2k.annexe
                = ANY(
                    ARRAY[
                        'Annexe II, Annexe IV'::text,
                        'Annexe IV, Annexe II'::text
                    ]
                )
            )
            THEN 'Annexes II, IV'::text
        ELSE n2k.annexe
    END AS n2k,
    STRING_AGG(DISTINCT bonn.annexe, ', '::text) AS conv_bonn
FROM (((((((((((((
    taxonomie.taxref t
    LEFT JOIN taxonomie.mv_c_cor_vn_taxref AS cor ON ((t.cd_nom = cor.cd_ref))
)
LEFT JOIN lr_auv ON ((cor.cd_ref = lr_auv.cd_ref)))
LEFT JOIN lr_ra ON ((cor.cd_ref = lr_ra.cd_ref)))
LEFT JOIN lr_aura ON ((cor.cd_ref = lr_aura.cd_ref)))
LEFT JOIN lr_fr ON ((cor.cd_ref = lr_fr.cd_ref)))
LEFT JOIN lr_euro ON ((cor.cd_ref = lr_euro.cd_nom)))
LEFT JOIN lr_monde ON ((cor.cd_ref = lr_monde.cd_nom)))
LEFT JOIN prot_nat ON ((cor.cd_ref = prot_nat.cd_ref)))
LEFT JOIN n2k ON ((cor.cd_ref = n2k.cd_ref)))
LEFT JOIN berne ON ((cor.cd_ref = berne.cd_ref)))
LEFT JOIN bonn ON ((cor.cd_ref = bonn.cd_ref)))
LEFT JOIN pna_en_cours ON ((cor.cd_ref = pna_en_cours.cd_ref)))
LEFT JOIN pna_ex ON ((cor.cd_ref = pna_ex.cd_ref)))
GROUP BY
    cor.vn_nom_fr,
    cor.vn_nom_sci,
    cor.cd_ref,
    lr_ra.code_statut,
    lr_ra.lrra_nich,
    lr_ra.lrra_hiv,
    lr_ra.lrra_migr,
    lr_aura.code_statut,
    lr_fr.lr_fr_nich,
    lr_fr.lr_fr_hiv,
    lr_fr.lr_fr_migr,
    lr_euro.code_statut,
    lr_monde.code_statut,
    n2k.annexe,
    berne.annexe,
    pna_en_cours.statut,
    pna_ex.statut,
    cor.groupe_taxo_fr
WITH NO DATA;

-- View indexes:
CREATE INDEX mv_c_statut_cd_ref_idx ON taxonomie.mv_c_statut USING btree (
    cd_ref
);
CREATE INDEX mv_c_statut_lr_aura_idx ON taxonomie.mv_c_statut USING btree (
    lr_aura
);
CREATE INDEX mv_c_statut_lr_auv_idx ON taxonomie.mv_c_statut USING btree (
    lr_auv
);
CREATE INDEX mv_c_statut_lr_france_idx ON taxonomie.mv_c_statut USING btree (
    lr_france
);
CREATE INDEX mv_c_statut_lr_ra_idx ON taxonomie.mv_c_statut USING btree (lr_ra);

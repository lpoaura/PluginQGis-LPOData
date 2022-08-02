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


drop materialized view taxonomie.mv_statut;
create materialized view taxonomie.mv_statut as (
with 
prep_lrra as (
         SELECT DISTINCT 
                 tx.classe,	
         	sp.id_redlist,
            sp.status_order,
            tx.cd_ref,
            sp.category,
            sp.criteria,
            sp.id_source
           FROM taxonomie.t_redlist sp
             LEFT JOIN taxonomie.taxref tx ON sp.cd_nom = tx.cd_nom
             inner join taxonomie.bib_redlist_source art ON sp.id_source = art.id_source
             where (classe='Aves' or  (classe ='Mammalia' and ordre <>'Chiroptera')) and art.area_name ='Rhône-Alpes'
)
,
prep_statut_lrra as 
(select  distinct
sp.cd_ref ,
CASE
                    WHEN classe!~~*'Aves' AND (id_source <> ALL (ARRAY[18, 19, 20])) THEN sp.category
                    WHEN classe='Aves' AND id_source = 18 THEN sp.category
                    WHEN classe='Aves' AND id_source = 19 THEN (sp.category::text || 'w'::text)::character varying
                    WHEN classe='Aves' AND id_source = 20 THEN (sp.category::text || 'm'::text)::character varying
                    ELSE NULL::character varying
                END AS lrra,
                CASE
                    WHEN sp.id_source = 18 THEN sp.category
                    ELSE NULL::character varying
                END AS lrra_nich,
                CASE
                    WHEN sp.id_source = 19 THEN sp.category
                    ELSE NULL::character varying
                END AS lrra_hiv,
                CASE
                    WHEN sp.id_source = 20 THEN sp.category
                    ELSE NULL::character varying
                END AS lrra_migr
from prep_lrra sp),
prep_lrra_ok as(
select
	cd_ref 
	, string_agg(distinct lrra,', ')  lrra
	, string_agg(distinct lrra_nich,', ') lrra_nich
	, string_agg(distinct lrra_hiv,', ') lrra_hiv
	, string_agg(distinct lrra_migr,', ') lrra_migr
from prep_statut_lrra
group by cd_ref)
,
prep_t_redlist_fr AS (
         SELECT DISTINCT sp.id_redlist,
            sp.status_order,
            tx.cd_ref,
            sp.category,
            sp.criteria,
            sp.id_source,
            groupe_taxo_fr,
            vn_nom_fr,
            vn_nom_sci
           FROM taxonomie.t_redlist sp
             JOIN taxonomie.taxref tx ON sp.cd_nom = tx.cd_nom
             join taxonomie.mv_c_cor_vn_taxref ctx on sp.cd_ref=ctx.cd_ref
             where groupe_taxo_fr='Oiseaux'
        ), prep2 AS (
         SELECT DISTINCT 
         	ptlr.cd_ref,
            groupe_taxo_fr,
            vn_nom_fr,
            vn_nom_sci,
                CASE
                    WHEN groupe_taxo_fr ~~* 'Oiseaux'::text AND ptlr.id_source = 5 THEN ptlr.category
                    WHEN groupe_taxo_fr ~~* 'Oiseaux'::text AND ptlr.id_source = 4 THEN (ptlr.category::text || 'w'::text)::character varying
                    WHEN groupe_taxo_fr ~~* 'Oiseaux'::text AND ptlr.id_source = 3 THEN (ptlr.category::text || 'm'::text)::character varying
                    ELSE NULL::character varying
                END AS lr_france
               ,
                CASE
                    WHEN ptlr.id_source = 5 THEN ptlr.category
                    ELSE NULL::character varying
                END AS lr_fr_nich,
                CASE
                    WHEN ptlr.id_source = 4 THEN ptlr.category
                    ELSE NULL::character varying
                END AS lr_fr_hiv,
                CASE
                    WHEN ptlr.id_source = 3 THEN ptlr.category
                    ELSE NULL::character varying
                END AS lr_fr_migr
           FROM prep_t_redlist_fr ptlr
             LEFT JOIN taxonomie.taxref tr ON ptlr.cd_ref = tr.cd_nom
             LEFT JOIN taxonomie.bib_redlist_source art ON ptlr.id_source = art.id_source
            where cd_nom =2563
        )
, prep_lrf_ok as (SELECT 
    prep2.cd_ref,
    prep2.groupe_taxo_fr,
    prep2.vn_nom_fr,
    prep2.vn_nom_sci,
    string_agg(DISTINCT prep2.lr_france::text, ', '::text) AS lr_france,
    string_agg(DISTINCT prep2.lr_fr_nich::text, ', '::text) AS lr_fr_nich,
    string_agg(DISTINCT prep2.lr_fr_hiv::text, ', '::text) AS lr_fr_hiv,
    string_agg(DISTINCT prep2.lr_fr_migr::text, ', '::text) AS lr_fr_migr
   FROM prep2
  GROUP BY prep2.groupe_taxo_fr, prep2.vn_nom_fr, prep2.vn_nom_sci, prep2.cd_ref
  )
,lr_auv as (
select 
	bs.cd_ref 
	, bs.code_statut 
	, bs.label_statut 
FROM taxonomie.bdc_statut bs 
where bs.cd_type_statut='LRR' and bs.lb_adm_tr='Auvergne'
),	
lr_ra as (
select 
--	bs.cd_nom
	bs.cd_ref 
	, bs.code_statut 
--	, bs.label_statut 
	, null::text as lrra_nich
	, null::text as lrra_hiv 
	, null::text as lrra_migr
FROM taxonomie.bdc_statut bs 
where bs.cd_type_statut='LRR' and bs.lb_adm_tr='Rhône-Alpes'
union
	select cd_ref 
	, lrra
/*	, case when lrra_nich='CR' then 'En danger critique'
		when lrra_nich='EN' then 'En danger'
		when lrra_nich='VU' then 'Vulnérable'
		when lrra_nich='NT' then 'Quasi menacée'
		when lrra_nich='DD' then 'Données insuffisantes'
		when lrra_nich='LC' then 'Préoccupation mineure'
		else null end label_statut*/
	, lrra_nich 
	, lrra_hiv 
	, lrra_migr
from prep_lrra_ok
),
lr_aura as (
select 
	 bs.cd_ref 
	, bs.code_statut 
	, bs.label_statut 
FROM taxonomie.bdc_statut bs 
where bs.cd_type_statut='LRR' and bs.lb_adm_tr='Auvergne-Rhône-Alpes'
),
lr_fr as (
select 
	bs.cd_ref 
	, bs.code_statut lr_france
	, null::text as lr_fr_nich
	, null::text as lr_fr_hiv
	, null::text as lr_fr_migr
FROM taxonomie.bdc_statut bs 
	join taxonomie.taxref on bs.cd_nom =taxref.cd_nom
	where bs.cd_type_statut='LRN' and bs.lb_adm_tr='France métropolitaine' and taxref.classe <>'Aves'
union
select 
	cd_ref, 
	lr_france,
    	lr_fr_nich,
    	lr_fr_hiv,
    	lr_fr_migr
from prep_lrf_ok
),
lr_euro as (
select 
	bs.cd_ref 
	,bs.cd_nom
	, bs.code_statut 
	, bs.label_statut 
FROM taxonomie.bdc_statut bs 
where bs.cd_type_statut='LRE'
),
lr_monde as (
select 
	 bs.cd_ref
	 , bs.cd_nom 
	, bs.code_statut 
	, bs.label_statut 
FROM taxonomie.bdc_statut bs 
where bs.cd_type_statut ='LRM'
)
,
prot_nat as (
select 
	 bs.cd_ref 
	, split_part(label_statut,' : ',2) article
	, bs.code_statut 
	, bs.label_statut 
FROM taxonomie.bdc_statut bs 
where bs.cd_type_statut ='PN' and bs.lb_adm_tr='France métropolitaine'
)
,
n2k as (
select 
	 bs.cd_ref 
	, string_agg(distinct split_part(label_statut,' : ',2),', ') annexe
/*	, bs.code_statut 
	, bs.label_statut */
FROM taxonomie.bdc_statut bs 
where bs.cd_type_statut in ('DH','DO') and bs.lb_adm_tr='France métropolitaine'
group by 1
)
,
berne as (
select 
	 bs.cd_ref 
	, split_part(label_statut,' : ',2) annexe
	, bs.code_statut 
	, bs.label_statut 
FROM taxonomie.bdc_statut bs 
where bs.cd_type_statut ='BERN' and bs.lb_adm_tr='France métropolitaine'
)
, 
bonn as (
select 
	 bs.cd_ref 
	, string_agg(distinct split_part(label_statut,' : ',2),', ') annexe
/*	, bs.code_statut 
	, bs.label_statut */
FROM taxonomie.bdc_statut bs 
where bs.cd_type_statut ='BONN'
group by cd_ref
)
,
pna_en_cours as (
select 
	 bs.cd_ref 
	, case when bs.code_statut ='true' then 'Oui' else null end statut
	, bs.label_statut 
FROM taxonomie.bdc_statut bs 
where bs.cd_type_statut ='PNA'
)
,
pna_ex as (
select 
	 bs.cd_ref 
	, case when bs.code_statut ='true' then 'Oui' else null end statut
	, bs.code_statut 
	, bs.label_statut 
FROM taxonomie.bdc_statut bs 
where bs.cd_type_statut ='exPNA'
)
,
sc38 as 
(select t.cd_ref, sc38_2015  
from lpo38_aat.tabesp1806 tb 
	left join taxonomie.cor_c_vn_taxref ccvt on ccvt.vn_id =tb.id_species
	left join taxonomie.taxref t on ccvt.taxref_id =t.cd_nom
where sc38_2015 is not null)
select distinct
	cor.groupe_taxo_fr,
    cor.vn_nom_fr,
    cor.vn_nom_sci,
    cor.cd_ref,
    lr_auv.code_statut lr_auv,
    lr_ra.code_statut lr_ra
    ,lrra_nich
    , lrra_hiv
    , lrra_migr
    , lr_aura.code_statut lr_aura
    , lr_fr.lr_france
    , lr_fr.lr_fr_nich
    , lr_fr.lr_fr_hiv
    , lr_fr.lr_fr_migr
    , lr_euro.code_statut lr_euro
    , lr_monde.code_statut lr_monde
    , prot_nat.article prot_nat
    , case when n2k.annexe in ('Annexe II, Annexe IV','Annexe IV, Annexe II') then 'Annexes II, IV' else n2k.annexe end n2k
    , berne.annexe conv_berne
    , bonn.annexe conv_bonn
    , pna_en_cours.statut pna_en_cours
    , pna_ex.statut pna_ex
    ,sc38.sc38_2015
from taxonomie.taxref t	
	/*left join (SELECT cor.vn_id, t.cd_ref AS cd_ref 
						FROM taxonomie.mv_c_cor_vn_taxref_dev cor
						LEFT JOIN taxonomie.taxref t ON cor.cd_ref = t.cd_nom) cor ON t.cd_nom =cor.cd_ref*/
	left join (select * from taxonomie.mv_c_cor_vn_taxref_dev mccvtd where vn_utilisation) cor on cor.cd_nom=t.cd_nom
      left join lr_auv on lr_auv.cd_ref=cor.cd_ref
		left join lr_ra on lr_ra.cd_ref=cor.cd_ref
		left join lr_aura on lr_aura.cd_ref=cor.cd_ref
	left join lr_fr on lr_fr.cd_ref=cor.cd_ref
	left join lr_euro on lr_euro.cd_nom=cor.cd_ref
	left join lr_monde on lr_monde.cd_nom=cor.cd_ref
	left join prot_nat on prot_nat.cd_ref=cor.cd_ref
	left join n2k on n2k.cd_ref=cor.cd_ref
	left join berne on berne.cd_ref=cor.cd_ref
	left join bonn on bonn.cd_ref=cor.cd_ref
	left join pna_en_cours on pna_en_cours.cd_ref=cor.cd_ref
	left join pna_ex on pna_ex.cd_ref=cor.cd_ref
	left join sc38 on sc38.cd_ref=cor.cd_ref
where t.cd_nom =t.cd_ref 
	order by groupe_taxo_fr, vn_nom_fr
	);


select * from taxonomie.mv_statut ms where cd_ref =631131;
select * from taxonomie.mv_statut ms where vn_nom_sci ilike '%mustela nivalis%';
select 
tx_nom_sci 
, vn_id 
, count(vcod.*)
from taxonomie.mv_c_cor_vn_taxref_dev mccvtd 
join src_lpodatas.v_c_observations_dev vcod on mccvtd.vn_id =vcod.source_id_sp 
where vn_utilisation is false
group by 1,2;

select * from taxonomie.mv_c_cor_vn_taxref_dev mccvtd where vn_nom_sci ilike 'mustela ni%'


-- intégration de l'ensemble des tables sur bdc_statut
  select distinct
	*
FROM taxonomie.bdc_statut bs 
	 join taxonomie.bdc_statut_text bst on (bst.cd_doc =bs.cd_doc and bst.cd_sig =bs.cd_sig )
	 join taxonomie.bdc_statut_type bsty on bsty.cd_type_statut =bst.cd_type_statut 
	 join taxonomie.bdc_statut_cor_text_values bsctv2 on bsctv2.id_text =bst.id_text
	 join taxonomie.bdc_statut_taxons bst2 on bst2.id_value_text =bsctv2.id_value_text and bst2.cd_nom =bs.cd_nom 
	 join taxonomie.bdc_statut_values bsv on bsv.id_value =bsctv2.id_value and bsv.code_statut =bs.code_statut 
where bst.cd_type_statut='LRN' and bst.lb_adm_tr='France métropolitaine' and bs.cd_ref  =54265 /*and bs.cd_type_statut='ZDET' and bs.lb_adm_tr ilike '%rhôn%'*/
  


-- contrôle de coérence

select cd_ref, count(*) 
from taxonomie.mv_statut ms 
where lr_ra is not null or lr_auv is not null and vn_nom_fr is not null
group by 1
having count(*)>1; 
  



-- bac à sable

select * from taxonomie.mv_statut ms 
join taxonomie.taxref t on t.cd_nom =ms.cd_ref
where ms.cd_ref=54265;


select * from taxonomie.taxref t where cd_nom in (219768,608318);
select * from taxonomie.taxref t where lb_nom ilike 'phyllo%abietinus%';
select * from taxonomie.bdc_statut_type;
select * from taxonomie.bdc_statut_text bst ;
select * from taxonomie.bdc_statut_values bsv  ;
select * from taxonomie.bdc_statut_type;
select * from taxonomie.bdc_statut where lb_adm_tr ilike '%rh%ne-alpes';
select distinct lb_adm_tr from taxonomie.bdc_statut where cd_type_statut ='PN';
select * from taxonomie.bdc_statut where cd_nom =2489 and lb_adm_tr ilike 'auvergne';
select * from taxonomie.bdc_statut where cd_nom =2489 and lb_adm_tr ilike 'france';
select * from taxonomie.bdc_statut_values where code_statut ='NO3'
select * from taxonomie.taxref t where nom_vern ilike '%barge à que%'
select * from taxonomie.taxref t where cd_nom =2492;
select * from taxonomie.taxref t where nom_vern  ilike '%héron g%';


select 
	 bs.cd_ref 
	, bs.code_statut 
	, bs.label_statut 
FROM taxonomie.bdc_statut bs 
where bs.cd_type_statut ='LRM' and cd_nom =69182

select * from taxonomie.mv_c_cor_vn_taxref_dev mccvtd where vn_utilisation and cd_ref =69182;
select * from taxonomie.mv_statut ms where cd_ref =69182;


--
with 
lr_monde as (
select 
	 bs.cd_nom 
	, bs.code_statut 
	, bs.label_statut 
FROM taxonomie.bdc_statut bs 
where bs.cd_type_statut ='LRM'
)
select distinct
/*	cor.groupe_taxo_fr,
    cor.vn_nom_fr,
    cor.vn_nom_sci,
    cor.cd_ref
        , lr_monde.* */
        lr_monde.*
from taxonomie.taxref t	
	/*left join (SELECT cor.vn_id, t.cd_ref AS cd_ref 
						FROM taxonomie.mv_c_cor_vn_taxref_dev cor
						LEFT JOIN taxonomie.taxref t ON cor.cd_ref = t.cd_nom) cor ON t.cd_nom =cor.cd_ref*/
	left join (select * from taxonomie.mv_c_cor_vn_taxref_dev mccvtd where vn_utilisation) cor on cor.cd_nom=t.cd_nom
   	left join lr_monde on lr_monde.cd_nom=cor.cd_ref
where t.cd_nom =t.cd_ref and t.cd_nom =69182
	--order by groupe_taxo_fr, vn_nom_fr
;



select 
	*
FROM taxonomie.bdc_statut bs 
where bs.cd_type_statut ='LRM' and cd_ref =69182


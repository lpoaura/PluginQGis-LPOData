/*****************************************************************************************
 * 			Intégration de la liste statuts à utiliser dans gn_commons.t_parameters
 *****************************************************************************************/

BEGIN;
INSERT INTO gn_commons.t_parameters ( 
       parameter_name, 
       parameter_desc, 
       parameter_value,
       parameter_extra_value
       )
VALUES (
       'plugin_qgis_lpo_status_columns',
       'Liste des colonnes de statuts de protection/conservation à utilisées pour le plugin QGIS LPO'
       , '"{''lr_france'':''LR France'',''lr_r'': ''LR Régionale'',''n2k'':''Natura 2000'',''prot_nat'':''Protection nationale'',''conv_berne'':''Convention de Berne'',''conv_bonn'':''Convention de Bonn''}"'
       , NULL);

COMMIT;

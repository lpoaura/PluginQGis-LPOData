# Filtres personnalisés en langage SQL

📢 Pour chaque traitement, il vous est possible de **filtrer de manière personnalisée** les données traitées, en ajoutant des **clauses "where" en langage SQL** dans les `Paramètres avancés`. Vous trouverez ci-dessous les exemples possibles.

## Filtres classiques

:::{Warning}
A partir de la version `3.0.0`, le `and` en début de requête n'est plus à mentionner.
:::


|Filtrer sur...|Un seul critère|Plusieurs critères|
|-|-|-|
|id espèce VisioNature|`and source_id_sp = 386`|`and source_id_sp in (386, 394, 370)`|
|cd_nom|`and obs.cd_nom = 4001`|`and obs.cd_nom in (4001, 4035, 3764)`|
|Nom vernaculaire|`and t.nom_vern ilike 'Rougegorge familier'` ou `and t.nom_vern ilike '%rougegorge%'`|`and t.nom_vern in ('Rougegorge familier', 'Rougequeue noir', 'Mésange charbonnière')`|
|Nom scientifique|`and t.lb_nom ilike 'erithacus rubecula'`|`and t.lb_nom in ('Erithacus rubecula', 'Phoenicurus ochruros', 'Parus major')`|
|Observateur|`and observateur = 'NOM Prénom'`|`and observateur in ('NOM Prénom', 'NOM Prénom', 'NOM Prénom')`|
|Code de nidification|`and oiso_code_nidif = 1`|`and oiso_code_nidif in (1, 2, 3)`|
|Statut de reproduction (valable pour tous les groupes taxo)|`and statut_repro = 'Certain'`|`and statut_repro in ('Certain', 'Probable', 'Possible')`|
|Cause de mortalité|`and mortalite_cause = 'ROAD_VEHICLE'`|`and mortalite_cause in ('ROAD_VEHICLE', 'HUNTING')`|
|Code étude|`and code_etude = 'EPOC'`|`and code_etude in ('EPOC', 'EPOC-ODF')`|

La fonction `ilike` permet de s'affranchir des majuscules et minuscules. Le % remplace un ou plusieurs caractères (et ne fonctionne qu'avec ilike).


## Autres filtres plus complexes

- Filtrer sur l'**altitude** :
  - Entre deux altitudes : `and altitude >= 1000 and altitude < 2000`
  - Sous un seuil d'altitude et au-dessus d'un autre seuil : `and (altitude <= 1000 or altitude > 2000)`
- Filtrer sur la **mortalité** :
  - Ne garder que les données de mortalité : `and mortalite = true`
  - Exclure les données de mortalité : `and mortalite = false`
- Rechercher un mot ou une expression dans les **commentaires** : `and commentaires like '%mangeoire%'`
- Filtrer sur le **comportement** :
  - Rechercher un comportement particulier : `and comportement @> '{"Se nourrit"}'`
  - Rechercher plusieurs comportements <u>simultanés</u> : `and comportement @> '{"Se nourrit", "Se déplace"}'`
  - Rechercher plusieurs comportements pas forcément simultanés : `and (comportement @> '{"Se nourrit"}' or comportement @> '{"Se déplace"}')`

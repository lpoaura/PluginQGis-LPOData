# Filtres personnalisés en langage SQL

📢 Pour chaque traitement, il vous est possible de **filtrer de manière personnalisée** les données traitées, en ajoutant des **clauses "where" en langage SQL** dans les `Paramètres avancés`. Vous trouverez ci-dessous les exemples possibles.

## Filtres classiques

:::{Warning}
Pour les versions antérieures à la version `3.0.0` un `and` en début de requête est plus à ajouter (ne concerne pas la LPO AuRA).
:::

:::{Info}
**Pour tout le monde, en cas de cumul de plusieurs clauses de recherche, il faut les séparer avec un `and`**.
:::

|Filtrer sur...|Un seul critère|Plusieurs critères|
|-|-|-|
|id espèce VisioNature|`source_id_sp = 386`|`source_id_sp in (386, 394, 370)`|
|cd_nom|`obs.cd_nom = 4001`|`obs.cd_nom in (4001, 4035, 3764)`|
|Nom vernaculaire|`t.nom_vern ilike 'Rougegorge familier'` ou `t.nom_vern ilike '%rougegorge%'`|`t.nom_vern in ('Rougegorge familier', 'Rougequeue noir', 'Mésange charbonnière')`|
|Nom scientifique|`t.lb_nom ilike 'erithacus rubecula'`|`t.lb_nom in ('Erithacus rubecula', 'Phoenicurus ochruros', 'Parus major')`|
|Observateur|`observateur = 'NOM Prénom'`|`observateur in ('NOM Prénom', 'NOM Prénom', 'NOM Prénom')`|
|Code de nidification|`oiso_code_nidif = 1`|`oiso_code_nidif in (1, 2, 3)`|
|Statut de reproduction (valable pour tous les groupes taxo)|`statut_repro = 'Certain'`|`statut_repro in ('Certain', 'Probable', 'Possible')`|
|Cause de mortalité|`mortalite_cause = 'ROAD_VEHICLE'`|`mortalite_cause in ('ROAD_VEHICLE', 'HUNTING')`|
|Code étude|`code_etude = 'EPOC'`|`code_etude in ('EPOC', 'EPOC-ODF')`|

La fonction `ilike` permet de s'affranchir des majuscules et minuscules. Le `%` remplace un ou plusieurs caractères (et ne fonctionne qu'avec ilike).

:::{Info}
Le langage SQL est sensible aux caractères accentué `mésange`est différent de `mesange`. Par ailleurs, il est possible d'utiliser `%` pour remplacer un ou plusieurs caractères.
:::


## Autres filtres plus complexes

- Filtrer sur l'**altitude** :
  - Entre deux altitudes : `altitude >= 1000 and altitude < 2000`
  - Sous un seuil d'altitude et au-dessus d'un autre seuil : `(altitude <= 1000 or altitude > 2000)`
- Filtrer sur la **mortalité** :
  - Ne garder que les données de mortalité : `mortalite = true`
  - Exclure les données de mortalité : `mortalite = false`
- Rechercher un mot ou une expression dans les **commentaires** : `commentaires like '%mangeoire%'`
- Filtrer sur le **comportement** :
  - Rechercher un comportement particulier : `comportement @> '{"Se nourrit"}'`
  - Rechercher plusieurs comportements <u>simultanés</u> : `comportement @> '{"Se nourrit", "Se déplace"}'`
  - Rechercher plusieurs comportements pas forcément simultanés : `(comportement @> '{"Se nourrit"}' or comportement @> '{"Se déplace"}')`

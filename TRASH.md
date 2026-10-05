# Corbeille commune — Android et Linux 3.8

Android 3.8 (code 35) et Linux 3.8.

## Utilisation

Installer les deux versions 3.8 avec le même compte et au moins un relais commun. Dans une note publiée, Supprimer propose son déplacement dans la corbeille. Les modifications non publiées sont abandonnées seulement après confirmation. Le bouton Corbeille affiche les notes retirées de la liste principale. Une note de la corbeille est consultable mais ne peut pas être modifiée : Restaurer la note la remet dans la liste principale, avec son contenu, son épinglage et sa sauvegarde précédente.

Supprimer définitivement, depuis la corbeille, demande une confirmation distincte. Aucune expiration, aucun vidage programmé, aucune tâche de suppression automatique. Les suppressions sont individuelles et manuelles. Une demande aux relais ne garantit pas l’effacement de toutes leurs copies.

Après une action, utiliser Actualiser sur l’autre application. Une modification de corbeille exige l’acceptation d’au moins un relais ; si tous échouent, l’état local reste inchangé et l’action doit être recommencée manuellement. Pas de file d’actions hors connexion. La consultation du cache reste possible.

Les versions publiques 3.7.1 et antérieures ignorent la corbeille et peuvent encore afficher ses notes comme actives. Utiliser les deux versions 3.8 ; ne pas employer Supprimer dans une ancienne version pour tester la corbeille.

## Protocole et conflits

Événement signé kind 30078, tag d = `notestr/trash/` + SHA-256 UTF-8 de l’identifiant de note, contenu NIP-44 pour soi-même contenant exactement `true` ou `false`. État distinct de la note kind 33457, sans réécriture du Markdown. Classement des états concurrents : timestamp le plus élevé puis identifiant d’événement le plus petit, comme NIP-01. Deux actions dans la même seconde sur l’état local sont refusées ; recommencer manuellement une seconde plus tard. Pas d’expiration publiée.

Une suppression définitive kind 5 vise la note, sa sauvegarde, son épinglage et son état de corbeille. Pour ces nouveaux clients, cette adresse de note reste définitivement supprimée même si un ancien client publie une version tardive : recréer une note utilise une nouvelle adresse. Le cache supprime les contenus chiffrés visés et conserve le marqueur de suppression. Cela ne signifie pas un effacement sécurisé des blocs du disque ni de toutes les copies distantes. Les états inconnus ou indéchiffrables ne sont pas transformés silencieusement en restauration.

La convergence exige que les deux clients reçoivent les événements pertinents. Les limites de récupération des relais restent celles de l’application ; une synchronisation partielle n’est pas une garantie de cohérence globale.

## Validation et limites

Données de test synthétiques uniquement (scalaire privé public 1 identifié comme tel). Tests de protocole, cache, échecs de relais, conflit, suppression terminale, interface et échanges chiffrés Android/Linux. Aucun compte personnel ni relais public utilisé pour ces tests. Les tests physiques dépendent des appareils disponibles.

Les réserves natives de sécurité de 3.7.1 restent ouvertes. Le contrôle du 4 octobre identifie aussi quatre avis supplémentaires analysés dans le rapport natif ; aucun nouveau candidat Ubuntu disponible dans les index consultés. Ne pas présenter ces paquets comme exempts de vulnérabilité. TOAST UI reste archivé.

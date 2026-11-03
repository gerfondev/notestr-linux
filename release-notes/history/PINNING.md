# Épinglage synchronisé — version 3.6

Version commune Android/Linux 3.6. Android : versionCode 22.

## Utilisation

Android : icône d’épingle à droite de chaque note dans la liste. Linux : sélectionner une note, puis utiliser l’épingle dans la barre d’actions. L’infobulle devient « Désépingler » lorsque la note est épinglée. Une marque distingue les notes épinglées.

Les notes épinglées apparaissent en premier, puis chaque groupe est classé par date de modification décroissante et identifiant croissant en cas d’égalité. L’épinglage ne modifie ni le texte, ni la date, ni la sauvegarde précédente. Sous Linux, il préserve également le brouillon ouvert.

L’action exige l’acceptation d’au moins un relais configuré. Un refus de tous les relais conserve l’état précédent. Utiliser le même compte et au moins un relais commun, puis Actualiser sur l’autre appareil. Le cache chiffré permet de retrouver le dernier état connu après redémarrage. Les mises à jour réalisées hors connexion ne sont pas mises en attente.

## Format partagé v1

Événement Nostr signé kind 30078, tag `d` = `notestr/pin/` + SHA-256 hexadécimal minuscule de l’identifiant de note encodé UTF-8. Contenu NIP-44 v2 chiffré vers soi-même : chaîne exacte `true` ou `false`. Aucun titre ni texte clair ajouté aux tags. Les identifiants de note sont déjà publics dans leurs événements ; leur hash ne constitue pas une anonymisation.

À adresse égale, timestamp le plus récent, puis ID d’événement lexicographiquement le plus petit à timestamp égal. Signature et auteur vérifiés avant utilisation. Un changement local à la même seconde ou avant le dernier état connu est refusé : réessayer la seconde suivante. Deux changements simultanés de la même note convergent selon cette règle ; les changements sur des notes distinctes sont indépendants.

Le préfixe `notestr/previous/` des sauvegardes reste séparé. Le cache ne conserve que le dernier état d’épinglage par adresse, y compris `false`, afin d’éviter le retour d’un ancien épinglage. Les métadonnées malformées ne changent pas le contenu des notes. Les anciennes applications ignorent ce statut ; elles peuvent l’éliminer de leur cache, mais ne le suppriment pas du relais.

## Limites

Pas de classement manuel entre épingles. La synchronisation dépend des relais et des horloges des appareils. Android conserve sa limite de récupération de 2 000 événements par kind ; la pagination exhaustive reste à prévoir. Le statut chiffré peut rester sur les relais après suppression de la note ; une note supprimée n’apparaît pas dans la liste. Amber réel, téléphone physique et tous les comportements d’accessibilité restent à tester.

# Notestr 3.8 — Android et Linux

## Nouveautés

- **Corbeille commune** : déplacer une note dans la corbeille, la consulter, la restaurer ou la supprimer définitivement depuis Android ou Linux. Les actions sont synchronisées par les relais. Aucun vidage automatique ni délai d’expiration : la suppression définitive reste individuelle et manuelle, avec confirmation.
- **Délai de verrouillage Android de 3 minutes** en arrière-plan. Un retour avant ce délai conserve la session ; le bouton Verrouiller reste immédiat. Le temps écoulé est vérifié au retour même si Android a suspendu l’application. Si le processus est fermé par Android, un nouveau déverrouillage est nécessaire.
- **Modifications hors connexion** : Envoyer/Publier enregistre localement une version signée et chiffrée. Les envois reprennent avec la connexion et une session déverrouillée. Les changements en attente survivent au redémarrage ; un conflit conserve la version distante et propose explicitement de publier une copie ou d’abandonner la modification locale.

## Corrections

- Chargement Android après biométrie ou mot de passe accéléré ; suppression de traitements bloquants sur le fil de l’interface et amélioration du traitement des événements supprimés.
- Notes de la corbeille Android affichées en mode visuel et en lecture seule, avec liens accessibles.
- Bouton Corbeille/Notes explicite sur Android ; alignement de Corbeille avec Visuel et Markdown sous Linux.
- Protection des brouillons et des modifications locales pendant la synchronisation ; gestion des modifications concurrentes et des réponses tardives renforcée.

## Installation et fonctionnement

Mettre à jour **les deux applications vers 3.8** pour utiliser la corbeille commune ; les anciennes versions l’ignorent. Installer l’APK par-dessus la version actuelle sans désinstaller. Android versionCode 35, certificat conservé. Linux : AppImage x86_64 pour glibc 2.39 ou ultérieure, wheel et archive source disponibles.

L’enregistrement hors connexion concerne les notes ; déplacer/restaurer/supprimer dans la corbeille exige une connexion et l’acceptation d’un relais. La reprise automatique des notes nécessite une lecture complète des relais configurés ; un relais inaccessible peut la retarder. Une demande de suppression ne garantit pas l’effacement de toutes les copies conservées par les relais. Enregistrer les brouillons avant une absence prolongée : les modifications non enregistrées sont perdues au verrouillage.

## Sécurité et confidentialité

Contrôles des versions, avis de sécurité, sources et paquets renouvelés. Les composants corrigés déjà qualifiés sont conservés lorsqu’aucune nouvelle mise à jour corrective compatible n’est disponible. Les réserves de maintenance et d’exposition restent décrites dans SECURITY-REVIEW.md : notamment TOAST UI archivé et avis natifs Linux analysés. Ces vérifications ciblées ne constituent pas un audit exhaustif ni une garantie d’absence de vulnérabilité. Anciennes métadonnées d’auteur déjà publiques conservées, sans réécriture des historiques. Chaque paquet est accompagné de son empreinte SHA-256.

# Version et langue — candidats locaux du 1er octobre 2026

Android 3.6-test.25 (versionCode 25) ; Linux 3.6.dev25. Aucune publication, aucun push, tag distant ou téléversement. Les copies de publication 3.6 restent inchangées.

## Nouveautés et essai

Dans les paramètres, le numéro de version affiché provient de la version compilée. Le français reste le choix initial.

- Android : ouvrir Réglages, choisir English. Les libellés changent immédiatement. Revenir aux notes, ouvrir une note, vérifier les outils de mise en forme et Copier/Copy. Revenir aux paramètres pour choisir Français. Le choix est conservé après fermeture et réouverture.
- Linux : ouvrir Compte et relais, choisir Français ou English, puis Enregistrer la langue. Fermer et relancer Notestr pour appliquer ce choix. Ce bouton est indépendant de l’enregistrement du compte et des relais. Les paramètres défilent sur les petits écrans.
- La langue ne traduit pas le contenu des notes et ne modifie pas leur chiffrement ni les événements Nostr. Les dialogues fournis par le système et les erreurs brutes de bibliothèques peuvent conserver la langue du système ou de la bibliothèque.

Installer l’APK par-dessus le candidat précédent. Rendre l’AppImage exécutable si nécessaire puis le lancer. Sauvegardes préalables des sources dans sauvegardes/avant-langues-2026-10-01.

## Validation

14 tests JVM et 28 tests Android instrumentés réussis, dont changement de langue, persistance, version installée, éditeur anglais, conservation du Markdown, clavier, sauvegardes, épinglage et Amber simulé. 70 tests Python réussis. Tests graphiques sur le paquet AppImage final : paramètres anglais, préférence française appliquée à la réouverture, texte préservé, modes de l’éditeur, chiffrement et export PDF.

Signature v2 et certificat Android inchangés, APK non débogable, alignement 16 Ko vérifié. Comparaison des bibliothèques natives Android avec les AAR contrôlés et du contenu AppImage après extraction. Contrôles ciblés sur 4 160 entrées des paquets, sans marqueur personnel recherché détecté. Cinq clés publiques d’autotest GnuTLS classifiées par empreinte. Contrôles non exhaustifs ; comptes et notes synthétiques uniquement.

699 coordonnées OSV sans alerte retournée et métadonnées officielles reconsultées sans erreur ; 181 paquets natifs comparés aux index Ubuntu actualisés, aucune mise à jour supplémentaire proposée. Pas de nouvelle dépendance. Sources et images conservées ou contrôlées ; historiques de publication inchangés, hors paquets locaux.

**Réserve Linux préexistante : WSA-2026-0006.** WebKitGTK 2.52.6 proposé par Ubuntu Noble reste inférieur à la version amont corrigée 2.54.0. Les restrictions de contenu limitent l’exposition sans garantir son absence. Une version compatible corrigée ou un correctif rétroporté vérifié reste nécessaire avant publication. Réserve de maintenance TOAST UI archivé également conservée.

Les empreintes des deux paquets figurent dans SHA256SUMS.txt.

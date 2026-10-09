# Candidats locaux — menu des liens

Linux 3.6.dev24 et Android 3.6-test.24 (versionCode 24), 1er octobre 2026. Aucune publication GitHub.

## À tester

- Linux : ouvrir une note contenant un lien HTTP/HTTPS, passer la souris dessus (curseur main), puis clic droit et « Ouvrir le lien dans le navigateur ». Vérifier le navigateur par défaut et que la note conserve son texte. « Copy Link Location » reste disponible.
- Le clic gauche conserve son fonctionnement. Un menu ouvert sur une ancienne note ne doit pas agir après un changement de note.
- Android : ouverture habituelle des liens conservée ; curseur main avec une souris connectée. Aucun menu supplémentaire ajouté pour l’appui long.

Installer l’APK par-dessus la version locale précédente. Pour Linux, rendre l’AppImage exécutable si nécessaire, puis le lancer. Sauvegardes des sources avant modification dans sauvegardes/avant-menu-liens-2026-10-01.

## Contrôles

68 tests Python, 14 tests JVM, 10 tests instrumentés Android réussis. Test graphique du vrai menu contextuel : action transmise au lanceur externe, note et adresse interne de l’éditeur conservées ; appel du lanceur intercepté pour ne pas ouvrir un site pendant le test. Tests graphiques et export PDF du paquet AppImage réussis. L’association réelle au navigateur reste à vérifier sur votre poste.

Signature v2 Android et certificat inchangés, APK non débogable, alignement 16 Ko vérifié. Contenu Linux comparé après extraction ; bibliothèques Android comparées aux AAR contrôlés. Contrôles ciblés de 4 159 entrées : aucun marqueur personnel recherché détecté. Les cinq clés d’autotest publiques GnuTLS sont classifiées par empreinte ; ces contrôles ne sont pas exhaustifs.

699 requêtes OSV sans alerte retournée et métadonnées officielles reconsultées ; 181 paquets natifs comparés aux index Ubuntu actualisés, aucune mise à jour supplémentaire proposée. Dépendances inchangées depuis le candidat 23.

**Réserve Linux conservée : WSA-2026-0006.** WebKitGTK 2.52.6 fourni par Ubuntu Noble reste inférieur à la version amont corrigée 2.54.0. Les restrictions de contenu réduisent l’exposition sans garantir son absence. Ce candidat reste destiné au test local ; moteur corrigé compatible ou correctif rétroporté vérifié nécessaire avant publication. TOAST UI archivé : réserve de maintenance conservée.

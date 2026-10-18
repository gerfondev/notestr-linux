# Notestr 3.6

Les versions Android et Linux portent désormais le même numéro : **3.6**. Cette version remplace Android 2.0 et Linux 3.5.2.

## Nouveautés et corrections

- Possibilité d’épingler plusieurs notes en tête de liste. Les notes épinglées restent classées entre elles par date de modification décroissante.
- Épinglage et désépinglage chiffrés, signés et envoyés aux relais. Sur l’autre appareil, **Actualiser** récupère le statut avec le même compte et un relais commun.
- Épingle barrée pour l’action **Désépingler**, sur Android et Linux ; infobulles et descriptions accessibles.
- Texte, date et sauvegarde précédente de la note conservés lors de l’épinglage. Le brouillon ouvert sur Linux est également préservé.
- En cas de refus de tous les relais, l’état précédent est conservé et une erreur est affichée.

## Sécurité et confidentialité

Linux intègre DOMPurify 3.4.16 et retire l’ancien filtre HTML interne de l’éditeur. L’AppImage inclut les correctifs Ubuntu de cURL (8.5.0-2ubuntu10.15) et Expat (2.6.1-2ubuntu0.6), en complément des mises à jour Kerberos précédentes. Les exemples de clé privée présents dans la documentation embarquée d’une dépendance sont retirés du paquet.

Android conserve le SDK Nostr natif corrigé, JNA aux métadonnées nettoyées et DOMPurify 3.4.16. Le contrôle renouvelé ne signale pas de correctif supplémentaire nécessaire dans les versions inventoriées. Les dépendances, sources et paquets font l’objet de contrôles ciblés avant publication ; ces vérifications ne constituent pas un audit exhaustif. TOAST UI reste archivé et devra être remplacé à terme.

## Installation

Android : installer le nouvel APK par-dessus la version existante, sans désinstaller l’application. Certificat conservé, APK non débogable, versionCode 22.

Linux : fermer l’ancienne application avant de lancer l’AppImage 3.6. Les notes et réglages existants sont conservés. L’AppImage x86_64 cible Ubuntu 24.04 / Zorin OS 18 et glibc 2.39 ou ultérieure. Le wheel et l’archive source Python sont également fournis.

Les fichiers SHA-256 accompagnent les paquets. Les limites de validation et les détails du protocole figurent dans les documents de sécurité et PINNING.md de chaque dépôt. Les historiques Git et les anciennes versions sont conservés.

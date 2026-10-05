# Version 3.8 — contrôle du 5 octobre 2026

Android 3.8 (code 35), Linux 3.8. Publication GitHub demandée explicitement pour les deux applications. Corbeille commune manuelle, modification chiffrée hors connexion, correction des blocages Android, corbeille visuelle et boutons clarifiés/alignés. Android : verrouillage après 180 000 ms en arrière-plan, horloge monotone et contrôle au retour, verrouillage manuel immédiat. Aucun vidage automatique de la corbeille. Sauvegardes préalables des sources effectuées.

## Dépendances et exposition

699 coordonnées directes/transitives et registres officiels reconsultés, bibliothèques JavaScript, Rust/JNA, outils de compilation et maintenance inclus : aucune alerte OSV applicative retournée ni erreur de récupération. Deux versions stables nouvelles intégrées sous Linux : aiohttp 3.14.4 et cachetools 7.2.1 ; empreintes des wheels vérifiées sur PyPI, nouveaux numéros interrogés dans OSV sans alerte retournée. Les versions natives et Android qualifiées sont conservées. Index Ubuntu rafraîchis : aucune nouvelle version candidate pour les 191 composants de référence. Chaîne Gradle/JDK/SDK conservée selon les exceptions de compatibilité antérieures ; absence d’alerte ne signifie pas absence de risque.

WebKitGTK/JavaScriptCore 2.54.0 embarqué : les neuf avis Ubuntu récemment indexés renvoient à WSA-2026-0006, déjà corrigé dans ce moteur ; les métadonnées Ubuntu 2.52.6 ne décrivent pas le binaire remplacé. Les autres réserves de l’analyse native étendue de 3.7.1 et les quatre avis additionnels d’octobre restent documentés dans release-3.8-native-exposure.json, sans les réduire aux seuls codecs. TOAST UI demeure archivé ; rendu assaini par DOMPurify et réseau de l’éditeur restreint. WebView Android fourni par le système. Les paquets ne sont pas déclarés exempts de vulnérabilité.

## Validation

14 tests JVM. Suite principale Android : 45 tests signalés (cas relais désactivé dans cette suite), une assertion de position du clavier en échec ; reprise isolée réussie. Suite sur relais local : 8 tests réussis, comprenant cette reprise et sauvegarde/corbeille/hors connexion ; 2 tests biométriques réussis. 48 cas Android distincts exercés, avec limite d’intermittence du test clavier conservée. Émulateur Android 11/API30, pas d’essai physique Android17. 92 tests Python réussis avec les dépendances actualisées, pip check sans incompatibilité. Essais GTK du moteur embarqué : enregistrement/reprise/conflits et copie, corbeille manuelle et alignement.

## Confidentialité et livraison

Contrôles ciblés des sources destinées à publication, ressources, métadonnées d’images, fichiers de revue et historiques. Comptes et notes synthétiques uniquement pour les tests, clés de test identifiées. Les anciens commits publics portant une identité d’auteur personnelle restent dans l’historique (3 Android, 2 Linux avant publication), sans réécriture. Les nouveaux commits utilisent une identité générique. Les contrôles ciblés ne garantissent pas l’absence de toute donnée inconnue ou encodée.

Paquets : examens du contenu décompressé, signature/certificat et alignement de l’APK, comparaison des bibliothèques natives avec les AAR contrôlés, comparaison de l’AppImage extraite avec l’AppDir et anonymisation des propriétaires de l’archive Python. Rapports datés, empreintes et résultats finaux dans security/release-3.8-*.json. Les fichiers de travail locaux, caches de compte, keystores et journaux bruts ne font pas partie des livrables. Notes utilisateur dans RELEASE-NOTES-3.8.md.

---

# Version 3.7.1 — 3 octobre 2026

Correction du collage natif dans les champs URL et Texte du lien de l’éditeur visuel, sur Android et Linux. Android versionCode 28. Publication GitHub explicitement autorisée pour cette version. Sauvegardes des sources réalisées avant préparation.

## Dépendances et réserves

699 coordonnées Android, JavaScript, Rust, Python et outils de compilation réinterrogées : aucune nouvelle alerte OSV retournée, aucune erreur de métadonnées. Versions stables et maintenance consultées sur les registres officiels. Les composants applicatifs examinés restent aux versions qualifiées de 3.7. TOAST UI 3.2.2 est archivé ; DOMPurify 3.4.16 et les restrictions de contenu sont conservés. WebView Android dépend du système.

Index Ubuntu isolés rafraîchis : 191 composants de référence contrôlés ; libgbm1 passe à 25.2.8-0ubuntu0.24.04.4, testé dans le paquet final. WebKitGTK/JavaScriptCore 2.54.0 et leurs typelibs restent ceux compilés pour 3.7. Aucun autre candidat Ubuntu plus récent trouvé dans ce périmètre.

Le contrôle natif élargi à 137 paquets sources a retourné 140 signalements bruts pour 31 paquets. Deux proviennent de métadonnées de l’ancien WebKit 2.52.6 alors que le moteur distribué est 2.54.0. Les autres sont analysés par famille dans `security/release-3.7.1-native-exposure.json` : outils ou fonctions non utilisés, architectures différentes, erreurs d’attribution de composants Python, restrictions de contenu et risques résiduels. **Ils ne sont pas annoncés tous corrigés ni tous inexploitables.** Le précédent résumé limité aux cinq avis de codecs n’était pas un inventaire complet des avis natifs.

Les versions Ubuntu maintenues sont conservées pour compatibilité ABI en l’absence de candidats corrigés dans les index consultés. Les images et SVG des notes sont exclus, le HTML brut et les accès réseau de l’éditeur restreints, les relais utilisent Python websockets. Cela réduit certaines expositions sans démontrer leur absence. Points à suivre : rendu Cairo/HarfBuzz, chemins indirects libsoup/GTK, IDNA Python, aperçus du sélecteur de fichiers et serveur X non fiable. Une migration des bibliothèques amont et de TOAST UI exige une qualification dédiée. Ces limites sont explicites ; aucune certification « sans vulnérabilité » n’est donnée.

## Validation et confidentialité

14 tests JVM, 29 tests Android instrumentés sur l’APK final, 75 tests Python. Collage Linux natif : URL, remplacement, libellé, annulation conservant le Markdown et insertion préservant les titres/listes. Paquet AppImage final : moteur 2.54.0, éditeur, paramètres/version/langues et export PDF validés. APK non débogable, signature v2/certificat conservés, alignement 16 Ko et bibliothèques natives comparées aux AAR examinés.

Sources, images/métadonnées, historique et paquets décompressés soumis aux contrôles ciblés de chemins personnels, identités connues, clés privées et jetons. Aucun marqueur recherché non expliqué détecté. Les cinq clés publiques de test GnuTLS sont identifiées par empreinte. Archives Python sans identité du compte de construction. Tests exclusivement synthétiques ; aucune note, capture personnelle, base locale ou journal brut distribué.

Des identités personnelles préexistantes restent dans les anciens commits publics ; historique conservé et nouveaux commits avec identité neutre du projet. Les vérifications ne sont pas exhaustives et peuvent manquer des données inconnues ou encodées. Empreintes et résultats datés dans les rapports `security/release-3.7.1-*.json`.

---


# Contrôles de sécurité — Notestr Linux 3.9 (9 octobre 2026)

Les artefacts livrés sont l’AppImage x86_64, le wheel et l’archive source. Leurs empreintes sont enregistrées dans `SHA256SUMS` joint aux livrables. Le texte GPLv3 est inclus dans l’AppImage, le wheel et l’archive source.

Les versions de 191 paquets Ubuntu présents dans l’AppImage ont été comparées à des index officiels actualisés ; sept bibliothèques ont été mises à jour (libsoup 3.4.4-5ubuntu0.9, FreeType 2.13.2+dfsg-1ubuntu0.2, libpng 1.6.43-5ubuntu0.7, librsvg 2.58.0+dfsg-1ubuntu0.1 et libxml2 2.9.14+dfsg-1.3ubuntu3.10). WebKitGTK/JavaScriptCore 2.54.0 reste la version corrigée par l’avis de sécurité WSA-2026-0006 ; le correctif ProseMirror GHSA-c8x8-7fp4-3x9w est fourni par le bundle reconstruit avec `prosemirror-view` 1.42.6. Les composants d’outils/tests du workspace npm historique gardent 178 alertes d’audit ; ils ne sont pas embarqués. Les réserves natives antérieures de `security/release-3.8-native-exposure.json` restent applicables.

103 tests Python réussissent. Le test GTK/WebKit de l’AppImage vérifie l’insertion et le rendu d’image à l’emplacement du curseur, l’ouverture de la visionneuse, le zoom, le déplacement, la réinitialisation, la fermeture sans modifier la note, les paramètres/relais, la langue et l’export PDF. WebKitGTK 2.54.0 a été vérifié dans le paquet.

Un scan ciblé des sources et du contenu décompressé n’a trouvé aucun chemin personnel du propriétaire, identifiant privé `nsec` complet ni jeton GitHub. Trois fichiers système contiennent des marqueurs PEM (deux bibliothèques système et le code de sérialisation cryptographique) ; aucun fichier de clé propre au compte n’est livré. Des adresses électroniques apparaissent dans les licences et avis d’attribution de composants tiers. Ce scan n’est pas exhaustif. Les anciennes identités d’auteur de l’historique public restent inchangées.

---

# Zoom et déplacement des images — candidat local Linux du 9 octobre 2026

Linux 3.8.dev46, AppImage SHA-256 `4db35faaab58229bd04c34d64a78227044462a7f87f261e8a65b0212460e9c8a`. La visionneuse permet zoom +/−, réinitialisation, molette/double-clic, déplacement à la souris, pincement tactile et déplacement clavier. Les gestes sont bornés et n’altèrent pas la note.

102 tests Python et test graphique GTK/WebKit de l’AppImage réussis ; moteur embarqué WebKitGTK 2.54.0. Aucune dépendance ni bibliothèque native modifiée. Dernier audit large du 6 octobre ; pas de revue complète de registres le 9 octobre. GHSA-c8x8-7fp4-3x9w / CVE-2026-104847 de ProseMirror/TOAST UI et réserves natives de 3.8 restent ouvertes.

Le scan ciblé des 3 832 fichiers n’a trouvé aucun chemin local nominatif du propriétaire. L’unique sous-chaîne de nom ressemblant à celui du propriétaire est une attribution d’artiste tierce préexistante dans le copyright Adwaita. Les occurrences `nsec1` sont des chaînes WebKit et le validateur de format applicatif, pas des clés de compte complètes. Trois en-têtes PEM de clé privée apparaissent dans les vecteurs de test de `libgnutls.so.30` ; l’inventaire reste à rapprocher d’une classification antérieure de cinq clés, car les méthodes de comptage diffèrent. Pas d’affirmation d’absence de risque. Candidat local uniquement, aucune publication.

Rapport : `../../App Android/livrables/test-zoom-images-40-46/security/zoom-pan-images-2026-10-09.json`.

---

# Visionneuse d’images — candidat local Linux du 9 octobre 2026

Linux 3.8.dev45, AppImage SHA-256 `f3af555c196b82e1683608761f69c0c0ac4fb28adf1178d5d514639fab5b7237`. Un clic sur une image déjà déchiffrée ouvre une vue agrandie ; Échap, la croix ou le fond la referment. Aucun changement du Markdown ni téléchargement supplémentaire.

102 tests Python réussis. Test graphique de l’AppImage réussi avec GTK/WebKitGTK 2.54.0, dont l’ouverture/fermeture de l’image, la conservation de la note, le rendu de l’éditeur, les paramètres/langues et l’export PDF.

Aucune dépendance ni bibliothèque native modifiée. Dernier audit large du 6 octobre ; pas de nouvel audit complet de registres le 9 octobre. L’avis GHSA-c8x8-7fp4-3x9w / CVE-2026-104847 de ProseMirror embarqué dans TOAST UI demeure ouvert. Le contrôle ciblé des 3 832 entrées ne relève ni chemin/nom du propriétaire ni clé `nsec`. Il trouve 10 blocs PEM de clé complets dans `libgnutls.so.30`. Cette bibliothèque est identique à celle du candidat 3.8.dev36 précédemment contrôlé et décrite comme contenant des vecteurs d’autotest publics ; le présent décompte diffère des cinq clés explicitement classées dans le précédent rapport et doit être rapproché avant distribution publique. Les autres réserves natives restent applicables.

Candidat local uniquement, aucune publication. Rapports et empreintes : `livrables/test-plein-ecran-images-39-45/security/plein-ecran-images-2026-10-09.json`.

---

# Rendu visuel des images — candidat Linux local 3.8.dev44, 9 octobre 2026

AppImage SHA-256 `ed463dd9f2e392040f99766d515ba8a4747dfc418308abc5a35cc7493e3d5478`. Le défaut venait de Toast UI : son modèle WYSIWYG supprimait la source temporaire, et le code ciblait la prévisualisation Markdown cachée. Les images chiffrées utilisent maintenant un marqueur local réservé, sont conservées dans le modèle de l’éditeur, puis le déchiffrement remplit l’élément réellement éditable. La politique CSP continue à bloquer toute connexion du WebView.

102 tests Python réussis. Contrôles sur l’AppImage : auto-vérification, GTK4/libadwaita, chiffrement Nostr, WebKitGTK 2.54.0, tests graphiques d’éditeur, langue et export PDF. Le test de la référence exacte a confirmé un JPEG de 1 055 px de largeur et une géométrie visible de 671 × 948 px dans la zone Visuel ; le Markdown original reste inchangé. Le clair n’a été ni enregistré ni inspecté. Le test synthétique couvre aussi l’insertion au curseur et le retour Visuel/Markdown.

Scan ciblé des sources modifiées : aucun chemin local nominatif du propriétaire, courriel, `nsec` complet ou code de diagnostic temporaire. Les 3 832 autres entrées proviennent du paquet déjà examiné ; les réserves TOAST UI/ProseMirror et natives restent ouvertes. Aucun changement de dépendance, moteur WebKit, outil de compilation ou bibliothèque native ; le scan n’est pas exhaustif. Sauvegarde source : `../../App Android/sauvegardes/avant-image-visuel-2026-10-09-dev43/notestr-linux-source.tar.gz`. Rapport : `../../App Android/livrables/test-image-view-44/security/image-visual-2026-10-09.json`. Candidat local uniquement ; aucune publication.

# Diagnostic d’affichage d’image — candidat Linux local du 9 octobre 2026

Linux 3.8.dev42, AppImage SHA-256 `804378a0fe8824668d873f4d02be1ae6680252ef06d8df4fb267e6dd9f7832ee`. Le filtre JavaScript ne rejette plus silencieusement les références à clé encodée avec remplissage ; le décodeur natif valide les paramètres. Les échecs de chargement ou de placement de l’image apparaissent dans l’éditeur. Sauvegarde préalable : `../../App Android/sauvegardes/avant-image-visuel-2026-10-09/notestr-linux-source.tar.gz`.

102 tests Python réussis. Tests sur l’AppImage finale : GTK4/libadwaita, chiffrement/signature Nostr et WebKitGTK 2.54.0 ; test graphique de l’image synthétique, du passage Visuel/Markdown, de l’insertion et du cas d’une clé encodée avec remplissage ; tests langue et PDF réussis. Version `--version` vérifiée. Les cinq fichiers source remplacés dans le paquet correspondent aux sources testées.

Contrôle ciblé : les cinq sources mises à jour ne contiennent aucun chemin local nominatif du propriétaire, adresse e-mail, ni marqueur complet `nsec`. Les autres 3 832 entrées sont reprises du paquet 3.8.dev41, dont le contrôle ciblé précédent n’avait pas trouvé ces marqueurs. Cela ne constitue pas une vérification exhaustive. Aucun changement de dépendance, moteur WebKit, outil de compilation ou bibliothèque native ; les réserves TOAST UI/ProseMirror et natives déjà consignées restent ouvertes.

La référence exacte fournie par l’utilisateur a ensuite été passée dans le chemin GTK/WebKit complet de 3.8.dev42 avec le blob chiffré placé dans le cache temporaire : empreinte correspondante, déchiffrement AES-GCM valide et JPEG rendu à 1 055 × 1 491. Le clair n’a existé qu’en mémoire pendant le test, sans être enregistré ni examiné. Le téléchargement réseau n’a pas été rejoué dans cette intégration GTK ; le candidat précédent avait reçu HTTP 200 avec empreinte correspondante. Voir le rapport `../../App Android/livrables/test-image-view-42/security/image-visual-diagnostics-2026-10-09.json`. Candidat local uniquement ; aucune publication.

# Chargement direct de l’image — candidat Linux local du 9 octobre 2026

Linux 3.8.dev41, AppImage SHA-256 `cddd751e458df0961e5856399be2501e47888c26a84c48e0f980b4809b94559a`. 102 tests Python réussis et test GTK/WebKit/AppImage réussi, avec une image placée juste après une puce comme dans la capture. Le serveur Yakihonne a répondu HTTP 200 ; le SHA-256 du blob chiffré téléchargé correspond à la référence. Le test n’a ni envoyé la clé/nonce ni déchiffré ou affiché cette image. Le chargeur tente désormais d’abord l’origine HTTPS de la référence, puis interroge les serveurs Blossom du profil en secours. Empreinte et déchiffrement authentifié restent contrôlés, redirections désactivées.

Aucun changement de dépendance ni nouvel audit complet. Les réserves TOAST UI/ProseMirror et d’exposition native précédemment documentées restent ouvertes. Aucune publication.

Voir `security/image-origin-first-2026-10-09.json` et `LIRE-MOI.md` dans le dossier de test local.

# Affichage des références d’image — candidat Linux local du 9 octobre 2026

Linux 3.8.dev40, AppImage SHA-256 `4054e9bddd6c71501b17dac996ca4b6d0efb260b7739ca39a5d5fb59650eaa51`. 100 tests Python réussis, contrôle AppImage et test graphique GTK/WebKit réussis. Linux essaie d’abord les relais d’images du profil, puis l’origine HTTPS de la référence si les serveurs actuels ne possèdent pas l’ancien blob. Aucun secret de déchiffrement n’est envoyé ; l’empreinte du blob et l’authentification AES-GCM sont vérifiées. Les redirections HTTP sont bloquées. Le test graphique couvre le format de serveur Yakihonne, l’aperçu et le changement Visuel/Markdown.

Scan ciblé du paquet : aucun chemin personnel du propriétaire, courriel recherché ou `nsec` complet ; cinq chaînes PEM sont des constantes de parseurs/sérialiseurs SSH/TLS/cryptographie, pas des clés privées. Aucun changement de dépendance et aucun nouvel audit général le 9 octobre. L’avis TOAST UI/ProseMirror et les réserves natives antérieures restent ouverts ; ce scan n’est pas exhaustif. Aucune publication.

Voir `security/image-origin-fallback-2026-10-09.json` et le dossier `livrables/test-image-view-40` du projet Android.

# Insertion d’image à la position choisie — candidat Linux local du 9 octobre 2026

Linux 3.8.dev39, AppImage SHA-256 `bc7e99c6adf5f828ed3cf3ade5b8dbb2f0e2775d42cb7f948c20f10515782bea`. 99 tests Python réussis. Le contrôle AppImage confirme GTK4/libadwaita, WebKitGTK 2.54.0 et le test crypto Nostr ; le test graphique vérifie l’aperçu après insertion au curseur, le retour Markdown/Visuel et la conservation de la référence complète renvoyée par le téléversement. Le bouton texte devient une icône accessible. Paquet dérivé de l’AppImage candidate déjà contrôlée ; moteur et bibliothèques natifs conservés, module Python remplacé par les sources courantes.

Aucun changement de dépendance et aucun nouvel audit complet le 9 octobre. Le scan ciblé du paquet ne relève ni chemin personnel du propriétaire, ni courriel recherché, ni clé `nsec` complète. Cinq chaînes d’en-tête PEM sont des constantes de parseurs/sérialiseurs des bibliothèques SSH/TLS/cryptographie, sans clé privée incluse. Les avis TOAST UI/ProseMirror et les réserves d’exposition native déjà consignés restent ouverts ; ce contrôle ciblé ne constitue pas un audit exhaustif de sécurité ou de confidentialité. Aucune publication.

Voir `security/image-position-candidate-2026-10-09.json` et `LIRE-MOI.md` dans le dossier local de livrables Android.

# Aperçu et insertion au curseur — candidat Linux local du 9 octobre 2026

Linux 3.8.dev38, AppImage SHA-256 `a50f89d7c384dc34bdd82e4ba3c2360fac7d7f32df800c50477f6b654dfaae62`. 99 tests Python réussis et test GTK/WebKit de l’AppImage réussi : l’aperçu après téléversement utilise le cache chiffré immédiat, et l’insertion reste à la position choisie en modes Visuel et Markdown. WebKitGTK 2.54.0 conservé. Sauvegardes précédentes dans `../../App Android/sauvegardes/avant-aperçu-images-2026-10-09`.

Contrôle ciblé de 3 832 entrées décompressées : aucun chemin personnel ou courriel propriétaire, ni chaîne de clé `nsec` complète. Le marqueur `nsec1` relevé dans une bibliothèque système et le validateur de format de l’application ne sont pas des clés. Les 12 marqueurs PEM documentés proviennent des bibliothèques/fixtures amont déjà examinées ; ils ne suffisent pas à reconnaître des clés privées. Les 53 images de paquet ont été contrôlées ; les EXIF ne portent que des pointeurs `ExifOffset`. Ces recherches ciblées ne sont pas exhaustives.

Dépendances inchangées ; pas de nouvel audit complet des registres depuis le 6 octobre. La réserve GHSA-c8x8-7fp4-3x9w / CVE-2026-104847 dans ProseMirror intégré à TOAST UI demeure ouverte ; l’interception du collage n’est pas le correctif amont. Les autres réserves natives de 3.8 restent applicables. Voir `security/images-cache-candidate-2026-10-09.json`.

Aucune publication.

# Candidat Linux initial d’insertion d’images — 3.8.dev37

Linux 3.8.dev37, AppImage SHA-256 `6de9e987e4f15053e93d8985f0b2d2234ee14a4c7476a3a6a9590df009239d98`. 98 tests Python réussis ; test graphique du paquet final avec WebKitGTK 2.54.0 réussi pour le rendu de l’image, la conservation du Markdown, les langues/paramètres et le PDF. L’image dérive du candidat 3.8.dev36 contrôlé le 6 octobre ; seules les sources de l’application ont été remplacées, et les 27 fichiers du module livré correspondent aux sources. Aucun `.pyc` ni cache dans le paquet.

AES-256-GCM avant téléversement, conversion JPEG sans métadonnées, blob maximal de 20 Mio. Recherche des serveurs via les tags `server` du kind 10063 vérifié, nostr.build en secours seulement lorsqu’aucun serveur valide n’est listé. Cache disque limité aux blobs chiffrés. Les versions antérieures ne savent pas afficher ce format.

Contrôle ciblé des 3 832 fichiers décompressés : aucun marqueur connu de chemin du propriétaire, de courriel ou d’identifiant `nsec`. Douze chaînes correspondant à des débuts d’en-têtes PEM se trouvent dans GnuTLS, libssh et cryptography ; ces marqueurs de parseur/fixtures amont sont connus et documentés, et ne constituent pas des identifiants ou clés du propriétaire. Les 53 images embarquées ont été examinées : les 51 entrées EXIF ne contiennent qu’un pointeur `ExifOffset`, sans valeurs GPS, auteur ou date ; l’image source n’a pas de métadonnée. Contrôle non exhaustif.

Aucune dépendance modifiée ; le moteur natif 2.54.0 et le reste du paquet dérivent du candidat contrôlé le 6 octobre. Audit général des registres non rafraîchi le 9 octobre. Réserves de sécurité de 3.8 conservées, notamment GHSA-c8x8-7fp4-3x9w / CVE-2026-104847 dans ProseMirror intégré à TOAST UI. L’interception applicative du collage limite le chemin signalé, mais ne remplace pas le correctif amont et ne démontre pas l’absence d’autres chemins. Voir `security/images-candidate-2026-10-09.json`.

Paquet local uniquement, sans publication.

# Réglages des relais — candidat Linux 3.8.dev36

Paquet construit et contrôlé le 6 octobre 2026, livré le 9 octobre sans recompilation ni nouvel audit des dépendances. Bouton Enregistrer les relais indépendant du compte et du trousseau, liste défilante. Sauvegarde avant-relais-2026-10-06. 15 tests Python et tests GTK depuis le paquet final réussis, dont conservation du compte et de la configuration précédente en cas d’erreur. Contrôles ciblés de 3 831 entrées décompressées sans marqueur personnel non expliqué ; non exhaustifs. Empreinte revérifiée à la livraison.

Nouvelle réserve : GHSA-c8x8-7fp4-3x9w / CVE-2026-104847, collage HTML dans prosemirror-view 1.27.0 intégré à TOAST UI. Version amont corrigée 1.42.3. Le gestionnaire applicatif de collage bloque le chemin HTML et insère uniquement du texte brut, vérifié dans le moteur embarqué ; il ne s’agit pas du correctif amont ni d’une preuve d’absence d’autres chemins d’attaque. Le modèle ProseMirror ancien ne possède pas checkAttrs, nécessaire au correctif amont ; remplacement isolé non qualifié. Exception limitée au candidat local, mise à jour compatible requise avant future publication. La version Android publique possède aussi cet ancien éditeur ; elle n’est ni modifiée ni recompilée ici. Autres réserves natives conservées. Aucun nouveau candidat Ubuntu ni nouvel avis natif depuis 3.8 lors de la vérification du 6 octobre. Rapports security/relay-settings-*.json.

Aucune publication, aucun push ni tag distant ; copies de publication et Android inchangés.

---

# Publication 3.8 vérifiée — 5 octobre 2026

Android 229a579 (code 35), Linux 6eeec99, tags v3.8. Huit fichiers publics téléchargés anonymement et comparés aux fichiers contrôlés ; signature et certificat de l’APK public vérifiés. Rapport security/release-3.8-publication.json. Anciens auteurs publics conservés et réserves documentées maintenues. Toute publication suivante nécessite son propre accord.

---

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

# Boutons de corbeille — candidats locaux du 5 octobre 2026

Android 3.7.1-test.33 (code 33) : accès à la corbeille par bouton texte « Corbeille », retour « Notes », distinct de l’icône de suppression dans la note. Linux 3.7.1.dev33 : marges et hauteur de rangée communes aux boutons Corbeille / Visuel / Markdown ; messages d’attente placés sous la rangée. Sauvegardes avant-boutons-corbeille-2026-10-05. Aucun changement du protocole, cache ou synchronisation.

Android : 15 des 16 tests instrumentés passent initialement ; assertion de position du clavier en échec, puis test isolé réussi sans modification du code. Émulateur Android 11 uniquement. Linux : contrôles GTK depuis l’AppImage finale extraite, alignement vertical et hauteur vérifiés avec/sans message d’attente ; corbeille, restauration et suppression manuelles validées. Cohérence de version vérifiée après correction du README de packaging. Pas de nouveau test JVM pour ce changement d’interface.

699 coordonnées OSV, registres officiels et maintenance reconsultés, aucune alerte applicative ni erreur, métadonnées identiques au candidat précédent. Index Ubuntu rafraîchis : aucune nouvelle version candidate. Neuf nouveaux avis Ubuntu concernent les métadonnées WebKit 2.52.6 : tous renvoient à WSA-2026-0006, corrigé dans le moteur 2.54.0 réellement embarqué depuis 3.7. Voir trash-buttons-native-exposure.json et les avis détaillés. Les autres réserves natives et l’état archivé de TOAST UI restent documentés, sans affirmation d’absence de vulnérabilité.

Sources/archives et paquets décompressés contrôlés par motifs ciblés, métadonnées d’images et anciens auteurs examinés : aucun marqueur personnel recherché non expliqué. Historiques publics conservés. APK non débogable, signature et certificat historiques, natifs comparés aux AAR et alignement vérifiés. AppImage extraite et comparée à l’AppDir. Contrôles non exhaustifs. Empreintes et résultats dans security/trash-buttons-*.json. Aucun push, tag distant, release ou téléversement ; copies de publication inchangées.

---

# Mode hors connexion — candidats locaux du 5 octobre 2026

Android 3.7.1-test.31 (code 31), Linux 3.7.1.dev31. Sauvegardes avant-hors-ligne-2026-10-05. Le bouton Publier enregistre d’abord une modification locale chiffrée NIP-44 et signée, puis l’envoie lorsque les relais sont joignables et l’application ouverte/déverrouillée. État en attente, reprise au redémarrage, protection des brouillons de l’éditeur, détection des conflits et publication explicite d’une copie. Corbeille et épinglage restent manuels. Dernière copie locale acceptée conservée pour détecter les envois simultanés, puis retirée si sa suppression définitive manuelle est connue. Détails et limites dans OFFLINE.md.

Validation : 14 tests JVM ; suite principale Android de 40 cas (le cas nécessitant un relais est activé séparément), 7 cas avec relais local et 2 biométriques, soit 43 cas distincts exercés. Émulateur Android 11/API 30 ; aucun test physique Android 17. 91 tests Python fonctionnels et 1 test de cohérence de version passent. Tests GTK de corbeille et de mode hors connexion, dont ce dernier sur l’AppImage extraite ; éditeur, langues, version et PDF du paquet contrôlés. Formats chiffrés vérifiés dans les deux sens entre Linux et Android. Les tests dédiés à la synchronisation utilisent des relais locaux ou simulés et des comptes fictifs identifiés. Le test graphique historique interceptait l’ancien envoi direct : il a été adapté à l’enregistrement local, avec reprises automatiques neutralisées pour isoler ce test.

699 coordonnées OSV applicatives et registres/maintenance officiels réinterrogés, sans alerte retournée ni erreur de métadonnées. Composants et chaîne de compilation qualifiés inchangés, exceptions de compatibilité maintenues ; TOAST UI reste archivé. AAR Rust/JNA inchangés et contrôlés, WebView Android fourni par le système. Index Ubuntu rafraîchis pour les 191 composants de référence : aucune mise à jour candidate supplémentaire. Aucun nouvel identifiant d’avis natif depuis le contrôle du 4 octobre. Les 140 signalements bruts de 3.7.1 et les quatre avis ajoutés le 4 octobre restent analysés dans les rapports cités, sans affirmation qu’ils sont tous corrigés ou inexploitables. WebKitGTK 2.54.0 conservé ; anciennes métadonnées de distribution distinguées du moteur réellement inclus.

Contrôles ciblés : 1 597 entrées de sources/archives, images/métadonnées, historiques et identités auteur ; 4 320 entrées de paquets décompressées. Aucun marqueur personnel recherché non expliqué. Cinq fixtures publiques GnuTLS reconnues par empreinte. Sources et paquets ne comprennent pas de compte utilisateur ni de notes personnelles utilisés pour les essais. Contrôles non exhaustifs. APK non débogable, signature v2/certificat conservés, alignement 16 Ko et natifs comparés aux AAR. AppImage extraite et comparée à l’AppDir. Empreintes et limites dans security/offline-*.json.

Aucune publication, aucun push ou tag distant ; copies de publication 3.7.1 inchangées. Les anciens auteurs personnels présents dans les historiques publics sont conservés, sans réécriture.

---

# Corbeille commune — candidats locaux du 4 octobre 2026

Android 3.7.1-test.29 (code 29), Linux 3.7.1.dev29. Corbeille chiffrée commune, restauration et suppression définitive manuelles, aucune expiration ni vidage automatique. Sauvegardes avant-corbeille-2026-10-04. Aucun push, tag distant, release ou téléversement autorisé ; copies de publication 3.7.1 inchangées. Protocole et limites détaillés dans TRASH.md.

14 tests JVM, 31 tests instrumentés Android et 1 test avec relais local, 79 Python ; test graphique de corbeille Linux et contrôles AppImage éditeur/langue/version/PDF réussis. Échanges NIP-44 signés validés Linux vers Android et Android vers Linux. Annulation, échec d’envoi, restauration, suppression terminale et retrait des contenus du cache testés. Comptes fictifs identifiés uniquement, aucun relais public. Aucun test effectué sur le téléphone physique de l’utilisateur.

699 coordonnées OSV et registres officiels recontrôlés sans nouvelle alerte applicative ni erreur de récupération. Index Ubuntu rafraîchis et 191 composants de référence relus : aucune mise à jour candidate disponible. Bibliothèques natives inchangées depuis 3.7.1. Les réserves natives étendues de 3.7.1 restent ouvertes. Quatre avis supplémentaires : SoupServer non utilisé (CVE-2026-103399), serveur TLS SNI non utilisé (CVE-2026-19445), hostname TLS explicitement transmis par websockets 17.1 (CVE-2026-19553), polices CID malveillantes exclues du contenu des notes mais environnement de polices système à considérer (CVE-2026-95512). Ces analyses d’exposition ne constituent pas des correctifs du code natif. TOAST UI demeure archivé.

Contrôles ciblés de 1 586 entrées de sources/archives et du contenu décompressé des paquets, métadonnées d’images et historique : aucun marqueur propriétaire recherché non expliqué détecté. Clés publiques d’autotest GnuTLS reconnues par empreinte. APK non débogable, signature v2 et certificat inchangés, alignement et AAR natifs vérifiés. AppImage extraite et comparée à l’AppDir. Anciennes identités auteur déjà publiques conservées ; aucun historique réécrit. Contrôles non exhaustifs. Rapports datés, versions et empreintes : security/trash-*.json.

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

# Candidats locaux — collage URL — 2 octobre 2026

Android 3.7-test.27 (code 27) et Linux 3.7.dev27 corrigent le gestionnaire global de collage : les champs input/textarea utilisent désormais le collage natif, sans insertion dans le corps de la note. Sauvegardes avant-collage-url-2026-10-02. Aucune publication autorisée ou effectuée ; copies de publication 3.7 inchangées.

Validation : 14 tests JVM, 29 tests Android instrumentés sur émulateur (collage natif URL et annulation sans modification du Markdown), régression JavaScript sur les deux plateformes. Test natif Linux WebKit 2.54.0 : collage/remplacement URL, annulation, collage du libellé, insertion du lien avec conservation de la structure titres/listes. Le paquet Linux décompressé correspond à l’AppDir ; seuls editor.js et le numéro de version diffèrent du paquet 3.7 contrôlé. Test sur téléphone physique restant à faire par l’utilisateur. L’APK conserve son certificat, est non débogable, signé v2 et aligné ; bibliothèques natives comparées aux AAR examinés.

Nouvelle interrogation de 699 coordonnées OSV et des métadonnées officielles : aucune alerte retournée ni erreur de récupération ; cela ne démontre pas l’absence de vulnérabilité. Les versions des bibliothèques restent celles de 3.7. Les candidats APT de 181 composants de référence ont été relus dans les index locaux existants, sans rafraîchissement APT dans cette exécution. WebKit source 2.54.0 et mises à jour natives du paquet final 3.7 sont conservés octet pour octet. Les cinq exceptions de codecs, TOAST UI archivé et l’historique auteur personnel restent documentés dans les rapports de sécurité 3.7.

Contrôles ciblés : 1 567 entrées de sources/archives et 4 319 entrées de paquets ; aucun marqueur personnel ou secret recherché non expliqué. Les cinq clés publiques d’autotest GnuTLS sont reconnues par empreinte, pas ignorées globalement. Métadonnées d’images et historique examinés ; deux anciens commits Android et un Linux conservent leurs identités auteur. Aucun historique réécrit. La capture personnelle fournie n’est pas intégrée aux sources ou paquets. Rapports datés et empreintes dans security/paste-url-*.json. Ces contrôles ne sont pas exhaustifs.

# Validation de Notestr

## V3.1 — modification du mot de passe

- 29 tests automatisés réussis, compilation Python et contrôle intégré réussis.
- Le changement exige le mot de passe actuel.
- Une erreur ou un nouveau mot de passe trop court conserve l’ancien verrouillage.
- Un changement réussi crée un nouveau sel et une nouvelle empreinte Argon2id.
- L’ancien mot de passe est refusé et le nouveau est accepté.
- Test graphique du bouton, des trois champs et du remplacement du mot de passe réussi.

## V3 — verrouillage au démarrage

- 26 tests automatisés réussis, compilation Python et contrôle intégré réussis.
- Création et vérification du mot de passe avec Argon2id.
- Mot de passe absent du fichier local ; sel et empreinte uniquement.
- Refus des mots de passe de moins de huit caractères et des fichiers de verrouillage invalides.
- Permissions privées du fichier `lock.json` vérifiées.
- La clé Nostr et les notes ne sont chargées qu’après déverrouillage réussi.
- Test graphique de création puis de déverrouillage au démarrage réussi.
- Test graphique GTK/WebKit complet réussi sans régression de l’éditeur visuel.

- 18 tests pytest réussis (17 tests Nostr/réseau de la V1 + ressources et CSP).
- Compilation de tous les modules et contrôle syntaxique JavaScript réussis.
- Imports GTK4/libadwaita/WebKitGTK et aller-retour NIP-44 réussis.
- Test réel GTK/WebKit via Broadway : chargement de tous les fichiers embarqués,
  éditeur visuel, rendu des titres/gras, bouton Gras avec saisie native, passage Markdown/Visuel, conservation exacte du texte non modifié
  (Unicode, liens, listes, code, HTML et référence à une image), insertion de texte,
  état modifié, synchronisation avant signature/chiffrement et rejet d’une mise à
  jour tardive d’une autre note réussis. Historique Annuler isolé entre les notes.
- HTML actif neutralisé par le filtre HTML et la CSP.
- Test du blocage de fetch par CSP et vérification du mode éphémère WebKit réussis.

Environnement : Zorin OS 18.1, Python 3.12, GTK 4.14, libadwaita 1.5,
WebKitGTK 2.52.6 (API 6.0), monstr 0.1.9.

Les tests de transport restent simulés. Le test graphique intercepte la publication
avant tout envoi. Aucun événement n’a été publié sur un relais public ; la compatibilité
interactive avec Pages doit encore être vérifiée avec une note jetable sur le poste cible.
L’édition visuelle normalise le Markdown modifié : privilégier le mode source pour les
syntaxes que TOAST UI ne représente pas fidèlement. Voir README.md.

## Correctif 0.2.1

Test graphique supplémentaire réussi : saisir Gras, Entrée, Barré, Entrée, Italique
dans le vrai contenteditable produit `Gras  \nBarré  \nItalique`, avec deux espaces
avant chaque retour. Les sauts sont conservés après passage Markdown/Visuel.
Les tests existants, notamment les blocs de code et la conservation du source, passent.

## Correctif 0.2.2 — 13 septembre 2026

- Quatre nouveaux tests de régression exécutés : exemple utilisateur rendu par
  CommonMark, code/HTML/tableaux/sauts existants préservés, listes/citations/CRLF,
  contenu chiffré et identifiant conservé. Tous passent.
- Test graphique GTK/WebKit complet réussi avec la V2.2 : les positions verticales
  de Gras/Barré/Italique sont distinctes après lecture de sauts explicites ; les
  deux phrases saisies en Markdown sont séparées après publication simulée,
  déchiffrement et réouverture. Les vérifications graphiques antérieures passent.
- La publication du test est interceptée avant envoi : aucun compte utilisateur
  ni relais public n’a été utilisé. Le rendu externe est validé avec markdown-it-py
  CommonMark, sans session interactive dans Pages.

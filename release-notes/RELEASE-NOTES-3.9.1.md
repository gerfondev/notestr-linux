# Notestr 3.9.1 — Android et Linux

## Nouveautés et corrections

- Ajout du verrouillage/déverrouillage synchronisé d’une note, compatible entre Android et Linux. Une note verrouillée reste consultable et bloque sa modification ou sa suppression depuis les versions compatibles.
- Correction de bugs mineurs, dont la remise à jour des commandes flottantes de copie après chargement d’un bloc de code.
- Mises à jour Python : aiohttp 3.14.5, cryptography 50.0.2 et websockets 17.2. Les mises à jour natives Ubuntu intégrées à la 3.9 sont conservées ; les réserves de sécurité ouvertes sont décrites dans `SECURITY-REVIEW.md`.
- Correction de l’export PDF Linux : les images de la note sont intégrées au fichier après déchiffrement local. Si une image manque, l’export s’arrête avec un message explicite.
- Numéros de version Android et Linux alignés sur 3.9.1. Les fonctions d’insertion d’image, de zoom et de déplacement ainsi que la licence GPLv3 sont conservées.

Android versionCode 46. Linux x86_64 : AppImage, wheel Python et archive source. Les contrôles de sécurité et de confidentialité sont ciblés, avec leurs limites décrites dans `SECURITY-REVIEW.md`.

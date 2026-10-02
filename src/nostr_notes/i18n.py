"""Application-owned messages. Never translate note contents or protocol fields."""
_language = "fr"

def set_language(language):
    global _language
    _language = language if language in ("fr", "en") else "fr"

def get_language():
    return _language

def tr(message, *values):
    text = ENGLISH.get(message, message) if _language == "en" else message
    return text.format(*values) if values else text

ENGLISH = {' Mode Markdown rétabli avec le dernier texte reçu ; vérifier les dernières frappes.': ' Markdown mode '
                                                                                        'restored with the '
                                                                                        'last received text; '
                                                                                        'check your latest '
                                                                                        'edits.',
 ' Utilisez le mot de passe ; vous pourrez réactiver la biométrie dans les réglages.': ' Use your password; '
                                                                                       'you can re-enable '
                                                                                       'biometrics in '
                                                                                       'Settings.',
 ' Vous pouvez utiliser votre mot de passe.': ' You can use your password.',
 'Abandonner les modifications': 'Discard changes',
 'Abonnement refusé par le relais.': 'Subscription rejected by the relay.',
 'Accéder à vos notes privées': 'Access your private notes',
 'Activer la biométrie': 'Enable biometrics',
 'Activez la biométrie dans les réglages après déverrouillage par mot de passe.': 'Enable biometrics in '
                                                                                  'Settings after unlocking '
                                                                                  'with your password.',
 'Actualiser': 'Refresh',
 'Ajoutez au moins un relais.': 'Add at least one relay.',
 'Amber conserve la clé privée et réalise le chiffrement et les signatures. Notestr ne reçoit jamais votre nsec.': 'Amber '
                                                                                                                   'stores '
                                                                                                                   'your '
                                                                                                                   'private '
                                                                                                                   'key '
                                                                                                                   'and '
                                                                                                                   'handles '
                                                                                                                   'encryption '
                                                                                                                   'and '
                                                                                                                   'signing. '
                                                                                                                   'Notestr '
                                                                                                                   'never '
                                                                                                                   'receives '
                                                                                                                   'your '
                                                                                                                   'nsec.',
 'Amber n’est pas installé sur cet appareil.': 'Amber is not installed on this device.',
 "Android Keystore n'a pas généré d'IV": 'Android Keystore did not generate an IV',
 'Annuler': 'Cancel',
 'Application verrouillée': 'App locked',
 'Attendre la fin de l’opération avant de fermer.': 'Wait for the operation to finish before closing.',
 'Attendre la seconde suivante avant de changer l’épinglage ; vérifier l’horloge si nécessaire.': 'Wait '
                                                                                                  'until the '
                                                                                                  'next '
                                                                                                  'second '
                                                                                                  'before '
                                                                                                  'changing '
                                                                                                  'the pin; '
                                                                                                  'check the '
                                                                                                  'clock if '
                                                                                                  'needed.',
 'Attendre la seconde suivante avant de republier cette note ; vérifier l’horloge si nécessaire.': 'Wait '
                                                                                                   'until '
                                                                                                   'the next '
                                                                                                   'second '
                                                                                                   'before '
                                                                                                   'republishing '
                                                                                                   'this '
                                                                                                   'note; '
                                                                                                   'check '
                                                                                                   'the '
                                                                                                   'clock if '
                                                                                                   'needed.',
 'Aucun compte ouvert': 'No account open',
 'Aucun navigateur disponible pour ouvrir ce lien.': 'No browser is available to open this link.',
 'Aucun relais n’a accepté la note. Votre texte reste dans l’éditeur.': 'No relay accepted the note. Your '
                                                                        'text remains in the editor.',
 'Aucun relais n’a accepté la sauvegarde. La note n’a pas été modifiée.': 'No relay accepted the backup. The '
                                                                          'note was not changed.',
 'Aucun relais n’a accepté la suppression.': 'No relay accepted the deletion.',
 'Aucun relais n’a accepté l’épinglage. Réessayez après reconnexion.': 'No relay accepted the pin update. '
                                                                       'Try again after reconnecting.',
 'Aucune biométrie forte disponible. Configurez une empreinte ou un visage compatible dans les réglages du téléphone, ou utilisez votre mot de passe.': 'No '
                                                                                                                                                        'strong '
                                                                                                                                                        'biometric '
                                                                                                                                                        'method '
                                                                                                                                                        'is '
                                                                                                                                                        'available. '
                                                                                                                                                        'Set '
                                                                                                                                                        'up '
                                                                                                                                                        'a '
                                                                                                                                                        'supported '
                                                                                                                                                        'fingerprint '
                                                                                                                                                        'or '
                                                                                                                                                        'face '
                                                                                                                                                        'in '
                                                                                                                                                        'your '
                                                                                                                                                        'phone '
                                                                                                                                                        'settings, '
                                                                                                                                                        'or '
                                                                                                                                                        'use '
                                                                                                                                                        'your '
                                                                                                                                                        'password.',
 'Aucune note trouvée.': 'No notes found.',
 'Aucune version précédente disponible pour cette note.': 'No previous version is available for this note.',
 'Authentification biométrique impossible. Utilisez votre mot de passe.': 'Biometric authentication failed. '
                                                                          'Use your password.',
 'Biométrie activée': 'Biometrics enabled',
 'Biométrie indisponible.': 'Biometrics unavailable.',
 'Ce relais exige NIP-42, non pris en charge en V1.': 'This relay requires NIP-42, which is not supported.',
 'Changer de compte ou utiliser Amber': 'Change account or use Amber',
 'Changer le mot de passe': 'Change password',
 'Chaque relais doit commencer par wss://': 'Each relay must start with wss://',
 'Chaque relais doit être une URL wss:// valide sans identifiants ni fragment.': 'Each relay must be a valid '
                                                                                 'wss:// URL without '
                                                                                 'credentials or a fragment.',
 'Chargement de l’éditeur visuel local…': 'Loading the local visual editor…',
 'Chargement visuel impossible.': 'Unable to load the visual editor.',
 'Charger': 'Load',
 'Charger la version précédente ?': 'Load the previous version?',
 'Choisir un emplacement local pour le fichier PDF.': 'Choose a local location for the PDF file.',
 'Choisissez le mot de passe demandé à chaque ouverture de Notestr.': 'Choose the password required each '
                                                                      'time you open Notestr.',
 'Choisissez où votre clé privée est conservée.': 'Choose where your private key is stored.',
 'Clé biométrique indisponible.': 'Biometric key unavailable.',
 'Clé locale': 'Local key',
 'Clé privée invalide : saisir une nsec ou 64 caractères hexadécimaux.': 'Invalid private key: enter an nsec '
                                                                         'or 64 hexadecimal characters.',
 'Clé privée nsec': 'Private key (nsec)',
 'Clé privée nsec ou hex (laisser vide pour garder le compte ouvert)': 'Private key in nsec or hex (leave '
                                                                       'blank to keep the current account)',
 'Clé publique : ': 'Public key: ',
 'Code copié dans le presse-papiers.': 'Code copied to clipboard.',
 'Coffre non configuré': 'Vault not configured',
 'Coffre non configuré.': 'Vault not configured.',
 'Compte et relais': 'Account and relays',
 'Configuration Amber invalide.': 'Invalid Amber configuration.',
 'Configuration biométrique modifiée.': 'Biometric configuration changed.',
 'Configuration du verrouillage local invalide.': 'Invalid local lock configuration.',
 'Configuration impossible.': 'Setup failed.',
 'Configurer Notestr': 'Set up Notestr',
 'Confirmer': 'Confirm',
 'Confirmer le mot de passe': 'Confirm password',
 'Confirmer le nouveau mot de passe': 'Confirm new password',
 'Connexion Nostr': 'Nostr connection',
 'Connexion à Amber annulée.': 'Connection to Amber cancelled.',
 'Connexion à Amber impossible.': 'Unable to connect to Amber.',
 'Créer et ouvrir': 'Create and open',
 'Créer le coffre': 'Create vault',
 'Créer le mot de passe Notestr': 'Create Notestr password',
 'Demander la suppression de cette note sur les relais ? Les éventuelles modifications seront abandonnées. Nostr ne garantit pas l’effacement de toutes les copies.': 'Request '
                                                                                                                                                                      'deletion '
                                                                                                                                                                      'of '
                                                                                                                                                                      'this '
                                                                                                                                                                      'note '
                                                                                                                                                                      'on '
                                                                                                                                                                      'relays? '
                                                                                                                                                                      'Any '
                                                                                                                                                                      'changes '
                                                                                                                                                                      'will '
                                                                                                                                                                      'be '
                                                                                                                                                                      'discarded. '
                                                                                                                                                                      'Nostr '
                                                                                                                                                                      'does '
                                                                                                                                                                      'not '
                                                                                                                                                                      'guarantee '
                                                                                                                                                                      'removal '
                                                                                                                                                                      'of '
                                                                                                                                                                      'all '
                                                                                                                                                                      'copies.',
 'Des modifications ne sont pas publiées. Les abandonner ?': 'There are unpublished changes. Discard them?',
 'Document PDF': 'PDF document',
 'Délai dépassé': 'Timed out',
 'Désactiver la biométrie': 'Disable biometrics',
 'Désépingler': 'Unpin',
 'Déverrouillage biométrique': 'Biometric unlock',
 'Déverrouillage biométrique activé.': 'Biometric unlock enabled.',
 'Déverrouillage biométrique désactivé.': 'Biometric unlock disabled.',
 'Déverrouillage impossible.': 'Unable to unlock.',
 'Déverrouiller': 'Unlock',
 'Déverrouiller Notestr': 'Unlock Notestr',
 'Déverrouiller par biométrie': 'Unlock with biometrics',
 'Déverrouillez d’abord Notestr avec votre mot de passe.': 'First unlock Notestr with your password.',
 'Déverrouillez d’abord le coffre avec votre mot de passe.': 'First unlock the vault with your password.',
 'Enregistrement du coffre impossible.': 'Unable to save the vault.',
 'Enregistrement impossible. Vérifier la clé et le trousseau, ou décocher l’enregistrement pour utiliser la clé uniquement pendant cette session.\n': 'Unable '
                                                                                                                                                      'to '
                                                                                                                                                      'save. '
                                                                                                                                                      'Check '
                                                                                                                                                      'the '
                                                                                                                                                      'key '
                                                                                                                                                      'and '
                                                                                                                                                      'keyring, '
                                                                                                                                                      'or '
                                                                                                                                                      'uncheck '
                                                                                                                                                      'storage '
                                                                                                                                                      'to '
                                                                                                                                                      'use '
                                                                                                                                                      'the '
                                                                                                                                                      'key '
                                                                                                                                                      'only '
                                                                                                                                                      'for '
                                                                                                                                                      'this '
                                                                                                                                                      'session.\n',
 'Enregistrer cette clé dans le trousseau Linux': 'Store this key in the Linux keyring',
 'Enregistrer la langue': 'Save language',
 'Enregistrer le nouveau mot de passe': 'Save new password',
 'Enregistrer les relais': 'Save relays',
 'Export PDF impossible : ': 'PDF export failed: ',
 'Export PDF impossible : {0}': 'PDF export failed: {0}',
 'Exporter en PDF': 'Export as PDF',
 'Exporter la note en PDF': 'Export note as PDF',
 'Fermer et perdre les modifications non publiées ?': 'Close and lose unpublished changes?',
 'Fichier local illisible : {0}. Le sauvegarder puis le retirer pour repartir.': 'Unreadable local file: '
                                                                                 '{0}. Back it up, then '
                                                                                 'remove it to start again.',
 'Importer une clé privée pour commencer.': 'Import a private key to get started.',
 'Impossible de démarrer la biométrie. Utilisez votre mot de passe.': 'Unable to start biometric '
                                                                      'authentication. Use your password.',
 'Impossible de synchroniser l’éditeur visuel.': 'Unable to synchronize the visual editor.',
 'Impossible d’afficher le mode Visuel. Votre Markdown est conservé.': 'Unable to display Visual mode. Your '
                                                                       'Markdown is preserved.',
 'Impossible d’enregistrer le déverrouillage biométrique.': 'Unable to save biometric unlock.',
 'Impossible d’ouvrir Amber. Vérifiez que l’application est installée.': 'Unable to open Amber. Check that '
                                                                         'the app is installed.',
 'Impossible d’ouvrir le navigateur. Vérifier le navigateur par défaut du système.': 'Unable to open the '
                                                                                     'browser. Check the '
                                                                                     'system default '
                                                                                     'browser.',
 'Indiquer au moins un relais wss://.': 'Enter at least one wss:// relay.',
 'La clé est chiffrée par votre mot de passe et par Android Keystore. Elle ne quitte pas l’appareil.': 'Your '
                                                                                                       'key '
                                                                                                       'is '
                                                                                                       'encrypted '
                                                                                                       'with '
                                                                                                       'your '
                                                                                                       'password '
                                                                                                       'and '
                                                                                                       'Android '
                                                                                                       'Keystore. '
                                                                                                       'It '
                                                                                                       'never '
                                                                                                       'leaves '
                                                                                                       'this '
                                                                                                       'device.',
 'La langue sera appliquée au prochain lancement.': 'The language will be applied on the next launch.',
 'La note a changé sur les relais. Copiez vos modifications puis ouvrez sa dernière version avant de publier.': 'The '
                                                                                                                'note '
                                                                                                                'has '
                                                                                                                'changed '
                                                                                                                'on '
                                                                                                                'the '
                                                                                                                'relays. '
                                                                                                                'Copy '
                                                                                                                'your '
                                                                                                                'changes, '
                                                                                                                'then '
                                                                                                                'open '
                                                                                                                'its '
                                                                                                                'latest '
                                                                                                                'version '
                                                                                                                'before '
                                                                                                                'publishing.',
 'La note a changé. Actualisez et ouvrez sa dernière version.': 'The note has changed. Refresh and open its '
                                                                'latest version.',
 'La note est vide.': 'The note is empty.',
 'La page de l’éditeur n’a pas pu être chargée.': 'The editor page could not be loaded.',
 'La version précédente est invalide.': 'The previous version is invalid.',
 'Langue': 'Language',
 'Langue enregistrée. Relancez Notestr pour l’appliquer.': 'Language saved. Restart Notestr to apply it.',
 'Le Markdown doit contenir entre 1 et 65 535 octets UTF-8 (NIP-44 v2).': 'Markdown must contain between 1 '
                                                                          'and 65,535 UTF-8 bytes (NIP-44 '
                                                                          'v2).',
 'Le chargement de l’éditeur a dépassé 15 secondes.': 'The editor took more than 15 seconds to load.',
 'Le coffre et le cache locaux seront effacés. Les notes publiées sur les relais ne seront pas supprimées.': 'The '
                                                                                                             'local '
                                                                                                             'vault '
                                                                                                             'and '
                                                                                                             'cache '
                                                                                                             'will '
                                                                                                             'be '
                                                                                                             'erased. '
                                                                                                             'Notes '
                                                                                                             'published '
                                                                                                             'to '
                                                                                                             'relays '
                                                                                                             'will '
                                                                                                             'not '
                                                                                                             'be '
                                                                                                             'deleted.',
 'Le dossier de destination n’existe pas.': 'The destination folder does not exist.',
 'Le fichier PDF généré est invalide.': 'The generated PDF is invalid.',
 'Le mode visuel peut normaliser le Markdown modifié. Pour les syntaxes spéciales ou le HTML, utiliser Markdown.': 'Visual '
                                                                                                                   'mode '
                                                                                                                   'may '
                                                                                                                   'normalize '
                                                                                                                   'edited '
                                                                                                                   'Markdown. '
                                                                                                                   'Use '
                                                                                                                   'Markdown '
                                                                                                                   'mode '
                                                                                                                   'for '
                                                                                                                   'special '
                                                                                                                   'syntax '
                                                                                                                   'or '
                                                                                                                   'HTML.',
 'Le mot de passe actuel est incorrect.': 'The current password is incorrect.',
 'Le mot de passe de l’application a été modifié.': 'The app password has been changed.',
 'Le mot de passe doit contenir au moins 8 caractères.': 'The password must contain at least 8 characters.',
 'Le moteur visuel n’a pas répondu.': 'The visual editor did not respond.',
 'Le moteur visuel s’est arrêté.': 'The visual editor stopped.',
 'Le texte dans l’éditeur sera remplacé par la sauvegarde. Vérifiez-le puis appuyez sur Publier pour confirmer la restauration.': 'The '
                                                                                                                                  'backup '
                                                                                                                                  'will '
                                                                                                                                  'replace '
                                                                                                                                  'the '
                                                                                                                                  'text '
                                                                                                                                  'in '
                                                                                                                                  'the '
                                                                                                                                  'editor. '
                                                                                                                                  'Review '
                                                                                                                                  'it, '
                                                                                                                                  'then '
                                                                                                                                  'tap '
                                                                                                                                  'Publish '
                                                                                                                                  'to '
                                                                                                                                  'confirm '
                                                                                                                                  'the '
                                                                                                                                  'restore.',
 'Les deux mots de passe sont différents.': 'The passwords do not match.',
 'Les deux nouveaux mots de passe sont différents.': 'The new passwords do not match.',
 'Les mots de passe ne correspondent pas.': 'The passwords do not match.',
 'Les nouveaux mots de passe ne correspondent pas.': 'The new passwords do not match.',
 'Limite de pagination atteinte ; récupération incomplète.': 'Pagination limit reached; retrieval '
                                                             'incomplete.',
 'Logo Notestr': 'Notestr logo',
 'L’identifiant de connexion est obligatoire.': 'A login identifier is required.',
 'L’éditeur visuel ne répond pas.': 'The visual editor is not responding.',
 'Markdown : les retours simples seront rendus explicites à la publication. Les blocs de code sont préservés.': 'Markdown: '
                                                                                                                'single '
                                                                                                                'line '
                                                                                                                'breaks '
                                                                                                                'will '
                                                                                                                'be '
                                                                                                                'made '
                                                                                                                'explicit '
                                                                                                                'when '
                                                                                                                'publishing. '
                                                                                                                'Code '
                                                                                                                'blocks '
                                                                                                                'are '
                                                                                                                'preserved.',
 'Mode visuel : installer gir1.2-webkit-6.0 puis relancer. Le mode Markdown reste disponible.': 'Visual '
                                                                                                'mode: '
                                                                                                'install '
                                                                                                'gir1.2-webkit-6.0 '
                                                                                                'and '
                                                                                                'restart. '
                                                                                                'Markdown '
                                                                                                'mode '
                                                                                                'remains '
                                                                                                'available.',
 'Modification impossible.': 'Unable to save changes.',
 'Modifier le mot de passe': 'Change password',
 'Mot de passe': 'Password',
 'Mot de passe (8 caractères minimum)': 'Password (at least 8 characters)',
 'Mot de passe actuel': 'Current password',
 'Mot de passe incorrect': 'Incorrect password',
 'Mot de passe incorrect.': 'Incorrect password.',
 'Mot de passe modifié. Vous pouvez réactiver la biométrie dans les réglages.': 'Password changed. You can '
                                                                                're-enable biometrics in '
                                                                                'Settings.',
 'Note Nostr': 'Nostr note',
 'Note désépinglée.': 'Note unpinned.',
 'Note publiée, mais écriture du cache local impossible. Actualisez avant de fermer l’application.': 'Note '
                                                                                                     'published, '
                                                                                                     'but '
                                                                                                     'the '
                                                                                                     'local '
                                                                                                     'cache '
                                                                                                     'could '
                                                                                                     'not be '
                                                                                                     'written. '
                                                                                                     'Refresh '
                                                                                                     'before '
                                                                                                     'closing '
                                                                                                     'the '
                                                                                                     'app.',
 'Note publiée.': 'Note published.',
 'Note épinglée.': 'Note pinned.',
 'Notes en cache disponibles · synchronisation des relais…': 'Cached notes available · synchronizing with '
                                                             'relays…',
 'Notes privées Nostr': 'Private Nostr notes',
 'Notes privées Nostr • modifications non publiées': 'Private Nostr notes • unpublished changes',
 'Notestr est déjà déverrouillé.': 'Notestr is already unlocked.',
 'Notestr est verrouillé': 'Notestr is locked',
 'Notestr se verrouille en quittant l’application. Les modifications non publiées seront perdues. Annulez pour les publier d’abord.': 'Notestr '
                                                                                                                                      'locks '
                                                                                                                                      'when '
                                                                                                                                      'you '
                                                                                                                                      'leave '
                                                                                                                                      'the '
                                                                                                                                      'app. '
                                                                                                                                      'Unpublished '
                                                                                                                                      'changes '
                                                                                                                                      'will '
                                                                                                                                      'be '
                                                                                                                                      'lost. '
                                                                                                                                      'Cancel '
                                                                                                                                      'to '
                                                                                                                                      'publish '
                                                                                                                                      'them '
                                                                                                                                      'first.',
 'Nouveau mot de passe': 'New password',
 'Nouveau mot de passe (8 caractères minimum)': 'New password (at least 8 characters)',
 'Nouvelle note': 'New note',
 'Opération Amber annulée ou interrompue. Votre note reste dans l’éditeur.': 'Amber operation cancelled or '
                                                                             'interrupted. Your note remains '
                                                                             'in the editor.',
 'Opération en cours…': 'Operation in progress…',
 'Opération refusée dans Amber.': 'Operation rejected in Amber.',
 'Opération refusée dans Amber. Vous pouvez modifier cette autorisation dans Amber.': 'Operation rejected in '
                                                                                      'Amber. You can change '
                                                                                      'this permission in '
                                                                                      'Amber.',
 'Ouvrir': 'Open',
 'Ouvrir le compte': 'Open account',
 'Ouvrir le lien dans le navigateur': 'Open link in browser',
 'Ouvrir le navigateur ?': 'Open the browser?',
 'PDF exporté : ': 'PDF exported: ',
 'PDF exporté : {0}': 'PDF exported: {0}',
 'Pagination saturée sur une même seconde ; récupération incomplète.': 'Too many events in the same second; '
                                                                       'retrieval incomplete.',
 'Port du relais invalide.': 'Invalid relay port.',
 'Protéger l’accès à votre coffre': 'Protect access to your vault',
 'Publication': 'Publication',
 'Publication acceptée, mais écriture du cache local impossible.': 'Publication accepted, but the local '
                                                                   'cache could not be written.',
 'Publication refusée : ': 'Publication rejected: ',
 'Publier': 'Publish',
 'Quitter': 'Quit',
 'Rechercher dans les notes': 'Search notes',
 'Reconfigurer': 'Reset connection',
 'Reconfigurer la connexion ?': 'Reset the connection?',
 'Relais invalides.': 'Invalid relays.',
 'Relais wss://, un par ligne': 'wss:// relays, one per line',
 'Relais, un par ligne': 'Relays, one per line',
 'Ressource interdite': 'Resource blocked',
 'Retour': 'Back',
 'Réessayer': 'Retry',
 'Réglages': 'Settings',
 'Réponse Amber incomplète.': 'Incomplete response from Amber.',
 'Réponse Amber invalide.': 'Invalid response from Amber.',
 'Réponse Amber vide.': 'Empty response from Amber.',
 'Réponse du relais trop volumineuse.': 'Relay response too large.',
 'Réponse invalide de l’éditeur.': 'Invalid response from the editor.',
 'Réponse vide d’Amber.': 'Empty response from Amber.',
 'Saisir la clé privée du compte Pages.': 'Enter the account private key.',
 'Saisissez le mot de passe actuel, puis choisissez le nouveau.': 'Enter your current password, then choose '
                                                                  'a new one.',
 'Saisissez le mot de passe de l’application.': 'Enter the app password.',
 'Sans titre': 'Untitled',
 'Se connecter avec Amber': 'Connect with Amber',
 'Signature Amber invalide.': 'Invalid Amber signature.',
 'Suppression': 'Deletion',
 'Suppression publiée.': 'Deletion published.',
 'Supprimer': 'Delete',
 'Supprimer cette note ?': 'Delete this note?',
 'Synchronisation des relais en cours…': 'Synchronizing with relays…',
 'Synchronisation en cours ; réessayer dans un instant.': 'Synchronization in progress; try again shortly.',
 'Sélectionner une note publiée à supprimer.': 'Select a published note to delete.',
 'Sélectionner une note publiée.': 'Select a published note.',
 'Trop de tentatives. Nouvel essai dans 30 secondes.': 'Too many attempts. Try again in 30 seconds.',
 'Une demande Amber est déjà en cours.': 'An Amber request is already in progress.',
 'Une demande de suppression de la note et de sa sauvegarde sera publiée sur les relais.': 'A request to '
                                                                                           'delete this note '
                                                                                           'and its backup '
                                                                                           'will be '
                                                                                           'published to the '
                                                                                           'relays.',
 'Une erreur est survenue.': 'An error occurred.',
 'Utiliser le mot de passe': 'Use password',
 'Utilisez une empreinte ou un visage compatible pour ouvrir Notestr. Votre mot de passe reste disponible en secours.': 'Use '
                                                                                                                        'a '
                                                                                                                        'supported '
                                                                                                                        'fingerprint '
                                                                                                                        'or '
                                                                                                                        'face '
                                                                                                                        'to '
                                                                                                                        'open '
                                                                                                                        'Notestr. '
                                                                                                                        'Your '
                                                                                                                        'password '
                                                                                                                        'remains '
                                                                                                                        'available '
                                                                                                                        'as '
                                                                                                                        'a '
                                                                                                                        'fallback.',
 'Verrouiller': 'Lock',
 'Version de l’application': 'App version',
 'Version précédente': 'Previous version',
 'Version précédente chargée. Vérifier puis cliquer sur Publier pour la restaurer.': 'Previous version '
                                                                                     'loaded. Review it, '
                                                                                     'then click Publish to '
                                                                                     'restore it.',
 'Version précédente chargée. Vérifiez puis appuyez sur Publier pour la restaurer.': 'Previous version '
                                                                                     'loaded. Review it, '
                                                                                     'then tap Publish to '
                                                                                     'restore it.',
 'Visuel': 'Visual',
 'Vos notes privées apparaîtront ici.': 'Your private notes will appear here.',
 'Vous pouvez réessayer.': 'You can try again.',
 'inconnue': 'unknown',
 'non exportée': 'not exported',
 '{0} acceptée par {1}/{2} relais. ': '{0} accepted by {1}/{2} relays. ',
 '{0} note(s) en cache · {1} indéchiffrable(s).': '{0} cached note(s) · {1} could not be decrypted.',
 '{0} note(s) · {1} indéchiffrable(s). ': '{0} note(s) · {1} could not be decrypted. ',
 'Épinglage accepté, mais écriture du cache local impossible.': 'Pin accepted, but the local cache could not '
                                                                'be written.',
 'Épinglage synchronisé, mais écriture du cache local impossible. Actualisez avant de fermer.': 'Pin '
                                                                                                'synchronized, '
                                                                                                'but the '
                                                                                                'local cache '
                                                                                                'could not '
                                                                                                'be written. '
                                                                                                'Refresh '
                                                                                                'before '
                                                                                                'closing.',
 'Épingler': 'Pin',
 'Épinglée': 'Pinned'}

ENGLISH["Mode visuel : WebKitGTK 2.54.0 ou ultérieur est requis. Utiliser l’AppImage à jour ou mettre à jour le moteur système. Le mode Markdown reste disponible."] = "Visual mode requires WebKitGTK 2.54.0 or later. Use the updated AppImage or update the system engine. Markdown mode remains available."

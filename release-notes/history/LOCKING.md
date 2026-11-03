# Verrouillage synchronisé des notes

Le verrouillage est un état de note chiffré et signé, commun aux versions Notestr Android et Linux qui prennent en charge cette fonction. Il ne modifie ni le texte, ni l’identifiant, ni la date de la note.

L’application publie un événement Nostr kind `30078` avec le tag `d` égal à `notestr/lock/` suivi du SHA-256 hexadécimal minuscule de l’identifiant de note UTF-8. Le contenu est le booléen `true` ou `false` chiffré en NIP-44 v2 vers le compte lui-même. Le dernier événement valide détermine l’état. Il est synchronisé par les relais et conservé dans le cache chiffré.

Une note verrouillée reste lisible. Notestr désactive l’édition, la mise à la corbeille et la suppression définitive jusqu’à un déverrouillage explicite. Les brouillons locaux en attente ne peuvent pas être verrouillés ; un verrouillage reçu avant leur synchronisation crée un conflit et bloque leur publication automatique.

La suppression définitive inclut l’adresse de verrouillage dans ses tombstones. Les anciennes versions Android/Linux ignorent cet état, et les clients Nostr tiers peuvent toujours publier une nouvelle version ou une suppression. Il s’agit d’une protection applicative contre les changements accidentels, pas d’une règle imposée par les relais.

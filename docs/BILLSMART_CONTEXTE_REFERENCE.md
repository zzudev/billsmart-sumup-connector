# BillSmart — Contexte de référence et décisions architecturales

**Projet :** Projet_BiLB_x_AEDF_et_MBOUCHE
**Sous-projet :** Interfaçage universel BillSmart avec logiciels de caisse et systèmes de paiement
**État documentaire :** référence initiale du 10 octobre 2026 ; revue d’alignement du 15 octobre 2026
**Portée :** synthèse du contexte de projet et des résultats rapportés dans les sessions ; ne remplace pas une vérification du code ou des API en production.

## 1. Vision non négociable

BillSmart doit pouvoir s'interfacer avec **tout logiciel de caisse (POS)** et **tout système de paiement** compatible avec un mécanisme d'intégration. **SumUp est le premier fournisseur expérimenté, pas le modèle métier ni une dépendance architecturale.**

L'objectif est de générer et distribuer un **ticket BillSmart** (potentiellement enrichi), consultable par QR code via BSM5. Les connecteurs traduisent les données externes vers un contrat universel BillSmart. Le cœur BillSmart ne doit pas reprendre la structure propriétaire d'un fournisseur.

Le livrable central du POC en cours est le **BillSmart Transaction Simulator** : banc d'essai d'une vente universelle et de son paiement. Il ne faut pas confondre cet outil avec une caisse complète ni transformer le projet en simple refonte du connecteur SumUp.

## 2. Trois configurations commerciales à préserver

### A — Logiciel de caisse existant

POS externe → connecteur POS → contrat universel BillSmart (articles, quantités, prix, taxes, totaux) → paiement par un fournisseur → association vente/paiement → ticket enrichi BillSmart → BSM1/BSM5/QR.

### B — Terminal de paiement seul

Terminal / fournisseur de paiement → connecteur fournisseur → normalisation BillSmart → **ticket de paiement BillSmart**, même en l'absence de vente BillSmart préexistante → BSM1/BSM5/QR.

Les données commerciales peuvent être limitées. Utiliser le nombre d'articles, les prix ou les lignes de produits **seulement s'ils sont réellement fournis** ; sinon conserver un ticket fondé sur le montant, la devise et les informations de paiement disponibles. Ne jamais inventer les produits, les quantités ou la TVA. Le mode « dernière transaction POS » du POC historique était un choix **conforme à son objectif**, et non un défaut rétroactif.

### C — Aucune caisse existante

Une future **caisse BillSmart** saisit les articles, quantités, prix et taxes ; elle produit une transaction BillSmart, demande un paiement via un adaptateur, reçoit la confirmation et produit le ticket enrichi. La caisse complète est un objectif futur, **pas le livrable immédiat**.

## 3. POC prioritaire — BillSmart Transaction Simulator

Un petit outil doit permettre de :

1. Saisir ou éditer une transaction BillSmart (initialement JSON).
2. Valider son contrat et calculer les totaux.
3. Déclencher explicitement **PAYER**.
4. Créer/conserver une vente BillSmart identifiable **avant** l'appel au fournisseur.
5. Envoyer au fournisseur seulement la demande de paiement nécessaire.
6. Recevoir et vérifier l'état du paiement.
7. Corréler sans ambiguïté la vente, la demande de checkout et la transaction fournisseur, lorsque le flux comporte une vente préexistante.
8. Fusionner données commerciales BillSmart et données de paiement confirmées.
9. Générer le ticket enrichi BillSmart, puis l'envoyer à BSM5 pour affichage QR et consultation sur téléphone.

**Critère de succès fonctionnel final :** saisie des articles → clic PAYER → montant affiché sur Solo → paiement réel → confirmation associée à la bonne vente → ticket reprenant les articles BillSmart → BSM5/QR, sans manipulation SSH pour l'opérateur.

Le simulateur est un **banc de test du contrat universel**, non une intégration spécifique SumUp ni une caisse industrialisée.

## 4. Architecture et frontières

```text
POS externe ── adaptateur POS ───┐
Caisse BillSmart / Simulateur ───┼──> Transaction / vente universelle BillSmart
                                 │                  │
Terminal seul ─ adaptateur ──────┘                  ├──> Demande de paiement neutre
       │                                            │                │
       └──> Données de paiement normalisées         │        Adaptateur fournisseur
                                                    │                │
                                                    │          SumUp / autre
                                                    │                │
                                                    └──> Corrélation si vente préexistante
                                                                  │
                                                    Ticket BillSmart normalisé
                                                                  │
                                                            BSM1 → BSM5 → QR
```

**Nuance importante :** un ticket « terminal seul » ne requiert pas de vente BillSmart préalable ; la corrélation avec une vente préexistante concerne les parcours de vente détaillée.

**Composants :** BSM1 fournit les services backend et d'ingestion ; BSM5 assure l'affichage Edge / QR. L'intégration SumUp actuelle utilise une API Cloud et un Solo physique ; le connecteur historique effectue un polling des transactions et alimente la chaîne d'ingestion/ticket existante.

**Contrat conceptuel :** `sale`, `items`, `taxes`, `payment`, `merchant`, `source`, `metadata` (le schéma v0.1 actuel n'implémente pas nécessairement toutes ces sections séparément). Séparer **état de vente** et **état de paiement**. Le modèle universel ne doit pas intégrer de champs SumUp obligatoires.

## 5. Décisions actées

- **Indépendance fournisseur :** adaptateurs propriétaires à la périphérie, contrat BillSmart au centre.
- **Préserver le connecteur historique :** il valide le scénario « terminal seul » et la génération de tickets depuis des données de paiement.
- **Ne pas réécrire l'historique :** la sélection de la dernière transaction était adéquate pour le POC initial ; elle n'est pas suffisante, à elle seule, pour associer de manière certaine plusieurs ventes BillSmart concurrentes.
- **Pas de produits fictifs :** le ticket reprend les données réellement disponibles. Enrichissement commercial si les données sont présentes ; ticket de paiement sinon.
- **Corrélation déterministe :** pour les ventes détaillées, enregistrer la relation `sale_id ↔ demande de checkout ↔ transaction fournisseur`, selon les identifiants réellement disponibles.
- **Idempotence :** éviter les doubles tickets et les doubles traitements à partir d'identifiants métier/fournisseur pertinents.
- **Vérifier les API officielles :** ne pas supposer que l'endpoint Reader SumUp accepte `checkout_reference` ou un champ personnalisé sans preuve documentaire/testée.
- **Ne pas casser les jalons validés :** tests, commits et changements limités ; conserver le tag historique `poc-physical-solo-v1` intact.
- **Avancer par petites étapes :** une commande ou modification à la fois, validation de la sortie avant la suivante ; ne pas exposer les secrets `.env`, clés API, codes d'appairage ou domaines privés.

## 6. État technique connu au 10 octobre 2026

### Dépôts et branche

- Backend : `/home/billsmart1/boulxblb_receipts`, branche de travail connue `feature/sumup-edge-integration`.
- Connecteur : `/home/billsmart1/billsmart-sumup-connector`, branche `poc_sumup-solo_interfacage_blb-billsmart`.
- Dernier commit du connecteur confirmé : **`736ee2a`**, `Add real BillSmart sale to physical Solo flow`.
- État Git propre confirmé à la reprise de la Session 2.

### Jalons de référence

| Référence | Signification |
|---|---|
| `poc-physical-solo-v1` / `de6bdf5` | POC historique Solo physique → ticket BillSmart → BSM5, validé et figé |
| `b58e426` | Contrat universel BillSmart v0.1 |
| `bfddf03` | Demande de paiement neutre + adaptateur SumUp |
| `e58984f` | Client Reader + test du flux BillSmart → Solo mocké |
| `736ee2a` | Point d'entrée pour paiement réel à partir d'une vente BillSmart |

### Code du POC universel

- `connector/billsmart_transaction.py` : validation, total, `build_payment_request()`.
- `connector/sumup_payment_adapter.py` : conversion d'un montant EUR à deux décimales en payload Reader SumUp (`minor_unit=2`, `value` en centimes).
- `connector/sumup_reader_client.py` : profil marchand, readers, sélection Solo physique, envoi checkout.
- `connector/send_billsmart_sale_to_solo.py` : transaction de démonstration `BLB-REAL-0001`, 2 cafés à 2,50 € + 1 croissant à 1,20 € ; montant 6,20 € ; déclenchement du checkout réel.
- Tests : `tests/test_billsmart_transaction.py`, `tests/test_sumup_payment_adapter.py`, `tests/test_sumup_reader_client.py`, `tests/test_billsmart_sumup_flow.py`.

**Résultat validé :** 35 tests passés ; le Solo physique a affiché 6,20 €, un paiement carte réel a été effectué, et un ticket BillSmart est apparu sur BSM5. **Ce test ne prouve pas encore** que le ticket final contient les désignations « Café » et « Croissant » de la vente d'origine : la voie retour emprunte encore le connecteur historique.

### Connecteur historique

`connector/build_billsmart_ticket.py` : charge la configuration SumUp, récupère `/v0.1/me`, l'historique des 20 transactions, filtre `payment_type == "POS"`, prend la plus récente par timestamp, vérifie l'idempotence, récupère ses détails, extrait les données de produits disponibles, construit le ticket et poursuit la livraison. Ce flux répondait à son objectif initial de récupération du paiement terminal autonome.

Autres modules historiques : `connector/poll_sumup.py`, `connector/billsmart_csv.py`, `connector/receipt_delivery.py`, `connector/idempotency.py`, `connector/billsmart_ingestion.py`, et scripts de création de checkout. Un service systemd de polling avait été validé lors du POC historique.

## 7. Limites connues, sans extrapolation

- Le contrat v0.1 exige actuellement au moins un article : il devra être adapté pour représenter proprement un **paiement seul**, sans inventer de ligne commerciale.
- `item.total` n'est pas encore vérifié contre `quantity × unit_price` ; la politique de TVA (HT/TTC, arrondis) reste à définir.
- `issued_at`, `source`, `merchant`, `payment.status` et les montants non finis ne sont pas encore complètement validés.
- L'adaptateur SumUp v0.1 suppose **EUR / deux décimales** ; ce n'est pas une règle universelle des devises.
- La corrélation déterministe entre `sale_id`, checkout Reader et transaction fournisseur n'est **pas encore implémentée**.
- Le statut et les identifiants réellement renvoyés par l'API Reader doivent être examinés et vérifiés ; aucune hypothèse de champ de référence personnalisé ne doit être codée sans validation.
- L'interface du Transaction Simulator et le moteur de ticket enrichi basé sur la vente d'origine restent à développer.
- La gestion de plusieurs transactions, des échecs, des annulations et de la reprise après redémarrage reste à spécifier/tester.

## 8. Règle de reprise et de clôture

**Au début de chaque session :** lire ce document, lire la dernière entrée du journal, vérifier branche/commit/état Git, puis reprendre la prochaine étape prévue. Ne pas redéfinir les objectifs sans changement explicitement acté.

**À la fin de chaque session :** compléter `BILLSMART_JOURNAL_SESSIONS.md` avec résultats vérifiés, modifications, commits, décisions, questions ouvertes et **première commande de reprise**. Modifier ce document de référence uniquement si une décision d'architecture évolue ; documenter la raison et la date.

**Confidentialité :** ne jamais consigner les secrets, `.env`, jetons, identifiants sensibles ou informations de paiement personnelles dans ces documents.

## 9. Revue d’alignement et état d’avancement — 15 octobre 2026

**Nature de cette mise à jour :** actualisation factuelle, **sans changement des décisions architecturales** des sections 1 à 5. Les états et limites historiques des sections 6 et 7 décrivent la situation au 10 octobre et ne doivent pas être lus comme l’état courant.

### Direction confirmée

- Le **BillSmart Transaction Simulator** reste le livrable prioritaire du POC : vente éditable (JSON au départ), validation, commande explicite **PAYER**, persistance de la vente avant paiement, corrélation déterministe, ticket enrichi, puis livraison BSM1 → BSM5 → QR.
- Le cœur BillSmart demeure indépendant des logiciels de caisse et des fournisseurs de paiement ; SumUp Reader/Solo n’est que le premier adaptateur concret.
- Préserver les trois scénarios : caisse externe, terminal seul (sans vente préalable ni articles inventés), et future caisse BillSmart.
- Ne pas modifier rétroactivement le poller historique ni le jalon `poc-physical-solo-v1` (`de6bdf5`).

### État logiciel confirmé pendant la Session 3

**Dépôt :** `/home/billsmart1/billsmart-sumup-connector` ; **branche :** `poc_sumup-solo_interfacage_blb-billsmart` ; **dernier commit publié et synchronisé :** `7e4b4f0` (`Enforce BillSmart payment confirmation state transitions`). **Suite complète : 86 tests réussis.** Répertoire de travail propre au dernier `git status -sb` transmis.

| Composant | État observé |
|---|---|
| `connector/billsmart_transaction.py` | Contrat de vente v0.1 et `build_payment_request()` neutre |
| `connector/billsmart_sale_registry.py` | Persistance/chargement des ventes et contrôles de doublons |
| `connector/billsmart_payment_registry.py` | Persistance des paiements, références fournisseur, transitions et idempotence |
| `connector/billsmart_payment_link.py` | Création d’un paiement lié à une vente persistée |
| `connector/sumup_payment_adapter.py` | Payload Reader, extraction d’identifiants et normalisation de réponses simulées |
| `connector/sumup_reader_client.py` | Envoi au Solo et GET ciblé `get_reader_checkout()` ; GET non exécuté en réel dans cette session |
| `connector/billsmart_payment_verification.py` | Correspondance des identifiants, montant/devise, et transitions autorisées ; tests positifs/négatifs |

**Précision importante :** la corrélation dispose de briques de persistance et de vérification, **mais le parcours de confirmation authentifiée de bout en bout n’est pas encore intégré ni démontré**. Les fonctions de vérification ne constituent pas une preuve d’authenticité de la réponse fournisseur. Les tests de normalisation reposent sur des formats simulés ; vérifier le schéma réel et la documentation officielle de SumUp Reader avant tout traitement automatique de paiement.

### Limites et risques toujours ouverts

1. Orchestration sécurisée `load_payment → GET fournisseur authentifié → normalisation → vérification → update_payment_status`, avec tests mockés de non-modification en cas d’erreur ; vérifier la présence réelle des identifiants et les champs de statut/montant retournés par SumUp.
2. Le vérificateur initial exige deux références fournisseur (`checkout_id` et `client_transaction_id`) : confirmer leur disponibilité réelle, et concevoir à terme une stratégie adaptée aux autres fournisseurs sans affaiblir la corrélation.
3. Le registre JSON écrit via fichier temporaire, mais **sans verrouillage concurrent** ; traiter les courses critiques avant exploitation multiprocessus.
4. Vente détaillée → ticket enrichi reprenant les vrais articles → BSM1/BSM5/QR : **non encore réalisé**.
5. Interface du simulateur (édition JSON, validation, bouton PAYER, état du paiement) : **non encore réalisée**.
6. Contrat terminal seul sans article fictif, validation arithmétique des lignes, politique TVA/arrondis, multi-devises, erreurs, reprise et absence de doubles tickets : travaux ouverts.

### Priorités de développement proposées

1. Vérifier les champs réels de l’API Reader et réaliser une orchestration de confirmation **testée hors réseau** ; aucun paiement réel sans autorisation explicite.
2. Réaliser la fusion vente + paiement confirmé et le ticket enrichi, avec tests déterministes et sans altérer le poller terminal seul.
3. Réaliser une première interface **BillSmart Transaction Simulator** minimale, puis brancher le parcours complet jusqu’à BSM5/QR.
4. Valider ensuite les scénarios d’erreur, idempotence de livraison, concurrence et redémarrage, avant toute industrialisation.

**Règle documentaire :** garder les jalons historiques inchangés ; compléter le journal à chaque session et actualiser cette section de synthèse lorsqu’un état majeur change.

# BillSmart – Connecteur SumUp

## Présentation

Ce projet vise à développer un connecteur entre SumUp
et BillSmart, exclusivement pour l'application BOUL.

## Objectif

Automatiser la récupération des données de vente SumUp
afin de générer des tickets numériques BillSmart.

## Architecture cible

SumUp Sandbox
    |
    v
Connecteur SumUp
    |
    v
BSM1 - Backend BOUL
    |
    v
BSM5 - Écran e-Paper
    |
    v
QR Code
    |
    v
Ticket numérique BillSmart

## Périmètre

- Intégration avec les API SumUp.
- Récupération des transactions et, lorsque disponibles,
  des informations sur les articles achetés.
- Transformation des données au format BOUL.
- Transmission au backend BOUL sur BSM1.
- Affichage du QR Code sur BSM5.
- Tests initiaux sans matériel SumUp.

## État du projet

Phase 1 : initialisation du dépôt GitHub et
étude des API SumUp.

## Sécurité

Les identifiants, clés API et jetons d'authentification
ne doivent jamais être enregistrés dans ce dépôt.
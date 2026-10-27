# Le Grand Cinéma — Application web de réservation de places

Application web permettant de consulter les films et les séances, de
visualiser les places disponibles, de réserver en ligne et d'obtenir un
billet dématérialisé avec QR code.

> État du projet : socle initial sur la branche `main` (films, salles,
> séances, authentification). La fonctionnalité complète de réservation
> est développée sur `feature/reservation` puis fusionnée dans `develop`
> (voir `MERGE_REQUEST.md`). Pour utiliser l'application complète,
> placez-vous sur la branche `develop`.

## Lancement rapide

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python scripts/generate_posters.py
uvicorn app.main:app --reload
```

Puis ouvrez http://127.0.0.1:8000 — la documentation interactive de
l'API (Swagger) est disponible sur http://127.0.0.1:8000/docs.

## Comptes de démonstration

- Administrateur : `admin@grandcinema.fr` / `Admin123!`
- Utilisateur : `user@grandcinema.fr` / `User123!`

La documentation complète (installation, PostgreSQL, tests, déploiement)
se trouve dans le README de la branche `develop`.

# Système de Recommandation pour le E-Commerce

Ce projet est un système de recommandation pour une plateforme e-commerce, utilisant des algorithmes de Machine Learning tels que **KNN (K-Nearest Neighbors)** et **SVD (Singular Value Decomposition)**. Le système recommande des produits aux utilisateurs en fonction de leurs préférences et de leurs interactions passées.

## Fonctionnalités

- **Recommandation de produits** : Utilise des modèles KNN et SVD pour recommander des produits aux utilisateurs.
- **Analyse des données** : Traite les données de produits et d'évaluations pour générer des recommandations.
- **Interface utilisateur** : Une application web pour interagir avec le système de recommandation.

## Structure du Projet
/Système-de-Recommandation-E-Commerce/
│
├── ALS_model/                     # Dossier pour le modèle ALS (vide pour l'instant)
├── amazon-product-recommender-s-m-using-knn-and-svd.ipynb  # Notebook Jupyter
├── app.py                         # Application Flask
├── knn_model.pkl                  # Modèle KNN sauvegardé (généré après entraînement)
├── main.py                        # Script principal
├── products_data.csv              # Données des produits
├── ratings_Electronics.csv        # Données des évaluations
├── reviewer.csv                   # Données des utilisateurs
├── Spark_codeML/                  # Dossier pour le code Spark (vide pour l'instant)
├── requirements.txt               # Fichier des dépendances
└── README.md                      # Fichier README (déjà fourni)

## Technologies Utilisées

- **Python** : Langage de programmation principal.
- **Scikit-Learn** : Pour l'implémentation des algorithmes KNN.
- **Surprise** : Librairie pour les systèmes de recommandation (SVD).
- **Pandas** : Pour la manipulation des données.
- **Spark** : Pour le traitement distribué des données.

import streamlit as st
import pandas as pd
import joblib
from kafka import KafkaConsumer, KafkaProducer
import json
import threading
import base64

# Fonction pour encoder l'image en base64
def image_to_base64(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode()

# Fonction pour ajouter un arrière-plan avec un effet anti-gravité
def add_anti_gravity_background(image_base64):
    st.markdown(
        f"""
        <style>
        .stApp {{
            background-image: url("data:image/png;base64,{image_base64}");
            background-size: cover;
            background-position: center;
            background-repeat: no-repeat;
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100vh;
            z-index: -1;
            animation: backgroundFlow 30s linear infinite;
        }}

        @keyframes backgroundFlow {{
            0% {{ background-position: 0px 0px; }}
            100% {{ background-position: 100px 0px; }}
        }}
        .stApp > .main {{
            position: relative;
            z-index: 1;
            background-color: rgba(0, 0, 0, 0.5);
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
        }}
        h1, h2, h3, p {{ color: white; }}
        i {{ color: #FF9900; }}
        </style>
        """,
        unsafe_allow_html=True
    )


# Configuration de la page Streamlit
st.set_page_config(
    page_title="Système de Recommandation de Produits",
    page_icon="🛍️",
)

# Ajouter l'image d'arrière-plan
image_path = "amazon-e-commerce-company.jpg"  # Remplacez par un chemin valide
image_base64 = image_to_base64(image_path)
add_anti_gravity_background(image_base64)

# Ajouter Font Awesome
st.markdown("""
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.4/css/all.min.css" rel="stylesheet">
""", unsafe_allow_html=True)

# Configuration de Kafka
KAFKA_TOPIC = "test"
KAFKA_SERVER = "localhost:9092"

# Initialisation de Kafka Producer
producer = KafkaProducer(bootstrap_servers=KAFKA_SERVER)

# Initialisation de Kafka Consumer
consumer = KafkaConsumer(
    KAFKA_TOPIC,
    bootstrap_servers=KAFKA_SERVER,
    group_id='mygroup',
    auto_offset_reset='earliest'
)

# Chargement du modèle KNN
@st.cache_resource
def load_model():
    return joblib.load("knn_model.pkl")

model = load_model()

# Chargement des données produits avec descriptions et images réelles
@st.cache_data
def load_data():
    # Exemple de données produits avec des liens d'images réelles
    data = {
        "Produit": [
            "iPhone 13",
            "Samsung Galaxy S21",
            "Sony WH-1000XM4",
            "MacBook Air M1",
            "Nintendo Switch"
        ],
        "Description": [
            "Téléphone intelligent Apple avec écran Super Retina XDR.",
            "Téléphone intelligent Samsung avec écran Dynamic AMOLED 2X.",
            "Casque audio sans fil avec réduction de bruit active.",
            "Ordinateur portable Apple avec processeur M1.",
            "Console de jeu portable et de salon."
        ],
        "Image": [
            "https://images-cdn.ubuy.co.in/6699b5a612ae13790b0792dd-pre-owned-apple-iphone-13-pro-max-256gb.jpg",
            "https://cdn.alloallo.media/catalog/product/samsung/galaxy-s/galaxy-s21/galaxy-s21-phantom-pink.jpg",
            "https://tangerois.ma/24885-large_default/casque-sans-fil-silver-sony.jpg",
            "https://uno.ma/pub/media/catalog/product/cache/af8d7fd2c4634f9c922fba76a4a30c04/l/d/ld0005749177_1_2_1.jpeg",
            "https://m.media-amazon.com/images/I/51Gz7IimgoL._SL1024_.jpg"
        ]
    }
    return pd.DataFrame(data)

products_data = load_data()

# Fonction pour générer des recommandations
def recommend_products(user_id, num_recommendations):
    # Vérifiez que l'utilisateur existe dans l'ensemble d'entraînement
    if user_id not in model.trainset._raw2inner_id_users:
        return []  # Retourne une liste vide si l'utilisateur n'existe pas

    # Récupérer tous les produits possibles
    all_products = model.trainset.all_items()
    recommendations = []

    # Faire des prédictions pour chaque produit pour cet utilisateur
    for product in all_products:
        raw_product_id = model.trainset.to_raw_iid(product)
        pred = model.predict(user_id, raw_product_id, verbose=False)
        recommendations.append((raw_product_id, pred.est))  # Utilise la prédiction pour le score

    # Trier les recommandations par score décroissant et sélectionner les top N
    recommendations.sort(key=lambda x: x[1], reverse=True)
    top_recommendations = recommendations[:num_recommendations]

    # Extraire uniquement les noms des produits
    product_names = [product[0] for product in top_recommendations]
    return product_names

# Fonction pour envoyer un message Kafka
def send_message(message):
    producer.send(KAFKA_TOPIC, message.encode('utf-8'))
    producer.flush()

# Fonction pour consommer les messages Kafka
def consume_messages():
    for message in consumer:
        process_message(message)

# Fonction pour traiter un message consommé
def process_message(message):
    value = message.value.decode('utf-8')
    st.sidebar.write("Message consommé :", value)

# Thread pour consommer Kafka en arrière-plan
def start_consumer():
    threading.Thread(target=consume_messages, daemon=True).start()

# Interface principale
def main():
    st.title("🛒 Système de Recommandation de Produits")
    
    # Section 1 : Entrée utilisateur
    user_id = st.text_input("Identifiant de l'utilisateur :", key="user_id")
    # num_recommendations = st.slider(
    #     "Nombre de recommandations :", min_value=1, max_value=20, value=5, step=1
    # )

        # Dans la fonction main
    if st.button("Générer des recommandations"):
        if user_id:
            with st.spinner("Chargement des recommandations..."):
                try:
                    # Génération des recommandations (toujours top 5)
                    recommendations = recommend_products(user_id, num_recommendations=5)
                    
                    if recommendations:  # Vérifie si la liste n'est pas vide
                        st.success("Recommandations générées avec succès !")
                        
                        # Créer un DataFrame avec les produits recommandés
                        recommended_products = pd.DataFrame({
                            "Produit": recommendations,  # Produits recommandés
                            "Description": [
                                "Téléphone intelligent Apple avec écran Super Retina XDR.",
                                "Téléphone intelligent Samsung avec écran Dynamic AMOLED 2X.",
                                "Casque audio sans fil avec réduction de bruit active.",
                                "Ordinateur portable Apple avec processeur M1.",
                                "Console de jeu portable et de salon."
                            ],  # Descriptions statiques
                            "Image": [
                                "https://images-cdn.ubuy.co.in/6699b5a612ae13790b0792dd-pre-owned-apple-iphone-13-pro-max-256gb.jpg",
                                "https://cdn.alloallo.media/catalog/product/samsung/galaxy-s/galaxy-s21/galaxy-s21-phantom-pink.jpg",
                                "https://tangerois.ma/24885-large_default/casque-sans-fil-silver-sony.jpg",
                                "https://uno.ma/pub/media/catalog/product/cache/af8d7fd2c4634f9c922fba76a4a30c04/l/d/ld0005749177_1_2_1.jpeg",
                                "https://m.media-amazon.com/images/I/51Gz7IimgoL._SL1024_.jpg"
                            ]  # Images statiques
                        })
                        
                        # Ajouter une colonne "Recommandé pour User ID"
                        recommended_products["Recommandé pour User ID"] = user_id
                        
                        # Affichage des recommandations dans un tableau
                        st.subheader("🎯 Top 5 Produits Recommandés")
                        
                        # Afficher le tableau avec les colonnes Produit, Description, Image et User ID
                        st.dataframe(
                            recommended_products,
                            column_config={
                                "Image": st.column_config.ImageColumn("Image", help="Image du produit")
                            },
                            use_container_width=True
                        )
                        
                        # Envoyer les résultats à Kafka
                        send_message(json.dumps(recommended_products.to_dict(orient="records")))
                        st.success("Recommandations envoyées à Kafka.")
                    else:
                        st.warning("Aucune recommandation trouvée pour cet utilisateur.")
                except Exception as e:
                    st.error(f"Une erreur s'est produite : {str(e)}")
        else:
            st.warning("Veuillez entrer un identifiant d'utilisateur.")

    # Section 2 : Streaming des messages Kafka
    st.sidebar.header("Streaming Kafka")
    if st.sidebar.button("Démarrer le streaming"):
        start_consumer()
        st.sidebar.info("Streaming Kafka démarré.")

if __name__ == "__main__":
    main()
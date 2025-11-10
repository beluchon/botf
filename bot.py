
# api.py
import os
import uuid
import psycopg2
from flask import Flask, request, jsonify
from datetime import datetime
import sys

# Configuration de la base de données
DB_CONFIG = {
    "dbname": os.getenv("POSTGRES_DB", "streamfusion"),
    "user": os.getenv("POSTGRES_USER", "postgres"),
    "password": os.getenv("POSTGRES_PASSWORD", "postgres"),
    "host": os.getenv("POSTGRES_HOST", "host.docker.internal"),
    "port": os.getenv("POSTGRES_PORT", "5432")
}

# Clé secrète pour l'API
SECRET_KEY = os.getenv("API_SECRET_KEY", "testuu")

app = Flask(__name__)

def connect_db(max_retries=5, retry_delay=5):
    import time
    for attempt in range(max_retries):
        try:
            conn = psycopg2.connect(**DB_CONFIG)
            print("Connexion à la base de données établie avec succès")
            return conn
        except Exception as e:
            print(f"Tentative {attempt + 1}/{max_retries} - Erreur de connexion: {e}")
            if attempt < max_retries - 1:
                print(f"Nouvelle tentative dans {retry_delay} secondes...")
                time.sleep(retry_delay)
    return None

def authenticate_request():
    """Vérifie la clé secrète dans l'en-tête de la requête"""
    secret_key = request.headers.get('secret-key')
    return secret_key == SECRET_KEY

@app.route('/api/auth/new', methods=['POST'])
def generate_api_key():
    """Génère une nouvelle clé API"""
    
    # Authentification
    if not authenticate_request():
        return jsonify({"error": "Clé secrète invalide"}), 401
    
    # Récupération des paramètres
    name = request.args.get('name', 'API User')
    never_expires = request.args.get('never_expires', 'true').lower() == 'true'
    
    try:
        conn = connect_db()
        if not conn:
            return jsonify({"error": "Impossible de se connecter à la base de données"}), 500

        api_key = str(uuid.uuid4())
        is_active = True
        total_queries = -1  # Illimité

        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO api_keys (api_key, is_active, never_expire, total_queries, name)
                VALUES (uuid(%s), %s, %s, %s, %s)
                RETURNING api_key, created_at
                """,
                (api_key, is_active, never_expires, total_queries, name)
            )
            result = cur.fetchone()
            returned_key = result[0]
            created_at = result[1]
            conn.commit()

            print(f"Nouvelle clé API générée pour l'utilisateur: {name}")
            
            response_data = {
                "success": True,
                "api_key": returned_key,
                "name": name,
                "never_expires": never_expires,
                "total_queries": "unlimited",
                "created_at": created_at.isoformat() if created_at else datetime.now().isoformat()
            }
            
            return jsonify(response_data), 201
            
    except Exception as e:
        error_msg = f"Erreur lors de la génération de la clé API: {e}"
        print(error_msg)
        return jsonify({"error": "Erreur interne du serveur"}), 500
    finally:
        if conn:
            conn.close()

@app.route('/api/auth/keys', methods=['GET'])
def list_api_keys():
    """Liste toutes les clés API (pour administration)"""
    
    if not authenticate_request():
        return jsonify({"error": "Clé secrète invalide"}), 401
    
    try:
        conn = connect_db()
        if not conn:
            return jsonify({"error": "Impossible de se connecter à la base de données"}), 500

        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT api_key, name, is_active, never_expire, total_queries, created_at
                FROM api_keys
                ORDER BY created_at DESC
                """
            )
            keys = cur.fetchall()
            
            result = []
            for key_data in keys:
                result.append({
                    "api_key": key_data[0],
                    "name": key_data[1],
                    "is_active": key_data[2],
                    "never_expires": key_data[3],
                    "total_queries": "unlimited" if key_data[4] == -1 else key_data[4],
                    "created_at": key_data[5].isoformat() if key_data[5] else None
                })
            
            return jsonify({"keys": result}), 200
            
    except Exception as e:
        error_msg = f"Erreur lors de la récupération des clés API: {e}"
        print(error_msg)
        return jsonify({"error": "Erreur interne du serveur"}), 500
    finally:
        if conn:
            conn.close()

@app.route('/api/auth/revoke', methods=['POST'])
def revoke_api_key():
    """Révoque une clé API"""
    
    if not authenticate_request():
        return jsonify({"error": "Clé secrète invalide"}), 401
    
    api_key = request.args.get('api_key')
    if not api_key:
        return jsonify({"error": "Paramètre api_key manquant"}), 400
    
    try:
        conn = connect_db()
        if not conn:
            return jsonify({"error": "Impossible de se connecter à la base de données"}), 500

        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE api_keys 
                SET is_active = FALSE 
                WHERE api_key = uuid(%s)
                RETURNING api_key, name
                """,
                (api_key,)
            )
            result = cur.fetchone()
            
            if result:
                conn.commit()
                print(f"Clé API révoquée: {result[1]} ({result[0]})")
                return jsonify({
                    "success": True,
                    "message": f"Clé API révoquée pour {result[1]}"
                }), 200
            else:
                return jsonify({"error": "Clé API non trouvée"}), 404
            
    except Exception as e:
        error_msg = f"Erreur lors de la révocation de la clé API: {e}"
        print(error_msg)
        return jsonify({"error": "Erreur interne du serveur"}), 500
    finally:
        if conn:
            conn.close()

@app.route('/health', methods=['GET'])
def health_check():
    """Endpoint de santé"""
    try:
        conn = connect_db()
        if conn:
            conn.close()
            return jsonify({"status": "healthy", "database": "connected"}), 200
        else:
            return jsonify({"status": "unhealthy", "database": "disconnected"}), 503
    except Exception as e:
        return jsonify({"status": "unhealthy", "error": str(e)}), 503

if __name__ == '__main__':
    port = int(os.getenv("API_PORT", 8082))
    debug = os.getenv("DEBUG", "false").lower() == "true"
    
    print(f"Démarrage de l'API sur le port {port}")
    app.run(host='0.0.0.0', port=port, debug=debug)

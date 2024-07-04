from flask import Flask, request, jsonify
import requests
from bs4 import BeautifulSoup
import Levenshtein
import hashlib
import os
import redis
import logging
from datetime import datetime, timedelta

app = Flask(__name__)

# Настройка кэша
cache = redis.Redis(host='localhost', port=6379, db=0)

# Настройка логирования
logging.basicConfig(filename='service.log', level=logging.INFO,
                    format='%(asctime)s %(levelname)s %(message)s')

# Порог расстояния Левенштейна
LEVENSHTEIN_THRESHOLD = 2

# Функция для генерации токена
def generate_token():
    token = os.urandom(32).hex()
    hashed_token = hashlib.sha3_512(token.encode()).hexdigest()
    return token, hashed_token

# Эндпоинт для генерации токенов
@app.route('/generate_token', methods=['POST'])
def generate_token_endpoint():
    token, hashed_token = generate_token()
    # Сохраните hashed_token в базу данных
    return jsonify({'token': token})

# Авторизация
def check_auth(token):
    hashed_token = hashlib.sha3_512(token.encode()).hexdigest()
    # Проверьте hashed_token в базе данных
    return True

# Основной эндпоинт
@app.route('/analyze', methods=['POST'])
def analyze():
    data = request.json
    url = data.get('url')
    phrase = data.get('phrase')
    token = request.headers.get('Authorization')

    if not check_auth(token):
        return jsonify({'error': 'Unauthorized'}), 401

    cache_key = f'{url}_{phrase}'
    cached_result = cache.get(cache_key)
    if cached_result:
        logging.info(f'Cache hit for {url} with phrase {phrase}')
        return jsonify(eval(cached_result))

    try:
        response = requests.get(url)
        response.raise_for_status()
        content = response.text
    except requests.exceptions.RequestException as e:
        logging.error(f'Error fetching {url}: {str(e)}')
        return jsonify({'error': str(e)}), response.status_code

    soup = BeautifulSoup(content, 'html.parser')
    text = soup.get_text()
    text = ''.join(text.split()).lower()
    phrase = ''.join(phrase.split()).lower()

    distances = [Levenshtein.distance(text[i:i+len(phrase)], phrase)
                 for i in range(len(text) - len(phrase) + 1)]
    min_distance = min(distances)

    result = {
        'found': min_distance <= LEVENSHTEIN_THRESHOLD,
        'levenshtein_distance': min_distance
    }

    cache.setex(cache_key, timedelta(minutes=60), str(result))

    logging.info(f'Processed request for {url} with phrase {phrase}')
    return jsonify(result)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

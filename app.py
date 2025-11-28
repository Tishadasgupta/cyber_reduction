from flask import Flask, render_template, request, jsonify
from logic import get_redacted_result

app = Flask(__name__)

# Levenshtein Similarity Calculation (Accuracy Score)
def calculate_similarity(s1, s2):
    if not s1 or not s2: return 0.0
    rows = len(s1) + 1
    cols = len(s2) + 1
    distance = [[0 for _ in range(cols)] for _ in range(rows)]
    for i in range(1, rows):
        for k in range(1, cols):
            distance[i][0] = i
            distance[0][k] = k
    for col in range(1, cols):
        for row in range(1, rows):
            cost = 0 if s1[row-1] == s2[col-1] else 2
            distance[row][col] = min(distance[row-1][col]+1, distance[row][col-1]+1, distance[row-1][col-1]+cost)
    
    max_len = len(s1) + len(s2)
    return round(((max_len - distance[rows-1][cols-1]) / max_len) * 100, 2)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/api/redact', methods=['POST'])
def redact():
    data = request.json
    text = data.get('text', '')
    mode = data.get('mode', 'Redact')

    redacted_text, entities = get_redacted_result(text, mode)
    score = calculate_similarity(text, redacted_text)

    return jsonify({
        'original': text,
        'redacted': redacted_text,
        'entities': entities,
        'score': score
    })

if __name__ == '__main__':
    app.run(debug=True)
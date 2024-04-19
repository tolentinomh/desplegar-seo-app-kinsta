from flask import Flask, request, render_template_string
import requests
import openai
import os
import base64
from collections import Counter
import re

app = Flask(__name__)

# Función para limpiar y extraer palabras clave
def extract_keywords(titles):
    words = []
    for title in titles:
        # Remover caracteres especiales y dividir en palabras
        tokens = re.findall(r'\b\w+\b', title.lower())
        words.extend(tokens)
    # Contar frecuencia de cada palabra, ignorando palabras comunes
    stop_words = set(["a","de", "en", "y", "el", "la", "los", "las", "un", "una", "unos", "unas", "del", "al", "que","por"])
    keyword_counts = Counter(word for word in words if word not in stop_words)
    return keyword_counts.most_common(10)  # Devuelve las 10 palabras más comunes

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Generador de Títulos SEO basados en el Top 10</title>
    <link href="https://maxcdn.bootstrapcdn.com/bootstrap/4.5.2/css/bootstrap.min.css" rel="stylesheet">
    <script src="https://d3js.org/d3.v5.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/d3-cloud/1.2.5/d3.layout.cloud.js"></script>


    <style>
        body { padding: 20px; }
        .container { max-width: 800px; margin: auto; }
        .result-list, .keyword-analysis { margin-top: 20px; }
        .suggested-title { margin-top: 20px; color: #007bff; }
        #tag-cloud {width: 100%;height: 300px;position: relative;font-family: 'Arial', sans-serif;}
        .recommended-title-card {
        display: flex;
        flex-direction: column;
        justify-content: center; /* Centra verticalmente el contenido en la tarjeta */
        height: 100%; /* Asegura que la tarjeta ocupa la altura total del contenedor de la columna */
       }
        .recommended-title {
            font-size: 1.5rem; /* Aumenta el tamaño de la fuente */
            font-weight: bold; /* Hace el texto en negrita */
            color: #007bff; /* Color del texto */
            margin: 0; /* Elimina los márgenes por defecto */
        }
        /* Ajusta el tamaño del título basado en el viewport para responsividad */
        @media (min-width: 768px) {
            .recommended-title {
                font-size: 2rem; /* Tamaño de la fuente para pantallas más grandes */
            }
        }

    </style>
</head>
<body>
    <div class="container">
        <h1 class="mb-4">Generador de Títulos SEO</h1>
        <form method="post" class="mb-5">
            <div class="form-group">
                <label for="keyword">Introduce un término de búsqueda</label>
                <input type="text" class="form-control" id="keyword" name="keyword" placeholder="Introduce un término de búsqueda...">
            </div>
            <div class="form-group">
                <label for="length">Longitud del título:</label>
                <select class="form-control" id="length" name="length">
                    <option value="short">Corto</option>
                    <option value="medium">Medio</option>
                    <option value="long">Largo</option>
                </select>
            </div>
            <div class="form-group">
                <label for="focus">Centrarse en tipos de palabras clave:</label>
                <select class="form-control" id="focus" name="focus">
                    <option value="general">General</option>
                    <option value="specific">Específica</option>
                </select>
            </div>
            <button type="submit" class="btn btn-primary">Crear Titular</button>
        </form>

        {% if suggested_topic %}
    <div class="row">
        <div id="tag-cloud" class="mb-4 col-lg-12" style="height: 300px;"></div>

        <div class="col-lg-12 mb-4">
            <div class="card recommended-title-card">
                <div class="card-body">
                    <p class="recommended-title">{{ suggested_topic }}</p>
                </div>
            </div>
        </div>
        
        <div class="col-lg-4 mb-4">
            <div class="card h-100">
                <div class="card-body">
                    <h3 class="card-title">Palabras más usadas en los Títulos:</h3>
                    <ul class="list-group list-group-flush">
                        {% for word, count in keywords %}
                            <li class="list-group-item">{{ word }} ({{ count }})</li>
                        {% endfor %}
                    </ul>
                </div>
            </div>
        </div>

        <div class="col-lg-8 mb-4">
            <div class="card h-100">
                <div class="card-body">
                    <h3 class="card-title">Basados en los Títulos:</h3>
                    <ul class="list-group list-group-flush">
                        {% for title in top_titles %}
                            <li class="list-group-item">{{ title }}</li>
                        {% endfor %}
                    </ul>
                </div>
            </div>
        </div>
    </div>
{% endif %}

    </div>
<script type="text/javascript">
window.onload = function() {
    var fill = d3.scaleOrdinal(d3.schemeCategory10);  // Escala de colores categórica

    var words = [
        {% for word, count in keywords %}
            {text: "{{ word }}", size: Math.log({{ count }} + 1) * 30},  // Ajusta el tamaño de la fuente
        {% endfor %}
    ];

    var layout = d3.layout.cloud()
        .size([960, 300])  // Dimensiones de la nube
        .words(words)
        .padding(10)  // Espaciado entre palabras
        .rotate(0)  // Sin rotación o como prefieras
        .font("Impact")
        .fontSize(function(d) { return d.size; })  // Función para el tamaño de la fuente
        .on("end", draw);

    layout.start();

    function draw(words) {
        var svg = d3.select("#tag-cloud").append("svg")
            .attr("width", layout.size()[0])
            .attr("height", layout.size()[1])
            .append("g")
            .attr("transform", "translate(" + (layout.size()[0] / 2 - 80) + "," + layout.size()[1] / 2 + ")");


        svg.selectAll("text")
            .data(words)
            .enter().append("text")
            .style("font-size", function(d) { return d.size + "px"; })
            .style("font-family", "Impact")
            .style("fill", function(d, i) { return fill(i); })  // Color
            .attr("text-anchor", "middle")
            .attr("transform", function(d) {
                return "translate(" + [d.x, d.y] + ")";
            })
            .text(function(d) { return d.text; });
    }
};
</script>

</body>
</html>

'''

@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        keyword = request.form['keyword']
        length_preference = request.form.get('length', 'medium')  # Defaults to medium if not specified
        keyword_focus = request.form.get('focus', 'general')  # Defaults to general if not specified

        # Obtener credenciales de las variables de entorno
        dataforseo_username = os.getenv('DATAFORSEO_USERNAME')
        dataforseo_password = os.getenv('DATAFORSEO_PASSWORD')

         # Codificar las credenciales en base64 para la autorización
        credentials = f"{dataforseo_username}:{dataforseo_password}".encode('utf-8')
        encoded_credentials = base64.b64encode(credentials).decode('utf-8')

        # Obtener resultados de SEO
        url = "https://api.dataforseo.com/v3/serp/google/organic/live/advanced"
        payload = f"""[{{
            "keyword": "{keyword}",
            "location_code": 2724,
            "language_code": "es",
            "device": "desktop",
            "os": "windows",
            "depth": 100
        }}]"""
        headers = {
            'Authorization': f'Basic {encoded_credentials}',
            'Content-Type': 'application/json'
        }

        response = requests.post(url, headers=headers, data=payload)
        results = response.json()['tasks'][0]['result'][0]['items']
        top_titles = [item['title'] for item in results[:10] if 'title' in item]
        keywords = extract_keywords(top_titles)

        # Ajustar prompt basado en preferencias
        title_length = "un título largo y detallado" if length_preference == 'long' else "un título corto y conciso" if length_preference == 'short' else "un título de longitud media"
        focus_type = "con un enfoque en términos específicos y técnicos" if keyword_focus == 'specific' else "con un enfoque en términos más generales y amplios"
        
        prompt = f"Genera {title_length} {focus_type}, basado en los siguientes títulos de artículos bien posicionados en Google: " + ", ".join(top_titles)

        openai.api_key = os.getenv("OPENAI_API_KEY")
        client = openai.OpenAI(api_key=openai.api_key)

        chat_completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": "Eres un experto en marketing online y SEO."},
                {"role": "user", "content": prompt}
            ],
            model="gpt-3.5-turbo",
        )

        suggested_topic = chat_completion.choices[0].message.content if chat_completion.choices else "No se pudo generar un tema."

        return render_template_string(HTML_TEMPLATE, suggested_topic=suggested_topic, top_titles=top_titles, keywords=keywords)

    return render_template_string(HTML_TEMPLATE, suggested_topic=None, top_titles=[], keywords=[])

if __name__ == '__main__':
    app.run(debug=True)

from flask import Flask
from flask_cors import CORS
from routes.search import search_bp
from routes.paper import paper_bp

app = Flask(__name__)
CORS(app)

app.register_blueprint(search_bp)
app.register_blueprint(paper_bp)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
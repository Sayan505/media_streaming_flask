import os

from flask              import Flask
from flask_cors         import CORS
from flask_jwt_extended import JWTManager

from config.orm         import db

# import modules
from modules            import oauth_module, user_module


# init server
app = Flask(__name__)
app.url_map.strict_slashes   = False
app.config["JSON_SORT_KEYS"] = False
app.secret_key               = os.environ["FLASK_SECRET_KEY"]

# init CORS
CORS(app)

# init PyJWT
app.config["JWT_SECRET_KEY"]           = os.environ["JWT_SECRET_KEY"]
app.config["JWT_TOKEN_LOCATION"]       = ["headers"]  # bearer
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = False
JWTManager(app)


# init db
app.config["SQLALCHEMY_DATABASE_URI"] = f"postgresql+psycopg://{os.environ["POSTGRES_USER"]}:{os.environ["POSTGRES_PASSWORD"]}@db:5432/{os.environ["POSTGRES_DB"]}"
db.init_app(app)
with app.app_context():
    db.create_all()


# register modules
module_blueprints = [
    oauth_module.blueprint,
    user_module.blueprint
]
for mbp in module_blueprints:
    app.register_blueprint(mbp)


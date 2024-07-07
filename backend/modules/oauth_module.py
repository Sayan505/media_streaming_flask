import os

from flask import current_app, url_for, redirect

from authlib.integrations.flask_client import OAuth
from flask_jwt_extended                import create_access_token

from config.orm        import db
from models.user_model import User 

from config.logger     import log


from flask import Blueprint
blueprint = Blueprint("oauth_module", __name__)


oauth = OAuth(current_app)
oauth.register(
    name="google",
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    client_id=os.environ["GOOGLE_CLIENT_ID"],
    client_secret=os.environ["GOOGLE_CLIENT_SECRET"],
    client_kwargs={ "scope": "openid email profile" }
)


# oauth commence route
@blueprint.route("/api/login", methods=["GET"])
def login():
    redirect_uri = url_for("oauth_module.auth", _external=True)
    return oauth.google.authorize_redirect(redirect_uri)


# oauth callback route
@blueprint.route("/api/auth", methods=["GET"])
def auth():
    token       = oauth.google.authorize_access_token()
    userinfo    = token["userinfo"]
    oauth_sub   = str(userinfo["sub"])
    oauth_name  = str(userinfo["name"])
    oauth_email = str(userinfo["email"])


    user_role   = db.session.execute(db.select(User.user_role).filter_by(oauth_sub=oauth_sub)).scalar_one_or_none()  # get role if user exists or None
    if not user_role:
        user             = User()      # register new user
        user.oauth_sub   = oauth_sub
        user.displayname = oauth_name
        db.session.add(user)
        db.session.commit()

        user_role        = user.user_role

        log.info(f"new registration: {oauth_email} <{oauth_sub}>")

    # FIXME: TOKEN HAS EXPIRED
    jwt = create_access_token(identity=oauth_sub, fresh=True)
    log.info(f"auth - {oauth_email} <{oauth_sub}> as {str(user_role)}")

    return redirect(f"{os.environ["FRONTEND_URL"]}/login/callback/?jwt={jwt}&role={str(user_role)}")


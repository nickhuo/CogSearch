from __future__ import annotations

import os
from flask import Flask


def create_app() -> Flask:
    """Application factory. Config is loaded from env and instance."""
    # Since templates, static, and instance are now in the src package
    template_folder = os.path.join(os.path.dirname(__file__), 'templates')
    static_folder = os.path.join(os.path.dirname(__file__), 'static')
    instance_folder = os.path.join(os.path.dirname(__file__), 'instance')

    app = Flask(__name__,
                template_folder=template_folder,
                static_folder=static_folder,
                instance_path=instance_folder)

    # Defaults (kept to avoid breaking current local dev)
    app.config.update(
        SECRET_KEY=os.environ.get("SECRET_KEY", "dev-secret-key"),
        MYSQL_HOST=os.environ.get("MYSQL_HOST", "localhost"),
        MYSQL_USER=os.environ.get("MYSQL_USER", "root"),
        # 使用非空默认值避免出现 "using password: NO"；若不匹配，请在环境变量或 instance/config.py 中覆盖
        MYSQL_PASSWORD=os.environ.get("MYSQL_PASSWORD", "root"),
        MYSQL_DB=os.environ.get("MYSQL_DB", "cogsearch_textsearch3"),
    )

    # Load instance config if present
    app.config.from_pyfile("config.py", silent=True)

    # Register blueprints
    from .routes.core import core_bp
    from .routes.practice import practice_bp

    app.register_blueprint(core_bp)
    app.register_blueprint(practice_bp)

    return app


# For `flask --app src run`
app = create_app()

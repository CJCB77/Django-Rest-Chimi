server {
    listen ${LISTEN_PORT};  # ← Replaced with an env variable (e.g., 80 or 443)

    # Serve static files (CSS, JS, images) directly from /vol/static
    location /static {
        alias /vol/static;
    }

    # Proxy all other requests to Django (via uWSGI)
    location / {
        uwsgi_pass           ${APP_HOST}:${APP_PORT};  # ← e.g., `app:9000`
        include              /etc/nginx/uwsgi_params;  # Standard uWSGI settings
        client_max_body_size 10M;  # Allow file uploads up to 10MB
    }
}
FROM apache/airflow:3.3.1

USER root

RUN rm -f /etc/apt/sources.list.d/microsoft-prod.list \
    /etc/apt/sources.list.d/mssql-release.list \
    && rm -f /usr/share/keyrings/microsoft-prod.gpg \
    && apt-get update \
    && apt-get install -y --no-install-recommends \
        curl \
        ca-certificates \
        gnupg \
        unixodbc \
        unixodbc-dev \
        libgssapi-krb5-2 \
    && curl -fsSL https://packages.microsoft.com/keys/microsoft.asc \
        | gpg --dearmor \
        -o /usr/share/keyrings/microsoft-prod.gpg \
    && echo "deb [arch=amd64 signed-by=/usr/share/keyrings/microsoft-prod.gpg] https://packages.microsoft.com/debian/12/prod bookworm main" \
        > /etc/apt/sources.list.d/microsoft-prod.list \
    && apt-get update \
    && ACCEPT_EULA=Y apt-get install -y --no-install-recommends \
        msodbcsql18 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

USER airflow

RUN pip install --no-cache-dir \
    "pyodbc==5.3.0"

COPY --chown=airflow:root src /opt/northstar/src

ENV PYTHONPATH="/opt/northstar/src"
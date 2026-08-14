FROM mcr.microsoft.com/mssql/server:2019-latest
# Based on https://github.com/usil/mssql-docker-enhanced/blob/main/Dockerfile

USER root

# Install SQL Server command-line tools
ENV ACCEPT_EULA=Y
RUN apt-get update && apt-get install -y mssql-tools unixodbc-dev

RUN mkdir -p /docker-entrypoint-initdb.d
RUN mkdir -p /var/log/docker/
RUN chown mssql /var/log/docker/

USER mssql
RUN echo "" > /var/log/docker/sqlserver_db_init.log
COPY entrypoint.sh /entrypoint.sh 
COPY db_init.sh /db_init.sh 

ENV PATH "$PATH:/opt/mssql-tools/bin"

ENTRYPOINT ["./entrypoint.sh"]

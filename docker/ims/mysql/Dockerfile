FROM mysql:8.0.40
COPY init.sh /docker-entrypoint-initdb.d/10-ims.sh
COPY entrypoint.sh /ims-entrypoint.sh
ENTRYPOINT ["bash", "/ims-entrypoint.sh"]
CMD ["mysqld"]

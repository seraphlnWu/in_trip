/etc/mysql/my.cnf:
    file.managed:
        - source: salt://mysql/my.cnf
        - user: root
        - group: root
        - mode: 644
        - makedirs: True

/data/mysql:
    file.directory:
        - user: mysql
        - group: mysql
        - mode: 700

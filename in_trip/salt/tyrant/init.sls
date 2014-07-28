{% if grains['host'] == "bj-social-42" %}
/data/ttserver:
    file.directory:
        - user: root
        - group: root
        - mode: 755
        - makedirs: True

/data/ttserver/master:
    file.directory:
        - user: root
        - group: root
        - mode: 755 
        - makedirs: True

/data/ttserver/slave:
    file.directory:
        - user: root
        - group: root
        - mode: 755
        - makedirs: True

{% else %}
/data2/ttserver:
    file.directory:
        - user: root
        - group: root
        - mode: 755
        - makedirs: True

/data2/ttserver/master:
    file.directory:
        - user: root
        - group: root
        - mode: 755 
        - makedirs: True

/data2/ttserver/slave:
    file.directory:
        - user: root
        - group: root
        - mode: 755
        - makedirs: True
{% endif %}


/etc/init.d/ttservctl_master:
    file.managed:
        - user: root
        - group: root
        - template: jinja
        - source: salt://buzzMaster/scripts/init.d/ttservctl_master
        - mode: 755

/etc/init.d/ttservctl_slave:
    file.managed:
        - user: root
        - group: root
        - template: jinja
        - source: salt://buzzMaster/scripts/init.d/ttservctl_slave
        - mode: 755


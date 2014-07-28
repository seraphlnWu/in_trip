/home/operation/buzzMaster:
    file.recurse:
        - source: salt://buzzMaster
        - user: operation
        - group: operation
        #- clean: True
        #- exclude_pat: 'E@(^\.git/*)|(^buzz/configurations/\.git/*)'
        - exclude_pat: .git/*

/home/operation/buzzMaster/conf/config.ini:
    file.managed:
        - source: salt://buzz/config.ini
        - template: jinja
        - user: operation
        - group: operation
        - require:
            - file: /home/operation/buzzMaster

/home/operation/buzzMaster/.tld_set:
    file.managed:
        - source: salt://buzz/tld_set
        - user: operation
        - group: operation
        - mode: 644

# logrotate
/etc/logrotate.d/buzz:
    file.managed:
        - source: salt://buzzMaster/scripts/logrotate/buzz
        - user: root
        - group: root

# spdier
{% if 'spider' in grains['host'] %}
/etc/resolv.conf:
    file.managed:
        - source: salt://buzz/resolv.conf
        - template: jinja
        - user: root
        - group: root
        - mode: 644

{% endif %}

{% if grains['os'] == 'CentOS' %}
/usr/local/lib/python2.7/site-packages/jieba/dict.txt:
{% else %}
/usr/local/lib/python2.7/dist-packages/jieba/dict.txt:
{% endif %}
    file.managed:
        - source: salt://buzz/dict.txt
        - user: operation
        - group: operation
        - mode: 644


# service
{% for service in ['engine', 'timer', 'spider', 'extractor'] %}
/usr/local/bin/{{ service }}:
    file.managed:
        - source: salt://buzzMaster/bin/{{ service }}
        - user: root
        - group: root
        - mode: 755

/etc/init.d/{{ service }}:
    file.managed:
        - source: salt://buzzMaster/scripts/init.d/{{ service }}
        - user: root
        - group: root
        - mode: 755
        - require:
            - file: /home/operation/buzzMaster
            - file: /usr/local/bin/{{ service }}
{% endfor %}

{% if grains['host'] == "bj-buzz-db02" %}
/etc/init.d/buzzadmin:
    file.managed:
        - source: salt://buzzMaster/scripts/init.d/buzzadmin
        - user: root
        - group: root
        - mode: 755

{% endif %}

# backup script
/home/operation/buzzMaster/scripts/backup.sh:
    file.managed:
        - mode: 777

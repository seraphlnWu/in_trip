/etc/scribe.conf:  # scribe config file
    file.managed:
        - source: salt://scribe/client.conf
        # {% if grains['host'] == 'bj-social-23' %}
        # {% else %}
        # {% endif %}
        # - source: salt://scribe/central.conf

/usr/local/sbin/scribe_ctrl:        # scribe control script
    file.managed:
        - source: salt://scribe/scribe_ctrl
        - user: root
        - group: root
        - mode: 755

/usr/local/bin/scribe_cat:          # scribe service test script
    file.managed:
        - source: salt://scribe/scribe_cat
        - user: root
        - group: root
        - mode: 755

scribe-init:
    file.managed:
        {% if grains['os'] == 'CentOS' %}
        - name: /etc/rc.d/init.d/scribe
        {% else %}
        - name: /etc/init.d/scribe
        {% endif %}
        - source: salt://buzzMaster/scripts/init.d/scribe
        - user: root
        - group: root
        - mode: 755    # -rwxr-xr-x 
        - require:
            - file: /usr/local/sbin/scribe_ctrl

scribe:
    service.running:
        #- user: root
        #- group: root  # no effect
        - enable: True
        - sig: scribed
        - require:
            - file: /etc/scribe.conf
            - file: scribe-init
        - watch:
            - file: /etc/scribe.conf

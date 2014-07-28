salt-minion:
    file.managed:
        {% if grains['os'] == 'CentOS' %}
        - name: /etc/rc.d/init.d/salt-minion
        - source: salt://buzzMaster/scripts/init.d/salt-minion-rpm
        {% else %}
        - name: /etc/init.d/salt-minion
        - source: salt://buzzMaster/scripts/init.d/salt-minion-deb
        {% endif %}
        - user: root
        - group: root
        - mode: 755    # -rwxr-xr-x 

{% if grains['host'] == "bj-social-23" %}
salt-master:
    file.managed:
        {% if grains['os'] == 'CentOS' %}
        - name: /etc/rc.d/init.d/salt-master
        - source: salt://buzzMaster/scripts/init.d/salt-master-rpm
        {% else %}
        - name: /etc/init.d/salt-master
        - source: salt://buzzMaster/scripts/init.d/salt-master-deb
        {% endif %}
        - user: root
        - group: root
        - mode: 755    # -rwxr-xr-x 
{% endif %}

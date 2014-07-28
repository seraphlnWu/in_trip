#coding=utf-8

from admin.controllers import home, site, feeds, channel, blacklist, special, project, topic, download, auth


def setup_routing(app):
    #app.route('/<action>/<item>')
    app.route('/', method='GET', callback=home.index)
    #app.route('/rule/add', method='POST', callback=rule.add)
    app.route('/static/<path:path>', method="GET", callback=home.static)

    #site
    app.route('/site/index/<page:int>', method="GET", callback=site.index)
    app.route('/site/add', method="POST", callback=site.add)
    app.route('/site/update', method="POST", callback=site.update)
    app.route('/site/j_delete', method="POST", callback=site.j_delete)
    app.route('/site/j_op', method="GET", callback=site.j_op)
    app.route('/site/j_get_site/<_id:int>', method="GET", callback=site.j_get_site)

    #xpath
    # app.route('/xpath/index/<page:int>', method="GET", callback=xpath.index)
    # app.route('/xpath/add', method="POST", callback=xpath.add)
    # app.route('/xpath/update', method="POST", callback=xpath.update)
    # app.route('/xpath/update/<id:int>', method="GET", callback=xpath.update_form)
    # app.route('/xpath/j_delete', method="GET", callback=xpath.j_delete)
    # app.route('/xpath/j_get_xpaths', method="GET", callback=xpath.j_get_xpaths)
    # app.route('/xpath/validate', method="POST", callback=xpath.validate)
    # app.route('/xpath/validate2', method="POST", callback=xpath.validate2)
    # app.route('/xpath/check_for_exist',method="GET",callback=xpath.check_for_exist)

   #url_regex
    # app.route('/url_regex/index', method="GET", callback=url_regex.index)
    # app.route('/url_regex/add', method="POST", callback=url_regex.add)
    # app.route('/url_regex/update', method="POST", callback=url_regex.update)
    # app.route('/url_regex/check', method='GET', callback=url_regex.check)
    # app.route('/url_regex/check_url_regex', method="GET", callback=url_regex.check_url_regex)
    # app.route('/url_regex/j_associate_xpath', method="POST", callback=url_regex.j_associate_xpath)
    # app.route('/url_regex/j_dissociate', method="POST", callback=url_regex.j_dissociate)
    # app.route('/url_regex/j_delete/<_id:int>', method="GET", callback=url_regex.j_delete)
    # app.route('/url_regex/j_get_url_regex_by_level', method="GET", callback=url_regex.j_get_url_regex_by_level)

    #feed
    app.route('/feeds/index/<page:int>', method="GET", callback=feeds.index)
    app.route('/feeds/j_get_feed', method="GET", callback=feeds.j_get_feed)
    app.route('/feeds/add', method="POST", callback=feeds.add)
    app.route('/feeds/update', method="POST", callback=feeds.update)
    app.route('/feeds/j_op', method="GET", callback=feeds.j_op)
    app.route('/feeds/j_test_feed', method="POST", callback=feeds.j_test_feed)

    #channel
    app.route('/channel/index/<page:int>', method="GET", callback=channel.index)
    app.route('/channel/add', method="POST", callback=channel.add)
    app.route('/channel/update', method="POST", callback=channel.update)
    app.route('/channel/j_get_channels', method="GET", callback=channel.j_get_channels)
    app.route('/channel/j_get_channel', method="GET", callback=channel.j_get_channel)
    app.route('/channel/j_delete', method="GET", callback=channel.j_delete)

    #blacklist
    app.route('/blacklist/index/<page:int>', method="GET", callback=blacklist.index)
    app.route('/blacklist/add', method="POST", callback=blacklist.add)
    app.route('/blacklist/update', method="POST", callback=blacklist.update)
    app.route('/blacklist/j_get_blacklist', method="GET", callback=blacklist.j_get_blacklist)
    app.route('/blacklist/j_get_black', method="GET", callback=blacklist.j_get_black)
    app.route('/blacklist/j_delete', method="GET", callback=blacklist.j_delete)

    #special
    app.route('/special/index/<page:int>', method="GET", callback=special.index)
    app.route('/special/add', method="POST", callback=special.add)
    app.route('/special/update', method="POST", callback=special.update)
    app.route('/special/j_get_speciallist', method="GET", callback=special.j_get_speciallist)
    app.route('/special/j_get_special', method="GET", callback=special.j_get_special)
    app.route('/special/j_delete', method="GET", callback=special.j_delete)

    #project
    app.route('/project/index/<page:int>', method="GET", callback=project.index)
    app.route('/project/add', method="POST", callback=project.add)
    app.route('/project/delete/<_id:int>', method="GET", callback=project.delete)
    app.route('/project/dump/<_id:int>', method="POST", callback=project.dump)
    app.route('/project/get_project/<_id:int>', method="GET", callback=project.get_project)
    app.route('/project/update/<_id:int>', method="POST", callback=project.update)

    #topic
    app.route('/topic/index/<page:int>', method="GET", callback=topic.index)
    app.route('/topic/dump/<_id:int>', method="POST", callback=topic.dump)
    app.route('/topic/add', method="POST", callback=topic.add)
    app.route('/topic/get_topic/<_id:int>', method="GET", callback=topic.get_topic)
    app.route('/topic/update/<_id:int>', method="POST", callback=topic.update)
    app.route('/topic/delete/<_id:int>', method="GET", callback=topic.delete)

    #download
    app.route('/download/index/<page:int>', method="GET", callback=download.index)
    app.route('/download/file/<filename:re:.*\.zip>', method="GET", callback=download.file)

    #auth
    app.route('/auth/index/<page:int>', method="GET", callback=auth.index)
    app.route('/auth/login', method="POST", callback=auth.login)
    app.route('/auth/logout', method="POST", callback=auth.logout)
    app.route('/auth/add', method="POST", callback=auth.add)
    app.route('/auth/update', method="POST", callback=auth.update)
    app.route('/auth/j_delete', method="POST", callback=auth.j_delete)
    app.route('/auth/j_get_user/<_id:int>', method="GET", callback=auth.j_get_user)

    return app

#coding=utf-8


def time_extract(match_result):
    month_name = [
        ' ',
        'Jan', 'Feb', 'Mar',
        'Apr', 'May', 'Jun',
        'Jul', 'Aug', 'Sep',
        'Oct', 'Nov', 'Dec',
        u'一月', u'二月', u'三月',
        u'四月', u'五月', u'六月',
        u'七月', u'八月', u'九月',
        u'十月', u'十一月', u'十二月',
        ]
    r = match_result.groupdict()
    for key, value in r.iteritems():
        if value.isdigit():
            r[key] = int(value)
        elif value.strip() in month_name:
            r[key] = value
        else:
            return (key, value), False

    month = r['month'].strip() if isinstance(r['month'], basestring) else r['month']
    if month in month_name:
        m_index = month_name.index(month)
        r['month'] = m_index % 12 if m_index % 12 else 12
    return r, True

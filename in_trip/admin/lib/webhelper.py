#coding=utf-8

def pagination(current_page_no):
    pages = []
    if current_page_no < 4:
        pages += zip(range(1, 7), range(1, 7))
        pages.append((-1, '...'))
    else:
        pages = [(-1, '...')]
        page_nos = range(current_page_no-3, current_page_no+4)
        pages += zip(page_nos, page_nos)
        pages.append((-1, '...'))
    pages.insert(0, (current_page_no - 1, '&laquo;'))
    pages.append((current_page_no + 1, '&raquo;'))
    return pages

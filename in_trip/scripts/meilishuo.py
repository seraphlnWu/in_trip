import urllib
import re
import json

def getcomments_meilishuo(url):
    tid = re.match("http://www\.meilishuo\.com/share/(\d+)\?d_r=.*",url).groups()[0]
    comments = []
    page_index = 0
    while True:
        url_request = "http://www.meilishuo.com/aj/getComment/?tid=%s&page=%d"%(tid,page_index)
        comment_list = json.loads(urllib.urlopen(url_request).read())
        if comment_list:
            comments.extend(comment_list)
            page_index = page_index + 1
            print page_index
        else:
            break
    return tid,comments

if __name__ == "__main__":
    print getcomments_meilishuo("http://www.meilishuo.com/share/1186078515?d_r=0.1.1.2")

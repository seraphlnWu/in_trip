#coding=utf-8

from in_trip.lib.consts import PAGE_TYPE, INDUSTRY

from admin.model import get_feeds, parse_feed, Project, Topic

from scripts.insert_feed import insert_feed_url

def main(project_id, page_range=(2, )):
    keywords = {}
    project = Project.get(project_id)
    keywords[project.industry_id] = []
    for topic in Topic.find(project_id=project_id):
        keywords[project.industry_id].append(topic.main_key)
        keywords[project.industry_id].extend(topic.synonyms)

    for key in keywords.values():
        print key

    """
    industry_ids = keywords.keys()
    if INDUSTRY['*'] not in industry_ids:
        industry_ids.append(INDUSTRY['*'])
    """
    feeds = get_feeds()

    for feed in feeds:
        if feed.feed_type == PAGE_TYPE.NORMAL_FEED_PAGE:
            continue
        urls = parse_feed(feed, keywords, page_range)
        print feed._id, len(urls)
        insert_feed_url(urls, page_type=feed.feed_type)

if __name__ == '__main__':
    main(87, (2, 100))

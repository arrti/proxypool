from .rule_base import CrawlerRuleBase


class ProxyMimi(CrawlerRuleBase):
    """Rule for www.mimiip.com"""

    start_url = 'http://www.mimiip.com/gngao/'
    page_count = 3
    urls_format = '{0}{1}'

    use_phantomjs = False

    ip_xpath   = '//td[1]'  # 序号从1开始
    port_xpath = '//td[2]'

    def __init__(self):
        pass

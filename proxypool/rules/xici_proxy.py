from .rule_base import CrawlerRuleBase


class ProxyXici(CrawlerRuleBase):
    """Rule for www.xicidaili.com"""

    start_url =  'http://www.xicidaili.com/nn/'
    page_count = 10
    # urls_format = '{0}{1}'
    next_page_xpath = '//div[@class="pagination"]/a[@class="next_page"]/@href'
    next_page_host = 'http://www.xicidaili.com'

    use_phantomjs = False

    ip_xpath   = '//td[2]'  # 序号从1开始
    port_xpath = '//td[3]'

    def __init__(self):
        pass

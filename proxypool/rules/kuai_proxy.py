from .rule_base import CrawlerRuleBase

class ProxyKuai(CrawlerRuleBase):
    start_url = 'http://www.kuaidaili.com/free/inha/'
    page_count = 10
    urls_format = '{0}{1}'

    use_phantomjs = True
    phantomjs_load_flag = '<td data-title="IP">'

    ip_xpath   = '//td[1]' # index start from 1 not 0
    port_xpath = '//td[2]'

    def __init__(self):
        pass

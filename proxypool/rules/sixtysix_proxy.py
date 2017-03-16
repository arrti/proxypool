from .rule_base import CrawlerRuleBase

class ProxySixtysix(CrawlerRuleBase):
    start_url = 'http://www.66ip.cn/areaindex_1/1.html' # beijing proxy
    page_count = 10
    urls_format = 'http://www.66ip.cn/areaindex_1/{1}.html' # skip start_url


    use_phantomjs = False

    ip_xpath   = '//*[@id="footer"]/div/table/tr[position()>1]/td[1]'  # 序号从1开始, 不要带有tbody节点
    port_xpath = '//*[@id="footer"]/div/table/tr[position()>1]/td[2]'

    def __init__(self):
        pass

from .rule_base import CrawlerRuleBase


class Proxy360(CrawlerRuleBase):
    """Rule for www.proxy360.cn"""

    start_url = 'http://www.proxy360.cn/default.aspx/'
    page_count = 1

    use_phantomjs = False

    filters = ('高匿',)

    ip_xpath   = '//div[@id="ctl00_ContentPlaceHolder1_upProjectList"]/div/div[1]/span[1]'  # 序号从1开始
    port_xpath = '//div[@id="ctl00_ContentPlaceHolder1_upProjectList"]/div/div[1]/span[2]'

    filters_xpath = ('//div[@id="ctl00_ContentPlaceHolder1_upProjectList"]/div/div[1]/span[3]',) # 匿名


    def __init__(self):
        pass




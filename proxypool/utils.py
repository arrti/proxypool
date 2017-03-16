from proxypool.config import phantomjs_path, headers, delay, verbose
import aiohttp
import asyncio
from selenium import webdriver
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from async_timeout import timeout
from random import random, uniform
from bs4 import UnicodeDammit
from lxml import html
import logging
import logging.config
import yaml
from pathlib import Path


PROJECT_ROOT = Path(__file__).parent
# set logger for proxy crawler and alidator
logging.config.dictConfig(yaml.load(open(str(PROJECT_ROOT / 'logging.yaml'), 'r'))) # load config from YAML file
if verbose:
    logger = logging.getLogger('console_logger') # output to both stdout and file
else:
    logger = logging.getLogger('file_logger')


def decode_html(html_string):
    """Use bs4 to decode html file.

    Source: http://lxml.de/elementsoup.html#Using only the encoding detection
    """
    converted = UnicodeDammit(html_string)
    if not converted.unicode_markup:
        raise UnicodeDecodeError(
            "Failed to detect encoding, tried [%s]",
            ', '.join(converted.tried_encodings))
    return converted.unicode_markup

async def page_download(urls, pages, flag):
    """Download web page with aiohttp.

    Args:
        urls: url generator for next web page.
        pages: asyncio.Queue object, save downloaded web pages.
        flag: asyncio.Event object, stop flag.
    """
    url_generator = urls
    async with aiohttp.ClientSession() as session:
        for url in url_generator:
            if flag.is_set():
                break

            await asyncio.sleep(uniform(delay - 0.5, delay + 1))
            logger.debug('crawling proxy web page {0}'.format(url))
            try:
                async with session.get(url, headers=headers, timeout=10) as response:
                    page = await response.text()
                    parsed = html.fromstring(decode_html(page))
                    await pages.put(parsed)
                    url_generator.send(parsed)
            except StopIteration:
                break
            except asyncio.TimeoutError:
                logger.error('crawling {0} timeout'.format(url))
                continue # TODO: use a proxy
            except Exception as e:
                logger.error(e)

async def page_download_phantomjs(urls, pages, element, flag):
    """Download web page with PhantomJS.

    Args:
        urls: url generator for next web page.
        pages: asyncio.Queue object, save downloaded web pages.
        element: element for PhantomJS to check if page was loaded.
        flag: asyncio.Event object, stop flag.
    """
    dcap = dict(DesiredCapabilities.PHANTOMJS)
    dcap["phantomjs.page.settings.userAgent"] = headers
    browser = webdriver.PhantomJS(executable_path=phantomjs_path, desired_capabilities=dcap)
    url_generator = urls
    for url in url_generator:
        if flag.is_set():
            break

        await asyncio.sleep(uniform(delay - 0.5, delay + 1))
        logger.debug('phantomjs was crawling proxy web page {0}'.format(url))
        try:
            with timeout(10):
                browser.get(url)
                while browser.page_source.find(element) == -1:
                    await asyncio.sleep(random())

            parsed = html.fromstring(decode_html(browser.page_source))
            await pages.put(parsed)
            url_generator.send(parsed)
        except StopIteration:
            break
        except asyncio.TimeoutError:
            logger.error('phantomjs was crawling {0} timeout'.format(url))
            continue  # TODO: use a proxy
        except Exception as e:
            logger.error(e)

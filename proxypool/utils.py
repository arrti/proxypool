import asyncio
from random import random, uniform
import logging
import logging.config
from pathlib import Path
from collections import namedtuple
from functools import wraps, partial

import yaml
from bs4 import UnicodeDammit
from lxml import html
import aiohttp
from selenium import webdriver
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from async_timeout import timeout

from proxypool.config import PHANTOMJS_PATH, HEADERS, DELAY, VERBOSE


PROJECT_ROOT = Path(__file__).parent

def _log_async(func):
    """Send func to be executed by ThreadPoolExecutor of event loop."""

    @wraps(func)
    def wrapper(*args, **kwargs):
        loop = asyncio.get_event_loop()
        return loop.run_in_executor(None, partial(func, *args, **kwargs))

    return wrapper


class _LoggerAsync:
    """Logger's async proxy.

    Logging were executed in a thread pool executor to avoid blocking the event loop.
    """

    def __init__(self, *, is_server=False):
        logging.config.dictConfig(
            yaml.load(open(str(PROJECT_ROOT / 'logging.yaml'), 'r')))  # load config from YAML file

        if is_server:
            self._logger = logging.getLogger('server_logger')
        elif VERBOSE:
            self._logger = logging.getLogger('console_logger')  # output to both stdout and file
        else:
            self._logger = logging.getLogger('file_logger')

    def __getattr__(self, name):
        if hasattr(self._logger, name):
            return getattr(self._logger, name)
        else:
            msg = 'logger object has no attribute {!r}'
            raise AttributeError(msg.format(name))

    @_log_async
    def debug(self, msg, *args, **kwargs):
        self._logger.debug(msg, *args, exc_info=False, stack_info=False, **kwargs)

    @_log_async
    def info(self, msg, *args, **kwargs):
        self._logger.info(msg, *args, exc_info=False, stack_info=False, **kwargs)

    @_log_async
    def warning(self, msg, *args, **kwargs):
        self._logger.warning(msg, *args, exc_info=False, stack_info=False, **kwargs)

    @_log_async
    def error(self, msg, *args, **kwargs):
        self._logger.error(msg, *args, exc_info=False, stack_info=False, **kwargs)

    @_log_async
    def exception(self, msg, *args, exc_info=True, **kwargs):
        self._logger.exception(msg, *args, exc_info=False, stack_info=False, **kwargs)

    @_log_async
    def critical(self, msg, *args, **kwargs):
        self._logger.critical(msg, *args, exc_info=False, stack_info=False, **kwargs)

logger = _LoggerAsync()

Result = namedtuple('Result', 'content rule')

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

async def _fetch(url, session):
    await asyncio.sleep(uniform(DELAY - 0.5, DELAY + 1))
    logger.debug('crawling proxy web page {0}'.format(url.content))
    try:
        async with session.get(url.content, headers=HEADERS, timeout=10) as response:
            if response.status != 200:
                raise aiohttp.errors.ClientConnectionError(
                    'get {} return "{} {}"'.format(url.content, response.status, response.reason))
            page = await response.text()
            parsed = html.fromstring(decode_html(page))
            return parsed
    except asyncio.TimeoutError:
        pass

async def page_download(url_gen, pages, flag):
    """Download web page with aiohttp.

    Args:
        url_gen: url generator for next web page.
        pages: asyncio.Queue object, save downloaded web pages.
        flag: asyncio.Event object, stop flag.
    """
    
    async with aiohttp.ClientSession() as session:
        for url in url_gen:
            if flag.is_set():
                break

            parsed = None
            try:
                parsed = await _fetch(url, session)
                await pages.put(Result(parsed, url.rule))
            except Exception as e:
                logger.error(e)
            finally:
                try:
                    url_gen.send(parsed)
                except StopIteration:
                    break

async def page_download_phantomjs(url_gen, pages, element, flag):
    """Download web page with PhantomJS.

    Args:
        url_gen: url generator for next web page.
        pages: asyncio.Queue object, save downloaded web pages.
        element: element for PhantomJS to check if page was loaded.
        flag: asyncio.Event object, stop flag.
    """
    
    dcap = dict(DesiredCapabilities.PHANTOMJS)
    dcap["phantomjs.page.settings.userAgent"] = HEADERS
    browser = webdriver.PhantomJS(executable_path=PHANTOMJS_PATH, desired_capabilities=dcap)
    for url in url_gen:
        if flag.is_set():
            break

        await asyncio.sleep(uniform(DELAY - 0.5, DELAY + 1))
        logger.debug('phantomjs was crawling proxy web page {0}'.format(url.content))
        try:
            with timeout(10):
                browser.get(url.content)
                while browser.page_source.find(element) == -1:
                    await asyncio.sleep(random())

            parsed = html.fromstring(decode_html(browser.page_source))
            await pages.put(Result(parsed, url.rule))
            url_gen.send(parsed)
        except StopIteration:
            break
        except asyncio.TimeoutError:
            continue  # TODO: use a proxy
        except Exception as e:
            logger.error(e)

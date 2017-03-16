from proxypool.config import server_on
from proxypool.proxy_pool import proxy_pool_run
from proxypool.proxy_validator import proxy_validator_run
from proxypool.proxy_server import server_run
from multiprocessing import Process


def main():
    """Start proxy pool.
    """
    pool = Process(target=proxy_pool_run)
    pool.start()
    validator = Process(target=proxy_validator_run)
    validator.start()
    if server_on:
        server = Process(target=server_run)
        server.start()

if __name__ == '__main__':
    main()

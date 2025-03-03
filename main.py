import argparse
import os
import re
import signal
import time
from pathlib import Path
from xvfbwrapper import Xvfb

from loguru import logger
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.firefox.service import Service


def kill_with_force(pid: int or None):
    if pid is None:
        return

    try:
        os.kill(pid, signal.SIGTERM)
    except ProcessLookupError:
        return

    time.sleep(1)
    try:
        os.kill(pid, signal.SIGKILL)
    except ProcessLookupError:
        return


def get_qr(args):
    os.environ['WDM_LOCAL'] = '1'
    os.environ['GH_TOKEN'] = "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"
    # options = webdriver.ChromeOptions()
    # options.add_argument("--disable-infobars")
    # options.add_argument("--ignore-certificate-error")
    # options.add_argument("--test-type")
    # options.add_argument("--disable-extensions")
    # options.add_argument("--headless")
    # options.add_argument("--no-sandbox")
    # options.add_argument("--remote-debugging-port=0")
    # options.add_argument("--disable-gpu")
    # options.add_argument('--disable-dev-shm-usage')
    # options.add_experimental_option('debuggerAddress', 'localhost:9222')
    # driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), chrome_options=options)
    options = FirefoxOptions()
    # options.add_argument("--headless")
    driver_pid = None
    browser_pid = None
    # https://qr.nspk.ru/AD100004H78D7MV99L889P4FGTI8TE29?type=02&bank=100000000111&sum=20000&cur=RUB&crc=94EB
    try:
        driver = webdriver.Firefox(options=options, service=Service())
        driver_pid = driver.capabilities['moz:processID']
        browser_pid = driver.service.process.pid
        driver.get(args.i)
        driver.maximize_window()
        time.sleep(3)
        # svg_wrapper = driver.find_element_by_class_name('qr__wrap')
        svg = driver.find_element(by=By.TAG_NAME, value='canvas')

        svg.screenshot(args.o)
        logger.success(f'file saved at path: {args.o}')
    except NoSuchElementException as err:
        logger.error(err.msg)
    finally:
        driver.close()
        driver.quit()
        kill_with_force(browser_pid)
        kill_with_force(driver_pid)


if __name__ == "__main__":
    logger.add('logs/logs.log', level="DEBUG",
               format="{time:YYYY-MM-DD at HH:mm:ss} | {level}     | {message}     | {module} {file}:{line}")
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', help='input url', required=True, type=str)
    parser.add_argument('-o', help='output file name', required=True, type=str)
    parser.set_defaults(func=get_qr)
    args = parser.parse_args()

    if not vars(args):
        parser.print_usage()
    else:
        regex = re.compile(
            r'^(?:http|ftp)s?://'  # http:// or https://
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'  # domain...
            r'localhost|'  # localhost...
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
            r'(?::\d+)?'  # optional port
            r'(?:/?|[/?]\S+)$', re.IGNORECASE)

        if re.match(regex, args.i) is not None:
            logger.info('Start parsing url: ' + args.i)
        else:
            logger.error('Invalid url given: ' + args.i)
            exit(0)
        path = Path(args.o)
        if path.is_file():
            logger.error(f'file already exist {args.o}')
            exit(0)

        vdisplay = Xvfb()
        vdisplay.start()
        try:
            args.func(args)
        finally:
            vdisplay.stop()
            # vdisplay.sendstop()


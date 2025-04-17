#!/usr/bin/env python3
# generar_playlist.py

import time
import re
from seleniumwire import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import requests

MAIN_URL    = "https://la12hd.com/"  # Cambia a "https://streamtp4.com/" si deseas cambiar el sitio
OUTPUT_FILE = "playlist.m3u"
WAIT_SEC    = 15


def crea_driver():
    chrome_options = Options()
    chrome_options.binary_location = "/usr/bin/chromium-browser"
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")

    return webdriver.Chrome(options=chrome_options)


def extrae_canales(driver):
    if "la12hd.com" in MAIN_URL:
        return extrae_canales_la12hd()
    else:
        driver.get(MAIN_URL)
        WebDriverWait(driver, WAIT_SEC).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, "#channel-list li"))
        )
        out = []
        for li in driver.find_elements(By.CSS_SELECTOR, "#channel-list li"):
            try:
                title = li.find_element(By.TAG_NAME, "h2").text.strip()
                href  = li.find_element(By.CSS_SELECTOR, ".channel-buttons a").get_attribute("href")
                out.append((title, href))
            except:
                continue
        return out


def extrae_canales_la12hd():
    canales = []
    headers = {
        "User-Agent": "Mozilla/5.0"
    }
    res = requests.get(MAIN_URL, headers=headers)
    soup = BeautifulSoup(res.text, "html.parser")
    items = soup.select(".cardsection [data-canal]")
    for item in items:
        canal = item.get("data-canal", "Canal")
        a_tag = item.select_one("a[href*='canal.php']")
        if a_tag:
            link = a_tag.get("href")
            if link.startswith("/"):
                link = MAIN_URL.rstrip("/") + link
            canales.append((canal, link))
    return canales


def captura_m3u8(driver, url):
    if "la12hd.com" in url:
        return captura_m3u8_la12hd(url)

    m3u8_urls = []

    def interceptor(request):
        if ".m3u8" in request.url and request.url not in m3u8_urls:
            m3u8_urls.append(request.url)

    driver.request_interceptor = interceptor
    driver.get(url)
    try:
        WebDriverWait(driver, WAIT_SEC).until(
            EC.presence_of_element_located((By.TAG_NAME, "video"))
        )
        time.sleep(3)
    except:
        pass

    driver.request_interceptor = None
    return m3u8_urls[0] if m3u8_urls else None


def captura_m3u8_la12hd(url):
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Referer": "https://la12hd.com"
    }
    res = requests.get(url, headers=headers)
    soup = BeautifulSoup(res.text, "html.parser")
    scripts = soup.find_all("script")
    for script in scripts:
        if script.string and "hls.loadSource" in script.string:
            match = re.search(r'hls\.loadSource\("(.*?)"\)', script.string)
            if match:
                return match.group(1)
    return None


def main():
    driver = crea_driver() if "la12hd.com" not in MAIN_URL else None
    canales = extrae_canales(driver) if driver else extrae_canales_la12hd()

    m3u_lines = ["#EXTM3U\n"]
    for title, page_url in canales:
        print(f"\u2192 Procesando «{title}» …")
        m3u8 = captura_m3u8(driver, page_url) if driver else captura_m3u8_la12hd(page_url)
        if m3u8:
            m3u_lines.append(f'#EXTINF:-1 group-title="La12HD",{title}\n{m3u8}\n')
            print(f"   ✔ {m3u8}")
        else:
            print(f"   ⚠️ No encontré .m3u8 en {page_url}")
        time.sleep(1)

    if driver:
        driver.quit()

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.writelines(m3u_lines)
    print(f"\n✔ Guardado {len(m3u_lines)-1} canales en {OUTPUT_FILE}")


if __name__ == "__main__":
    main()

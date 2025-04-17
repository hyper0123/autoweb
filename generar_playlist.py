#!/usr/bin/env python3
# generar_playlist.py

import time
from seleniumwire import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

MAIN_URL    = "https://streamtp4.com/"
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

def captura_m3u8(driver, url):
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
        time.sleep(3)  # pequeño margen adicional
    except:
        pass

    driver.request_interceptor = None  # desactiva después de cargar

    return m3u8_urls[0] if m3u8_urls else None

def main():
    driver = crea_driver()
    canales = extrae_canales(driver)

    m3u_lines = ["#EXTM3U\n"]
    for title, page_url in canales:
        print(f"→ Procesando «{title}» …")
        m3u8 = captura_m3u8(driver, page_url)
        if m3u8:
            m3u_lines.append(f'#EXTINF:-1 group-title="StreamTP4",{title}\n')
            print(f"   ✔ {m3u8}")
        else:
            print(f"   ⚠️ No encontré .m3u8 en {page_url}")
        time.sleep(1)

    driver.quit()
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.writelines(m3u_lines)
    print(f"\n✔ Guardado {len(m3u_lines)-1} canales en {OUTPUT_FILE}")

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
# generar_playlist.py

import time
from seleniumwire import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

MAIN_URL = "https://streamtp4.com/"  # Cambiar por la URL deseada
OUTPUT_FILE = "playlist.m3u"
WAIT_SEC = 25

def crea_driver():
    chrome_options = Options()
    chrome_options.binary_location = "/usr/bin/chromium-browser"
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")

    return webdriver.Chrome(options=chrome_options)

def detectar_estructura(driver):
    driver.get(MAIN_URL)
    
    try:
        # Detectar si es streamtp4.com
        WebDriverWait(driver, WAIT_SEC).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "#channel-list"))
        )
        return "streamtp4"
    except:
        try:
            # Detectar si es la12hd.com
            WebDriverWait(driver, WAIT_SEC).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".canal"))
            )
            return "la12hd"
        except:
            return "desconocida"

def extraer_streamtp4(driver):
    WebDriverWait(driver, WAIT_SEC).until(
        EC.presence_of_all_elements_located((By.CSS_SELECTOR, "#channel-list li"))
    )
    canales = []
    for li in driver.find_elements(By.CSS_SELECTOR, "#channel-list li"):
        try:
            title = li.find_element(By.TAG_NAME, "h2").text.strip()
            href = li.find_element(By.CSS_SELECTOR, ".channel-buttons a").get_attribute("href")
            canales.append((title, href, "StreamTP4"))
        except Exception as e:
            continue
    return canales

def extraer_la12hd(driver):
    WebDriverWait(driver, WAIT_SEC).until(
        EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".canal"))
    )
    canales = []
    for canal in driver.find_elements(By.CSS_SELECTOR, ".canal"):
        try:
            title = canal.find_element(By.CSS_SELECTOR, ".font-bold.text-md.text-white").text.strip()
            href = canal.find_element(By.CSS_SELECTOR, ".btn-red").get_attribute("href")
            canales.append((title, href, "LA12HD"))
        except Exception as e:
            continue
    return canales

def extraer_canales(driver):
    estructura = detectar_estructura(driver)
    
    if estructura == "streamtp4":
        return extraer_streamtp4(driver)
    elif estructura == "la12hd":
        return extraer_la12hd(driver)
    else:
        raise Exception("Estructura de página no reconocida")

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
        time.sleep(5)  # Tiempo adicional para cargar
    except:
        pass

    driver.request_interceptor = None

    return m3u8_urls[0] if m3u8_urls else None

def main():
    driver = crea_driver()
    
    try:
        canales = extraer_canales(driver)
        m3u_lines = ["#EXTM3U\n"]
        
        for title, page_url, group in canales:
            print(f"→ Procesando «{title}» ({group})...")
            try:
                m3u8 = captura_m3u8(driver, page_url)
                if m3u8:
                    m3u_lines.append(f'#EXTINF:-1 group-title="{group}",{title}\n{m3u8}\n')
                    print(f"   ✔ {m3u8}")
                else:
                    print(f"   ⚠️ No se encontró .m3u8 en {page_url}")
                time.sleep(2)
            except Exception as e:
                print(f"   ✖ Error: {str(e)}")
                continue
        
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            f.writelines(m3u_lines)
            
        print(f"\n✔ Guardados {len(m3u_lines)-1} canales en {OUTPUT_FILE}")
        
    finally:
        driver.quit()

if __name__ == "__main__":
    main()

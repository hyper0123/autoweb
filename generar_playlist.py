import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import time

main_url = "https://streamtp4.com/"
output_file = "playlist.m3u"

# Configurar Selenium en modo headless
chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")

m3u_content = "#EXTM3U\n"

# Extraer enlaces de la página principal
response = requests.get(main_url)
soup = BeautifulSoup(response.text, 'html.parser')

for li in soup.select('#channel-list li'):
    title = li.find('h2').text.strip()
    link_tag = li.find('a', href=True)
    
    if link_tag:
        channel_page_url = link_tag['href']
        print(f"Procesando: {title} - {channel_page_url}")
        
        try:
            # Iniciar navegador Chrome con Selenium
            driver = webdriver.Chrome(options=chrome_options)
            driver.get(channel_page_url)
            time.sleep(10)  # Esperar a que cargue la página
            
            # Buscar la URL del video
            video_element = driver.find_element("tag name", "video")
            m3u8_url = video_element.get_attribute('src')
            
            # Si no se encuentra, buscar en un iframe
            if not m3u8_url:
                iframe = driver.find_element("tag name", "iframe")
                driver.switch_to.frame(iframe)
                video_element = driver.find_element("tag name", "video")
                m3u8_url = video_element.get_attribute('src')
                driver.switch_to.default_content()
            
            # Añadir a la playlist
            if m3u8_url:
                m3u_content += f'#EXTINF:-1 group-title="WebExtraido", {title}\n{m3u8_url}\n'
            
            driver.quit()
        
        except Exception as e:
            print(f"Error en {title}: {str(e)}")
            continue

# Guardar playlist
with open(output_file, 'w', encoding='utf-8') as f:
    f.write(m3u_content)

from selenium import webdriver

html_file = "rostov_route_map.html"
screenshot_file = "route_map.png"

options = webdriver.ChromeOptions()
options.add_argument("--headless")
options.add_argument("--window-size=1920,1080")

driver = webdriver.Chrome(options=options)
driver.get(f"file:///home/mihask79/hakaton/rostov_route_map.html")
driver.save_screenshot(screenshot_file)
driver.quit()
print(f"Скриншот сохранён в {screenshot_file}")

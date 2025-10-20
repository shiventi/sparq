import json
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
import time

# JS code modified to return the JSON string
js_code = """
// Get the DataTable instance
const table = $('#classSchedule').DataTable();

// Get all row data
const data = table.rows().data().toArray();

// Get headers
const headers = [];
$('#classSchedule thead th').each(function() {
  headers.push($(this).text().trim());
});

// Clean up function for cell content
function cleanCell(cell) {
  if (typeof cell === 'string') {
    const tempDiv = document.createElement('div');
    tempDiv.innerHTML = cell;
    let text = tempDiv.textContent || tempDiv.innerText || '';
    text = text.replace(/\\n/g, ' ').trim();
    return text;
  }
  return cell;
}

// Map to array of objects
const courses = data.map(row => {
  const obj = {};
  headers.forEach((header, index) => {
    obj[header] = cleanCell(row[index]);
  });
  return obj;
});

// Return the JSON string
return JSON.stringify(courses, null, 2);
"""

# Set up Selenium in headless mode
options = webdriver.ChromeOptions()
options.add_argument('--headless')
options.add_argument('--disable-gpu')  # Sometimes needed for headless
options.add_argument('--window-size=1920,1080')  # Set a window size to avoid visibility issues
service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=options)

try:
    # Open the URL need to change url every semester
    driver.get("https://www.sjsu.edu/classes/schedules/fall-2025.php")
    
    # Wait for the page to load
    WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
    
    # Try to find and click "Load Class Schedule" button using JS click to avoid interception
    try:
        load_button = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//button[text()='Load Class Schedule']"))
        )
        # Scroll to the button
        driver.execute_script("arguments[0].scrollIntoView(true);", load_button)
        time.sleep(1)  # Small delay after scrolling
        # Use JS to click
        driver.execute_script("arguments[0].click();", load_button)
        print("Clicked Load Class Schedule button using JS")
        
        # Wait for the table to appear after clicking
        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.ID, "classSchedule"))
        )
    except (TimeoutException, NoSuchElementException):
        print("No Load Class Schedule button found or not clickable. Assuming table is already loaded.")
    
    # Wait for DataTable to be initialized
    WebDriverWait(driver, 30).until(
        lambda d: d.execute_script("return typeof $.fn.DataTable !== 'undefined' && $('#classSchedule').hasClass('dataTable');")
    )
    
    # Execute the JS code
    json_str = driver.execute_script(js_code)
    
    # Parse and save to file
    courses = json.loads(json_str)
    with open('json/schedule.json', 'w', encoding='utf-8') as f:
        json.dump(courses, f, indent=2)
    
    print("JSON file saved successfully.")
    print(f"Number of courses: {len(courses)}")

finally:
    driver.quit()
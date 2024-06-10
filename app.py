from flask import Flask, render_template, request
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import time

app = Flask(__name__)

def extract_and_print_jobs(soup):
    job_listings = soup.find_all('div', class_='flex w-full flex-col')

    if not job_listings:
        return "No job listings found."
    else:
        jobs = []
        for job in job_listings:
            job_title_element = job.find('h4', class_='bodyemphasis')
            if job_title_element:
                job_title = job_title_element.text.strip()
                company_name_element = job.find('h2', class_='text-xs font-semibold text-indigo-700')
                company_name = company_name_element.text.strip() if company_name_element else "N/A"

                job_details = {
                    "Job Title": job_title,
                    "Company Name": company_name,
                }
                jobs.append(job_details)

        return jobs

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        selected_sites = request.form.getlist('sites')
        search_query = request.form.get('search', '').lower().strip()

        job_results = {}

        if 'technopark' in selected_sites:
            job_results['Technopark'] = scrape_technopark(search_query)

        if 'infopark' in selected_sites:
            job_results['Infopark'] = scrape_infopark(search_query)

        return render_template('index.html', job_results=job_results)

    return render_template('index.html', job_results=None)

def scrape_technopark(search_query):
    driver = webdriver.Chrome()
    url = "https://technopark.org/job-search"
    driver.get(url)

    css_selector = "#app > div.relative.min-h-screen.w-full.pt-20 > div > div.grid.grid-cols-1.gap-5.px-4.pb-6.md\\:px-6.lg\\:grid-cols-2.lg\\:px-10.xl\\:px-10.\\32 xl\\:px-10"
    parent_div = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, css_selector))
    )

    html_content = parent_div.get_attribute("outerHTML")
    soup = BeautifulSoup(html_content, 'html.parser')

    job_details = extract_and_print_jobs(soup)

    # Scroll down repeatedly to load more content
    last_height = driver.execute_script("return Math.max( document.body.scrollHeight, document.body.offsetHeight, document.documentElement.clientHeight, document.documentElement.scrollHeight, document.documentElement.offsetHeight);")
    while True:
        # Scroll to the end of the page
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

        # Wait for a short time to allow the content to load
        time.sleep(5)

        # Extract the updated HTML content
        updated_html_content = driver.find_element(By.CSS_SELECTOR, css_selector).get_attribute("outerHTML")

        # If the HTML content did not change, break out of the loop
        if updated_html_content == html_content:
            break

        # Update the HTML content
        html_content = updated_html_content

        # Parse the updated content with BeautifulSoup
        soup = BeautifulSoup(html_content, 'html.parser')

        # Extract and print job details from the updated content
        job_details += extract_and_print_jobs(soup)

        # Check if the page has reached the end
        new_height = driver.execute_script("return Math.max( document.body.scrollHeight, document.body.offsetHeight, document.documentElement.clientHeight, document.documentElement.scrollHeight, document.documentElement.offsetHeight);")
        if new_height == last_height:
            break

        # Update last height
        last_height = new_height

    if search_query:
        job_details = [job for job in job_details if search_query in job['Job Title'].lower() or search_query in job['Company Name'].lower()]

    driver.quit()
    return job_details

def scrape_infopark(search_query):
    driver = webdriver.Chrome()
    url = "https://infopark.in/companies/job-search"
    driver.get(url)

    # Wait for the page to load and display the job listings
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CLASS_NAME, 'company-list'))
    )

    # Get the HTML content of the job listings
    html_content = driver.page_source
    soup = BeautifulSoup(html_content, 'html.parser')

    job_details = extract_and_print_infopark_jobs(soup)

    if search_query:
        job_details = [job for job in job_details if search_query in job['Job Title'].lower() or search_query in job['Company Name'].lower()]

    driver.quit()
    return job_details

def extract_and_print_infopark_jobs(soup):
    job_listings = soup.find_all('div', class_='row company-list joblist')

    if not job_listings:
        return "No job listings found."
    else:
        jobs = []
        for job in job_listings:
            job_title_element = job.find('div', class_='col-xs-6 col-md-4 mt5').a
            if job_title_element:
                job_title = job_title_element.text.strip()
                company_name_element = job.find('div', class_='col-xs-6 col-md-4 mt5 jobs-comp-name text-center').a
                company_name = company_name_element.text.strip() if company_name_element else "N/A"

                job_details = {
                    "Job Title": job_title,
                    "Company Name": company_name
                }
                jobs.append(job_details)

        return jobs

if __name__ == '__main__':
    app.run(debug=True)

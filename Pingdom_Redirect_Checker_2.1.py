import os
import csv
import requests
from time import sleep
from concurrent.futures import ThreadPoolExecutor, as_completed
import dns.resolver
from datetime import datetime, timezone  # Import datetime module

# Get the API key from environment variable
api_key = os.getenv('API_KEY')

# Function to retrieve Pingdom checks using requests
def retrieve_pingdom_checks(api_key):
    url = 'https://api.pingdom.com/api/3.1/checks'
    headers = {'Authorization': f'Bearer {api_key}'}
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        result = response.json()
        return result.get('checks', [])
    except requests.exceptions.RequestException as e:
        print(f"Failed to retrieve Pingdom checks: {e}")
        return []

# Function to perform Pingdom check and return results
def perform_pingdom_check(api_key, check_id, check_name, target_url):
    url = f'https://api.pingdom.com/api/3.1/single?type=http&host={target_url}'
    headers = {'Authorization': f'Bearer {api_key}'}
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        result = response.json()
        result_data = result.get('result', None)
        
        if result_data:
            status = result_data.get('status', 'N/A')
            probedesc = result_data.get('probedesc', 'N/A')
            statusdesc = result_data.get('statusdesc', 'N/A')
            statusdesclong = result_data.get('statusdesclong', 'N/A')
            return (target_url, [check_name, target_url, status, probedesc, statusdesc, statusdesclong, check_id])
        else:
            return (target_url, [check_name, target_url, "No result returned", "N/A", "N/A", "N/A", check_id])
    except requests.exceptions.RequestException as e:
        return (target_url, [check_name, target_url, f"Error: {e}", "N/A", "N/A", "N/A", check_id])

# Function to check redirects and DNS for a hostname
def check_redirects_and_dns(hostname):
    result = {'A Records': '', 'CNAME Records': '', 'NS Records': '', 'Redirect Path': ''}
    
    try:
        resolver = dns.resolver.Resolver()

        # DNS Lookup for A records
        try:
            answers_A = resolver.resolve(hostname, 'A', raise_on_no_answer=False)
            result['A Records'] = ', '.join([rdata.to_text() for rdata in answers_A]) if answers_A else 'No A Records Found'
        except Exception as e:
            result['A Records'] = f'DNS Lookup A Failed: {e}'

        # DNS Lookup for CNAME records
        try:
            answers_CNAME = resolver.resolve(hostname, 'CNAME', raise_on_no_answer=False)
            result['CNAME Records'] = ', '.join([rdata.to_text() for rdata in answers_CNAME]) if answers_CNAME else 'No CNAME Records Found'
        except Exception as e:
            result['CNAME Records'] = f'DNS Lookup CNAME Failed: {e}'

        # DNS Lookup for NS records
        try:
            answers_NS = resolver.resolve(hostname, 'NS', raise_on_no_answer=False)
            result['NS Records'] = ', '.join([rdata.to_text() for rdata in answers_NS]) if answers_NS else 'No NS Records Found'
        except Exception as e:
            result['NS Records'] = f'DNS Lookup NS Failed: {e}'

    except Exception as e:
        result['A Records'] = f'DNS Lookup Failed: {e}'
    
    # Checking redirects
    try:
        session = requests.Session()
        response = session.get(f"http://{hostname}", allow_redirects=False, timeout=20)
        
        # Capture the initial response
        if response.status_code == 200:
            result['Redirect Path'] = f"200 => {response.url} (No redirection)"
        elif response.is_redirect:
            redirects = []
            redirect_count = 0
            while response.is_redirect and redirect_count < 5:
                location = response.headers.get('Location')
                if not location.startswith('http://') and not location.startswith('https://'):
                    if location.startswith('/'):
                        location = f"http://{hostname}{location}"
                    else:
                        location = f"http://{hostname}/{location}"

                status_code = response.status_code
                redirects.append(f"{status_code} => {location}")
                response = session.get(location, allow_redirects=False, timeout=20)
                redirect_count += 1

            # Final response after redirects
            redirects.append(f"{response.status_code} => {response.url}")
            result['Redirect Path'] = ' | '.join(redirects)
        else:
            result['Redirect Path'] = f"No Redirect"

    except requests.exceptions.RequestException as e:
        result['Redirect Path'] = f'Request Failed: {e}'

    return (hostname, result)

# Function to process a batch of hostnames sequentially with delays
def process_hostname_batch(api_key, batch):
    results = []
    for check in batch:
        check_id = check.get('id')
        check_name = check.get('name')
        hostname = check.get('hostname')
        # Perform Pingdom check
        pingdom_result = perform_pingdom_check(api_key, check_id, check_name, hostname)
        # Perform DNS and redirect check
        dns_redirect_result = check_redirects_and_dns(hostname)
        # Combine the results
        combined_result = pingdom_result[1] + [
            hostname,
            dns_redirect_result[1]['A Records'],
            dns_redirect_result[1]['CNAME Records'],
            dns_redirect_result[1]['NS Records'],
            dns_redirect_result[1]['Redirect Path']
        ]
        results.append(combined_result)
        sleep(2)  # Delay between calls to avoid rate limiting
    return results

# Main function to combine the operations
def main(api_key, target_urls):
    # Step 1: Retrieve Pingdom checks
    checks = retrieve_pingdom_checks(api_key)
    if not checks:
        print("No Pingdom checks found.")
        return
    
    # Filter checks by target URLs
    filtered_checks = [check for check in checks if check.get('hostname') in target_urls]
    
    # Step 2: Divide the checks into equal batches for each thread
    max_workers = 16  # Fixed number of threads
    batch_size = len(filtered_checks) // max_workers + 1
    batches = [filtered_checks[i:i + batch_size] for i in range(0, len(filtered_checks), batch_size)]

    results = []

    # Step 3: Process the batches concurrently using ThreadPoolExecutor
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(process_hostname_batch, api_key, batch) for batch in batches]
        
        for future in as_completed(futures):
            batch_results = future.result()
            results.extend(batch_results)

    # Get the current UTC date and time to format the filename (timezone-aware UTC)
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d_%H-%M-%S")  # Use timezone-aware UTC time
    filename = f"Hostname_results_{timestamp}_UTC.csv"  # File name with UTC timestamp

    # Step 4: Write results to CSV
    with open(filename, mode='w', newline='') as csv_file:
        csv_writer = csv.writer(csv_file)
        # Write headers
        csv_writer.writerow(['Check Name', 'Target URL', 'Status', 'Probe Description', 'Status Description', 'Long Status Description', 'Pingdom Check ID', 'Hostname', 'A Records', 'CNAME Records', 'NS Records', 'Redirect Path'])
        for result in results:
            csv_writer.writerow(result)

    print(f"Results have been written to {filename}")

# Example usage
if __name__ == "__main__":
    api_key = os.getenv('API_KEY')
    target_urls_input = input("Enter the target URLs separated by commas: ")
    target_urls = [url.strip() for url in target_urls_input.split(",")]

    # Run the main function
    main(api_key, target_urls)

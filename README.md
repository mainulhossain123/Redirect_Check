# 🌐 Pingdom Monitor + DNS & Redirect Checker

This Python tool retrieves **Pingdom check data**, performs live **status testing**, and combines it with **DNS record analysis** and **redirect trace** per hostname. Results are exported in a timestamped CSV file for audit and analysis.

Ideal for **site reliability engineering (SRE)**, **DevOps**, and **Uptime Monitoring** teams.

---

## 📦 Features

- 🔐 Authenticated Pingdom API check fetcher
- 🌐 Real-time check status per URL
- 🧭 DNS lookups (A, CNAME, NS records)
- 🔁 HTTP redirect chain tracing (up to 5 steps)
- 🧵 Multi-threaded processing using `ThreadPoolExecutor`
- 📄 CSV output for further analysis or alerting

---

## 🧾 CSV Output Format

| Check Name | Target URL | Status | Probe Description | Status Description | Long Status Description | Check ID | Hostname | A Records | CNAME Records | NS Records | Redirect Path |
|------------|------------|--------|-------------------|--------------------|--------------------------|----------|----------|-----------|----------------|------------|----------------|

📁 Output file is timestamped using UTC: Hostname_results_2025-05-19_13-42-10_UTC.csv


---

## 🔐 Environment Variables

| Variable    | Description                            | Required | Default |
|-------------|----------------------------------------|----------|---------|
| `API_KEY`   | Your Pingdom API token (OAuth Bearer)  | ✅       | –       |

Set it via terminal or secrets manager:

```bash
export API_KEY="your_pingdom_api_token"
```

## ⚙️ How to Run
1. Install Dependencies
```bash
pip install requests dnspython
```
2. Clone and Run
```bash
git clone https://github.com/mainulhossain123/pingdom-dns-redirect-check.git
cd pingdom-dns-redirect-check
python pingdom_dns_redirect_checker.py
```
3. The script will prompt:
```csharp
Enter the target URLs separated by commas:
```
For example:
```bash
example.com, anotherdomain.com
```

It will then:

* Retrieve related Pingdom checks
* Validate live status
* Check DNS A, CNAME, NS records
* Detect redirect paths

## 🛠️ Example Output
```yaml
Check Name: Main Site Uptime
Target URL: example.com
Status: UP
Probe Description: US - NY
A Records: 192.0.2.1
Redirect Path: 301 => https://www.example.com | 200 => https://www.example.com/home
```

## 🔁 Parallel Execution
* ✅ Up to 16 threads (adjustable)
* ✅ Throttled by sleep(2) delay per call
* 🔄 Retries automatically via requests error handling

## 💡 Use Cases
* 🧪 Audit current Pingdom check behavior
* 🌐 Confirm DNS propagation and redirection setup
* 🛡️ Identify misconfigured records
* 📊 Generate uptime performance reports

## 🔐 API Access Requirements
Your Pingdom token must support:
* Read checks
* Access single check endpoint
*[Python API Docs](https://docs.pingdom.com/api/)*

## 🤝 Contributing
Pull requests are welcome. For major changes:
* Fork the repo
* Create a feature branch
* Test your changes
* ubmit a PR with context

## 📝 License
This project is licensed under the MIT License

## 📬 Contact
For issues, questions, or feature requests, please contact:
Author: Mainul Hossain
Email: hossainmainul83@gmail.com

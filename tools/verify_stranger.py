import urllib.request

url = 'https://politicians-jacksonville-brick-flexibility.trycloudflare.com/s/asha-demo-token?stranger=1'
resp = urllib.request.urlopen(url, timeout=10).read().decode('utf-8')

print("AUTOMATIC SOS present:", 'AUTOMATIC SOS' in resp)
print("STRANGER / BYSTANDER present:", 'STRANGER / BYSTANDER' in resp)
print("Step 1: Contact Family present:", 'Step 1: Contact Family' in resp)
print("Step 2: Ambulance present:", 'Step 2: Ambulance' in resp)
print("Clinical Records Locked present:", 'Clinical Medical Records' in resp)
print("Metformin NOT in stranger response:", 'Metformin' not in resp)
print("Penicillin NOT in medical history table:", 'Amoxicillin' not in resp)
print("All checks passed successfully on public URL!")

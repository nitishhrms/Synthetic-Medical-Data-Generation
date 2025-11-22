import requests
import time

SERVICES = [
    ("API Gateway", "http://localhost:8000/health"),
    ("EDC Service", "http://localhost:8001/health"),
    ("Data Generation", "http://localhost:8002/health"),
    ("Analytics Service", "http://localhost:8003/health"),
    ("Quality Service", "http://localhost:8004/health"),
    ("Security Service", "http://localhost:8005/health"),
    ("Daft Analytics", "http://localhost:8007/health"),
    ("Linkup Integration", "http://localhost:8008/health"),
    ("GAIN Service", "http://localhost:8009/health"),
    ("GAN Service", "http://localhost:8010/health"),
    ("AI Monitor", "http://localhost:8011/health"),
]

def check_services():
    print(f"{'Service':<25} | {'Status':<10} | {'Message'}")
    print("-" * 60)
    
    all_healthy = True
    for name, url in SERVICES:
        try:
            response = requests.get(url, timeout=2)
            if response.status_code == 200:
                print(f"{name:<25} | {'OK':<10} | {response.json().get('status', 'OK')}")
            else:
                print(f"{name:<25} | {'FAIL':<10} | Status {response.status_code}")
                all_healthy = False
        except requests.exceptions.ConnectionError:
            print(f"{name:<25} | {'DOWN':<10} | Connection Refused")
            all_healthy = False
        except Exception as e:
            print(f"{name:<25} | {'ERROR':<10} | {str(e)}")
            all_healthy = False

    return all_healthy

if __name__ == "__main__":
    print("Checking backend services...")
    if check_services():
        print("\nAll backend services are running and healthy!")
    else:
        print("\nSome services are down or unhealthy. Please check the terminal windows.")

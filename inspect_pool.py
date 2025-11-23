import requests
import json

# Pool address from the logs
pool_address = "XSKED5VKZZCSYNDWXZJI65JM2HP7HZFJWCOBIMOONKHTK5UVKENBNVDEYM"
algod_url = "https://mainnet-api.algonode.cloud"

# Get account info
url = f"{algod_url}/v2/accounts/{pool_address}"
response = requests.get(url, timeout=10)

if response.status_code == 200:
    data = response.json()
    
    print("=== POOL ACCOUNT INFO ===\n")
    print(f"ALGO Balance: {data.get('amount', 0) / 1_000_000:,.2f}")
    
    print("\n=== ASSETS HELD ===")
    for asset in data.get('assets', []):
        asset_id = asset['asset-id']
        amount = asset['amount']
        
        # Get asset info
        asset_url = f"{algod_url}/v2/assets/{asset_id}"
        asset_response = requests.get(asset_url, timeout=5)
        if asset_response.status_code == 200:
            asset_info = asset_response.json()
            name = asset_info['params'].get('name', 'Unknown')
            unit = asset_info['params'].get('unit-name', '')
            decimals = asset_info['params'].get('decimals', 6)
            actual_amount = amount / (10 ** decimals)
            print(f"  {asset_id}: {actual_amount:,.2f} {unit} ({name})")
    
    print("\n=== APPS LOCAL STATE ===")
    for app in data.get('apps-local-state', []):
        print(f"\nApp ID: {app.get('id')}")
        for kv in app.get('key-value', []):
            import base64
            try:
                key = base64.b64decode(kv['key']).decode('utf-8')
                value = kv.get('value', {})
                if 'uint' in value:
                    print(f"  {key}: {value['uint']}")
                elif 'bytes' in value:
                    print(f"  {key}: {value['bytes']}")
            except:
                print(f"  (binary key): {kv.get('value', {})}")
else:
    print(f"Failed to get account info: {response.status_code}")

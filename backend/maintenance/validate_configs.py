
import os
import yaml
import json

def validate_yaml(file_path):
    try:
        with open(file_path, 'r') as f:
            yaml.safe_load(f)
        print(f"✅ [YAML] Validated: {file_path}")
        return True
    except Exception as e:
        print(f"❌ [YAML] Error in {file_path}: {e}")
        return False

def validate_json(file_path):
    try:
        with open(file_path, 'r') as f:
            json.load(f)
        print(f"✅ [JSON] Validated: {file_path}")
        return True
    except Exception as e:
        print(f"❌ [JSON] Error in {file_path}: {e}")
        return False

def main():
    config_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'config'))
    all_valid = True
    
    print(f"--- Validating Configuration Files in {config_dir} ---")
    
    for root, _, files in os.walk(config_dir):
        for file in files:
            file_path = os.path.join(root, file)
            if file.endswith('.yaml') or file.endswith('.yml'):
                if not validate_yaml(file_path):
                    all_valid = False
            elif file.endswith('.json'):
                if not validate_json(file_path):
                    all_valid = False

    print("--- Validation Summary ---")
    if all_valid:
        print("✅ All configuration files are valid.")
    else:
        print("❌ Some configuration files have errors.")

if __name__ == "__main__":
    main()

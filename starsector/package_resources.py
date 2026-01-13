import zipfile
import os

def package():
    jar_name = "resources.jar"
    print(f"Creating {jar_name}...")
    with zipfile.ZipFile(jar_name, 'w', zipfile.ZIP_DEFLATED) as zf:
        if os.path.exists("console_log4j.properties"):
            print("Adding console_log4j.properties")
            zf.write("console_log4j.properties", "console_log4j.properties")
        
        # Add data directory
        for root, dirs, files in os.walk("data"):
            for file in files:
                file_path = os.path.join(root, file)
                zf.write(file_path, file_path)
    
    print("Done.")

if __name__ == "__main__":
    package()

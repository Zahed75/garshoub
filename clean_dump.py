import os

def clean_dump(file_path):
    temp_path = file_path + ".tmp"
    print(f"Cleaning {file_path}...")
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as infile:
        with open(temp_path, 'w', encoding='utf-8') as outfile:
            for line in infile:
                # Remove the proprietary \restrict command
                if line.strip().startswith('\\restrict'):
                    print(f"Removed line: {line.strip()}")
                    continue
                outfile.write(line)
    
    os.replace(temp_path, file_path)
    print("Done cleaning dump file.")

if __name__ == "__main__":
    clean_dump("syscomatic.dump/dump.sql")


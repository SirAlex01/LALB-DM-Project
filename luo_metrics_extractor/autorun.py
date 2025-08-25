import os
import zipfile
import shutil
import subprocess
import logging
# Configuration
base_dir = "."  # Replace with your target directory
script_to_run = "./metrics_from_logs.py"  # Replace with the path to your script

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# Step 1: Process all zip files
for file in os.listdir(base_dir):
    if file.endswith(".zip"):
        zip_path = os.path.join(base_dir, file)
        extract_dir = os.path.join(base_dir, file[:-4])  # remove .zip
        os.makedirs(extract_dir, exist_ok=True)
        logging.info(f"Processing zip file: {zip_path}")
        # Step 2: Extract zip
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_dir)
        logging.info(f"Extracted to: {extract_dir}")
        # Step 3: Copy script to extracted directory
        dest_script = os.path.join(extract_dir, os.path.basename(script_to_run))
        shutil.copy(script_to_run, dest_script)
        logging.info(f"Copied script to: {dest_script}")
        # Step 4: Run the script
        try:
            subprocess.run(["python", os.path.basename(dest_script)], cwd=extract_dir, check=True)
            logging.info(f"Script executed successfully in {extract_dir}")
        except subprocess.CalledProcessError as e:
            logging.error(f"Error running script in {extract_dir}: {e}")

        ## Step 5: Delete the copied script
        if os.path.exists(dest_script):
            os.remove(dest_script)
            logging.info(f"Deleted script: {dest_script}")
        # Step 6: Delete the zip file
        os.remove(zip_path)
        logging.info(f"Deleted zip file: {zip_path}")
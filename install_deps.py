import subprocess
import sys

def install_packages():
    packages = ['requests', 'opencv-python', 'python-nmap', 'urllib3']
    
    for package in packages:
        try:
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', package])
            print(f"Successfully installed {package}")
        except subprocess.CalledProcessError:
            print(f"Failed to install {package}")

if __name__ == "__main__":
    install_packages()
    print("Dependencies installed. Run: python main_attack.py")

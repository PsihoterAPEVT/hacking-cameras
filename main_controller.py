import threading
import subprocess
import requests
import nmap
import socket
import json
import time
from concurrent.futures import ThreadPoolExecutor

class CameraNetworkScanner:
    def __init__(self):
        self.cameras_found = []
        self.credentials_db = self.load_credentials()
        
    def load_credentials(self):
        """База данных стандартных паролей камер"""
        return {
            'admin': ['admin', '12345', 'password', '1234', ''],
            'root': ['root', 'default', '12345', 'admin'],
            'user': ['user', '12345', 'password'],
            'supervisor': ['supervisor', '12345'],
            'guest': ['guest', '']
        }
    
    def scan_network(self, network_range='192.168.1.0/24'):
        """Сканирование сети на наличие камер"""
        print(f"Scanning network {network_range} for cameras...")
        
        nm = nmap.PortScanner()
        # Сканируем порты commonly используемые камерами
        nm.scan(hosts=network_range, arguments='-p 80,443,554,8554,37777,34567 --open')
        
        for host in nm.all_hosts():
            if nm[host].state() == 'up':
                open_ports = nm[host].all_tcp()
                camera_ports = [p for p in open_ports if p in [80, 443, 554, 8554, 37777, 34567]]
                
                if camera_ports:
                    print(f"Potential camera found: {host} on ports {camera_ports}")
                    self.detect_camera_type(host, camera_ports)
    
    def detect_camera_type(self, ip, ports):
        """Определение типа камеры и производителя"""
        try:
            # Проверка HTTP сервисов
            for port in ports:
                if port in [80, 443]:
                    protocols = ['http', 'https'] if port == 443 else ['http']
                    
                    for protocol in protocols:
                        url = f"{protocol}://{ip}:{port}"
                        try:
                            response = requests.get(url, timeout=5, verify=False)
                            
                            # Анализ заголовков и контента для определения производителя
                            camera_info = self.analyze_response(response, ip, port)
                            if camera_info:
                                self.cameras_found.append(camera_info)
                                break
                        except:
                            continue
            
            # Проверка RTSP потоков
            if 554 in ports or 8554 in ports:
                rtsp_port = 554 if 554 in ports else 8554
                self.test_rtsp_streams(ip, rtsp_port)
                
        except Exception as e:
            print(f"Error detecting camera type for {ip}: {e}")
    
    def analyze_response(self, response, ip, port):
        """Анализ ответа для определения типа камеры"""
        camera_models = {
            'Hikvision': ['hikvision', 'hik-vision'],
            'Dahua': ['dahua', 'dhcdn'],
            'Axis': ['axis', 'axis communications'],
            'TP-Link': ['tp-link', 'tp_link'],
            'Xiaomi': ['xiaomi', 'mi camera'],
            'Foscam': ['foscam'],
            'Reolink': ['reolink']
        }
        
        content = response.text.lower()
        headers = str(response.headers).lower()
        
        for manufacturer, keywords in camera_models.items():
            if any(keyword in content or keyword in headers for keyword in keywords):
                return {
                    'ip': ip,
                    'port': port,
                    'manufacturer': manufacturer,
                    'protocol': 'http',
                    'url': response.url
                }
        
        return None
    
    def test_rtsp_streams(self, ip, port):
        """Тестирование RTSP потоков"""
        rtsp_paths = [
            '/live.sdp',
            '/cam/realmonitor',
            '/h264',
            '/11',
            '/1',
            '/main',
            '/video',
            '/stream'
        ]
        
        for path in rtsp_paths:
            rtsp_url = f"rtsp://{ip}:{port}{path}"
            camera_info = {
                'ip': ip,
                'port': port,
                'manufacturer': 'Unknown RTSP',
                'protocol': 'rtsp',
                'url': rtsp_url
            }
            self.cameras_found.append(camera_info)

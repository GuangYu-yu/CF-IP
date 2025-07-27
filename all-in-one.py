import requests
import subprocess
import os
import tempfile
import time

def download_file(url, filename):
    """下载文件"""
    try:
        response = requests.get(url)
        response.raise_for_status()
        with open(filename, 'wb') as f:
            f.write(response.content)
        print(f"已下载 {filename}")
        return True
    except Exception as e:
        print(f"下载 {url} 失败: {e}")
        return False

def get_cidr_list():
    """从指定URL获取CIDR列表"""
    url = "https://raw.githubusercontent.com/GuangYu-yu/PCF/refs/heads/main/VPS_CIDR_4.txt"
    try:
        response = requests.get(url)
        response.raise_for_status()
        cidr_list = response.text.strip().split('\n')
        # 过滤掉空行和注释行
        cidr_list = [cidr.strip() for cidr in cidr_list if cidr.strip() and not cidr.startswith('#')]
        return cidr_list
    except Exception as e:
        print(f"获取CIDR列表失败: {e}")
        return []

def run_masscan(cidr_list, output_file):
    """运行masscan扫描CIDR列表"""
    if not cidr_list:
        print("CIDR列表为空")
        return False
    
    # 构建masscan命令，添加sudo
    cmd = ["sudo", "masscan", "-p0-65535"] + cidr_list + ["-oL", output_file, "--rate", "1000000"]
    
    try:
        print("开始运行masscan...")
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"masscan扫描完成，结果保存到 {output_file}")
            return True
        else:
            print(f"masscan执行失败: {result.stderr}")
            return False
    except Exception as e:
        print(f"运行masscan时出错: {e}")
        return False

def convert_masscan_to_ip_port(masscan_output, ip_port_file):
    """将masscan输出转换为ip:port格式"""
    try:
        with open(masscan_output, 'r') as f:
            lines = f.readlines()
        
        with open(ip_port_file, 'w') as f:
            for line in lines:
                if line.startswith('open'):
                    parts = line.strip().split()
                    if len(parts) >= 4:
                        protocol, port, ip, timestamp = parts[0], parts[2], parts[3], parts[4]
                        f.write(f"{ip}:{port}\n")
        
        print(f"已将扫描结果转换为ip:port格式，保存到 {ip_port_file}")
        return True
    except Exception as e:
        print(f"转换masscan结果时出错: {e}")
        return False

def download_cloudflarest_rust():
    """下载CloudflareST-Rust可执行程序"""
    url = "https://raw.githubusercontent.com/GuangYu-yu/CloudflareST-Rust/refs/heads/main/binaries/Linux_AMD64/CloudflareST-Rust"
    # 在Linux上直接使用可执行程序
    try:
        # 创建临时目录存放可执行程序
        temp_dir = tempfile.mkdtemp()
        exe_path = os.path.join(temp_dir, "CloudflareST-Rust")
        
        if download_file(url, exe_path):
            # 给予执行权限
            subprocess.run(["chmod", "+x", exe_path])
            return exe_path
        return None
    except Exception as e:
        print(f"下载或准备CloudflareST-Rust时出错: {e}")
        return None

def run_cloudflarest_rust(cfst_path, ip_port_file, output_csv):
    """运行CloudflareST-Rust测试"""
    try:
        # 构建命令
        cmd = [cfst_path, "-f", ip_port_file, "-httping", "-sp", "-o", output_csv]
        
        print("开始运行CloudflareST-Rust测试...")
        # 在Linux上直接运行，不需要WSL
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=os.path.dirname(cfst_path))
        if result.returncode == 0:
            print(f"CloudflareST-Rust测试完成，结果保存到 {output_csv}")
            return True
        else:
            print(f"CloudflareST-Rust执行失败: {result.stderr}")
            return False
    except Exception as e:
        print(f"运行CloudflareST-Rust时出错: {e}")
        return False

def extract_ip_port_from_csv(csv_file, output_txt):
    """从CSV结果中提取第一列(ip:port)保存到txt文件"""
    try:
        with open(csv_file, 'r') as f:
            lines = f.readlines()
        
        # 跳过表头
        data_lines = lines[1:]
        
        with open(output_txt, 'w') as f:
            for line in data_lines:
                if line.strip():
                    # 提取第一列
                    ip_port = line.split(',')[0]
                    f.write(f"{ip_port}\n")
        
        print(f"已将结果中的ip:port提取到 {output_txt}")
        return True
    except Exception as e:
        print(f"提取CSV结果时出错: {e}")
        return False

def main():
    print("开始执行反代IP检测流程...")
    
    # 步骤1: 获取CIDR列表
    print("步骤1: 获取CIDR列表...")
    cidr_list = get_cidr_list()
    if not cidr_list:
        print("无法获取CIDR列表，退出程序")
        return
    
    print(f"成功获取 {len(cidr_list)} 个CIDR")
    
    # 步骤2: 运行masscan扫描
    print("步骤2: 运行masscan扫描...")
    masscan_output = "masscan_result.txt"
    if not run_masscan(cidr_list, masscan_output):
        print("masscan扫描失败，退出程序")
        return
    
    # 步骤3: 转换扫描结果为ip:port格式
    print("步骤3: 转换扫描结果...")
    ip_port_file = "ip_port_list.txt"
    if not convert_masscan_to_ip_port(masscan_output, ip_port_file):
        print("转换扫描结果失败，退出程序")
        return
    
    # 步骤4: 下载CloudflareST-Rust
    print("步骤4: 准备CloudflareST-Rust...")
    cfst_path = download_cloudflarest_rust()
    if not cfst_path:
        print("无法获取CloudflareST-Rust，退出程序")
        return
    
    # 步骤5: 运行CloudflareST-Rust测试
    print("步骤5: 运行CloudflareST-Rust测试...")
    result_csv = "result.csv"
    if not run_cloudflarest_rust(cfst_path, ip_port_file, result_csv):
        print("CloudflareST-Rust测试失败，退出程序")
        return
    
    # 步骤6: 提取结果中的ip:port
    print("步骤6: 提取测试结果...")
    final_result = "final_ip_port.txt"
    if not extract_ip_port_from_csv(result_csv, final_result):
        print("提取测试结果失败")
        return
    
    print("所有步骤完成！最终结果保存在 final_ip_port.txt 中")

if __name__ == "__main__":
    main()

import sys
import os

# 基本的Python运行时配置
def setup_runtime():
    # 添加必要的路径
    sys.path.append(os.path.join(os.getcwd(), 'build', 'web'))
    sys.path.append(os.path.join(os.getcwd(), 'static', 'archives', '0.9'))

    # 设置基本环境变量
    os.environ['PYTHONPATH'] = os.getcwd()
    
setup_runtime() 
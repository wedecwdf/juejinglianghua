# -*- coding: utf-8 -*-

"""
聚合所有配置子模块，保持对外接口不变。
"""

from .mail import *  # 邮件参数唯一出处
from .account import *  # 账户参数唯一出处
from .calendar import *  # 时间/日历参数唯一出处
from .strategy import *  # 策略参数唯一出处（现为包导入，兼容原接口）
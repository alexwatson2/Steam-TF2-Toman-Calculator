# -*- coding: utf-8 -*-
# ============================================================================
# Copyright (c) 2026 AlexWatson
# 
# MIT License
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
# ============================================================================
#
# نرم‌افزار محاسبه قیمت بازی‌های استیم به تومان
# نسخه PyQt5 - با قابلیت انتخاب ریجن/کشور + Proxy + تنظیمات کامل
#
# Project: Steam TF2 Toman Calculator
# Author: AlexWatson
# Version: 4.1.1
# License: MIT
#
# ============================================================================


# -*- coding: utf-8 -*-
"""
نرم‌افزار محاسبه قیمت بازی‌های استیم به تومان
نسخه PyQt5 - با قابلیت انتخاب ریجن/کشور + Proxy + تنظیمات کامل
"""

import sys
import re
import json
import os
import webbrowser
from datetime import datetime

import requests
from bs4 import BeautifulSoup

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QLineEdit, QComboBox, QTableWidget,
    QTableWidgetItem, QGroupBox, QRadioButton, QButtonGroup,
    QMessageBox, QSplitter, QFrame, QHeaderView,
    QStatusBar, QScrollArea, QDialog, QDialogButtonBox,
    QCheckBox, QSpinBox, QTabWidget
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QFont


# ==================== دیالوگ تنظیمات ====================
class SettingsDialog(QDialog):
    """پنجره تنظیمات برنامه"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.setWindowTitle("⚙️ تنظیمات پیشرفته")
        self.setMinimumSize(550, 600)
        self.setModal(True)
        self.setup_ui()
        self.load_settings()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        tabs = QTabWidget()
        
        # ========== تب Proxy ==========
        proxy_tab = QWidget()
        proxy_layout = QVBoxLayout(proxy_tab)
        
        proxy_group = QGroupBox("🌐 تنظیمات Proxy (فقط برای استیم مارکت)")
        proxy_group_layout = QVBoxLayout(proxy_group)
        
        self.enable_proxy_check = QCheckBox("فعال کردن Proxy")
        self.enable_proxy_check.toggled.connect(self.toggle_proxy_widgets)
        proxy_group_layout.addWidget(self.enable_proxy_check)
        
        # راهنمایی
        help_label = QLabel("⚠️ توجه: Proxy فقط برای اتصال به استیم مارکت استفاده می‌شود و سایت‌های ایرانی بدون Proxy متصل می‌شوند.")
        help_label.setWordWrap(True)
        help_label.setStyleSheet("color: #ff9800; font-size: 10px;")
        proxy_group_layout.addWidget(help_label)
        
        type_row = QHBoxLayout()
        type_row.addWidget(QLabel("نوع Proxy:"))
        self.proxy_type_combo = QComboBox()
        self.proxy_type_combo.addItems(["http", "https", "socks5", "socks4"])
        type_row.addWidget(self.proxy_type_combo)
        proxy_group_layout.addLayout(type_row)
        
        host_row = QHBoxLayout()
        host_row.addWidget(QLabel("آدرس (Host):"))
        self.proxy_host_entry = QLineEdit()
        self.proxy_host_entry.setPlaceholderText("مثال: 127.0.0.1 یا proxy.example.com")
        self.proxy_host_entry.setText("127.0.0.1")
        host_row.addWidget(self.proxy_host_entry)
        proxy_group_layout.addLayout(host_row)
        
        port_row = QHBoxLayout()
        port_row.addWidget(QLabel("پورت (Port):"))
        self.proxy_port_entry = QLineEdit()
        self.proxy_port_entry.setPlaceholderText("مثال: 8080 یا 1080")
        self.proxy_port_entry.setText("10808")
        port_row.addWidget(self.proxy_port_entry)
        proxy_group_layout.addLayout(port_row)
        
        auth_group = QGroupBox("🔐 احراز هویت (اختیاری)")
        auth_layout = QVBoxLayout(auth_group)
        
        self.proxy_username_entry = QLineEdit()
        self.proxy_username_entry.setPlaceholderText("نام کاربری")
        auth_layout.addWidget(self.proxy_username_entry)
        
        self.proxy_password_entry = QLineEdit()
        self.proxy_password_entry.setPlaceholderText("رمز عبور")
        self.proxy_password_entry.setEchoMode(QLineEdit.Password)
        auth_layout.addWidget(self.proxy_password_entry)
        
        proxy_group_layout.addWidget(auth_group)
        
        # دکمه تست پروکسی
        test_btn = QPushButton("🔍 تست اتصال Proxy")
        test_btn.clicked.connect(self.test_proxy)
        proxy_group_layout.addWidget(test_btn)
        
        self.proxy_status_label = QLabel("")
        self.proxy_status_label.setAlignment(Qt.AlignCenter)
        proxy_group_layout.addWidget(self.proxy_status_label)
        
        # راهنمای v2ray
        v2ray_help = QLabel("📌 راهنما: برای v2ray از نوع socks5 و پورت 10808 استفاده کنید")
        v2ray_help.setWordWrap(True)
        v2ray_help.setStyleSheet("color: #4caf50; font-size: 9px;")
        proxy_group_layout.addWidget(v2ray_help)
        
        proxy_layout.addWidget(proxy_group)
        proxy_layout.addStretch()
        
        # ========== تب تنظیمات برنامه ==========
        general_tab = QWidget()
        general_layout = QVBoxLayout(general_tab)
        
        general_group = QGroupBox("⚙️ تنظیمات عمومی")
        general_group_layout = QVBoxLayout(general_group)
        
        timeout_row = QHBoxLayout()
        timeout_row.addWidget(QLabel("زمان انتظار درخواست‌ها (ثانیه):"))
        self.timeout_spin = QSpinBox()
        self.timeout_spin.setRange(5, 60)
        self.timeout_spin.setValue(20)
        timeout_row.addWidget(self.timeout_spin)
        general_group_layout.addLayout(timeout_row)
        
        self.auto_save_check = QCheckBox("ذخیره خودکار تنظیمات")
        self.auto_save_check.setChecked(True)
        general_group_layout.addWidget(self.auto_save_check)
        
        general_layout.addWidget(general_group)
        general_layout.addStretch()
        
        tabs.addTab(proxy_tab, "🌐 Proxy")
        tabs.addTab(general_tab, "⚙️ عمومی")
        
        layout.addWidget(tabs)
        
        btn_layout = QHBoxLayout()
        save_btn = QPushButton("💾 ذخیره تنظیمات")
        save_btn.clicked.connect(self.save_settings)
        cancel_btn = QPushButton("❌ انصراف")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)
    
    def toggle_proxy_widgets(self, enabled):
        """فعال/غیرفعال کردن ویجت‌های Proxy"""
        widgets = [self.proxy_type_combo, self.proxy_host_entry, 
                   self.proxy_port_entry, self.proxy_username_entry, 
                   self.proxy_password_entry]
        for w in widgets:
            w.setEnabled(enabled)
    
    def test_proxy(self):
        """تست اتصال Proxy"""
        if not self.enable_proxy_check.isChecked():
            self.proxy_status_label.setText("❌ Proxy فعال نیست!")
            return
        
        host = self.proxy_host_entry.text().strip()
        port = self.proxy_port_entry.text().strip()
        
        if not host or not port:
            self.proxy_status_label.setText("❌ آدرس و پورت Proxy را وارد کنید!")
            return
        
        proxy_type = self.proxy_type_combo.currentText()
        
        # ساخت پروکسی
        if proxy_type in ["socks4", "socks5"]:
            proxy_url = f"{proxy_type}://{host}:{port}"
        else:
            proxy_url = f"{proxy_type}://{host}:{port}"
        
        if self.proxy_username_entry.text():
            proxy_url = f"{proxy_type}://{self.proxy_username_entry.text()}:{self.proxy_password_entry.text()}@{host}:{port}"
        
        proxies = {"http": proxy_url, "https": proxy_url}
        
        self.proxy_status_label.setText("🔄 در حال تست Proxy...")
        
        def test():
            try:
                # تست با آدرس‌های مختلف
                test_urls = [
                    "https://httpbin.org/ip",
                    "https://www.google.com",
                    "https://store.steampowered.com/"
                ]
                
                for url in test_urls:
                    try:
                        response = requests.get(url, proxies=proxies, timeout=10)
                        if response.status_code == 200:
                            if "httpbin.org/ip" in url:
                                try:
                                    ip_data = response.json()
                                    self.proxy_status_label.setText(f"✅ Proxy کار می‌کند! IP: {ip_data.get('origin', '')[:40]}")
                                except:
                                    self.proxy_status_label.setText(f"✅ Proxy کار می‌کند! (تست: {url[:40]})")
                            else:
                                self.proxy_status_label.setText(f"✅ Proxy کار می‌کند! (تست: {url[:40]})")
                            return
                    except:
                        continue
                
                self.proxy_status_label.setText("⚠️ Proxy وصل است اما آدرس‌ها پاسخ نمی‌دهند")
                
            except Exception as e:
                error_msg = str(e)
                if "SOCKS" in error_msg:
                    self.proxy_status_label.setText("❌ خطای SOCKS: مطمئن شوید پکیج pysocks نصب است")
                elif "Connection refused" in error_msg:
                    self.proxy_status_label.setText("❌ اتصال به Proxy برقرار نشد! v2ray را بررسی کنید")
                else:
                    self.proxy_status_label.setText(f"❌ خطا: {error_msg[:60]}")
        
        import threading
        threading.Thread(target=test, daemon=True).start()
    
    def load_settings(self):
        if self.parent:
            self.enable_proxy_check.setChecked(self.parent.proxy_enabled)
            self.proxy_type_combo.setCurrentText(self.parent.proxy_type)
            self.proxy_host_entry.setText(self.parent.proxy_host)
            self.proxy_port_entry.setText(self.parent.proxy_port)
            self.proxy_username_entry.setText(self.parent.proxy_username)
            self.proxy_password_entry.setText(self.parent.proxy_password)
            self.timeout_spin.setValue(self.parent.request_timeout)
            self.auto_save_check.setChecked(self.parent.auto_save_settings)
            self.toggle_proxy_widgets(self.parent.proxy_enabled)
    
    def save_settings(self):
        if self.parent:
            self.parent.proxy_enabled = self.enable_proxy_check.isChecked()
            self.parent.proxy_type = self.proxy_type_combo.currentText()
            self.parent.proxy_host = self.proxy_host_entry.text().strip()
            self.parent.proxy_port = self.proxy_port_entry.text().strip()
            self.parent.proxy_username = self.proxy_username_entry.text()
            self.parent.proxy_password = self.proxy_password_entry.text()
            self.parent.request_timeout = self.timeout_spin.value()
            self.parent.auto_save_settings = self.auto_save_check.isChecked()
            self.parent.save_settings()
            self.parent.statusBar.showMessage("✅ تنظیمات ذخیره شد")
            self.accept()


# ==================== دیالوگ انتخاب ریجن/کشور ====================
class RegionSearchDialog(QDialog):
    region_selected = pyqtSignal(str, str, str)
    
    def __init__(self, parent=None, current_currency="USD"):
        super().__init__(parent)
        self.setWindowTitle("🌍 انتخاب کشور و ارز استیم")
        self.setMinimumSize(550, 600)
        self.setModal(True)
        self.current_currency = current_currency
        self.setup_ui()
        self.load_regions()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        title = QLabel("انتخاب کشور یا ارز مورد نظر")
        title.setFont(QFont("Tahoma", 12, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        search_group = QGroupBox("🔍 جستجو")
        search_layout = QHBoxLayout(search_group)
        search_layout.addWidget(QLabel("نام کشور یا کد ارز:"))
        self.search_entry = QLineEdit()
        self.search_entry.setPlaceholderText("مثال: آمریکا, United States, USD, EUR, ...")
        self.search_entry.textChanged.connect(self.filter_regions)
        search_layout.addWidget(self.search_entry)
        layout.addWidget(search_group)
        
        list_group = QGroupBox("📋 لیست کشورها و ارزهای پشتیبانی شده")
        list_layout = QVBoxLayout(list_group)
        
        self.region_list = QComboBox()
        self.region_list.setEditable(True)
        self.region_list.setInsertPolicy(QComboBox.NoInsert)
        self.region_list.setMinimumHeight(450)
        self.region_list.setFont(QFont("Tahoma", 10))
        list_layout.addWidget(self.region_list)
        
        layout.addWidget(list_group)
        
        btn_layout = QHBoxLayout()
        select_btn = QPushButton("✅ انتخاب و اعمال")
        select_btn.setMinimumHeight(40)
        select_btn.setFont(QFont("Tahoma", 10, QFont.Bold))
        select_btn.clicked.connect(self.select_region)
        btn_layout.addWidget(select_btn)
        
        cancel_btn = QPushButton("❌ انصراف")
        cancel_btn.setMinimumHeight(40)
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)
        
        layout.addLayout(btn_layout)
        
        self.current_label = QLabel(f"💰 ارز فعلی: {self.current_currency}")
        self.current_label.setAlignment(Qt.AlignCenter)
        self.current_label.setFont(QFont("Tahoma", 9))
        self.current_label.setStyleSheet("color: #00adb5; padding: 5px;")
        layout.addWidget(self.current_label)
    
    def load_regions(self):
        self.regions = [
            ("USD", "$", "🇺🇸 ایالات متحده آمریکا (United States)"),
            ("CAD", "C$", "🇨🇦 کانادا (Canada)"),
            ("MXN", "$", "🇲🇽 مکزیک (Mexico)"),
            ("BRL", "R$", "🇧🇷 برزیل (Brazil)"),
            ("ARS", "$", "🇦🇷 آرژانتین (Argentina)"),
            ("CLP", "$", "🇨🇱 شیلی (Chile)"),
            ("COP", "$", "🇨🇴 کلمبیا (Colombia)"),
            ("PEN", "S/", "🇵🇪 پرو (Peru)"),
            ("UYU", "$", "🇺🇾 اوروگوئه (Uruguay)"),
            ("CRC", "₡", "🇨🇷 کاستاریکا (Costa Rica)"),
            ("EUR", "€", "🇪🇺 اتحادیه اروپا (European Union)"),
            ("GBP", "£", "🇬🇧 بریتانیا (United Kingdom)"),
            ("CHF", "CHF", "🇨🇭 سوئیس (Switzerland)"),
            ("RUB", "₽", "🇷🇺 روسیه (Russia)"),
            ("PLN", "zł", "🇵🇱 لهستان (Poland)"),
            ("NOK", "kr", "🇳🇴 نروژ (Norway)"),
            ("SEK", "kr", "🇸🇪 سوئد (Sweden)"),
            ("DKK", "kr", "🇩🇰 دانمارک (Denmark)"),
            ("CZK", "Kč", "🇨🇿 جمهوری چک (Czech Republic)"),
            ("HUF", "Ft", "🇭🇺 مجارستان (Hungary)"),
            ("RON", "lei", "🇷🇴 رومانی (Romania)"),
            ("BGN", "лв", "🇧🇬 بلغارستان (Bulgaria)"),
            ("TRY", "₺", "🇹🇷 ترکیه (Turkey)"),
            ("UAH", "₴", "🇺🇦 اوکراین (Ukraine)"),
            ("KZT", "₸", "🇰🇿 قزاقستان (Kazakhstan)"),
            ("BYN", "Br", "🇧🇾 بلاروس (Belarus)"),
            ("JPY", "¥", "🇯🇵 ژاپن (Japan)"),
            ("CNY", "¥", "🇨🇳 چین (China)"),
            ("KRW", "₩", "🇰🇷 کره جنوبی (South Korea)"),
            ("INR", "₹", "🇮🇳 هند (India)"),
            ("IDR", "Rp", "🇮🇩 اندونزی (Indonesia)"),
            ("MYR", "RM", "🇲🇾 مالزی (Malaysia)"),
            ("PHP", "₱", "🇵🇭 فیلیپین (Philippines)"),
            ("SGD", "S$", "🇸🇬 سنگاپور (Singapore)"),
            ("THB", "฿", "🇹🇭 تایلند (Thailand)"),
            ("VND", "₫", "🇻🇳 ویتنام (Vietnam)"),
            ("TWD", "NT$", "🇹🇼 تایوان (Taiwan)"),
            ("ILS", "₪", "🇮🇱 اسرائیل (Israel)"),
            ("SAR", "﷼", "🇸🇦 عربستان سعودی (Saudi Arabia)"),
            ("AED", "د.إ", "🇦🇪 امارات (UAE)"),
            ("QAR", "﷼", "🇶🇦 قطر (Qatar)"),
            ("KWD", "د.ك", "🇰🇼 کویت (Kuwait)"),
            ("AUD", "A$", "🇦🇺 استرالیا (Australia)"),
            ("NZD", "NZ$", "🇳🇿 نیوزیلند (New Zealand)"),
            ("ZAR", "R", "🇿🇦 آفریقای جنوبی (South Africa)"),
        ]
        
        for code, symbol, display in self.regions:
            self.region_list.addItem(display, (code, symbol))
        
        for i, (code, symbol, display) in enumerate(self.regions):
            if code == self.current_currency:
                self.region_list.setCurrentIndex(i)
                break
    
    def filter_regions(self):
        search_text = self.search_entry.text().strip().lower()
        current_data = self.region_list.currentData()
        self.region_list.clear()
        
        for code, symbol, display in self.regions:
            if (search_text == "" or 
                search_text in display.lower() or 
                search_text in code.lower()):
                self.region_list.addItem(display, (code, symbol))
        
        if current_data:
            idx = self.region_list.findData(current_data)
            if idx >= 0:
                self.region_list.setCurrentIndex(idx)
    
    def select_region(self):
        current_idx = self.region_list.currentIndex()
        if current_idx >= 0:
            code, symbol = self.region_list.itemData(current_idx)
            display_text = self.region_list.currentText()
            self.region_selected.emit(code, symbol, display_text)
            self.accept()


# ==================== Thread دریافت قیمت از استیم مارکت با Proxy ====================
class FetchSteamMarketThread(QThread):
    finished = pyqtSignal(float, str)
    status = pyqtSignal(str)
    
    def __init__(self, item_name="Mann Co. Supply Crate Key", app_id=440, currency="USD", 
                 proxy_enabled=False, proxy_type="http", proxy_host="", proxy_port="",
                 proxy_username="", proxy_password="", timeout=20):
        super().__init__()
        self.item_name = item_name
        self.app_id = app_id
        self.currency = currency
        self.proxy_enabled = proxy_enabled
        self.proxy_type = proxy_type
        self.proxy_host = proxy_host
        self.proxy_port = proxy_port
        self.proxy_username = proxy_username
        self.proxy_password = proxy_password
        self.timeout = timeout
    
    def get_proxy_dict(self):
        """ساخت دیکشنری Proxy برای requests"""
        if not self.proxy_enabled or not self.proxy_host or not self.proxy_port:
            return None
        
        # ساخت URL پروکسی
        if self.proxy_username and self.proxy_password:
            proxy_url = f"{self.proxy_type}://{self.proxy_username}:{self.proxy_password}@{self.proxy_host}:{self.proxy_port}"
        else:
            proxy_url = f"{self.proxy_type}://{self.proxy_host}:{self.proxy_port}"
        
        # دیکشنری پراکسی برای هر دو پروتکل HTTP و HTTPS
        return {"http": proxy_url, "https": proxy_url}
    
    def run(self):
        try:
            proxy_dict = self.get_proxy_dict()
            proxy_status = "با Proxy" if proxy_dict else "بدون Proxy"
            self.status.emit(f"🔄 در حال اتصال به استیم مارکت... ({proxy_status})")
            
            # تبدیل کد ارز به عدد
            currency_codes = {
                "USD": 1, "EUR": 2, "GBP": 3, "CHF": 4, "RUB": 5, "PLN": 6,
                "BRL": 7, "JPY": 8, "NOK": 9, "IDR": 10, "MYR": 11, "PHP": 12,
                "SGD": 13, "THB": 14, "VND": 15, "KRW": 16, "TRY": 17, "UAH": 18,
                "MXN": 19, "CAD": 20, "AUD": 21, "NZD": 22, "CNY": 23, "INR": 24,
                "CLP": 25, "PEN": 26, "COP": 27, "ZAR": 28, "HKD": 29, "TWD": 30,
                "SAR": 31, "AED": 32, "SEK": 33, "ARS": 34, "ILS": 35, "KZT": 36,
                "KWD": 37, "QAR": 38, "CRC": 39, "UYU": 40
            }
            currency_num = currency_codes.get(self.currency, 1)
            
            url = f"https://steamcommunity.com/market/priceoverview/?currency={currency_num}&appid={self.app_id}&market_hash_name={self.item_name.replace(' ', '%20')}"
            
            # ارسال درخواست با یا بدون پروکسی
            response = requests.get(url, proxies=proxy_dict, timeout=self.timeout)
            response.raise_for_status()
            data = response.json()
            
            if data and data.get('success') and data.get('lowest_price'):
                price_str = data['lowest_price']
                price_match = re.search(r'(\d+\.?\d*)', price_str)
                if price_match:
                    price_value = float(price_match.group(1))
                    self.finished.emit(price_value, "")
                else:
                    self.finished.emit(0, f"فرمت قیمت نامعتبر: {price_str}")
            else:
                self.finished.emit(0, "قیمت در استیم مارکت پیدا نشد!")
                
        except requests.exceptions.Timeout:
            self.finished.emit(0, "مدت زمان انتظار به پایان رسید! (Timeout)")
        except requests.exceptions.ProxyError as e:
            error_msg = str(e)
            if "SOCKS" in error_msg:
                self.finished.emit(0, "خطای SOCKS: پکیج pysocks را نصب کنید!")
            else:
                self.finished.emit(0, f"خطای Proxy: {error_msg[:60]}")
        except requests.exceptions.ConnectionError as e:
            error_msg = str(e)
            if "refused" in error_msg.lower():
                self.finished.emit(0, "اتصال به Proxy برقرار نشد! v2ray را بررسی کنید")
            else:
                self.finished.emit(0, f"خطا در اتصال به استیم! {error_msg[:40]}")
        except Exception as e:
            self.finished.emit(0, f"خطا: {str(e)[:80]}")


# ==================== Thread دریافت قیمت از سایت‌های ایرانی (بدون Proxy) ====================
class FetchPriceThread(QThread):
    finished = pyqtSignal(float, str)
    status = pyqtSignal(str)
    
    def __init__(self, url, site_name, timeout=20):
        super().__init__()
        self.url = url
        self.site_name = site_name
        self.timeout = timeout
    
    def run(self):
        try:
            self.status.emit(f"🔄 در حال اتصال به {self.site_name}...")
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            }
            
            # بدون Proxy برای سایت‌های ایرانی
            response = requests.get(self.url, headers=headers, timeout=self.timeout)
            response.raise_for_status()
            
            self.status.emit(f"📄 در حال تجزیه صفحه {self.site_name}...")
            soup = BeautifulSoup(response.text, 'html.parser')
            
            price = self.extract_price(soup)
            
            if price and price > 0:
                self.finished.emit(price, "")
            else:
                self.finished.emit(0, "قیمت در سایت پیدا نشد!")
                
        except requests.exceptions.Timeout:
            self.finished.emit(0, "مدت زمان انتظار به پایان رسید!")
        except requests.exceptions.ConnectionError:
            self.finished.emit(0, "خطا در اتصال به سایت!")
        except Exception as e:
            self.finished.emit(0, f"خطا: {str(e)[:50]}")
    
    def extract_price(self, soup):
        price = None
        
        price_patterns = [
            '.product-price', '.price', '.amount', '.current-price',
            '.woocommerce-Price-amount', 'ins .woocommerce-Price-amount',
            '.summary.entry-summary .price', '[class*="price"]'
        ]
        
        for pattern in price_patterns:
            elements = soup.select(pattern)
            for elem in elements:
                text = elem.get_text().strip()
                extracted = self.clean_price(text)
                if extracted and 100000 < extracted < 1000000:
                    price = extracted
                    break
            if price:
                break
        
        if not price:
            page_text = soup.get_text()
            matches = re.findall(r'(\d{1,3}(?:[\,\.]\d{3})*)\s*(?:تومان)', page_text)
            for match in matches:
                num = self.clean_number(match)
                if num and 100000 < num < 1000000:
                    price = num
                    break
        
        return price
    
    def clean_price(self, text):
        if not text:
            return None
        text = text.replace('٬', ',').replace('٫', '.').strip()
        matches = re.findall(r'(\d{1,3}(?:[\,\.]\d{3})*(?:\.\d+)?)\s*(?:تومان)', text)
        for match in matches:
            return self.clean_number(match)
        return None
    
    def clean_number(self, num_str):
        try:
            cleaned = num_str.replace(',', '').replace(' ', '').replace('٬', '').replace('٫', '.')
            return float(cleaned)
        except:
            return None


class SteamPriceCalculator(QMainWindow):
    """کلاس اصلی نرم‌افزار"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("🎮 Steam Price Calculator - ماشین حساب قیمت استیم")
        self.setMinimumSize(1300, 900)
        self.resize(1400, 980)
        
        # تنظیمات فونت
        self.default_font = QFont("Tahoma", 10)
        self.title_font = QFont("Tahoma", 13, QFont.Bold)
        self.group_font = QFont("Tahoma", 11, QFont.Bold)
        
        # تنظیمات پیش‌فرض
        self.current_theme = "steam"
        self.current_currency = "USD"
        self.current_currency_symbol = "$"
        self.current_country_display = "🇺🇸 ایالات متحده آمریکا (United States)"
        self.request_timeout = 20
        self.auto_save_settings = True
        
        # تنظیمات Proxy (پیش‌فرض برای v2ray)
        self.proxy_enabled = False
        self.proxy_type = "socks5"
        self.proxy_host = "127.0.0.1"
        self.proxy_port = "10808"
        self.proxy_username = ""
        self.proxy_password = ""
        
        # متغیرها
        self.key_market_price = 0.0
        self.key_rial_price = 0.0
        self.exchange_rate = 0.0
        self.key_net_price = 0.0
        self.price_mode = "auto_preset"
        self.selected_site = "wow-online"
        self.fetch_threads = []
        
        # سایت‌های پیش‌فرض
        self.preset_sites = {
            "wow-online": {
                "url": "https://wow-online.ir/product/%DA%A9%D9%84%DB%8C%D8%AF-%D8%AA%DB%8C%D9%85-%D9%81%D9%88%D8%B1%D8%AA%D8%B1%D8%B3-2-mann-co-supply-crate-key-tf2/",
                "name": "wow-online.ir"
            },
            "game4sell": {
                "url": "https://www.game4sell.ir/shop/tf2/mann-co-supply-crate-key",
                "name": "game4sell.ir"
            },
            "gamerzshop": {
                "url": "https://gamerzshop.ir/product/tf2-key/",
                "name": "gamerzshop.ir"
            }
        }
        
        self.setup_ui()
        self.load_settings()
        self.apply_theme()
        self.update_currency_display()
    
    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        self.setup_toolbar(main_layout)
        
        splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(splitter)
        
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        self.setup_left_panel(left_layout)
        splitter.addWidget(left_widget)
        
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        self.setup_right_panel(right_layout)
        splitter.addWidget(right_widget)
        
        splitter.setSizes([850, 400])
        
        self.setup_statusbar()
        self.setup_footer(main_layout)
    
    def setup_toolbar(self, layout):
        toolbar = QHBoxLayout()
        
        title = QLabel("🎮 ماشین حساب قیمت بازی های که با کلید خریداری می‌شوند")
        title.setFont(self.title_font)
        toolbar.addWidget(title)
        
        toolbar.addStretch()
        
        self.steam_market_btn = QPushButton("🎮 دریافت از استیم مارکت")
        self.steam_market_btn.setMinimumHeight(32)
        self.steam_market_btn.setFont(QFont("Tahoma", 9))
        self.steam_market_btn.clicked.connect(self.get_price_from_steam_market)
        toolbar.addWidget(self.steam_market_btn)
        
        self.region_btn = QPushButton("🌍 انتخاب کشور و ارز")
        self.region_btn.setMinimumHeight(32)
        self.region_btn.setFont(QFont("Tahoma", 9))
        self.region_btn.clicked.connect(self.open_region_selector)
        toolbar.addWidget(self.region_btn)
        
        self.currency_display_label = QLabel("")
        self.currency_display_label.setFrameStyle(QFrame.Panel)
        self.currency_display_label.setMinimumWidth(180)
        self.currency_display_label.setFont(QFont("Tahoma", 9))
        toolbar.addWidget(self.currency_display_label)
        
        toolbar.addWidget(QLabel("🎨 تم:"))
        
        light_btn = QPushButton("☀️ روشن")
        light_btn.clicked.connect(lambda: self.change_theme("light"))
        toolbar.addWidget(light_btn)
        
        dark_btn = QPushButton("🌙 تیره")
        dark_btn.clicked.connect(lambda: self.change_theme("dark"))
        toolbar.addWidget(dark_btn)
        
        gray_btn = QPushButton("⚙️ خاکستری")
        gray_btn.clicked.connect(lambda: self.change_theme("gray"))
        toolbar.addWidget(gray_btn)
        
        steam_btn = QPushButton("🎮 استیم")
        steam_btn.clicked.connect(lambda: self.change_theme("steam"))
        toolbar.addWidget(steam_btn)
        
        self.settings_btn = QPushButton("⚙️ تنظیمات")
        self.settings_btn.setMinimumHeight(32)
        self.settings_btn.clicked.connect(self.open_settings)
        toolbar.addWidget(self.settings_btn)
        
        layout.addLayout(toolbar)
    
    def open_settings(self):
        dialog = SettingsDialog(self)
        dialog.exec_()
    
    def open_region_selector(self):
        dialog = RegionSearchDialog(self, self.current_currency)
        dialog.region_selected.connect(self.on_region_selected)
        dialog.exec_()
    
    def on_region_selected(self, currency_code, currency_symbol, country_display):
        self.current_currency = currency_code
        self.current_currency_symbol = currency_symbol
        self.current_country_display = country_display
        self.update_currency_display()
        self.save_settings()
        self.statusBar.showMessage(f"✅ ارز به {currency_code} ({currency_symbol}) تغییر کرد")
    
    def update_currency_display(self):
        self.currency_display_label.setText(f"💰 {self.current_currency} ({self.current_currency_symbol})")
        self.currency_label.setText(self.current_currency)
    
    def setup_left_panel(self, layout):
        # ===== بخش اطلاعات کلید =====
        key_group = QGroupBox("🔑 اطلاعات کلید")
        key_group.setFont(self.group_font)
        key_layout = QVBoxLayout(key_group)
        
        market_row = QHBoxLayout()
        market_label = QLabel("💰 قیمت هر کلید در مارکت استیم:")
        market_label.setFont(QFont("Tahoma", 10))
        market_row.addWidget(market_label)
        
        self.currency_label = QLabel(self.current_currency)
        self.currency_label.setFrameStyle(QFrame.Panel)
        self.currency_label.setFixedWidth(55)
        self.currency_label.setFont(QFont("Tahoma", 10, QFont.Bold))
        self.currency_label.setAlignment(Qt.AlignCenter)
        market_row.addWidget(self.currency_label)
        
        self.market_entry = QLineEdit()
        self.market_entry.setPlaceholderText("مثال: 2.15")
        self.market_entry.setFont(QFont("Tahoma", 11))
        self.market_entry.setMinimumHeight(32)
        self.market_entry.textChanged.connect(self.on_market_price_changed)
        market_row.addWidget(self.market_entry)
        key_layout.addLayout(market_row)
        
        mode_group = QGroupBox("📋 حالت دریافت قیمت کلید در ایران")
        mode_group.setFont(QFont("Tahoma", 10))
        mode_layout = QVBoxLayout(mode_group)
        
        self.manual_radio = QRadioButton("🔹 حالت دستی (وارد کردن عدد)")
        self.auto_radio = QRadioButton("🔸 حالت خودکار (سایت‌های پیش‌فرض)")
        self.custom_radio = QRadioButton("🔹 حالت URL دستی (هر سایت دلخواه)")
        
        for rb in [self.manual_radio, self.auto_radio, self.custom_radio]:
            rb.setFont(QFont("Tahoma", 10))
        
        self.auto_radio.setChecked(True)
        
        mode_layout.addWidget(self.manual_radio)
        mode_layout.addWidget(self.auto_radio)
        mode_layout.addWidget(self.custom_radio)
        key_layout.addWidget(mode_group)
        
        self.setup_manual_frame(key_layout)
        self.setup_auto_frame(key_layout)
        self.setup_custom_frame(key_layout)
        
        self.manual_radio.toggled.connect(lambda checked: self.set_price_mode("manual") if checked else None)
        self.auto_radio.toggled.connect(lambda checked: self.set_price_mode("auto_preset") if checked else None)
        self.custom_radio.toggled.connect(lambda checked: self.set_price_mode("custom_url") if checked else None)
        
        calc_btn = QPushButton("🧮 محاسبه نرخ تبدیل")
        calc_btn.setMinimumHeight(45)
        calc_btn.setFont(QFont("Tahoma", 11, QFont.Bold))
        calc_btn.clicked.connect(self.calculate_exchange_rate)
        key_layout.addWidget(calc_btn)
        
        layout.addWidget(key_group)
        
        # ===== نرخ تبدیل =====
        rate_group = QGroupBox("📊 نرخ تبدیل")
        rate_group.setFont(self.group_font)
        rate_layout = QVBoxLayout(rate_group)
        
        self.rate_label = QLabel("⏳ هنوز محاسبه نشده")
        self.rate_label.setFont(QFont("Tahoma", 12, QFont.Bold))
        self.rate_label.setAlignment(Qt.AlignCenter)
        rate_layout.addWidget(self.rate_label)
        
        self.net_price_label = QLabel("")
        self.net_price_label.setFont(QFont("Tahoma", 10))
        self.net_price_label.setAlignment(Qt.AlignCenter)
        rate_layout.addWidget(self.net_price_label)
        
        layout.addWidget(rate_group)
        
        # ===== قیمت بازی‌ها =====
        games_group = QGroupBox("🎮 قیمت بازی‌ها")
        games_group.setFont(self.group_font)
        games_layout = QVBoxLayout(games_group)
        
        input_row = QHBoxLayout()
        input_label = QLabel("قیمت بازی‌ها به واحد استیم (با کاما جدا کنید):")
        input_label.setFont(QFont("Tahoma", 10))
        input_row.addWidget(input_label)
        
        self.games_entry = QLineEdit()
        self.games_entry.setPlaceholderText("مثال: 1050, 2100, 3500")
        self.games_entry.setFont(QFont("Tahoma", 11))
        self.games_entry.setMinimumHeight(32)
        input_row.addWidget(self.games_entry)
        games_layout.addLayout(input_row)
        
        btn_row = QHBoxLayout()
        add_btn = QPushButton("➕ افزودن به لیست")
        add_btn.setMinimumHeight(35)
        add_btn.setFont(QFont("Tahoma", 10))
        add_btn.clicked.connect(self.add_games)
        clear_btn = QPushButton("🗑 پاک کردن لیست")
        clear_btn.setMinimumHeight(35)
        clear_btn.setFont(QFont("Tahoma", 10))
        clear_btn.clicked.connect(self.clear_games)
        btn_row.addWidget(add_btn)
        btn_row.addWidget(clear_btn)
        games_layout.addLayout(btn_row)
        
        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels([
            "💰 قیمت بازی (واحد)", "💵 قیمت به تومان", "🔑 تعداد کلید مورد نیاز"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setAlternatingRowColors(True)
        self.table.setFont(QFont("Tahoma", 10))
        self.table.setMinimumHeight(200)
        games_layout.addWidget(self.table)
        
        remove_btn = QPushButton("❌ حذف آیتم انتخاب شده")
        remove_btn.setMinimumHeight(35)
        remove_btn.setFont(QFont("Tahoma", 10))
        remove_btn.clicked.connect(self.remove_game)
        games_layout.addWidget(remove_btn)
        
        layout.addWidget(games_group)
        
        # ===== جمع‌بندی =====
        summary_group = QGroupBox("📈 جمع‌بندی")
        summary_group.setFont(self.group_font)
        summary_layout = QVBoxLayout(summary_group)
        
        self.summary_label = QLabel("📋 هیچ بازی به لیست اضافه نشده است")
        self.summary_label.setFont(QFont("Tahoma", 11, QFont.Bold))
        self.summary_label.setAlignment(Qt.AlignCenter)
        summary_layout.addWidget(self.summary_label)
        
        layout.addWidget(summary_group)
    
    def setup_manual_frame(self, parent_layout):
        self.manual_frame = QWidget()
        layout = QHBoxLayout(self.manual_frame)
        label = QLabel("💰 قیمت هر کلید در ایران (تومان):")
        label.setFont(QFont("Tahoma", 10))
        layout.addWidget(label)
        self.manual_entry = QLineEdit()
        self.manual_entry.setPlaceholderText("مثال: 320000")
        self.manual_entry.setFont(QFont("Tahoma", 11))
        self.manual_entry.setMinimumHeight(32)
        self.manual_entry.textChanged.connect(self.on_manual_price_changed)
        layout.addWidget(self.manual_entry)
        parent_layout.addWidget(self.manual_frame)
        self.manual_frame.hide()
    
    def setup_auto_frame(self, parent_layout):
        self.auto_frame = QWidget()
        layout = QHBoxLayout(self.auto_frame)
        label = QLabel("🏪 انتخاب فروشگاه:")
        label.setFont(QFont("Tahoma", 10))
        layout.addWidget(label)
        self.site_combo = QComboBox()
        self.site_combo.addItems(list(self.preset_sites.keys()))
        self.site_combo.setFont(QFont("Tahoma", 10))
        self.site_combo.setMinimumHeight(32)
        self.site_combo.currentTextChanged.connect(lambda t: setattr(self, 'selected_site', t))
        layout.addWidget(self.site_combo)
        
        self.fetch_btn = QPushButton("📥 دریافت خودکار قیمت")
        self.fetch_btn.setMinimumHeight(32)
        self.fetch_btn.setFont(QFont("Tahoma", 10))
        self.fetch_btn.clicked.connect(lambda: self.start_fetch_price("preset"))
        layout.addWidget(self.fetch_btn)
        
        self.auto_price_label = QLabel("")
        self.auto_price_label.setFont(QFont("Tahoma", 10))
        layout.addWidget(self.auto_price_label)
        parent_layout.addWidget(self.auto_frame)
    
    def setup_custom_frame(self, parent_layout):
        self.custom_frame = QWidget()
        layout = QHBoxLayout(self.custom_frame)
        label = QLabel("🌐 آدرس وب‌سایت دلخواه:")
        label.setFont(QFont("Tahoma", 10))
        layout.addWidget(label)
        self.url_entry = QLineEdit()
        self.url_entry.setPlaceholderText("https://example.com/product/")
        self.url_entry.setFont(QFont("Tahoma", 10))
        self.url_entry.setMinimumHeight(32)
        layout.addWidget(self.url_entry)
        
        self.custom_fetch_btn = QPushButton("📥 دریافت قیمت")
        self.custom_fetch_btn.setMinimumHeight(32)
        self.custom_fetch_btn.setFont(QFont("Tahoma", 10))
        self.custom_fetch_btn.clicked.connect(lambda: self.start_fetch_price("custom"))
        layout.addWidget(self.custom_fetch_btn)
        
        self.custom_price_label = QLabel("")
        self.custom_price_label.setFont(QFont("Tahoma", 10))
        layout.addWidget(self.custom_price_label)
        parent_layout.addWidget(self.custom_frame)
        self.custom_frame.hide()
    
    def setup_right_panel(self, layout):
        title = QLabel("📡 قیمت لحظه‌ای سایت‌های پیش‌فرض")
        title.setFont(QFont("Tahoma", 12, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        refresh_btn = QPushButton("🔄 بروزرسانی همه قیمت‌ها")
        refresh_btn.setMinimumHeight(35)
        refresh_btn.setFont(QFont("Tahoma", 10))
        refresh_btn.clicked.connect(self.update_all_prices)
        layout.addWidget(refresh_btn)
        
        scroll = QScrollArea()
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        
        self.site_price_labels = {}
        
        for site_key, site_info in self.preset_sites.items():
            site_group = QGroupBox(site_info["name"])
            site_group.setFont(QFont("Tahoma", 10))
            site_group_layout = QVBoxLayout(site_group)
            
            price_label = QLabel("⏳ دریافت نشده")
            price_label.setAlignment(Qt.AlignCenter)
            price_label.setFont(QFont("Tahoma", 11, QFont.Bold))
            site_group_layout.addWidget(price_label)
            
            fetch_btn = QPushButton("📥 دریافت قیمت")
            fetch_btn.setMinimumHeight(30)
            fetch_btn.clicked.connect(lambda checked, k=site_key: self.fetch_single_price(k))
            site_group_layout.addWidget(fetch_btn)
            
            scroll_layout.addWidget(site_group)
            self.site_price_labels[site_key] = price_label
        
        scroll.setWidget(scroll_widget)
        scroll.setWidgetResizable(True)
        layout.addWidget(scroll)
    
    def setup_statusbar(self):
        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)
        self.statusBar.setFont(QFont("Tahoma", 9))
        self.statusBar.showMessage("✅ آماده | انتخاب کنید: دستی / خودکار / URL دلخواه")
    
    def setup_footer(self, layout):
        footer = QFrame()
        footer.setFrameShape(QFrame.HLine)
        
        footer_layout = QVBoxLayout(footer)
        
        copyright_label = QLabel("© 2026 CopyRight : AlexWatson - All Rights Reserved")
        copyright_label.setAlignment(Qt.AlignCenter)
        copyright_label.setFont(QFont("Tahoma", 9))
        footer_layout.addWidget(copyright_label)
        
        link_layout = QHBoxLayout()
        link_layout.addStretch()
        
        github_btn = QPushButton("🐙 GitHub")
        github_btn.setFlat(True)
        github_btn.setFont(QFont("Tahoma", 9))
        github_btn.clicked.connect(lambda: self.open_url("https://github.com/alexwatson2/Steam-TF2-Toman-Calculator"))
        link_layout.addWidget(github_btn)
        
        instagram_btn = QPushButton("📷 Instagram")
        instagram_btn.setFlat(True)
        instagram_btn.setFont(QFont("Tahoma", 9))
        instagram_btn.clicked.connect(lambda: self.open_url("https://www.instagram.com/vishata_1/"))
        link_layout.addWidget(instagram_btn)
        
        telegram_btn = QPushButton("✈ Telegram")
        telegram_btn.setFlat(True)
        telegram_btn.setFont(QFont("Tahoma", 9))
        telegram_btn.clicked.connect(lambda: self.open_url("https://t.me/veshata"))
        link_layout.addWidget(telegram_btn)
        
        link_layout.addStretch()
        footer_layout.addLayout(link_layout)
        
        layout.addWidget(footer)
    
    def open_url(self, url):
        webbrowser.open(url)
    
    def get_price_from_steam_market(self):
        """دریافت قیمت از استیم مارکت با رعایت تنظیمات Proxy"""
        self.steam_market_btn.setEnabled(False)
        self.steam_market_btn.setText("در حال دریافت...")
        
        proxy_status = "با Proxy" if self.proxy_enabled else "بدون Proxy"
        self.statusBar.showMessage(f"🔄 در حال دریافت قیمت از استیم مارکت... ({proxy_status})")
        
        self.steam_market_thread = FetchSteamMarketThread(
            currency=self.current_currency,
            proxy_enabled=self.proxy_enabled,
            proxy_type=self.proxy_type,
            proxy_host=self.proxy_host,
            proxy_port=self.proxy_port,
            proxy_username=self.proxy_username,
            proxy_password=self.proxy_password,
            timeout=self.request_timeout
        )
        self.steam_market_thread.finished.connect(self.on_steam_market_price_received)
        self.steam_market_thread.status.connect(lambda msg: self.statusBar.showMessage(msg))
        self.fetch_threads.append(self.steam_market_thread)
        self.steam_market_thread.start()
    
    def on_steam_market_price_received(self, price, error):
        self.steam_market_btn.setEnabled(True)
        self.steam_market_btn.setText("🎮 دریافت از استیم مارکت")
        
        if price > 0:
            self.key_market_price = price
            self.market_entry.setText(f"{price:.2f}")
            self.statusBar.showMessage(f"✅ قیمت از استیم دریافت شد: {price:.2f} {self.current_currency}")
            QMessageBox.information(self, "موفق", f"قیمت کلید TF2 از استیم مارکت:\n{price:.2f} {self.current_currency}")
        else:
            self.statusBar.showMessage(f"❌ {error}")
            QMessageBox.warning(self, "خطا", f"دریافت قیمت از استیم مارکت:\n{error}")
    
    def set_price_mode(self, mode):
        self.price_mode = mode
        self.manual_frame.hide()
        self.auto_frame.hide()
        self.custom_frame.hide()
        
        if mode == "manual":
            self.manual_frame.show()
            self.statusBar.showMessage("✏️ حالت دستی: عدد قیمت را وارد کنید")
        elif mode == "auto_preset":
            self.auto_frame.show()
            self.statusBar.showMessage("🤖 حالت خودکار: از سایت‌های پیش‌فرض قیمت بگیرید")
        elif mode == "custom_url":
            self.custom_frame.show()
            self.statusBar.showMessage("🌐 حالت URL دستی: آدرس هر سایت دلخواه را وارد کنید")
    
    def on_market_price_changed(self):
        try:
            self.key_market_price = float(self.market_entry.text() or 0)
        except:
            self.key_market_price = 0.0
    
    def on_manual_price_changed(self):
        try:
            self.key_rial_price = float(self.manual_entry.text() or 0)
        except:
            self.key_rial_price = 0.0
    
    def start_fetch_price(self, fetch_type):
        if fetch_type == "preset":
            url = self.preset_sites[self.site_combo.currentText()]["url"]
            site_name = self.preset_sites[self.site_combo.currentText()]["name"]
            self.fetch_btn.setEnabled(False)
            self.fetch_btn.setText("در حال دریافت...")
            self.auto_price_label.setText("🔄 در حال اتصال...")
        else:
            url = self.url_entry.text().strip()
            if not url:
                QMessageBox.warning(self, "خطا", "لطفا آدرس URL را وارد کنید!")
                return
            if not url.startswith(("http://", "https://")):
                url = "https://" + url
                self.url_entry.setText(url)
            site_name = "سایت دلخواه"
            self.custom_fetch_btn.setEnabled(False)
            self.custom_fetch_btn.setText("در حال دریافت...")
            self.custom_price_label.setText("🔄 در حال اتصال...")
        
        # برای سایت‌های ایرانی بدون Proxy
        thread = FetchPriceThread(url, site_name, timeout=self.request_timeout)
        thread.finished.connect(lambda price, err: self.on_fetch_finished(price, err, fetch_type))
        thread.status.connect(lambda msg: self.statusBar.showMessage(msg))
        self.fetch_threads.append(thread)
        thread.start()
    
    def on_fetch_finished(self, price, error, fetch_type):
        if fetch_type == "preset":
            self.fetch_btn.setEnabled(True)
            self.fetch_btn.setText("📥 دریافت خودکار قیمت")
            
            if price > 0:
                self.key_rial_price = price
                self.manual_entry.setText(str(int(price)))
                self.auto_price_label.setText(f"✅ {price:,.0f} تومان")
                self.statusBar.showMessage(f"✅ قیمت دریافت شد: {price:,.0f} تومان")
                QMessageBox.information(self, "موفق", f"قیمت کلید با موفقیت دریافت شد:\n{price:,.0f} تومان")
            else:
                self.auto_price_label.setText(f"❌ {error}")
                self.statusBar.showMessage(f"❌ {error}")
                QMessageBox.warning(self, "خطا", f"{error}\nلطفا قیمت را به صورت دستی وارد کنید.")
        else:
            self.custom_fetch_btn.setEnabled(True)
            self.custom_fetch_btn.setText("📥 دریافت قیمت")
            
            if price > 0:
                self.key_rial_price = price
                self.manual_entry.setText(str(int(price)))
                self.custom_price_label.setText(f"✅ {price:,.0f} تومان")
                self.statusBar.showMessage(f"✅ قیمت دریافت شد: {price:,.0f} تومان")
                QMessageBox.information(self, "موفق", f"قیمت کلید با موفقیت دریافت شد:\n{price:,.0f} تومان")
            else:
                self.custom_price_label.setText(f"❌ {error}")
                self.statusBar.showMessage(f"❌ {error}")
                QMessageBox.warning(self, "خطا", f"{error}\nلطفا قیمت را به صورت دستی وارد کنید.")
    
    def fetch_single_price(self, site_key):
        url = self.preset_sites[site_key]["url"]
        label = self.site_price_labels[site_key]
        label.setText("🔄 در حال دریافت...")
        
        thread = FetchPriceThread(url, site_key, timeout=self.request_timeout)
        thread.finished.connect(lambda price, err, l=label: self.on_single_fetch_finished(price, err, l))
        self.fetch_threads.append(thread)
        thread.start()
    
    def on_single_fetch_finished(self, price, error, label):
        if price > 0:
            label.setText(f"💰 {price:,.0f} تومان")
        else:
            label.setText(f"❌ {error}")
    
    def update_all_prices(self):
        for site_key in self.preset_sites:
            self.fetch_single_price(site_key)
    
    def calculate_exchange_rate(self):
        try:
            if self.key_rial_price <= 0:
                QMessageBox.warning(self, "اخطار", "⚠️ لطفا ابتدا قیمت کلید را وارد کنید!")
                return
            if self.key_market_price <= 0:
                QMessageBox.warning(self, "اخطار", "⚠️ لطفا قیمت کلید در مارکت استیم را وارد کنید!")
                return
            
            net_price = self.key_market_price * 0.85
            exchange_rate = self.key_rial_price / net_price
            
            self.key_net_price = net_price
            self.exchange_rate = exchange_rate
            
            self.rate_label.setText(f"💰 هر 1 واحد استیم = {exchange_rate:,.2f} تومان")
            self.net_price_label.setText(f"🔑 قیمت خالص هر کلید (پس از کسر ۱۵٪ کارمزد): {net_price:.2f} {self.current_currency}")
            self.statusBar.showMessage(f"✅ نرخ تبدیل محاسبه شد: 1 واحد = {exchange_rate:,.2f} تومان")
            
        except Exception as e:
            QMessageBox.critical(self, "خطا", f"❌ ورودی نامعتبر: {str(e)}")
    
    def add_games(self):
        if self.exchange_rate == 0:
            QMessageBox.warning(self, "اخطار", "⚠️ لطفا ابتدا نرخ تبدیل را محاسبه کنید!")
            return
        
        games_text = self.games_entry.text().strip()
        if not games_text:
            QMessageBox.warning(self, "اخطار", "⚠️ لطفا قیمت بازی‌ها را وارد کنید!")
            return
        
        try:
            game_prices = [float(x.strip()) for x in games_text.split(',')]
            row = self.table.rowCount()
            self.table.setRowCount(row + len(game_prices))
            
            for i, price in enumerate(game_prices):
                price_rial = price * self.exchange_rate
                keys_needed = price / self.key_net_price
                
                self.table.setItem(row + i, 0, QTableWidgetItem(f"{price:,.0f}"))
                self.table.setItem(row + i, 1, QTableWidgetItem(f"{price_rial:,.0f}"))
                self.table.setItem(row + i, 2, QTableWidgetItem(f"{keys_needed:.2f}"))
                
            self.games_entry.clear()
            self.update_summary()
            self.statusBar.showMessage(f"✅ {len(game_prices)} بازی به لیست اضافه شد")
            
        except Exception as e:
            QMessageBox.critical(self, "خطا", f"❌ قیمت بازی نامعتبر: {str(e)}")
    
    def remove_game(self):
        selected = self.table.currentRow()
        if selected < 0:
            QMessageBox.warning(self, "اخطار", "⚠️ لطفا یک بازی را برای حذف انتخاب کنید!")
            return
        
        self.table.removeRow(selected)
        self.update_summary()
        self.statusBar.showMessage("🗑 بازی انتخاب شده حذف شد")
    
    def clear_games(self):
        self.table.setRowCount(0)
        self.update_summary()
        self.statusBar.showMessage("🗑 لیست بازی‌ها پاک شد")
    
    def update_summary(self):
        row_count = self.table.rowCount()
        if row_count == 0:
            self.summary_label.setText("📋 هیچ بازی به لیست اضافه نشده است")
            return
        
        total_toman = 0
        for row in range(row_count):
            item = self.table.item(row, 1)
            if item:
                toman_str = item.text().replace(",", "")
                total_toman += float(toman_str)
        
        self.summary_label.setText(f"💰 جمع کل قیمت بازی‌ها: {total_toman:,.0f} تومان ({total_toman/10:,.0f} هزار تومان)")
    
    def change_theme(self, theme_name):
        self.current_theme = theme_name
        themes = {
            "light": """
                QMainWindow { background-color: #f0f0f0; }
                QWidget { background-color: #f0f0f0; color: #000000; }
                QGroupBox { font-weight: bold; border: 1px solid #ccc; border-radius: 8px; margin-top: 12px; }
                QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 8px 0 8px; }
                QPushButton { background-color: #e0e0e0; border: 1px solid #ccc; border-radius: 5px; padding: 8px; }
                QPushButton:hover { background-color: #0078d4; color: white; }
                QLineEdit, QComboBox { border: 1px solid #ccc; border-radius: 5px; padding: 6px; }
                QTableWidget { alternate-background-color: #e8e8e8; gridline-color: #ddd; }
                QHeaderView::section { background-color: #d0d0d0; padding: 8px; }
            """,
            "dark": """
                QMainWindow { background-color: #1e1e1e; }
                QWidget { background-color: #1e1e1e; color: #ffffff; }
                QGroupBox { font-weight: bold; border: 1px solid #555; border-radius: 8px; margin-top: 12px; color: #ffffff; }
                QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 8px 0 8px; }
                QPushButton { background-color: #3c3c3c; border: 1px solid #555; border-radius: 5px; padding: 8px; color: #ffffff; }
                QPushButton:hover { background-color: #0078d4; }
                QLineEdit, QComboBox { background-color: #3c3c3c; border: 1px solid #555; border-radius: 5px; padding: 6px; color: #ffffff; }
                QTableWidget { background-color: #252526; alternate-background-color: #2d2d2d; color: #ffffff; gridline-color: #444; }
                QHeaderView::section { background-color: #3c3c3c; color: #ffffff; padding: 8px; }
            """,
            "gray": """
                QMainWindow { background-color: #2b2b2b; }
                QWidget { background-color: #2b2b2b; color: #e0e0e0; }
                QGroupBox { font-weight: bold; border: 1px solid #666; border-radius: 8px; margin-top: 12px; }
                QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 8px 0 8px; }
                QPushButton { background-color: #4a4a4a; border: 1px solid #666; border-radius: 5px; padding: 8px; }
                QPushButton:hover { background-color: #0078d4; }
                QLineEdit, QComboBox { background-color: #4a4a4a; border: 1px solid #666; border-radius: 5px; padding: 6px; }
                QTableWidget { background-color: #333333; alternate-background-color: #3d3d3d; color: #e0e0e0; gridline-color: #555; }
                QHeaderView::section { background-color: #4a4a4a; color: #e0e0e0; padding: 8px; }
            """,
            "steam": """
                QMainWindow { background-color: #1a1a2e; }
                QWidget { background-color: #1a1a2e; color: #c3d4e6; }
                QGroupBox { font-weight: bold; border: 1px solid #0f3460; border-radius: 8px; margin-top: 12px; color: #00adb5; }
                QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 8px 0 8px; }
                QPushButton { background-color: #0f3460; border: 1px solid #16213e; border-radius: 5px; padding: 8px; color: #c3d4e6; min-height: 30px; }
                QPushButton:hover { background-color: #00adb5; color: #1a1a2e; }
                QLineEdit, QComboBox { background-color: #0f3460; border: 1px solid #16213e; border-radius: 5px; padding: 6px; color: #c3d4e6; }
                QTableWidget { background-color: #16213e; alternate-background-color: #1a1a2e; color: #c3d4e6; gridline-color: #0f3460; }
                QHeaderView::section { background-color: #0f3460; color: #00adb5; padding: 8px; }
                QTableWidget::item:selected { background-color: #00adb5; color: #1a1a2e; }
                QScrollArea { background-color: #1a1a2e; border: none; }
                QScrollBar:vertical { background-color: #16213e; width: 12px; }
                QScrollBar::handle:vertical { background-color: #0f3460; border-radius: 6px; }
                QScrollBar::handle:vertical:hover { background-color: #00adb5; }
            """
        }
        
        self.setStyleSheet(themes.get(theme_name, themes["steam"]))
        self.save_settings()
        self.statusBar.showMessage(f"🎨 تم تغییر کرد: {theme_name}")
    
    def apply_theme(self):
        self.change_theme(self.current_theme)
    
    def save_settings(self):
        config = {
            "last_theme": self.current_theme,
            "last_market_price": self.key_market_price,
            "current_currency": self.current_currency,
            "current_currency_symbol": self.current_currency_symbol,
            "current_country_display": self.current_country_display,
            "request_timeout": self.request_timeout,
            "auto_save_settings": self.auto_save_settings,
            "proxy_enabled": self.proxy_enabled,
            "proxy_type": self.proxy_type,
            "proxy_host": self.proxy_host,
            "proxy_port": self.proxy_port,
            "proxy_username": self.proxy_username,
            "proxy_password": self.proxy_password
        }
        try:
            with open("steam_calculator_config.json", "w", encoding="utf-8") as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
        except:
            pass
    
    def load_settings(self):
        config_file = "steam_calculator_config.json"
        if os.path.exists(config_file):
            try:
                with open(config_file, "r", encoding="utf-8") as f:
                    config = json.load(f)
                    if "last_theme" in config:
                        self.current_theme = config["last_theme"]
                    if "last_market_price" in config:
                        self.market_entry.setText(str(config["last_market_price"]))
                    if "current_currency" in config:
                        self.current_currency = config["current_currency"]
                    if "current_currency_symbol" in config:
                        self.current_currency_symbol = config["current_currency_symbol"]
                    if "current_country_display" in config:
                        self.current_country_display = config["current_country_display"]
                    if "request_timeout" in config:
                        self.request_timeout = config["request_timeout"]
                    if "auto_save_settings" in config:
                        self.auto_save_settings = config["auto_save_settings"]
                    if "proxy_enabled" in config:
                        self.proxy_enabled = config["proxy_enabled"]
                    if "proxy_type" in config:
                        self.proxy_type = config["proxy_type"]
                    if "proxy_host" in config:
                        self.proxy_host = config["proxy_host"]
                    if "proxy_port" in config:
                        self.proxy_port = config["proxy_port"]
                    if "proxy_username" in config:
                        self.proxy_username = config["proxy_username"]
                    if "proxy_password" in config:
                        self.proxy_password = config["proxy_password"]
            except:
                pass


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SteamPriceCalculator()
    window.show()
    sys.exit(app.exec_())

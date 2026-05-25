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
    QStatusBar, QScrollArea
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QFont


class FetchPriceThread(QThread):
    """Thread برای دریافت قیمت از سایت بدون هنگ کردن برنامه"""
    finished = pyqtSignal(float, str)
    status = pyqtSignal(str)
    
    def __init__(self, url, site_name):
        super().__init__()
        self.url = url
        self.site_name = site_name
    
    def run(self):
        try:
            self.status.emit(f"در حال اتصال به {self.site_name}...")
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            }
            
            response = requests.get(self.url, headers=headers, timeout=20)
            response.raise_for_status()
            
            self.status.emit(f"در حال تجزیه صفحه {self.site_name}...")
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
        """استخراج قیمت از صفحه HTML"""
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
    """کلاس اصلی نرم‌افزار با PyQt5"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Welcome - Steam Price Calculator")
        self.setMinimumSize(1250, 850)
        self.resize(1350, 960)
        
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
    
    def setup_ui(self):
        """راه‌اندازی رابط کاربری"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        # نوار ابزار
        self.setup_toolbar(main_layout)
        
        # اسپلیتر برای دو بخش چپ و راست
        splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(splitter)
        
        # بخش چپ
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        self.setup_left_panel(left_layout)
        splitter.addWidget(left_widget)
        
        # بخش راست
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        self.setup_right_panel(right_layout)
        splitter.addWidget(right_widget)
        
        # تنظیم نسبت اندازه
        splitter.setSizes([850, 400])
        
        # نوار وضعیت و فوتر
        self.setup_statusbar()
        self.setup_footer(main_layout)
    
    def setup_toolbar(self, layout):
        """نوار ابزار بالایی"""
        toolbar = QHBoxLayout()
        
        title = QLabel("🎮 ماشین حساب قیمت بازی های که با کلید خریداری میشن")
        title.setFont(QFont("Tahoma", 12, QFont.Bold))
        toolbar.addWidget(title)
        
        toolbar.addStretch()
        
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
        steam_btn.clicked.connect(lambda: self.change_theme("light"))
        toolbar.addWidget(steam_btn)
        
        layout.addLayout(toolbar)
    
    def setup_left_panel(self, layout):
        """بخش چپ - فرم اصلی"""
        
        # ===== بخش اطلاعات کلید =====
        key_group = QGroupBox("🔑 اطلاعات کلید")
        key_layout = QVBoxLayout(key_group)
        
        # قیمت مارکت استیم
        market_row = QHBoxLayout()
        market_row.addWidget(QLabel("💰 قیمت هر کلید در مارکت استیم (واحد):"))
        self.market_entry = QLineEdit()
        self.market_entry.setPlaceholderText("مثال: 2.15")
        self.market_entry.textChanged.connect(self.on_market_price_changed)
        market_row.addWidget(self.market_entry)
        key_layout.addLayout(market_row)
        
        # حالت دریافت قیمت
        mode_group = QGroupBox("📋 حالت دریافت قیمت کلید در ایران")
        mode_layout = QVBoxLayout(mode_group)
        
        self.manual_radio = QRadioButton("🔹 حالت دستی (وارد کردن عدد)")
        self.auto_radio = QRadioButton("🔸 حالت خودکار (سایت‌های پیش‌فرض)")
        self.custom_radio = QRadioButton("🔹 حالت URL دستی (هر سایت دلخواه)")
        
        self.auto_radio.setChecked(True)
        
        mode_layout.addWidget(self.manual_radio)
        mode_layout.addWidget(self.auto_radio)
        mode_layout.addWidget(self.custom_radio)
        key_layout.addWidget(mode_group)
        
        # === ساخت فریم‌ها ===
        self.setup_manual_frame(key_layout)
        self.setup_auto_frame(key_layout)
        self.setup_custom_frame(key_layout)
        
        # === اتصال سیگنال بعد از ساخت فریم‌ها ===
        self.manual_radio.toggled.connect(lambda checked: self.set_price_mode("manual") if checked else None)
        self.auto_radio.toggled.connect(lambda checked: self.set_price_mode("auto_preset") if checked else None)
        self.custom_radio.toggled.connect(lambda checked: self.set_price_mode("custom_url") if checked else None)
        
        # دکمه محاسبه
        calc_btn = QPushButton("🧮 محاسبه نرخ تبدیل")
        calc_btn.clicked.connect(self.calculate_exchange_rate)
        calc_btn.setMinimumHeight(40)
        key_layout.addWidget(calc_btn)
        
        layout.addWidget(key_group)
        
        # ===== نرخ تبدیل =====
        rate_group = QGroupBox("📊 نرخ تبدیل")
        rate_layout = QVBoxLayout(rate_group)
        
        self.rate_label = QLabel("هنوز محاسبه نشده")
        self.rate_label.setFont(QFont("Tahoma", 11, QFont.Bold))
        self.rate_label.setAlignment(Qt.AlignCenter)
        rate_layout.addWidget(self.rate_label)
        
        self.net_price_label = QLabel("")
        self.net_price_label.setAlignment(Qt.AlignCenter)
        rate_layout.addWidget(self.net_price_label)
        
        layout.addWidget(rate_group)
        
        # ===== قیمت بازی‌ها =====
        games_group = QGroupBox("🎮 قیمت بازی‌ها")
        games_layout = QVBoxLayout(games_group)
        
        input_row = QHBoxLayout()
        input_row.addWidget(QLabel("قیمت بازی‌ها به واحد استیم (با کاما جدا کنید):"))
        self.games_entry = QLineEdit()
        self.games_entry.setPlaceholderText("مثال: 1050, 2100, 3500")
        input_row.addWidget(self.games_entry)
        games_layout.addLayout(input_row)
        
        btn_row = QHBoxLayout()
        add_btn = QPushButton("➕ افزودن به لیست")
        add_btn.clicked.connect(self.add_games)
        clear_btn = QPushButton("🗑 پاک کردن لیست")
        clear_btn.clicked.connect(self.clear_games)
        btn_row.addWidget(add_btn)
        btn_row.addWidget(clear_btn)
        games_layout.addLayout(btn_row)
        
        # جدول
        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels([
            "💰 قیمت بازی (واحد)", 
            "💵 قیمت به تومان", 
            "🔑 تعداد کلید مورد نیاز"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setAlternatingRowColors(True)
        games_layout.addWidget(self.table)
        
        remove_btn = QPushButton("❌ حذف آیتم انتخاب شده")
        remove_btn.clicked.connect(self.remove_game)
        games_layout.addWidget(remove_btn)
        
        layout.addWidget(games_group)
        
        # ===== جمع‌بندی =====
        summary_group = QGroupBox("📈 جمع‌بندی")
        summary_layout = QVBoxLayout(summary_group)
        
        self.summary_label = QLabel("📋 هیچ بازی به لیست اضافه نشده است")
        self.summary_label.setAlignment(Qt.AlignCenter)
        self.summary_label.setFont(QFont("Tahoma", 10, QFont.Bold))
        summary_layout.addWidget(self.summary_label)
        
        layout.addWidget(summary_group)
    
    def setup_manual_frame(self, parent_layout):
        """ساخت فریم حالت دستی"""
        self.manual_frame = QWidget()
        layout = QHBoxLayout(self.manual_frame)
        layout.addWidget(QLabel("💰 قیمت هر کلید در ایران (تومان):"))
        self.manual_entry = QLineEdit()
        self.manual_entry.setPlaceholderText("مثال: 320000")
        self.manual_entry.textChanged.connect(self.on_manual_price_changed)
        layout.addWidget(self.manual_entry)
        parent_layout.addWidget(self.manual_frame)
        self.manual_frame.hide()
    
    def setup_auto_frame(self, parent_layout):
        """ساخت فریم حالت خودکار"""
        self.auto_frame = QWidget()
        layout = QHBoxLayout(self.auto_frame)
        layout.addWidget(QLabel("🏪 انتخاب فروشگاه:"))
        self.site_combo = QComboBox()
        self.site_combo.addItems(list(self.preset_sites.keys()))
        self.site_combo.currentTextChanged.connect(lambda t: setattr(self, 'selected_site', t))
        layout.addWidget(self.site_combo)
        
        self.fetch_btn = QPushButton("📥 دریافت خودکار قیمت")
        self.fetch_btn.clicked.connect(lambda: self.start_fetch_price("preset"))
        layout.addWidget(self.fetch_btn)
        
        self.auto_price_label = QLabel("")
        layout.addWidget(self.auto_price_label)
        parent_layout.addWidget(self.auto_frame)
    
    def setup_custom_frame(self, parent_layout):
        """ساخت فریم حالت URL دستی"""
        self.custom_frame = QWidget()
        layout = QHBoxLayout(self.custom_frame)
        layout.addWidget(QLabel("🌐 آدرس وب‌سایت دلخواه:"))
        self.url_entry = QLineEdit()
        self.url_entry.setPlaceholderText("https://example.com/product/")
        layout.addWidget(self.url_entry)
        
        self.custom_fetch_btn = QPushButton("📥 دریافت قیمت")
        self.custom_fetch_btn.clicked.connect(lambda: self.start_fetch_price("custom"))
        layout.addWidget(self.custom_fetch_btn)
        
        self.custom_price_label = QLabel("")
        layout.addWidget(self.custom_price_label)
        parent_layout.addWidget(self.custom_frame)
        self.custom_frame.hide()
    
    def setup_right_panel(self, layout):
        """بخش راست - نمایش قیمت سایت‌ها"""
        
        title = QLabel("📡 قیمت لحظه‌ای سایت‌های پیش‌فرض")
        title.setFont(QFont("Tahoma", 11, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        refresh_btn = QPushButton("🔄 بروزرسانی همه قیمت‌ها")
        refresh_btn.clicked.connect(self.update_all_prices)
        layout.addWidget(refresh_btn)
        
        scroll = QScrollArea()
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        
        self.site_price_labels = {}
        
        for site_key, site_info in self.preset_sites.items():
            site_group = QGroupBox(site_info["name"])
            site_group_layout = QVBoxLayout(site_group)
            
            price_label = QLabel("⏳ دریافت نشده")
            price_label.setAlignment(Qt.AlignCenter)
            price_label.setFont(QFont("Tahoma", 10, QFont.Bold))
            site_group_layout.addWidget(price_label)
            
            fetch_btn = QPushButton("📥 دریافت قیمت")
            fetch_btn.clicked.connect(lambda checked, k=site_key: self.fetch_single_price(k))
            site_group_layout.addWidget(fetch_btn)
            
            scroll_layout.addWidget(site_group)
            self.site_price_labels[site_key] = price_label
        
        scroll.setWidget(scroll_widget)
        scroll.setWidgetResizable(True)
        layout.addWidget(scroll)
    
    def setup_statusbar(self):
        """نوار وضعیت پایین"""
        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)
        self.statusBar.showMessage("✅ آماده | انتخاب کنید: دستی / خودکار / URL دلخواه")
    
    def setup_footer(self, layout):
        """فوتر با لینک‌های قابل کلیک"""
        footer = QFrame()
        footer.setFrameShape(QFrame.HLine)
        
        footer_layout = QVBoxLayout(footer)
        
        copyright_label = QLabel("© 2026 CopyRight : AlexWatson - All Rights Reserved")
        copyright_label.setAlignment(Qt.AlignCenter)
        copyright_label.setFont(QFont("Tahoma", 8))
        footer_layout.addWidget(copyright_label)
        
        link_layout = QHBoxLayout()
        link_layout.addStretch()
        
        github_btn = QPushButton("🐙 GitHub")
        github_btn.setFlat(True)
        github_btn.clicked.connect(lambda: self.open_url("https://github.com/alexwatson2/"))
        link_layout.addWidget(github_btn)
        
        instagram_btn = QPushButton("📷 Instagram")
        instagram_btn.setFlat(True)
        instagram_btn.clicked.connect(lambda: self.open_url("https://www.instagram.com/vishata_1/"))
        link_layout.addWidget(instagram_btn)
        
        telegram_btn = QPushButton("✈ Telegram")
        telegram_btn.setFlat(True)
        telegram_btn.clicked.connect(lambda: self.open_url("https://t.me/veshata"))
        link_layout.addWidget(telegram_btn)
        
        link_layout.addStretch()
        footer_layout.addLayout(link_layout)
        
        layout.addWidget(footer)
    
    def open_url(self, url):
        """باز کردن لینک در مرورگر"""
        webbrowser.open(url)
    
    def set_price_mode(self, mode):
        """تغییر حالت دریافت قیمت"""
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
        """تغییر قیمت مارکت استیم"""
        try:
            self.key_market_price = float(self.market_entry.text() or 0)
        except:
            self.key_market_price = 0.0
    
    def on_manual_price_changed(self):
        """تغییر قیمت دستی"""
        try:
            self.key_rial_price = float(self.manual_entry.text() or 0)
        except:
            self.key_rial_price = 0.0
    
    def start_fetch_price(self, fetch_type):
        """شروع دریافت قیمت"""
        
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
        
        thread = FetchPriceThread(url, site_name)
        thread.finished.connect(lambda price, err: self.on_fetch_finished(price, err, fetch_type))
        thread.status.connect(lambda msg: self.statusBar.showMessage(msg))
        self.fetch_threads.append(thread)
        thread.start()
    
    def on_fetch_finished(self, price, error, fetch_type):
        """پایان دریافت قیمت"""
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
        """دریافت قیمت یک سایت خاص برای بخش راست"""
        url = self.preset_sites[site_key]["url"]
        label = self.site_price_labels[site_key]
        label.setText("🔄 در حال دریافت...")
        
        thread = FetchPriceThread(url, site_key)
        thread.finished.connect(lambda price, err, l=label: self.on_single_fetch_finished(price, err, l))
        self.fetch_threads.append(thread)
        thread.start()
    
    def on_single_fetch_finished(self, price, error, label):
        if price > 0:
            label.setText(f"💰 {price:,.0f} تومان")
        else:
            label.setText(f"❌ {error}")
    
    def update_all_prices(self):
        """بروزرسانی همه قیمت‌ها"""
        for site_key in self.preset_sites:
            self.fetch_single_price(site_key)
    
    def calculate_exchange_rate(self):
        """محاسبه نرخ تبدیل"""
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
            self.net_price_label.setText(f"🔑 قیمت خالص هر کلید (پس از کسر ۱۵٪ کارمزد): {net_price:.2f} واحد")
            self.statusBar.showMessage(f"✅ نرخ تبدیل محاسبه شد: 1 واحد = {exchange_rate:,.2f} تومان")
            
        except Exception as e:
            QMessageBox.critical(self, "خطا", f"❌ ورودی نامعتبر: {str(e)}")
    
    def add_games(self):
        """افزودن بازی به جدول"""
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
        """حذف بازی انتخاب شده"""
        selected = self.table.currentRow()
        if selected < 0:
            QMessageBox.warning(self, "اخطار", "⚠️ لطفا یک بازی را برای حذف انتخاب کنید!")
            return
        
        self.table.removeRow(selected)
        self.update_summary()
        self.statusBar.showMessage("🗑 بازی انتخاب شده حذف شد")
    
    def clear_games(self):
        """پاک کردن همه بازی‌ها"""
        self.table.setRowCount(0)
        self.update_summary()
        self.statusBar.showMessage("🗑 لیست بازی‌ها پاک شد")
    
    def update_summary(self):
        """به‌روزرسانی جمع‌بندی"""
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
    
    def load_settings(self):
        """بارگذاری تنظیمات"""
        config_file = "steam_calculator_config.json"
        if os.path.exists(config_file):
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    if "last_market_price" in config:
                        self.market_entry.setText(str(config["last_market_price"]))
                    if "last_theme" in config:
                        self.change_theme(config["last_theme"])
            except:
                pass
    
    def apply_theme(self):
        """اعمال تم پیش‌فرض"""
        self.change_theme("steam")
    
    def change_theme(self, theme_name):
        """تغییر تم"""
        themes = {
            "light": """
                QMainWindow { background-color: #f0f0f0; }
                QWidget { background-color: #f0f0f0; color: #000000; }
                QGroupBox { font-weight: bold; border: 1px solid #ccc; border-radius: 5px; margin-top: 10px; }
                QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 5px 0 5px; }
                QPushButton { background-color: #e0e0e0; border: 1px solid #ccc; border-radius: 3px; padding: 5px; }
                QPushButton:hover { background-color: #0078d4; color: white; }
                QLineEdit, QComboBox { border: 1px solid #ccc; border-radius: 3px; padding: 3px; }
                QTableWidget { alternate-background-color: #e8e8e8; }
                QHeaderView::section { background-color: #d0d0d0; }
            """,
            "dark": """
                QMainWindow { background-color: #1e1e1e; }
                QWidget { background-color: #1e1e1e; color: #ffffff; }
                QGroupBox { font-weight: bold; border: 1px solid #555; border-radius: 5px; margin-top: 10px; color: #ffffff; }
                QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 5px 0 5px; }
                QPushButton { background-color: #3c3c3c; border: 1px solid #555; border-radius: 3px; padding: 5px; color: #ffffff; }
                QPushButton:hover { background-color: #0078d4; }
                QLineEdit, QComboBox { background-color: #3c3c3c; border: 1px solid #555; border-radius: 3px; padding: 3px; color: #ffffff; }
                QTableWidget { background-color: #252526; alternate-background-color: #2d2d2d; color: #ffffff; }
                QHeaderView::section { background-color: #3c3c3c; color: #ffffff; }
            """,
            "gray": """
                QMainWindow { background-color: #2b2b2b; }
                QWidget { background-color: #2b2b2b; color: #e0e0e0; }
                QGroupBox { font-weight: bold; border: 1px solid #666; border-radius: 5px; margin-top: 10px; }
                QPushButton { background-color: #4a4a4a; border: 1px solid #666; border-radius: 3px; padding: 5px; }
                QPushButton:hover { background-color: #0078d4; }
                QLineEdit, QComboBox { background-color: #4a4a4a; border: 1px solid #666; border-radius: 3px; padding: 3px; }
                QTableWidget { background-color: #333333; alternate-background-color: #3d3d3d; color: #e0e0e0; }
                QHeaderView::section { background-color: #4a4a4a; }
            """,
            "steam": """
                QMainWindow { background-color: #1a1a2e; }
                QWidget { background-color: #1a1a2e; color: #c3d4e6; }
                QGroupBox { font-weight: bold; border: 1px solid #0f3460; border-radius: 5px; margin-top: 10px; color: #00adb5; }
                QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 5px 0 5px; }
                QPushButton { background-color: #0f3460; border: 1px solid #16213e; border-radius: 3px; padding: 5px; color: #c3d4e6; min-height: 25px; }
                QPushButton:hover { background-color: #00adb5; color: #1a1a2e; }
                QLineEdit, QComboBox { background-color: #0f3460; border: 1px solid #16213e; border-radius: 3px; padding: 5px; color: #c3d4e6; }
                QTableWidget { background-color: #16213e; alternate-background-color: #1a1a2e; color: #c3d4e6; gridline-color: #0f3460; }
                QHeaderView::section { background-color: #0f3460; color: #00adb5; padding: 5px; }
                QTableWidget::item:selected { background-color: #00adb5; color: #1a1a2e; }
                QScrollArea { background-color: #1a1a2e; border: none; }
                QScrollBar:vertical { background-color: #16213e; width: 12px; }
                QScrollBar::handle:vertical { background-color: #0f3460; border-radius: 6px; }
                QScrollBar::handle:vertical:hover { background-color: #00adb5; }
            """
        }
        
        self.setStyleSheet(themes.get(theme_name, themes["steam"]))
        
        try:
            config = {}
            if os.path.exists("steam_calculator_config.json"):
                with open("steam_calculator_config.json", 'r', encoding='utf-8') as f:
                    config = json.load(f)
            config["last_theme"] = theme_name
            with open("steam_calculator_config.json", 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
        except:
            pass
        
        self.statusBar.showMessage(f"🎨 تم تغییر کرد: {theme_name}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SteamPriceCalculator()
    window.show()
    sys.exit(app.exec_())

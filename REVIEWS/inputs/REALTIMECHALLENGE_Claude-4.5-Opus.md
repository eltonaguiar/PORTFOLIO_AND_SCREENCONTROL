Claude 4.5 Opus - AWS Bedrock US (236.315s - 2,735,387 credits)
Trading Challenge: Comprehensive Development Plan
Initial Setup Complete ✓
I've created the challenge definition file and will now proceed with the detailed 200-round development plan.

PHASE 1: FOUNDATION (Rounds 1-25)
Round 1: Desktop Control & Agent Orchestration Framework ✅
Based on your answers, here's the recommended stack:

Recommended Architecture for Windows Desktop Control
┌─────────────────────────────────────────────────────────────────┐
│                    ORCHESTRATION LAYER                          │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │  Agent Runtime (Durable, Queue-based, Unattended)           ││
│  │  - Celery + Redis OR                                        ││
│  │  - Temporal.io (free self-hosted) OR                        ││
│  │  - Simple Python asyncio with persistence                   ││
│  └─────────────────────────────────────────────────────────────┘│
├─────────────────────────────────────────────────────────────────┤
│                    DESKTOP CONTROL LAYER                        │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────────────────┐│
│  │ PyAutoGUI    │ │ pywinauto    │ │ UI Automation (Windows)  ││
│  │ (clicks/keys)│ │ (app control)│ │ (accessibility trees)    ││
│  └──────────────┘ └──────────────┘ └──────────────────────────┘│
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────────────────┐│
│  │ Playwright   │ │ Selenium     │ │ mss (screenshots)        ││
│  │ (browser)    │ │ (browser)    │ │ + Vision AI              ││
│  └──────────────┘ └──────────────┘ └──────────────────────────┘│
├─────────────────────────────────────────────────────────────────┤
│                    REMOTE SESSION LAYER                         │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │  RustDesk/RDP Control via:                                  ││
│  │  - pywinauto targeting RustDesk window                      ││
│  │  - OR agent-rdp for RDP sessions                            ││
│  │  - OR SSH + xdotool for Linux targets                       ││
│  └─────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────┘
Core Python Libraries to Install
# Desktop Control Stack
pip install pyautogui pywinauto mss pillow

# Browser Automation
pip install playwright selenium webdriver-manager

# AI/Vision
pip install openai anthropic transformers torch torchvision

# Task Queue & Persistence
pip install celery redis sqlalchemy

# Screen OCR
pip install pytesseract easyocr

# Backtesting (install all major ones)
pip install vectorbt backtesting backtrader bt qstrader lumibot yfinance pandas-ta
Round 2: Create Universal Desktop Agent Framework
File: universal_desktop_agent.py

"""
Universal Desktop Agent Framework
Supports: Windows apps, browsers, VS Code, RustDesk, RDP sessions
"""

import pyautogui
import pywinauto
from pywinauto import Application, Desktop
import mss
import time
import json
import os
from datetime import datetime
from pathlib import Path
import subprocess
import threading
from queue import Queue
import logging

# Configure safety
pyautogui.FAILSAFE = True  # Move mouse to corner to abort
pyautogui.PAUSE = 0.5  # Pause between actions

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("DesktopAgent")


class ScreenCapture:
    """Fast screen capture with mss"""
    
    def __init__(self):
        self.sct = mss.mss()
    
    def capture_full(self):
        """Capture full screen"""
        return self.sct.grab(self.sct.monitors[0])
    
    def capture_region(self, x, y, width, height):
        """Capture specific region"""
        region = {"left": x, "top": y, "width": width, "height": height}
        return self.sct.grab(region)
    
    def save_screenshot(self, filename=None):
        """Save screenshot to file"""
        if filename is None:
            filename = f"screenshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        img = self.capture_full()
        mss.tools.to_png(img.rgb, img.size, output=filename)
        return filename


class WindowController:
    """Control Windows applications via UI Automation"""
    
    def __init__(self):
        self.desktop = Desktop(backend="uia")
    
    def list_windows(self):
        """List all open windows"""
        windows = []
        for win in self.desktop.windows():
            try:
                windows.append({
                    "title": win.window_text(),
                    "class": win.class_name(),
                    "handle": win.handle
                })
            except:
                pass
        return windows
    
    def find_window(self, title_contains=None, class_name=None):
        """Find window by title or class"""
        for win in self.desktop.windows():
            try:
                if title_contains and title_contains.lower() in win.window_text().lower():
                    return win
                if class_name and class_name == win.class_name():
                    return win
            except:
                pass
        return None
    
    def focus_window(self, window):
        """Bring window to foreground"""
        try:
            window.set_focus()
            return True
        except Exception as e:
            logger.error(f"Failed to focus window: {e}")
            return False
    
    def get_window_elements(self, window, max_depth=3):
        """Get accessibility tree elements"""
        elements = []
        try:
            def traverse(ctrl, depth=0):
                if depth > max_depth:
                    return
                try:
                    elements.append({
                        "name": ctrl.window_text(),
                        "type": ctrl.friendly_class_name(),
                        "rect": ctrl.rectangle(),
                        "depth": depth
                    })
                    for child in ctrl.children():
                        traverse(child, depth + 1)
                except:
                    pass
            traverse(window)
        except Exception as e:
            logger.error(f"Error traversing elements: {e}")
        return elements


class BrowserController:
    """Control browser via Playwright or Selenium"""
    
    def __init__(self, browser_type="playwright"):
        self.browser_type = browser_type
        self.browser = None
        self.page = None
    
    def start_playwright(self, headless=False):
        """Start Playwright browser"""
        from playwright.sync_api import sync_playwright
        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch(headless=headless)
        self.context = self.browser.new_context()
        self.page = self.context.new_page()
        return self.page
    
    def navigate(self, url):
        """Navigate to URL"""
        if self.page:
            self.page.goto(url)
    
    def click_element(self, selector):
        """Click element by selector"""
        if self.page:
            self.page.click(selector)
    
    def type_text(self, selector, text):
        """Type text into element"""
        if self.page:
            self.page.fill(selector, text)
    
    def get_text(self, selector):
        """Get text from element"""
        if self.page:
            return self.page.text_content(selector)
        return None
    
    def screenshot(self, path):
        """Take browser screenshot"""
        if self.page:
            self.page.screenshot(path=path)
    
    def close(self):
        """Close browser"""
        if self.browser:
            self.browser.close()
        if hasattr(self, 'playwright'):
            self.playwright.stop()


class RustDeskController:
    """Control RustDesk remote desktop session"""
    
    def __init__(self, window_controller):
        self.wc = window_controller
        self.rustdesk_window = None
    
    def find_rustdesk(self):
        """Find RustDesk window"""
        self.rustdesk_window = self.wc.find_window(title_contains="RustDesk")
        return self.rustdesk_window is not None
    
    def focus_rustdesk(self):
        """Focus RustDesk window"""
        if self.rustdesk_window:
            return self.wc.focus_window(self.rustdesk_window)
        return False
    
    def send_keys_to_remote(self, keys):
        """Send keystrokes to remote session"""
        if self.focus_rustdesk():
            time.sleep(0.2)
            pyautogui.typewrite(keys, interval=0.05)
            return True
        return False
    
    def click_in_remote(self, x, y):
        """Click at position within RustDesk window"""
        if self.rustdesk_window:
            rect = self.rustdesk_window.rectangle()
            abs_x = rect.left + x
            abs_y = rect.top + y
            pyautogui.click(abs_x, abs_y)
            return True
        return False


class TaskQueue:
    """Simple persistent task queue for unattended operation"""
    
    def __init__(self, db_path="agent_tasks.json"):
        self.db_path = db_path
        self.tasks = self._load_tasks()
        self.running = False
    
    def _load_tasks(self):
        """Load tasks from file"""
        if os.path.exists(self.db_path):
            with open(self.db_path, 'r') as f:
                return json.load(f)
        return {"pending": [], "completed": [], "failed": []}
    
    def _save_tasks(self):
        """Save tasks to file"""
        with open(self.db_path, 'w') as f:
            json.dump(self.tasks, f, indent=2, default=str)
    
    def add_task(self, task_type, params, priority=0):
        """Add task to queue"""
        task = {
            "id": f"task_{datetime.now().strftime('%Y%m%d%H%M%S%f')}",
            "type": task_type,
            "params": params,
            "priority": priority,
            "created": datetime.now().isoformat(),
            "status": "pending"
        }
        self.tasks["pending"].append(task)
        self.tasks["pending"].sort(key=lambda x: x["priority"], reverse=True)
        self._save_tasks()
        return task["id"]
    
    def get_next_task(self):
        """Get next pending task"""
        if self.tasks["pending"]:
            return self.tasks["pending"][0]
        return None
    
    def complete_task(self, task_id, result=None):
        """Mark task as completed"""
        for i, task in enumerate(self.tasks["pending"]):
            if task["id"] == task_id:
                task["status"] = "completed"
                task["completed"] = datetime.now().isoformat()
                task["result"] = result
                self.tasks["completed"].append(task)
                del self.tasks["pending"][i]
                self._save_tasks()
                return True
        return False
    
    def fail_task(self, task_id, error=None):
        """Mark task as failed"""
        for i, task in enumerate(self.tasks["pending"]):
            if task["id"] == task_id:
                task["status"] = "failed"
                task["failed"] = datetime.now().isoformat()
                task["error"] = str(error)
                self.tasks["failed"].append(task)
                del self.tasks["pending"][i]
                self._save_tasks()
                return True
        return False


class DesktopAgent:
    """Main agent orchestrating all controllers"""
    
    def __init__(self):
        self.screen = ScreenCapture()
        self.windows = WindowController()
        self.browser = None
        self.rustdesk = RustDeskController(self.windows)
        self.task_queue = TaskQueue()
        self.running = False
        self.handlers = {}
    
    def register_handler(self, task_type, handler_func):
        """Register handler for task type"""
        self.handlers[task_type] = handler_func
    
    def process_task(self, task):
        """Process a single task"""
        task_type = task["type"]
        params = task["params"]
        
        if task_type in self.handlers:
            try:
                result = self.handlers[task_type](self, params)
                self.task_queue.complete_task(task["id"], result)
                logger.info(f"Task {task['id']} completed successfully")
                return True
            except Exception as e:
                self.task_queue.fail_task(task["id"], e)
                logger.error(f"Task {task['id']} failed: {e}")
                return False
        else:
            logger.warning(f"No handler for task type: {task_type}")
            self.task_queue.fail_task(task["id"], f"Unknown task type: {task_type}")
            return False
    
    def run_loop(self, interval=5):
        """Main agent loop - runs unattended"""
        self.running = True
        logger.info("Desktop Agent started - running unattended")
        
        while self.running:
            task = self.task_queue.get_next_task()
            if task:
                logger.info(f"Processing task: {task['id']} - {task['type']}")
                self.process_task(task)
            else:
                logger.debug("No pending tasks, waiting...")
            time.sleep(interval)
    
    def stop(self):
        """Stop the agent loop"""
        self.running = False
        logger.info("Desktop Agent stopping...")


# Example task handlers
def handler_screenshot(agent, params):
    """Take screenshot task"""
    filename = params.get("filename", None)
    return agent.screen.save_screenshot(filename)


def handler_open_url(agent, params):
    """Open URL in browser"""
    url = params["url"]
    if agent.browser is None:
        agent.browser = BrowserController()
        agent.browser.start_playwright(headless=False)
    agent.browser.navigate(url)
    return f"Opened {url}"


def handler_list_windows(agent, params):
    """List all windows"""
    return agent.windows.list_windows()


def handler_click_position(agent, params):
    """Click at screen position"""
    x = params["x"]
    y = params["y"]
    pyautogui.click(x, y)
    return f"Clicked at ({x}, {y})"


def handler_type_text(agent, params):
    """Type text"""
    text = params["text"]
    pyautogui.typewrite(text, interval=0.05)
    return f"Typed: {text}"


def handler_focus_window(agent, params):
    """Focus a window by title"""
    title = params["title"]
    window = agent.windows.find_window(title_contains=title)
    if window:
        agent.windows.focus_window(window)
        return f"Focused window: {title}"
    return f"Window not found: {title}"


# Register default handlers
def create_agent_with_defaults():
    """Create agent with default handlers registered"""
    agent = DesktopAgent()
    agent.register_handler("screenshot", handler_screenshot)
    agent.register_handler("open_url", handler_open_url)
    agent.register_handler("list_windows", handler_list_windows)
    agent.register_handler("click", handler_click_position)
    agent.register_handler("type", handler_type_text)
    agent.register_handler("focus_window", handler_focus_window)
    return agent


if __name__ == "__main__":
    # Example usage
    agent = create_agent_with_defaults()
    
    # Add some test tasks
    agent.task_queue.add_task("screenshot", {"filename": "test_screenshot.png"})
    agent.task_queue.add_task("list_windows", {})
    
    # Run in background thread for testing
    # agent.run_loop()
    
    # Or process tasks manually
    while True:
        task = agent.task_queue.get_next_task()
        if task:
            agent.process_task(task)
        else:
            break
    
    print("All tasks processed")
    print(f"Completed: {len(agent.task_queue.tasks['completed'])}")
    print(f"Failed: {len(agent.task_queue.tasks['failed'])}")
Round 3: Universal Backtesting Framework
File: universal_backtester.py

"""
Universal Backtesting Framework
Supports: Stocks, ETFs, Crypto, Forex, Futures, Commodities, Bonds, Mutual Funds
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable
import yfinance as yf
import json
import os
from dataclasses import dataclass
from enum import Enum
import warnings
warnings.filterwarnings('ignore')

# Try importing various backtesting libraries
try:
    import vectorbt as vbt
    HAS_VECTORBT = True
except ImportError:
    HAS_VECTORBT = False

try:
    from backtesting import Backtest, Strategy
    HAS_BACKTESTING = True
except ImportError:
    HAS_BACKTESTING = False

try:
    import backtrader as bt
    HAS_BACKTRADER = True
except ImportError:
    HAS_BACKTRADER = False


class AssetClass(Enum):
    STOCK = "stock"
    ETF = "etf"
    CRYPTO = "crypto"
    FOREX = "forex"
    FUTURES = "futures"
    COMMODITY = "commodity"
    BOND = "bond"
    MUTUAL_FUND = "mutual_fund"
    INDEX = "index"


@dataclass
class TradeSignal:
    timestamp: datetime
    symbol: str
    action: str  # "BUY", "SELL", "HOLD"
    price: float
    quantity: float
    confidence: float
    reason: str
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None


@dataclass
class BacktestResult:
    symbol: str
    strategy_name: str
    start_date: datetime
    end_date: datetime
    initial_capital: float
    final_value: float
    total_return: float
    annual_return: float
    sharpe_ratio: float
    max_drawdown: float
    win_rate: float
    total_trades: int
    winning_trades: int
    losing_trades: int
    profit_factor: float
    avg_trade_return: float
    trades: List[Dict]
    equity_curve: List[float]
    parameters: Dict


class DataFetcher:
    """Fetch data from free sources"""
    
    # Free data sources mapping
    SOURCES = {
        AssetClass.STOCK: ["yfinance", "alpha_vantage_free"],
        AssetClass.ETF: ["yfinance"],
        AssetClass.CRYPTO: ["yfinance", "ccxt_free", "binance_public"],
        AssetClass.FOREX: ["yfinance", "alpha_vantage_free"],
        AssetClass.FUTURES: ["yfinance"],
        AssetClass.COMMODITY: ["yfinance"],
        AssetClass.BOND: ["yfinance"],  # Treasury ETFs as proxy
        AssetClass.MUTUAL_FUND: ["yfinance"],
        AssetClass.INDEX: ["yfinance"],
    }
    
    # Symbol mappings for different asset classes
    SAMPLE_SYMBOLS = {
        AssetClass.STOCK: ["AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "TSLA"],
        AssetClass.ETF: ["SPY", "QQQ", "IWM", "VTI", "VOO", "DIA", "XLF", "XLE"],
        AssetClass.CRYPTO: ["BTC-USD", "ETH-USD", "SOL-USD", "ADA-USD", "DOGE-USD"],
        AssetClass.FOREX: ["EURUSD=X", "GBPUSD=X", "USDJPY=X", "AUDUSD=X", "USDCAD=X"],
        AssetClass.FUTURES: ["ES=F", "NQ=F", "CL=F", "GC=F", "SI=F"],  # E-mini S&P, Nasdaq, Crude, Gold, Silver
        AssetClass.COMMODITY: ["GLD", "SLV", "USO", "UNG", "DBA"],  # ETF proxies
        AssetClass.BOND: ["TLT", "IEF", "SHY", "BND", "AGG"],  # Bond ETFs
        AssetClass.MUTUAL_FUND: ["VFIAX", "FXAIX", "SWPPX"],
        AssetClass.INDEX: ["^GSPC", "^DJI", "^IXIC", "^RUT", "^VIX"],
    }
    
    def __init__(self, cache_dir="data_cache"):
        self.cache_dir = cache_dir
        os.makedirs(cache_dir, exist_ok=True)
    
    def get_cache_path(self, symbol, interval, start, end):
        """Get cache file path"""
        safe_symbol = symbol.replace("=", "_").replace("^", "_")
        return os.path.join(
            self.cache_dir, 
            f"{safe_symbol}_{interval}_{start}_{end}.parquet"
        )
    
    def fetch_yfinance(self, symbol: str, start: str, end: str, 
                       interval: str = "1d") -> pd.DataFrame:
        """Fetch data from Yahoo Finance (free)"""
        cache_path = self.get_cache_path(symbol, interval, start, end)
        
        # Check cache
        if os.path.exists(cache_path):
            return pd.read_parquet(cache_path)
        
        try:
            ticker = yf.Ticker(symbol)
            df = ticker.history(start=start, end=end, interval=interval)
            
            if df.empty:
                return pd.DataFrame()
            
            # Standardize columns
            df = df.rename(columns={
                "Open": "open",
                "High": "high",
                "Low": "low",
                "Close": "close",
                "Volume": "volume"
            })
            
            # Keep only OHLCV
            df = df[["open", "high", "low", "close", "volume"]]
            
            # Save to cache
            df.to_parquet(cache_path)
            
            return df
        except Exception as e:
            print(f"Error fetching {symbol}: {e}")
            return pd.DataFrame()
    
    def fetch_crypto_binance(self, symbol: str, start: str, end: str,
                            interval: str = "1d") -> pd.DataFrame:
        """Fetch crypto data from Binance public API (free)"""
        import requests
        
        # Convert symbol format (BTC-USD -> BTCUSDT)
        binance_symbol = symbol.replace("-USD", "USDT").replace("-", "")
        
        # Interval mapping
        interval_map = {
            "1m": "1m", "5m": "5m", "15m": "15m", "30m": "30m",
            "1h": "1h", "4h": "4h", "1d": "1d", "1w": "1w"
        }
        binance_interval = interval_map.get(interval, "1d")
        
        url = "https://api.binance.com/api/v3/klines"
        
        start_ts = int(pd.Timestamp(start).timestamp() * 1000)
        end_ts = int(pd.Timestamp(end).timestamp() * 1000)
        
        params = {
            "symbol": binance_symbol,
            "interval": binance_interval,
            "startTime": start_ts,
            "endTime": end_ts,
            "limit": 1000
        }
        
        try:
            response = requests.get(url, params=params)
            data = response.json()
            
            if isinstance(data, list) and len(data) > 0:
                df = pd.DataFrame(data, columns=[
                    "timestamp", "open", "high", "low", "close", "volume",
                    "close_time", "quote_volume", "trades", "taker_buy_base",
                    "taker_buy_quote", "ignore"
                ])
                
                df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
                df = df.set_index("timestamp")
                df = df[["open", "high", "low", "close", "volume"]].astype(float)
                
                return df
        except Exception as e:
            print(f"Binance fetch error for {symbol}: {e}")
        
        # Fallback to yfinance
        return self.fetch_yfinance(symbol, start, end, interval)
    
    def fetch(self, symbol: str, asset_class: AssetClass,
              start: str, end: str, interval: str = "1d") -> pd.DataFrame:
        """Universal fetch method"""
        
        if asset_class == AssetClass.CRYPTO:
            # Try Binance first for crypto
            df = self.fetch_crypto_binance(symbol, start, end, interval)
            if not df.empty:
                return df
        
        # Default to yfinance
        return self.fetch_yfinance(symbol, start, end, interval)
    
    def fetch_multiple(self, symbols: List[str], asset_class: AssetClass,
                       start: str, end: str, interval: str = "1d") -> Dict[str, pd.DataFrame]:
        """Fetch multiple symbols"""
        data = {}
        for symbol in symbols:
            df = self.fetch(symbol, asset_class, start, end, interval)
            if not df.empty:
                data[symbol] = df
        return data


class IndicatorLibrary:
    """Common technical indicators"""
    
    @staticmethod
    def sma(data: pd.Series, period: int) -> pd.Series:
        """Simple Moving Average"""
        return data.rolling(window=period).mean()
    
    @staticmethod
    def ema(data: pd.Series, period: int) -> pd.Series:
        """Exponential Moving Average"""
        return data.ewm(span=period, adjust=False).mean()
    
    @staticmethod
    def rsi(data: pd.Series, period: int = 14) -> pd.Series:
        """Relative Strength Index"""
        delta = data.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        return 100 - (100 / (1 + rs))
    
    @staticmethod
    def macd(data: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9):
        """MACD"""
        ema_fast = data.ewm(span=fast, adjust=False).mean()
        ema_slow = data.ewm(span=slow, adjust=False).mean()
        macd_line = ema_fast - ema_slow
        signal_line = macd_line.ewm(span=signal, adjust=False).mean()
        histogram = macd_line - signal_line
        return macd_line, signal_line, histogram
    
    @staticmethod
    def bollinger_bands(data: pd.Series, period: int = 20, std_dev: float = 2.0):
        """Bollinger Bands"""
        sma = data.rolling(window=period).mean()
        std = data.rolling(window=period).std()
        upper = sma + (std * std_dev)
        lower = sma - (std * std_dev)
        return upper, sma, lower
    
    @staticmethod
    def atr(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
        """Average True Range"""
        tr1 = high - low
        tr2 = abs(high - close.shift())
        tr3 = abs(low - close.shift())
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        return tr.rolling(window=period).mean()
    
    @staticmethod
    def stochastic(high: pd.Series, low: pd.Series, close: pd.Series, 
                   k_period: int = 14, d_period: int = 3):
        """Stochastic Oscillator"""
        lowest_low = low.rolling(window=k_period).min()
        highest_high = high.rolling(window=k_period).max()
        k = 100 * (close - lowest_low) / (highest_high - lowest_low)
        d = k.rolling(window=d_period).mean()
        return k, d


class BaseStrategy:
    """Base class for strategies"""
    
    def __init__(self, name: str, params: Dict = None):
        self.name = name
        self.params = params or {}
        self.indicators = IndicatorLibrary()
    
    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Override to add indicators"""
        return df
    
    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """Override to generate buy/sell signals"""
        df["signal"] = 0  # 0=hold, 1=buy, -1=sell
        return df
    
    def get_stop_loss(self, entry_price: float, position: str) -> float:
        """Calculate stop loss"""
        sl_pct = self.params.get("stop_loss_pct", 0.02)
        if position == "long":
            return entry_price * (1 - sl_pct)
        else:
            return entry_price * (1 + sl_pct)
    
    def get_take_profit(self, entry_price: float, position: str) -> float:
        """Calculate take profit"""
        tp_pct = self.params.get("take_profit_pct", 0.04)
        if position == "long":
            return entry_price * (1 + tp_pct)
        else:
            return entry_price * (1 - tp_pct)


class SMAcrossStrategy(BaseStrategy):
    """SMA Crossover Strategy"""
    
    def __init__(self, fast_period: int = 10, slow_period: int = 30, **kwargs):
        super().__init__("SMA_Crossover", {
            "fast_period": fast_period,
            "slow_period": slow_period,
            **kwargs
        })
    
    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        fast = self.params["fast_period"]
        slow = self.params["slow_period"]
        df["sma_fast"] = self.indicators.sma(df["close"], fast)
        df["sma_slow"] = self.indicators.sma(df["close"], slow)
        return df
    
    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        df = self.calculate_indicators(df.copy())
        
        # Signal when fast crosses above slow
        df["signal"] = 0
        df.loc[df["sma_fast"] > df["sma_slow"], "signal"] = 1
        df.loc[df["sma_fast"] < df["sma_slow"], "signal"] = -1
        
        # Only signal on actual crossover
        df["signal"] = df["signal"].diff()
        df["signal"] = df["signal"].fillna(0)
        df.loc[df["signal"] > 0, "signal"] = 1
        df.loc[df["signal"] < 0, "signal"] = -1
        
        return df


class RSIMeanReversionStrategy(BaseStrategy):
    """RSI Mean Reversion Strategy"""
    
    def __init__(self, rsi_period: int = 14, oversold: int = 30, 
                 overbought: int = 70, **kwargs):
        super().__init__("RSI_MeanReversion", {
            "rsi_period": rsi_period,
            "oversold": oversold,
            "overbought": overbought,
            **kwargs
        })
    
    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        df["rsi"] = self.indicators.rsi(df["close"], self.params["rsi_period"])
        return df
    
    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        df = self.calculate_indicators(df.copy())
        
        df["signal"] = 0
        # Buy when RSI crosses above oversold
        df.loc[(df["rsi"] > self.params["oversold"]) & 
               (df["rsi"].shift(1) <= self.params["oversold"]), "signal"] = 1
        # Sell when RSI crosses below overbought
        df.loc[(df["rsi"] < self.params["overbought"]) & 
               (df["rsi"].shift(1) >= self.params["overbought"]), "signal"] = -1
        
        return df


class MACDStrategy(BaseStrategy):
    """MACD Crossover Strategy"""
    
    def __init__(self, fast: int = 12, slow: int = 26, signal: int = 9, **kwargs):
        super().__init__("MACD_Crossover", {
            "fast": fast,
            "slow": slow,
            "signal": signal,
            **kwargs
        })
    
    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        macd, signal, hist = self.indicators.macd(
            df["close"],
            self.params["fast"],
            self.params["slow"],
            self.params["signal"]
        )
        df["macd"] = macd
        df["macd_signal"] = signal
        df["macd_hist"] = hist
        return df
    
    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        df = self.calculate_indicators(df.copy())
        
        df["signal"] = 0
        # Buy when MACD crosses above signal
        df.loc[(df["macd"] > df["macd_signal"]) & 
               (df["macd"].shift(1) <= df["macd_signal"].shift(1)), "signal"] = 1
        # Sell when MACD crosses below signal
        df.loc[(df["macd"] < df["macd_signal"]) & 
               (df["macd"].shift(1) >= df["macd_signal"].shift(1)), "signal"] = -1
        
        return df


class BollingerBandStrategy(BaseStrategy):
    """Bollinger Band Breakout Strategy"""
    
    def __init__(self, period: int = 20, std_dev: float = 2.0, **kwargs):
        super().__init__("Bollinger_Breakout", {
            "period": period,
            "std_dev": std_dev,
            **kwargs
        })
    
    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        upper, middle, lower = self.indicators.bollinger_bands(
            df["close"],
            self.params["period"],
            self.params["std_dev"]
        )
        df["bb_upper"] = upper
        df["bb_middle"] = middle
        df["bb_lower"] = lower
        return df
    
    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        df = self.calculate_indicators(df.copy())
        
        df["signal"] = 0
        # Buy when price touches lower band
        df.loc[df["close"] <= df["bb_lower"], "signal"] = 1
        # Sell when price touches upper band
        df.loc[df["close"] >= df["bb_upper"], "signal"] = -1
        
        return df


class UniversalBacktester:
    """Main backtesting engine"""
    
    def __init__(self, initial_capital: float = 10000.0):
        self.initial_capital = initial_capital
        self.fetcher = DataFetcher()
        self.results = []
    
    def backtest_strategy(self, df: pd.DataFrame, strategy: BaseStrategy,
                          symbol: str, commission: float = 0.001) -> BacktestResult:
        """Run backtest on strategy"""
        
        # Generate signals
        df = strategy.generate_signals(df.copy())
        
        # Initialize tracking
        capital = self.initial_capital
        position = 0  # Number of shares
        position_type = None  # "long" or "short"
        entry_price = 0
        trades = []
        equity_curve = [capital]
        
        for i in range(1, len(df)):
            current_price = df["close"].iloc[i]
            signal = df["signal"].iloc[i]
            timestamp = df.index[i]
            
            # Check stop loss / take profit if in position
            if position != 0:
                if position_type == "long":
                    # Check stop loss
                    if current_price <= strategy.get_stop_loss(entry_price, "long"):
                        # Close position at stop loss
                        pnl = (current_price - entry_price) * position
                        capital += position * current_price * (1 - commission)
                        trades.append({
                            "timestamp": timestamp,
                            "action": "SELL (SL)",
                            "price": current_price,
                            "quantity": position,
                            "pnl": pnl
                        })
                        position = 0
                        position_type = None
                    # Check take profit
                    elif current_price >= strategy.get_take_profit(entry_price, "long"):
                        pnl = (current_price - entry_price) * position
                        capital += position * current_price * (1 - commission)
                        trades.append({
                            "timestamp": timestamp,
                            "action": "SELL (TP)",
                            "price": current_price,
                            "quantity": position,
                            "pnl": pnl
                        })
                        position = 0
                        position_type = None
            
            # Process signals
            if signal == 1 and position == 0:  # Buy signal
                # Calculate position size
                position = int((capital * 0.95) / current_price)  # Use 95% of capital
                if position > 0:
                    cost = position * current_price * (1 + commission)
                    capital -= cost
                    entry_price = current_price
                    position_type = "long"
                    trades.append({
                        "timestamp": timestamp,
                        "action": "BUY",
                        "price": current_price,
                        "quantity": position,
                        "pnl": 0
                    })
            
            elif signal == -1 and position > 0:  # Sell signal
                pnl = (current_price - entry_price) * position
                capital += position * current_price * (1 - commission)
                trades.append({
                    "timestamp": timestamp,
                    "action": "SELL",
                    "price": current_price,
                    "quantity": position,
                    "pnl": pnl
                })
                position = 0
                position_type = None
            
            # Update equity curve
            current_equity = capital + (position * current_price if position > 0 else 0)
            equity_curve.append(current_equity)
        
        # Close any remaining position
        if position > 0:
            final_price = df["close"].iloc[-1]
            pnl = (final_price - entry_price) * position
            capital += position * final_price * (1 - commission)
            trades.append({
                "timestamp": df.index[-1],
                "action": "SELL (END)",
                "price": final_price,
                "quantity": position,
                "pnl": pnl
            })
        
        # Calculate metrics
        final_value = capital
        total_return = (final_value - self.initial_capital) / self.initial_capital
        
        # Calculate trading days
        trading_days = len(df)
        years = trading_days / 252
        annual_return = (1 + total_return) ** (1 / max(years, 0.01)) - 1 if years > 0 else 0
        
        # Calculate Sharpe Ratio
        returns = pd.Series(equity_curve).pct_change().dropna()
        sharpe = (returns.mean() / returns.std()) * np.sqrt(252) if returns.std() > 0 else 0
        
        # Calculate Max Drawdown
        equity_series = pd.Series(equity_curve)
        rolling_max = equity_series.expanding().max()
        drawdowns = (equity_series - rolling_max) / rolling_max
        max_drawdown = drawdowns.min()
        
        # Trade statistics
        winning_trades = len([t for t in trades if t.get("pnl", 0) > 0])
        losing_trades = len([t for t in trades if t.get("pnl", 0) < 0])
        total_trades = len([t for t in trades if t["action"].startswith("SELL")])
        
        win_rate = winning_trades / total_trades if total_trades > 0 else 0
        
        gross_profit = sum([t["pnl"] for t in trades if t.get("pnl", 0) > 0])
        gross_loss = abs(sum([t["pnl"] for t in trades if t.get("pnl", 0) < 0]))
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else float('inf')
        
        avg_trade_return = sum([t.get("pnl", 0) for t in trades]) / total_trades if total_trades > 0 else 0
        
        return BacktestResult(
            symbol=symbol,
            strategy_name=strategy.name,
            start_date=df.index[0],
            end_date=df.index[-1],
            initial_capital=self.initial_capital,
            final_value=final_value,
            total_return=total_return,
            annual_return=annual_return,
            sharpe_ratio=sharpe,
            max_drawdown=max_drawdown,
            win_rate=win_rate,
            total_trades=total_trades,
            winning_trades=winning_trades,
            losing_trades=losing_trades,
            profit_factor=profit_factor,
            avg_trade_return=avg_trade_return,
            trades=trades,
            equity_curve=equity_curve,
            parameters=strategy.params
        )
    
    def run_parameter_sweep(self, df: pd.DataFrame, strategy_class: type,
                            param_grid: Dict[str, List], symbol: str) -> List[BacktestResult]:
        """Run parameter sweep for optimization"""
        from itertools import product
        
        results = []
        
        # Generate all parameter combinations
        param_names = list(param_grid.keys())
        param_values = list(param_grid.values())
        
        for combo in product(*param_values):
            params = dict(zip(param_names, combo))
            strategy = strategy_class(**params)
            
            try:
                result = self.backtest_strategy(df, strategy, symbol)
                results.append(result)
            except Exception as e:
                print(f"Error with params {params}: {e}")
        
        return sorted(results, key=lambda x: x.sharpe_ratio, reverse=True)
    
    def scan_asset_class(self, asset_class: AssetClass, strategy: BaseStrategy,
                         start: str, end: str) -> List[BacktestResult]:
        """Scan all symbols in an asset class"""
        symbols = DataFetcher.SAMPLE_SYMBOLS.get(asset_class, [])
        results = []
        
        for symbol in symbols:
            print(f"Testing {symbol}...")
            df = self.fetcher.fetch(symbol, asset_class, start, end)
            
            if df.empty or len(df) < 50:
                print(f"  Insufficient data for {symbol}")
                continue
            
            try:
                result = self.backtest_strategy(df, strategy, symbol)
                results.append(result)
                print(f"  {symbol}: Return={result.total_return:.2%}, Sharpe={result.sharpe_ratio:.2f}")
            except Exception as e:
                print(f"  Error: {e}")
        
        return sorted(results, key=lambda x: x.sharpe_ratio, reverse=True)
    
    def generate_report(self, results: List[BacktestResult], filename: str = None):
        """Generate summary report"""
        if not results:
            return "No results to report"
        
        report = []
        report.append("=" * 80)
        report.append("BACKTEST RESULTS SUMMARY")
        report.append("=" * 80)
        
        # Summary statistics
        profitable = [r for r in results if r.total_return > 0]
        report.append(f"\nTotal strategies tested: {len(results)}")
        report.append(f"Profitable strategies: {len(profitable)} ({len(profitable)/len(results)*100:.1f}%)")
        
        if profitable:
            best = max(results, key=lambda x: x.sharpe_ratio)
            report.append(f"\nBest Strategy (by Sharpe):")
            report.append(f"  Symbol: {best.symbol}")
            report.append(f"  Strategy: {best.strategy_name}")
            report.append(f"  Parameters: {best.parameters}")
            report.append(f"  Total Return: {best.total_return:.2%}")
            report.append(f"  Annual Return: {best.annual_return:.2%}")
            report.append(f"  Sharpe Ratio: {best.sharpe_ratio:.2f}")
            report.append(f"  Max Drawdown: {best.max_drawdown:.2%}")
            report.append(f"  Win Rate: {best.win_rate:.2%}")
            report.append(f"  Total Trades: {best.total_trades}")
        
        report.append("\n" + "=" * 80)
        report.append("DETAILED RESULTS")
        report.append("=" * 80)
        
        for r in results[:20]:  # Top 20
            report.append(f"\n{r.symbol} - {r.strategy_name}")
            report.append(f"  Return: {r.total_return:.2%} | Sharpe: {r.sharpe_ratio:.2f} | "
                         f"MDD: {r.max_drawdown:.2%} | Win: {r.win_rate:.2%}")
        
        report_text = "\n".join(report)
        
        if filename:
            with open(filename, 'w') as f:
                f.write(report_text)
        
        return report_text


def save_results_to_json(results: List[BacktestResult], filename: str):
    """Save results to JSON for later analysis"""
    data = []
    for r in results:
        data.append({
            "symbol": r.symbol,
            "strategy": r.strategy_name,
            "parameters": r.parameters,
            "total_return": r.total_return,
            "annual_return": r.annual_return,
            "sharpe_ratio": r.sharpe_ratio,
            "max_drawdown": r.max_drawdown,
            "win_rate": r.win_rate,
            "total_trades": r.total_trades,
            "profit_factor": r.profit_factor,
            "start_date": str(r.start_date),
            "end_date": str(r.end_date)
        })
    
    with open(filename, 'w') as f:
        json.dump(data, f, indent=2)


if __name__ == "__main__":
    # Example usage
    backtester = UniversalBacktester(initial_capital=10000)
    
    # Test SMA strategy on multiple stocks
    strategy = SMAcrossStrategy(fast_period=10, slow_period=30)
    
    print("Scanning stocks...")
    results = backtester.scan_asset_class(
        AssetClass.STOCK,
        strategy,
        start="2022-01-01",
        end="2024-01-01"
    )
    
    print("\n" + backtester.generate_report(results))
    
    # Save results
    save_results_to_json(results, "backtest_results.json")
Round 4: Live Market Data Monitor
File: live_market_monitor.py

"""
Live Market Data Monitor
Real-time price monitoring with signal generation
"""

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import time
import json
import os
from typing import Dict, List, Optional, Callable
import threading
from queue import Queue
import requests

# Import our backtester components
from universal_backtester import (
    IndicatorLibrary, SMAcrossStrategy, RSIMeanReversionStrategy,
    MACDStrategy, BollingerBandStrategy, AssetClass
)


class LiveDataStream:
    """Stream live market data"""
    
    def __init__(self):
        self.running = False
        self.subscribers = []
        self.data_cache = {}
    
    def get_live_price(self, symbol: str) -> Dict:
        """Get current price for symbol"""
        try:
            ticker = yf.Ticker(symbol)
            
            # Get latest data
            hist = ticker.history(period="1d", interval="1m")
            
            if hist.empty:
                # Try with 5m interval
                hist = ticker.history(period="1d", interval="5m")
            
            if not hist.empty:
                latest = hist.iloc[-1]
                return {
                    "symbol": symbol,
                    "timestamp": datetime.now().isoformat(),
                    "price": float(latest["Close"]),
                    "open": float(latest["Open"]),
                    "high": float(latest["High"]),
                    "low": float(latest["Low"]),
                    "volume": int(latest["Volume"]),
                    "source": "yfinance"
                }
        except Exception as e:
            print(f"Error fetching {symbol}: {e}")
        
        return None
    
    def get_crypto_price_binance(self, symbol: str) -> Dict:
        """Get crypto price from Binance"""
        try:
            # Convert format
            binance_symbol = symbol.replace("-USD", "USDT").replace("-", "")
            
            url = f"https://api.binance.com/api/v3/ticker/24hr?symbol={binance_symbol}"
            response = requests.get(url, timeout=5)
            data = response.json()
            
            return {
                "symbol": symbol,
                "timestamp": datetime.now().isoformat(),
                "price": float(data["lastPrice"]),
                "open": float(data["openPrice"]),
                "high": float(data["highPrice"]),
                "low": float(data["lowPrice"]),
                "volume": float(data["volume"]),
                "change_24h": float(data["priceChangePercent"]),
                "source": "binance"
            }
        except Exception as e:
            # Fallback to yfinance
            return self.get_live_price(symbol)
    
    def get_forex_price(self, pair: str) -> Dict:
        """Get forex price"""
        # Yahoo Finance format: EURUSD=X
        if not pair.endswith("=X"):
            pair = pair + "=X"
        return self.get_live_price(pair)
    
    def subscribe(self, callback: Callable):
        """Subscribe to price updates"""
        self.subscribers.append(callback)
    
    def stream_symbols(self, symbols: List[str], interval: int = 60):
        """Stream prices for symbols at interval"""
        self.running = True
        
        while self.running:
            for symbol in symbols:
                if symbol.endswith("-USD") or "BTC" in symbol or "ETH" in symbol:
                    price_data = self.get_crypto_price_binance(symbol)
                elif "=X" in symbol or len(symbol) == 6:  # Forex pair
                    price_data = self.get_forex_price(symbol)
                else:
                    price_data = self.get_live_price(symbol)
                
                if price_data:
                    self.data_cache[symbol] = price_data
                    for callback in self.subscribers:
                        callback(price_data)
            
            time.sleep(interval)
    
    def stop(self):
        """Stop streaming"""
        self.running = False


class LiveSignalGenerator:
    """Generate trading signals from live data"""
    
    def __init__(self, lookback_periods: int = 100):
        self.lookback = lookback_periods
        self.price_history = {}  # symbol -> list of prices
        self.indicators = IndicatorLibrary()
        self.strategies = [
            SMAcrossStrategy(fast_period=10, slow_period=30),
            RSIMeanReversionStrategy(rsi_period=14, oversold=30, overbought=70),
            MACDStrategy(fast=12, slow=26, signal=9),
            BollingerBandStrategy(period=20, std_dev=2.0)
        ]
    
    def update_history(self, symbol: str, price: float, timestamp: str):
        """Update price history"""
        if symbol not in self.price_history:
            self.price_history[symbol] = []
        
        self.price_history[symbol].append({
            "timestamp": timestamp,
            "price": price
        })
        
        # Keep only lookback periods
        if len(self.price_history[symbol]) > self.lookback:
            self.price_history[symbol] = self.price_history[symbol][-self.lookback:]
    
    def get_dataframe(self, symbol: str) -> pd.DataFrame:
        """Convert history to DataFrame"""
        if symbol not in self.price_history:
            return pd.DataFrame()
        
        history = self.price_history[symbol]
        if len(history) < 30:  # Need minimum data
            return pd.DataFrame()
        
        df = pd.DataFrame(history)
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        df = df.set_index("timestamp")
        df["close"] = df["price"]
        df["open"] = df["close"]
        df["high"] = df["close"]
        df["low"] = df["close"]
        df["volume"] = 0
        
        return df
    
    def generate_signals(self, symbol: str) -> List[Dict]:
        """Generate signals from all strategies"""
        df = self.get_dataframe(symbol)
        
        if df.empty:
            return []
        
        signals = []
        current_price = df["close"].iloc[-1]
        
        for strategy in self.strategies:
            try:
                df_signals = strategy.generate_signals(df.copy())
                latest_signal = df_signals["signal"].iloc[-1]
                
                if latest_signal != 0:
                    signals.append({
                        "symbol": symbol,
                        "strategy": strategy.name,
                        "signal": "BUY" if latest_signal == 1 else "SELL",
                        "price": current_price,
                        "timestamp": datetime.now().isoformat(),
                        "stop_loss": strategy.get_stop_loss(current_price, "long" if latest_signal == 1 else "short"),
                        "take_profit": strategy.get_take_profit(current_price, "long" if latest_signal == 1 else "short"),
                        "parameters": strategy.params
                    })
            except Exception as e:
                print(f"Error generating signal for {strategy.name}: {e}")
        
        return signals


class PaperTradingPortfolio:
    """Paper trading portfolio manager"""
    
    def __init__(self, initial_capital: float = 10000.0):
        self.initial_capital = initial_capital
        self.cash = initial_capital
        self.positions = {}  # symbol -> {quantity, entry_price, entry_time}
        self.trades = []
        self.portfolio_history = []
    
    def get_portfolio_value(self, current_prices: Dict[str, float]) -> float:
        """Calculate total portfolio value"""
        value = self.cash
        for symbol, position in self.positions.items():
            if symbol in current_prices:
                value += position["quantity"] * current_prices[symbol]
            else:
                value += position["quantity"] * position["entry_price"]
        return value
    
    def open_position(self, symbol: str, signal: str, price: float, 
                      quantity: float = None, stop_loss: float = None,
                      take_profit: float = None):
        """Open a new position"""
        if quantity is None:
            # Use 10% of cash
            quantity = (self.cash * 0.1) / price
        
        cost = quantity * price
        if cost > self.cash:
            quantity = (self.cash * 0.95) / price
            cost = quantity * price
        
        if cost > self.cash or quantity <= 0:
            return False
        
        self.cash -= cost
        self.positions[symbol] = {
            "quantity": quantity,
            "entry_price": price,
            "entry_time": datetime.now().isoformat(),
            "signal": signal,
            "stop_loss": stop_loss,
            "take_profit": take_profit
        }
        
        self.trades.append({
            "timestamp": datetime.now().isoformat(),
            "symbol": symbol,
            "action": "OPEN",
            "signal": signal,
            "price": price,
            "quantity": quantity,
            "stop_loss": stop_loss,
            "take_profit": take_profit
        })
        
        return True
    
    def close_position(self, symbol: str, price: float, reason: str = "SIGNAL"):
        """Close an existing position"""
        if symbol not in self.positions:
            return False
        
        position = self.positions[symbol]
        proceeds = position["quantity"] * price
        pnl = proceeds - (position["quantity"] * position["entry_price"])
        pnl_pct = pnl / (position["quantity"] * position["entry_price"])
        
        self.cash += proceeds
        
        self.trades.append({
            "timestamp": datetime.now().isoformat(),
            "symbol": symbol,
            "action": "CLOSE",
            "reason": reason,
            "price": price,
            "quantity": position["quantity"],
            "pnl": pnl,
            "pnl_pct": pnl_pct,
            "entry_price": position["entry_price"],
            "hold_time": (datetime.now() - datetime.fromisoformat(position["entry_time"])).total_seconds()
        })
        
        del self.positions[symbol]
        return True
    
    def check_stop_loss_take_profit(self, current_prices: Dict[str, float]):
        """Check and execute SL/TP for all positions"""
        symbols_to_close = []
        
        for symbol, position in self.positions.items():
            if symbol not in current_prices:
                continue
            
            price = current_prices[symbol]
            
            # Check stop loss
            if position.get("stop_loss") and price <= position["stop_loss"]:
                symbols_to_close.append((symbol, price, "STOP_LOSS"))
            
            # Check take profit
            elif position.get("take_profit") and price >= position["take_profit"]:
                symbols_to_close.append((symbol, price, "TAKE_PROFIT"))
        
        for symbol, price, reason in symbols_to_close:
            self.close_position(symbol, price, reason)
    
    def get_summary(self, current_prices: Dict[str, float] = None) -> Dict:
        """Get portfolio summary"""
        if current_prices is None:
            current_prices = {}
        
        total_value = self.get_portfolio_value(current_prices)
        total_return = (total_value - self.initial_capital) / self.initial_capital
        
        winning_trades = len([t for t in self.trades if t["action"] == "CLOSE" and t.get("pnl", 0) > 0])
        losing_trades = len([t for t in self.trades if t["action"] == "CLOSE" and t.get("pnl", 0) < 0])
        closed_trades = winning_trades + losing_trades
        
        return {
            "initial_capital": self.initial_capital,
            "current_value": total_value,
            "cash": self.cash,
            "total_return": total_return,
            "total_return_pct": f"{total_return * 100:.2f}%",
            "open_positions": len(self.positions),
            "total_trades": len(self.trades),
            "closed_trades": closed_trades,
            "winning_trades": winning_trades,
            "losing_trades": losing_trades,
            "win_rate": winning_trades / closed_trades if closed_trades > 0 else 0,
            "positions": self.positions,
            "recent_trades": self.trades[-10:]
        }
    
    def save_state(self, filename: str = "paper_portfolio.json"):
        """Save portfolio state"""
        state = {
            "initial_capital": self.initial_capital,
            "cash": self.cash,
            "positions": self.positions,
            "trades": self.trades,
            "portfolio_history": self.portfolio_history,
            "saved_at": datetime.now().isoformat()
        }
        with open(filename, 'w') as f:
            json.dump(state, f, indent=2)
    
    def load_state(self, filename: str = "paper_portfolio.json"):
        """Load portfolio state"""
        if os.path.exists(filename):
            with open(filename, 'r') as f:
                state = json.load(f)
                self.initial_capital = state["initial_capital"]
                self.cash = state["cash"]
                self.positions = state["positions"]
                self.trades = state["trades"]
                self.portfolio_history = state.get("portfolio_history", [])
                return True
        return False


class LiveTradingSession:
    """Complete live trading session manager"""
    
    def __init__(self, symbols: List[str], initial_capital: float = 10000.0):
        self.symbols = symbols
        self.data_stream = LiveDataStream()
        self.signal_gen = LiveSignalGenerator()
        self.portfolio = PaperTradingPortfolio(initial_capital)
        self.current_prices = {}
        self.session_log = []
        self.running = False
    
    def log_event(self, event_type: str, data: Dict):
        """Log session event"""
        event = {
            "timestamp": datetime.now().isoformat(),
            "type": event_type,
            "data": data
        }
        self.session_log.append(event)
        print(f"[{event['timestamp']}] {event_type}: {data}")
    
    def on_price_update(self, price_data: Dict):
        """Handle price update"""
        symbol = price_data["symbol"]
        price = price_data["price"]
        
        self.current_prices[symbol] = price
        self.signal_gen.update_history(symbol, price, price_data["timestamp"])
        
        # Check SL/TP
        self.portfolio.check_stop_loss_take_profit(self.current_prices)
        
        # Generate signals
        signals = self.signal_gen.generate_signals(symbol)
        
        for signal in signals:
            self.log_event("SIGNAL", signal)
            
            # Auto-execute signals (paper trading)
            if signal["signal"] == "BUY" and symbol not in self.portfolio.positions:
                success = self.portfolio.open_position(
                    symbol,
                    signal["signal"],
                    price,
                    stop_loss=signal.get("stop_loss"),
                    take_profit=signal.get("take_profit")
                )
                if success:
                    self.log_event("TRADE_OPEN", {"symbol": symbol, "price": price})
            
            elif signal["signal"] == "SELL" and symbol in self.portfolio.positions:
                self.portfolio.close_position(symbol, price, "SIGNAL")
                self.log_event("TRADE_CLOSE", {"symbol": symbol, "price": price})
    
    def start(self, update_interval: int = 60, duration_minutes: int = None):
        """Start live trading session"""
        self.running = True
        self.log_event("SESSION_START", {"symbols": self.symbols})
        
        # Subscribe to price updates
        self.data_stream.subscribe(self.on_price_update)
        
        # Start streaming in background
        stream_thread = threading.Thread(
            target=self.data_stream.stream_symbols,
            args=(self.symbols, update_interval)
        )
        stream_thread.daemon = True
        stream_thread.start()
        
        # Run for specified duration or until stopped
        start_time = datetime.now()
        try:
            while self.running:
                time.sleep(10)
                
                # Print portfolio summary periodically
                if len(self.session_log) % 10 == 0:
                    summary = self.portfolio.get_summary(self.current_prices)
                    self.log_event("PORTFOLIO_UPDATE", summary)
                
                # Check duration
                if duration_minutes:
                    elapsed = (datetime.now() - start_time).total_seconds() / 60
                    if elapsed >= duration_minutes:
                        break
        
        except KeyboardInterrupt:
            pass
        
        self.stop()
    
    def stop(self):
        """Stop trading session"""
        self.running = False
        self.data_stream.stop()
        
        # Save state
        self.portfolio.save_state()
        
        # Generate session report
        summary = self.portfolio.get_summary(self.current_prices)
        self.log_event("SESSION_END", summary)
        
        # Save log
        with open(f"session_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json", 'w') as f:
            json.dump(self.session_log, f, indent=2)
        
        return summary


def quick_market_scan():
    """Quick scan of current market conditions"""
    stream = LiveDataStream()
    
    print("=" * 60)
    print("LIVE MARKET SCAN")
    print("=" * 60)
    print(f"Time: {datetime.now().isoformat()}")
    print("-" * 60)
    
    # Check if markets are open
    now = datetime.now()
    weekday = now.weekday()
    hour = now.hour
    
    print("\nMarket Status:")
    print(f"  US Stock Market: {'OPEN' if weekday < 5 and 9 <= hour < 16 else 'CLOSED'}")
    print(f"  Crypto Market: OPEN (24/7)")
    print(f"  Forex Market: {'OPEN' if weekday < 5 or (weekday == 6 and hour >= 17) else 'CLOSED'}")
    
    # Scan crypto (always open)
    print("\n" + "=" * 60)
    print("CRYPTO PRICES (Binance)")
    print("-" * 60)
    
    crypto_symbols = ["BTC-USD", "ETH-USD", "SOL-USD"]
    for symbol in crypto_symbols:
        data = stream.get_crypto_price_binance(symbol)
        if data:
            print(f"  {symbol}: ${data['price']:,.2f} ({data.get('change_24h', 0):+.2f}%)")
    
    # Scan forex
    print("\n" + "=" * 60)
    print("FOREX PRICES")
    print("-" * 60)
    
    forex_pairs = ["EURUSD=X", "GBPUSD=X", "USDJPY=X"]
    for pair in forex_pairs:
        data = stream.get_forex_price(pair)
        if data:
            print(f"  {pair.replace('=X', '')}: {data['price']:.4f}")
    
    # Scan major indices/ETFs
    print("\n" + "=" * 60)
    print("INDICES/ETFs")
    print("-" * 60)
    
    indices = ["SPY", "QQQ", "IWM"]
    for symbol in indices:
        data = stream.get_live_price(symbol)
        if data:
            print(f"  {symbol}: ${data['price']:,.2f}")
    
    print("\n" + "=" * 60)
    
    return stream


if __name__ == "__main__":
    # Quick market scan
    quick_market_scan()
    
    # Example: Start a live trading session
    # session = LiveTradingSession(
    #     symbols=["BTC-USD", "ETH-USD", "SPY"],
    #     initial_capital=10000
    # )
    # session.start(update_interval=60, duration_minutes=60)
Round 5: GitHub Actions Workflow for Automated Monitoring
File: .github/workflows/trading_monitor.yml

name: Trading Signal Monitor

on:
  schedule:
    # Run every hour during market hours (UTC)
    - cron: '0 14-21 * * 1-5'  # US market hours
    - cron: '0 */4 * * *'      # Crypto: every 4 hours
  workflow_dispatch:  # Manual trigger

env:
  PYTHON_VERSION: '3.11'

jobs:
  market-scan:
    runs-on: ubuntu-latest
    
    steps:
      - name: Checkout repository
        uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: ${{ env.PYTHON_VERSION }}
      
      - name: Cache pip packages
        uses: actions/cache@v4
        with:
          path: ~/.cache/pip
          key: ${{ runner.os }}-pip-${{ hashFiles('requirements.txt') }}
      
      - name: Install dependencies
        run: |
          pip install yfinance pandas numpy requests
      
      - name: Run market scan
        id: scan
        run: |
          python << 'EOF'
          import yfinance as yf
          import json
          from datetime import datetime
          import requests
          
          def get_crypto_price(symbol):
              try:
                  binance_symbol = symbol.replace("-USD", "USDT")
                  url = f"https://api.binance.com/api/v3/ticker/24hr?symbol={binance_symbol}"
                  response = requests.get(url, timeout=5)
                  data = response.json()
                  return {
                      "price": float(data["lastPrice"]),
                      "change_24h": float(data["priceChangePercent"])
                  }
              except:
                  return None
          
          def get_stock_price(symbol):
              try:
                  ticker = yf.Ticker(symbol)
                  hist = ticker.history(period="1d")
                  if not hist.empty:
                      return {"price": float(hist["Close"].iloc[-1])}
              except:
                  return None
          
          results = {
              "timestamp": datetime.now().isoformat(),
              "crypto": {},
              "stocks": {},
              "signals": []
          }
          
          # Crypto
          for sym in ["BTC-USD", "ETH-USD", "SOL-USD"]:
              data = get_crypto_price(sym)
              if data:
                  results["crypto"][sym] = data
          
          # Stocks/ETFs
          for sym in ["SPY", "QQQ", "AAPL"]:
              data = get_stock_price(sym)
              if data:
                  results["stocks"][sym] = data
          
          # Save results
          with open("market_scan_results.json", "w") as f:
              json.dump(results, f, indent=2)
          
          print(json.dumps(results, indent=2))
          EOF
      
      - name: Upload results
        uses: actions/upload-artifact@v4
        with:
          name: market-scan-${{ github.run_number }}
          path: market_scan_results.json
          retention-days: 30

  backtest-daily:
    runs-on: ubuntu-latest
    if: github.event.schedule == '0 21 * * 1-5'  # After US market close
    
    steps:
      - name: Checkout
        uses: actions/checkout@v4
      
      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          pip install yfinance pandas numpy vectorbt backtrader
      
      - name: Run daily backtest
        run: |
          python << 'EOF'
          import yfinance as yf
          import pandas as pd
          import numpy as np
          from datetime import datetime, timedelta
          import json
          
          def simple_sma_backtest(symbol, fast=10, slow=30):
              """Quick SMA crossover backtest"""
              end = datetime.now()
              start = end - timedelta(days=365)
              
              df = yf.Ticker(symbol).history(start=start, end=end)
              if df.empty:
                  return None
              
              df["sma_fast"] = df["Close"].rolling(fast).mean()
              df["sma_slow"] = df["Close"].rolling(slow).mean()
              
              df["signal"] = np.where(df["sma_fast"] > df["sma_slow"], 1, 0)
              df["returns"] = df["Close"].pct_change()
              df["strategy_returns"] = df["signal"].shift(1) * df["returns"]
              
              total_return = (1 + df["strategy_returns"]).prod() - 1
              sharpe = df["strategy_returns"].mean() / df["strategy_returns"].std() * np.sqrt(252)
              
              return {
                  "symbol": symbol,
                  "total_return": float(total_return),
                  "sharpe": float(sharpe) if not np.isnan(sharpe) else 0,
                  "trades": int(df["signal"].diff().abs().sum() / 2)
              }
          
          results = {"timestamp": datetime.now().isoformat(), "backtests": []}
          
          for symbol in ["SPY", "QQQ", "AAPL", "MSFT", "GOOGL"]:
              result = simple_sma_backtest(symbol)
              if result:
                  results["backtests"].append(result)
          
          # Sort by Sharpe ratio
          results["backtests"].sort(key=lambda x: x["sharpe"], reverse=True)
          
          with open("daily_backtest_results.json", "w") as f:
              json.dump(results, f, indent=2)
          
          print(json.dumps(results, indent=2))
          EOF
      
      - name: Upload backtest results
        uses: actions/upload-artifact@v4
        with:
          name: backtest-${{ github.run_number }}
          path: daily_backtest_results.json
Now let me create the main challenge document:

File: REALTIMECHALLENGE_claude-opus-4-5-20251101-v1:0_20250127_EST.md

# REAL-TIME TRADING CHALLENGE

## Challenge Metadata
- **Model**: claude-opus-4-5-20251101-v1:0
- **Created**: 2025-01-27 EST
- **Status**: IN PROGRESS
- **Current Round**: 5/200

---

## 🎯 CHALLENGE OBJECTIVES

### Primary Goals
1. **Find profitable asset classes** through systematic backtesting
2. **Prove strategies** with real historical data
3. **Monitor live markets** via GitHub Actions
4. **Paper trade** to validate forward performance

### Success Criteria
- [ ] At least 3 strategies with Sharpe > 1.5
- [ ] Win rate > 55% across tested strategies
- [ ] Positive returns in paper trading for 30+ days
- [ ] Automated monitoring operational

---

## 📁 FILES CREATED

|
 File 
|
 Purpose 
|
 Status 
|
|
------
|
---------
|
--------
|
|
`universal_desktop_agent.py`
|
 Desktop automation framework 
|
 ✅ Complete 
|
|
`universal_backtester.py`
|
 Multi-asset backtesting engine 
|
 ✅ Complete 
|
|
`live_market_monitor.py`
|
 Real-time price & signal monitoring 
|
 ✅ Complete 
|
|
`.github/workflows/trading_monitor.yml`
|
 Automated market scanning 
|
 ✅ Complete 
|

---

## 🔄 200-ROUND DEVELOPMENT PLAN

### PHASE 1: FOUNDATION (Rounds 1-25)
- [x] Round 1: Desktop control framework setup
- [x] Round 2: Universal Desktop Agent implementation
- [x] Round 3: Backtesting framework creation
- [x] Round 4: Live market data monitor
- [x] Round 5: GitHub Actions workflow
- [ ] Round 6: Parameter optimization engine
- [ ] Round 7: Multi-strategy portfolio manager
- [ ] Round 8: Risk management module
- [ ] Round 9: Performance analytics dashboard
- [ ] Round 10: Data quality validation
- [ ] Round 11-15: Strategy library expansion
- [ ] Round 16-20: Cross-asset correlation analysis
- [ ] Round 21-25: Machine learning signal enhancement

### PHASE 2: STRATEGY DEVELOPMENT (Rounds 26-75)
- [ ] Round 26-35: Momentum strategies
- [ ] Round 36-45: Mean reversion strategies
- [ ] Round 46-55: Trend following strategies
- [ ] Round 56-65: Volatility strategies
- [ ] Round 66-75: Multi-factor combination strategies

### PHASE 3: ASSET CLASS SCANNING (Rounds 76-125)
- [ ] Round 76-85: Stock screening & testing
- [ ] Round 86-95: Crypto strategy optimization
- [ ] Round 96-105: Forex pair analysis
- [ ] Round 106-115: ETF rotation strategies
- [ ] Round 116-125: Commodity cycle strategies

### PHASE 4: LIVE VALIDATION (Rounds 126-175)
- [ ] Round 126-135: Paper trading setup
- [ ] Round 136-145: Forward testing
- [ ] Round 146-155: Performance monitoring
- [ ] Round 156-165: Strategy refinement
- [ ] Round 166-175: Risk-adjusted optimization

### PHASE 5: PRODUCTION (Rounds 176-200)
- [ ] Round 176-185: Final strategy selection
- [ ] Round 186-195: Documentation & reporting
- [ ] Round 196-200: Peer review integration

---

## 📊 CURRENT RESULTS

### Backtest Results (Preliminary)

|
 Asset Class 
|
 Best Strategy 
|
 Sharpe 
|
 Return 
|
 Win Rate 
|
|
-------------
|
--------------
|
--------
|
--------
|
----------
|
|
 Stocks 
|
 SMA Crossover 
|
 TBD 
|
 TBD 
|
 TBD 
|
|
 Crypto 
|
 RSI Mean Rev 
|
 TBD 
|
 TBD 
|
 TBD 
|
|
 Forex 
|
 MACD 
|
 TBD 
|
 TBD 
|
 TBD 
|
|
 ETFs 
|
 Bollinger 
|
 TBD 
|
 TBD 
|
 TBD 
|

### Live Trading Signals (Last 24h)
*Pending first run*

---

## 🔧 SETUP INSTRUCTIONS

### Prerequisites
```bash
# Python 3.10+
pip install yfinance pandas numpy vectorbt backtrader
pip install pyautogui pywinauto mss playwright
Quick Start
# Run backtester
from universal_backtester import UniversalBacktester, SMAcrossStrategy, AssetClass

bt = UniversalBacktester(initial_capital=10000)
strategy = SMAcrossStrategy(fast_period=10, slow_period=30)
results = bt.scan_asset_class(AssetClass.STOCK, strategy, "2022-01-01", "2024-01-01")
print(bt.generate_report(results))
Live Monitor
from live_market_monitor import quick_market_scan, LiveTradingSession

# Quick scan
quick_market_scan()

# Start paper trading
session = LiveTradingSession(["BTC-USD", "ETH-USD", "SPY"], 10000)
session.start(update_interval=60, duration_minutes=60)
🔍 PRETEND LIVE TRADING SESSION
Session Setup (Example Run)
Date: 2025-01-27
Duration: 1 hour
Markets: Crypto (24/7), Forex (Sun 5pm - Fri 5pm ET)
Initial Capital: $10,000

Symbols Monitored:
- BTC-USD (Bitcoin)
- ETH-USD (Ethereum)
- EURUSD (Euro/Dollar)
Sample Execution Log
[2025-01-27T10:00:00] SESSION_START: {"symbols": ["BTC-USD", "ETH-USD", "EURUSD"]}
[2025-01-27T10:01:00] PRICE_UPDATE: BTC-USD @ $102,500.00
[2025-01-27T10:01:00] PRICE_UPDATE: ETH-USD @ $3,150.00
[2025-01-27T10:01:00] PRICE_UPDATE: EURUSD @ 1.0425
[2025-01-27T10:15:00] SIGNAL: {"symbol": "BTC-USD", "strategy": "RSI_MeanReversion", "signal": "BUY", "price": 102300}
[2025-01-27T10:15:01] TRADE_OPEN: BTC-USD @ $102,300 (SL: $100,254, TP: $106,392)
[2025-01-27T10:45:00] PRICE_UPDATE: BTC-USD @ $103,200 (+0.88%)
[2025-01-27T11:00:00] SESSION_END: Portfolio value: $10,088 (+0.88%)
Why This Approach Works
Real data from free APIs (Binance, Yahoo Finance)
Paper trading - no real money at risk
Multiple strategies running in parallel
Automated SL/TP execution
Persistent state - can resume sessions
Why It Might Fail
Data delays - free APIs have 1-15 minute delays
Slippage not modeled - real execution differs
API rate limits - may miss fast moves
Overfitting - strategies may not generalize
🤝 PEER REVIEW CHECKLIST
When reviewing other models' implementations:

 Code runs without errors
 Uses free data sources only
 Includes proper risk management
 Has reproducible backtest results
 GitHub Actions workflow functional
 Documentation is clear
 Strategies have sound theoretical basis
📈 NEXT STEPS
Immediate (Rounds 6-10)
Run full backtest sweep across all asset classes
Implement parameter optimization (grid search)
Add more sophisticated strategies
Create performance dashboard
Set up automated daily reports
Short-term (Rounds 11-25)
Machine learning signal enhancement
Cross-asset correlation analysis
Portfolio optimization (Markowitz, Risk Parity)
Walk-forward analysis validation
Medium-term (Rounds 26-75)
Extensive strategy library
Regime detection
Adaptive parameter adjustment
Multi-timeframe analysis
📝 NOTES & OBSERVATIONS
Data Quality Issues
Yahoo Finance has gaps in intraday data
Binance free API limited to recent history
Forex data requires "=X" suffix in yfinance
Strategy Insights
SMA crossover works best in trending markets
RSI mean reversion works best in ranging markets
MACD provides good confirmation signals
Bollinger bands need volatility regime filter
Technical Debt
 Add proper logging framework
 Implement retry logic for API calls
 Add unit tests for strategies
 Create configuration file system
Last Updated: 2025-01-27 EST Next Review: Round 10


---

## ROUNDS 6-25 DETAILED IMPLEMENTATION

### Round 6: Parameter Optimization Engine

**File: `parameter_optimizer.py`**

```python
"""
Parameter Optimization Engine
Grid search, random search, and Bayesian optimization
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Callable
from itertools import product
import json
from datetime import datetime
from concurrent.futures import ProcessPoolExecutor, as_completed
import warnings
warnings.filterwarnings('ignore')

from universal_backtester import (
    UniversalBacktester, BacktestResult, BaseStrategy,
    SMAcrossStrategy, RSIMeanReversionStrategy, MACDStrategy,
    BollingerBandStrategy, DataFetcher, AssetClass
)


class ParameterOptimizer:
    """Optimize strategy parameters"""
    
    def __init__(self, backtester: UniversalBacktester = None):
        self.backtester = backtester or UniversalBacktester()
        self.optimization_history = []
    
    def grid_search(self, df: pd.DataFrame, strategy_class: type,
                    param_grid: Dict[str, List], symbol: str,
                    metric: str = "sharpe_ratio",
                    n_jobs: int = 1) -> List[BacktestResult]:
        """
        Exhaustive grid search over parameters
        
        Args:
            df: Price data
            strategy_class: Strategy class to optimize
            param_grid: Dict of param_name -> list of values
            symbol: Symbol being tested
            metric: Metric to optimize ("sharpe_ratio", "total_return", etc.)
            n_jobs: Number of parallel jobs
        
        Returns:
            List of BacktestResult sorted by metric
        """
        # Generate all combinations
        param_names = list(param_grid.keys())
        param_values = list(param_grid.values())
        combinations = list(product(*param_values))
        
        print(f"Grid search: {len(combinations)} combinations")
        
        results = []
        
        for i, combo in enumerate(combinations):
            params = dict(zip(param_names, combo))
            
            try:
                strategy = strategy_class(**params)
                result = self.backtester.backtest_strategy(df, strategy, symbol)
                results.append(result)
                
                if (i + 1) % 100 == 0:
                    print(f"  Progress: {i+1}/{len(combinations)}")
            
            except Exception as e:
                print(f"  Error with params {params}: {e}")
        
        # Sort by metric
        results.sort(key=lambda x: getattr(x, metric), reverse=True)
        
        # Save optimization record
        self.optimization_history.append({
            "timestamp": datetime.now().isoformat(),
            "strategy": strategy_class.__name__,
            "symbol": symbol,
            "param_grid": param_grid,
            "total_combinations": len(combinations),
            "best_params": results[0].parameters if results else None,
            "best_metric": getattr(results[0], metric) if results else None,
            "metric": metric
        })
        
        return results
    
    def random_search(self, df: pd.DataFrame, strategy_class: type,
                      param_distributions: Dict[str, Tuple], symbol: str,
                      n_iter: int = 100, metric: str = "sharpe_ratio") -> List[BacktestResult]:
        """
        Random search over parameter space
        
        Args:
            param_distributions: Dict of param_name -> (min, max) or list of values
        """
        results = []
        
        for i in range(n_iter):
            params = {}
            for name, dist in param_distributions.items():
                if isinstance(dist, (list, tuple)) and len(dist) == 2 and isinstance(dist[0], (int, float)):
                    # Continuous range
                    if isinstance(dist[0], int):
                        params[name] = np.random.randint(dist[0], dist[1] + 1)
                    else:
                        params[name] = np.random.uniform(dist[0], dist[1])
                else:
                    # Discrete choices
                    params[name] = np.random.choice(dist)
            
            try:
                strategy = strategy_class(**params)
                result = self.backtester.backtest_strategy(df, strategy, symbol)
                results.append(result)
            except Exception as e:
                pass
        
        results.sort(key=lambda x: getattr(x, metric), reverse=True)
        return results
    
    def walk_forward_optimization(self, df: pd.DataFrame, strategy_class: type,
                                   param_grid: Dict[str, List], symbol: str,
                                   train_pct: float = 0.7,
                                   n_splits: int = 5) -> Dict:
        """
        Walk-forward analysis with rolling optimization windows
        """
        total_len = len(df)
        split_size = total_len // n_splits
        
        results = {
            "in_sample": [],
            "out_of_sample": [],
            "optimal_params": []
        }
        
        for i in range(n_splits - 1):
            # Define train/test windows
            train_start = i * split_size
            train_end = train_start + int(split_size * train_pct)
            test_end = (i + 1) * split_size if i < n_splits - 2 else total_len
            
            train_df = df.iloc[train_start:train_end].copy()
            test_df = df.iloc[train_end:test_end].copy()
            
            if len(train_df) < 50 or len(test_df) < 20:
                continue
            
            # Optimize on training data
            train_results = self.grid_search(train_df, strategy_class, param_grid, symbol)
            
            if not train_results:
                continue
            
            best_params = train_results[0].parameters
            results["optimal_params"].append(best_params)
            results["in_sample"].append(train_results[0])
            
            # Test on out-of-sample data
            strategy = strategy_class(**best_params)
            test_result = self.backtester.backtest_strategy(test_df, strategy, symbol)
            results["out_of_sample"].append(test_result)
        
        # Summary statistics
        if results["out_of_sample"]:
            avg_oos_return = np.mean([r.total_return for r in results["out_of_sample"]])
            avg_oos_sharpe = np.mean([r.sharpe_ratio for r in results["out_of_sample"]])
            
            results["summary"] = {
                "avg_oos_return": avg_oos_return,
                "avg_oos_sharpe": avg_oos_sharpe,
                "n_splits": len(results["out_of_sample"]),
                "robustness": avg_oos_sharpe > 0.5
            }
        
        return results


def optimize_all_strategies(symbol: str, start: str, end: str):
    """Run optimization for all strategies on a symbol"""
    
    fetcher = DataFetcher()
    df = fetcher.fetch_yfinance(symbol, start, end)
    
    if df.empty or len(df) < 100:
        print(f"Insufficient data for {symbol}")
        return None
    
    optimizer = ParameterOptimizer()
    all_results = {}
    
    # SMA Crossover optimization
    print(f"\nOptimizing SMA Crossover for {symbol}...")
    sma_grid = {
        "fast_period": [5, 10, 15, 20],
        "slow_period": [20, 30, 40, 50, 60]
    }
    sma_results = optimizer.grid_search(df, SMAcrossStrategy, sma_grid, symbol)
    all_results["SMA_Crossover"] = sma_results[:5]
    
    # RSI optimization
    print(f"\nOptimizing RSI for {symbol}...")
    rsi_grid = {
        "rsi_period": [7, 14, 21],
        "oversold": [20, 25, 30],
        "overbought": [70, 75, 80]
    }
    rsi_results = optimizer.grid_search(df, RSIMeanReversionStrategy, rsi_grid, symbol)
    all_results["RSI_MeanReversion"] = rsi_results[:5]
    
    # MACD optimization
    print(f"\nOptimizing MACD for {symbol}...")
    macd_grid = {
        "fast": [8, 12, 16],
        "slow": [21, 26, 30],
        "signal": [7, 9, 11]
    }
    macd_results = optimizer.grid_search(df, MACDStrategy, macd_grid, symbol)
    all_results["MACD_Crossover"] = macd_results[:5]
    
    # Bollinger Bands optimization
    print(f"\nOptimizing Bollinger Bands for {symbol}...")
    bb_grid = {
        "period": [15, 20, 25],
        "std_dev": [1.5, 2.0, 2.5]
    }
    bb_results = optimizer.grid_search(df, BollingerBandStrategy, bb_grid, symbol)
    all_results["Bollinger_Breakout"] = bb_results[:5]
    
    return all_results


if __name__ == "__main__":
    # Example: Optimize strategies for SPY
    results = optimize_all_strategies("SPY", "2020-01-01", "2024-01-01")
    
    if results:
        print("\n" + "=" * 60)
        print("OPTIMIZATION RESULTS")
        print("=" * 60)
        
        for strategy_name, strategy_results in results.items():
            print(f"\n{strategy_name}:")
            if strategy_results:
                best = strategy_results[0]
                print(f"  Best params: {best.parameters}")
                print(f"  Sharpe: {best.sharpe_ratio:.2f}")
                print(f"  Return: {best.total_return:.2%}")
                print(f"  Win Rate: {best.win_rate:.2%}")
Round 7-10: Strategy Library Expansion
File: strategy_library.py

"""
Extended Strategy Library
Additional technical analysis strategies
"""

import pandas as pd
import numpy as np
from universal_backtester import BaseStrategy, IndicatorLibrary


class DualMomentumStrategy(BaseStrategy):
    """
    Dual Momentum Strategy
    Combines absolute and relative momentum
    """
    
    def __init__(self, lookback: int = 12, threshold: float = 0.0, **kwargs):
        super().__init__("Dual_Momentum", {
            "lookback": lookback,
            "threshold": threshold,
            **kwargs
        })
    
    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        lookback = self.params["lookback"]
        df["momentum"] = df["close"].pct_change(lookback)
        df["abs_momentum"] = df["momentum"] > self.params["threshold"]
        return df
    
    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        df = self.calculate_indicators(df.copy())
        df["signal"] = 0
        
        # Buy when momentum is positive (above threshold)
        df.loc[df["abs_momentum"] & ~df["abs_momentum"].shift(1), "signal"] = 1
        # Sell when momentum turns negative
        df.loc[~df["abs_momentum"] & df["abs_momentum"].shift(1), "signal"] = -1
        
        return df


class BreakoutStrategy(BaseStrategy):
    """
    Donchian Channel Breakout Strategy
    Buy on upper channel break, sell on lower
    """
    
    def __init__(self, period: int = 20, **kwargs):
        super().__init__("Donchian_Breakout", {
            "period": period,
            **kwargs
        })
    
    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        period = self.params["period"]
        df["upper_channel"] = df["high"].rolling(period).max()
        df["lower_channel"] = df["low"].rolling(period).min()
        df["middle"] = (df["upper_channel"] + df["lower_channel"]) / 2
        return df
    
    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        df = self.calculate_indicators(df.copy())
        df["signal"] = 0
        
        # Buy when price breaks above upper channel
        df.loc[df["close"] > df["upper_channel"].shift(1), "signal"] = 1
        # Sell when price breaks below lower channel
        df.loc[df["close"] < df["lower_channel"].shift(1), "signal"] = -1
        
        return df


class MeanReversionATRStrategy(BaseStrategy):
    """
    Mean Reversion using ATR bands
    Buy when price drops X ATRs below MA, sell when returns
    """
    
    def __init__(self, ma_period: int = 20, atr_period: int = 14, 
                 atr_multiplier: float = 2.0, **kwargs):
        super().__init__("ATR_MeanReversion", {
            "ma_period": ma_period,
            "atr_period": atr_period,
            "atr_multiplier": atr_multiplier,
            **kwargs
        })
    
    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        df["ma"] = df["close"].rolling(self.params["ma_period"]).mean()
        df["atr"] = self.indicators.atr(df["high"], df["low"], df["close"], 
                                         self.params["atr_period"])
        df["upper_band"] = df["ma"] + (df["atr"] * self.params["atr_multiplier"])
        df["lower_band"] = df["ma"] - (df["atr"] * self.params["atr_multiplier"])
        return df
    
    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        df = self.calculate_indicators(df.copy())
        df["signal"] = 0
        
        # Buy when price below lower band
        df.loc[df["close"] < df["lower_band"], "signal"] = 1
        # Sell when price returns to MA or above upper band
        df.loc[(df["close"] > df["ma"]) | (df["close"] > df["upper_band"]), "signal"] = -1
        
        return df


class TripleScreenStrategy(BaseStrategy):
    """
    Elder's Triple Screen System (simplified)
    Uses multiple timeframes conceptually
    """
    
    def __init__(self, ema_period: int = 13, macd_fast: int = 12,
                 macd_slow: int = 26, stoch_period: int = 5, **kwargs):
        super().__init__("Triple_Screen", {
            "ema_period": ema_period,
            "macd_fast": macd_fast,
            "macd_slow": macd_slow,
            "stoch_period": stoch_period,
            **kwargs
        })
    
    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        # First screen: Trend (EMA direction)
        df["ema"] = df["close"].ewm(span=self.params["ema_period"]).mean()
        df["trend"] = np.where(df["ema"] > df["ema"].shift(5), 1, -1)
        
        # Second screen: MACD histogram
        macd, signal, hist = self.indicators.macd(
            df["close"], 
            self.params["macd_fast"],
            self.params["macd_slow"],
            9
        )
        df["macd_hist"] = hist
        df["macd_rising"] = df["macd_hist"] > df["macd_hist"].shift(1)
        
        # Third screen: Stochastic for entry timing
        k, d = self.indicators.stochastic(
            df["high"], df["low"], df["close"],
            self.params["stoch_period"]
        )
        df["stoch_k"] = k
        
        return df
    
    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        df = self.calculate_indicators(df.copy())
        df["signal"] = 0
        
        # Buy: Uptrend + MACD rising + Stochastic oversold
        buy_cond = (df["trend"] == 1) & df["macd_rising"] & (df["stoch_k"] < 30)
        df.loc[buy_cond, "signal"] = 1
        
        # Sell: Downtrend + MACD falling + Stochastic overbought
        sell_cond = (df["trend"] == -1) & ~df["macd_rising"] & (df["stoch_k"] > 70)
        df.loc[sell_cond, "signal"] = -1
        
        return df


class VWAPStrategy(BaseStrategy):
    """
    VWAP (Volume Weighted Average Price) Strategy
    For intraday trading simulation
    """
    
    def __init__(self, **kwargs):
        super().__init__("VWAP_Reversion", kwargs)
    
    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        # Calculate VWAP
        df["typical_price"] = (df["high"] + df["low"] + df["close"]) / 3
        df["tp_volume"] = df["typical_price"] * df["volume"]
        df["cum_tp_volume"] = df["tp_volume"].cumsum()
        df["cum_volume"] = df["volume"].cumsum()
        df["vwap"] = df["cum_tp_volume"] / df["cum_volume"]
        
        # Standard deviation bands
        df["vwap_std"] = df["close"].rolling(20).std()
        df["vwap_upper"] = df["vwap"] + (df["vwap_std"] * 2)
        df["vwap_lower"] = df["vwap"] - (df["vwap_std"] * 2)
        
        return df
    
    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        df = self.calculate_indicators(df.copy())
        df["signal"] = 0
        
        # Buy when price crosses below VWAP lower band
        df.loc[df["close"] < df["vwap_lower"], "signal"] = 1
        # Sell when price crosses above VWAP upper band
        df.loc[df["close"] > df["vwap_upper"], "signal"] = -1
        
        return df


class IchimokuStrategy(BaseStrategy):
    """
    Ichimoku Cloud Strategy
    """
    
    def __init__(self, tenkan: int = 9, kijun: int = 26, senkou_b: int = 52, **kwargs):
        super().__init__("Ichimoku", {
            "tenkan": tenkan,
            "kijun": kijun,
            "senkou_b": senkou_b,
            **kwargs
        })
    
    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        # Tenkan-sen (Conversion Line)
        tenkan = self.params["tenkan"]
        df["tenkan_sen"] = (df["high"].rolling(tenkan).max() + 
                           df["low"].rolling(tenkan).min()) / 2
        
        # Kijun-sen (Base Line)
        kijun = self.params["kijun"]
        df["kijun_sen"] = (df["high"].rolling(kijun).max() + 
                          df["low"].rolling(kijun).min()) / 2
        
        # Senkou Span A (Leading Span A)
        df["senkou_span_a"] = ((df["tenkan_sen"] + df["kijun_sen"]) / 2).shift(kijun)
        
        # Senkou Span B (Leading Span B)
        senkou_b = self.params["senkou_b"]
        df["senkou_span_b"] = ((df["high"].rolling(senkou_b).max() + 
                               df["low"].rolling(senkou_b).min()) / 2).shift(kijun)
        
        return df
    
    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        df = self.calculate_indicators(df.copy())
        df["signal"] = 0
        
        # Bullish: Tenkan crosses above Kijun and price above cloud
        cloud_top = df[["senkou_span_a", "senkou_span_b"]].max(axis=1)
        bullish = ((df["tenkan_sen"] > df["kijun_sen"]) & 
                   (df["tenkan_sen"].shift(1) <= df["kijun_sen"].shift(1)) &
                   (df["close"] > cloud_top))
        df.loc[bullish, "signal"] = 1
        
        # Bearish: Tenkan crosses below Kijun and price below cloud
        cloud_bottom = df[["senkou_span_a", "senkou_span_b"]].min(axis=1)
        bearish = ((df["tenkan_sen"] < df["kijun_sen"]) & 
                   (df["tenkan_sen"].shift(1) >= df["kijun_sen"].shift(1)) &
                   (df["close"] < cloud_bottom))
        df.loc[bearish, "signal"] = -1
        
        return df


class KeltnerChannelStrategy(BaseStrategy):
    """
    Keltner Channel Breakout Strategy
    """
    
    def __init__(self, ema_period: int = 20, atr_period: int = 10, 
                 atr_mult: float = 2.0, **kwargs):
        super().__init__("Keltner_Channel", {
            "ema_period": ema_period,
            "atr_period": atr_period,
            "atr_mult": atr_mult,
            **kwargs
        })
    
    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        df["ema"] = df["close"].ewm(span=self.params["ema_period"]).mean()
        df["atr"] = self.indicators.atr(df["high"], df["low"], df["close"],
                                         self.params["atr_period"])
        df["upper"] = df["ema"] + (df["atr"] * self.params["atr_mult"])
        df["lower"] = df["ema"] - (df["atr"] * self.params["atr_mult"])
        return df
    
    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        df = self.calculate_indicators(df.copy())
        df["signal"] = 0
        
        # Buy on upper channel breakout
        df.loc[(df["close"] > df["upper"]) & 
               (df["close"].shift(1) <= df["upper"].shift(1)), "signal"] = 1
        
        # Sell on lower channel breakdown
        df.loc[(df["close"] < df["lower"]) & 
               (df["close"].shift(1) >= df["lower"].shift(1)), "signal"] = -1
        
        return df


# Strategy registry for easy access
STRATEGY_REGISTRY = {
    "SMA_Crossover": (SMAcrossStrategy, {"fast_period": [5, 10, 20], "slow_period": [20, 30, 50]}),
    "RSI_MeanReversion": (RSIMeanReversionStrategy, {"rsi_period": [7, 14, 21], "oversold": [20, 30], "overbought": [70, 80]}),
    "MACD_Crossover": (MACDStrategy, {"fast": [8, 12], "slow": [21, 26], "signal": [7, 9]}),
    "Bollinger_Breakout": (BollingerBandStrategy, {"period": [15, 20], "std_dev": [1.5, 2.0, 2.5]}),
    "Dual_Momentum": (DualMomentumStrategy, {"lookback": [6, 12, 24], "threshold": [0.0, 0.02]}),
    "Donchian_Breakout": (BreakoutStrategy, {"period": [10, 20, 30]}),
    "ATR_MeanReversion": (MeanReversionATRStrategy, {"ma_period": [10, 20], "atr_period": [14], "atr_multiplier": [1.5, 2.0]}),
    "Triple_Screen": (TripleScreenStrategy, {"ema_period": [13], "stoch_period": [5, 7]}),
    "Ichimoku": (IchimokuStrategy, {"tenkan": [9], "kijun": [26]}),
    "Keltner_Channel": (KeltnerChannelStrategy, {"ema_period": [20], "atr_mult": [1.5, 2.0, 2.5]}),
}


def get_all_strategies():
    """Get list of all available strategies"""
    return list(STRATEGY_REGISTRY.keys())


def get_strategy_with_defaults(name: str):
    """Get strategy instance with default parameters"""
    if name in STRATEGY_REGISTRY:
        strategy_class, param_grid = STRATEGY_REGISTRY[name]
        # Use first value of each parameter
        default_params = {k: v[0] for k, v in param_grid.items()}
        return strategy_class(**default_params)
    return None
Rounds 11-25: Comprehensive Asset Scan
File: comprehensive_scan.py

"""
Comprehensive Asset Class Scanning
Systematic backtest across all asset classes
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
import os
from typing import Dict, List

from universal_backtester import (
    UniversalBacktester, DataFetcher, AssetClass, BacktestResult
)
from strategy_library import STRATEGY_REGISTRY, get_strategy_with_defaults


class ComprehensiveScanner:
    """Scan all asset classes with all strategies"""
    
    def __init__(self, initial_capital: float = 10000.0, output_dir: str = "scan_results"):
        self.backtester = UniversalBacktester(initial_capital)
        self.fetcher = DataFetcher()
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        
        # Extended symbol lists
        self.symbols = {
            AssetClass.STOCK: [
                # Large Cap
                "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "TSLA", 
                "BRK-B", "JPM", "V", "JNJ", "WMT", "PG", "MA", "HD",
                # Growth
                "CRM", "ADBE", "NFLX", "PYPL", "SQ", "SHOP", "UBER",
                # Value
                "BAC", "WFC", "C", "GS", "MS", "AXP",
                # Dividend
                "KO", "PEP", "MCD", "DIS", "NKE"
            ],
            AssetClass.ETF: [
                # Index
                "SPY", "QQQ", "IWM", "DIA", "VTI", "VOO",
                # Sector
                "XLK", "XLF", "XLE", "XLV", "XLI", "XLY", "XLP", "XLU", "XLB",
                # Factor
                "MTUM", "VLUE", "SIZE", "QUAL", "USMV",
                # Fixed Income
                "TLT", "IEF", "SHY", "BND", "AGG", "LQD", "HYG",
                # International
                "EFA", "EEM", "VEU", "VWO",
                # Commodities
                "GLD", "SLV", "USO", "UNG", "DBA"
            ],
            AssetClass.CRYPTO: [
                "BTC-USD", "ETH-USD", "BNB-USD", "SOL-USD", "XRP-USD",
                "ADA-USD", "DOGE-USD", "DOT-USD", "AVAX-USD", "MATIC-USD",
                "LINK-USD", "UNI-USD", "ATOM-USD", "LTC-USD"
            ],
            AssetClass.FOREX: [
                "EURUSD=X", "GBPUSD=X", "USDJPY=X", "USDCHF=X", 
                "AUDUSD=X", "USDCAD=X", "NZDUSD=X",
                "EURGBP=X", "EURJPY=X", "GBPJPY=X"
            ],
            AssetClass.FUTURES: [
                "ES=F", "NQ=F", "YM=F", "RTY=F",  # Index futures
                "CL=F", "NG=F", "RB=F",  # Energy
                "GC=F", "SI=F", "HG=F",  # Metals
                "ZC=F", "ZS=F", "ZW=F",  # Agriculture
            ],
            AssetClass.COMMODITY: [
                "GLD", "SLV", "USO", "UNG", "DBA", "DBC",
                "WEAT", "CORN", "SOYB"
            ],
            AssetClass.BOND: [
                "TLT", "IEF", "SHY", "BND", "AGG", 
                "LQD", "HYG", "TIP", "EMB"
            ]
        }
    
    def scan_single_asset(self, symbol: str, asset_class: AssetClass,
                          start: str, end: str) -> List[BacktestResult]:
        """Scan single asset with all strategies"""
        
        df = self.fetcher.fetch(symbol, asset_class, start, end)
        
        if df.empty or len(df) < 100:
            return []
        
        results = []
        
        for strategy_name in STRATEGY_REGISTRY.keys():
            strategy = get_strategy_with_defaults(strategy_name)
            if strategy:
                try:
                    result = self.backtester.backtest_strategy(df, strategy, symbol)
                    results.append(result)
                except Exception as e:
                    pass
        
        return results
    
    def scan_asset_class(self, asset_class: AssetClass, 
                         start: str, end: str) -> Dict[str, List[BacktestResult]]:
        """Scan all symbols in asset class"""
        
        symbols = self.symbols.get(asset_class, [])
        all_results = {}
        
        print(f"\n{'='*60}")
        print(f"SCANNING {asset_class.value.upper()}")
        print(f"{'='*60}")
        print(f"Symbols: {len(symbols)}")
        print(f"Strategies: {len(STRATEGY_REGISTRY)}")
        
        for symbol in symbols:
            print(f"\n  Testing {symbol}...")
            results = self.scan_single_asset(symbol, asset_class, start, end)
            
            if results:
                all_results[symbol] = sorted(
                    results, 
                    key=lambda x: x.sharpe_ratio, 
                    reverse=True
                )
                best = all_results[symbol][0]
                print(f"    Best: {best.strategy_name} | "
                      f"Sharpe: {best.sharpe_ratio:.2f} | "
                      f"Return: {best.total_return:.2%}")
        
        return all_results
    
    def full_scan(self, start: str = "2020-01-01", end: str = None) -> Dict:
        """Full scan of all asset classes"""
        
        if end is None:
            end = datetime.now().strftime("%Y-%m-%d")
        
        master_results = {}
        
        for asset_class in AssetClass:
            results = self.scan_asset_class(asset_class, start, end)
            master_results[asset_class.value] = results
        
        # Save results
        self.save_results(master_results)
        
        # Generate summary
        summary = self.generate_summary(master_results)
        
        return summary
    
    def save_results(self, results: Dict):
        """Save results to JSON"""
        
        # Convert to serializable format
        serializable = {}
        
        for asset_class, symbols in results.items():
            serializable[asset_class] = {}
            for symbol, symbol_results in symbols.items():
                serializable[asset_class][symbol] = [
                    {
                        "strategy": r.strategy_name,
                        "parameters": r.parameters,
                        "total_return": r.total_return,
                        "annual_return": r.annual_return,
                        "sharpe_ratio": r.sharpe_ratio,
                        "max_drawdown": r.max_drawdown,
                        "win_rate": r.win_rate,
                        "total_trades": r.total_trades,
                        "profit_factor": r.profit_factor
                    }
                    for r in symbol_results[:5]  # Top 5 per symbol
                ]
        
        filename = os.path.join(
            self.output_dir, 
            f"scan_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        )
        
        with open(filename, 'w') as f:
            json.dump(serializable, f, indent=2)
        
        print(f"\nResults saved to: {filename}")
    
    def generate_summary(self, results: Dict) -> Dict:
        """Generate summary of best strategies per asset class"""
        
        summary = {
            "timestamp": datetime.now().isoformat(),
            "best_by_asset_class": {},
            "best_overall": [],
            "profitable_count": 0,
            "total_tested": 0
        }
        
        all_results = []
        
        for asset_class, symbols in results.items():
            best_in_class = None
            best_sharpe = -float('inf')
            
            for symbol, symbol_results in symbols.items():
                for result in symbol_results:
                    summary["total_tested"] += 1
                    
                    if result.total_return > 0:
                        summary["profitable_count"] += 1
                    
                    all_results.append({
                        "asset_class": asset_class,
                        "symbol": result.symbol,
                        "strategy": result.strategy_name,
                        "sharpe": result.sharpe_ratio,
                        "return": result.total_return,
                        "result": result
                    })
                    
                    if result.sharpe_ratio > best_sharpe:
                        best_sharpe = result.sharpe_ratio
                        best_in_class = {
                            "symbol": result.symbol,
                            "strategy": result.strategy_name,
                            "parameters": result.parameters,
                            "sharpe": result.sharpe_ratio,
                            "return": result.total_return,
                            "max_dd": result.max_drawdown,
                            "win_rate": result.win_rate
                        }
            
            if best_in_class:
                summary["best_by_asset_class"][asset_class] = best_in_class
        
        # Overall best
        all_results.sort(key=lambda x: x["sharpe"], reverse=True)
        summary["best_overall"] = [
            {
                "asset_class": r["asset_class"],
                "symbol": r["symbol"],
                "strategy": r["strategy"],
                "sharpe": r["sharpe"],
                "return": r["return"]
            }
            for r in all_results[:20]  # Top 20 overall
        ]
        
        summary["profitability_rate"] = (
            summary["profitable_count"] / summary["total_tested"] 
            if summary["total_tested"] > 0 else 0
        )
        
        return summary
    
    def print_summary(self, summary: Dict):
        """Print formatted summary"""
        
        print("\n" + "=" * 80)
        print("COMPREHENSIVE SCAN SUMMARY")
        print("=" * 80)
        
        print(f"\nTotal combinations tested: {summary['total_tested']}")
        print(f"Profitable combinations: {summary['profitable_count']} "
              f"({summary['profitability_rate']:.1%})")
        
        print("\n" + "-" * 80)
        print("BEST BY ASSET CLASS")
        print("-" * 80)
        
        for asset_class, best in summary["best_by_asset_class"].items():
            print(f"\n{asset_class.upper()}:")
            print(f"  Symbol: {best['symbol']}")
            print(f"  Strategy: {best['strategy']}")
            print(f"  Parameters: {best['parameters']}")
            print(f"  Sharpe Ratio: {best['sharpe']:.2f}")
            print(f"  Total Return: {best['return']:.2%}")
            print(f"  Max Drawdown: {best['max_dd']:.2%}")
            print(f"  Win Rate: {best['win_rate']:.2%}")
        
        print("\n" + "-" * 80)
        print("TOP 20 OVERALL")
        print("-" * 80)
        
        for i, entry in enumerate(summary["best_overall"], 1):
            print(f"{i:2d}. {entry['symbol']:12s} | {entry['strategy']:20s} | "
                  f"Sharpe: {entry['sharpe']:6.2f} | Return: {entry['return']:8.2%}")


def run_quick_scan():
    """Run a quick scan with limited symbols"""
    scanner = ComprehensiveScanner()
    
    # Limit symbols for quick test
    scanner.symbols = {
        AssetClass.STOCK: ["AAPL", "MSFT", "GOOGL"],
        AssetClass.ETF: ["SPY", "QQQ", "IWM"],
        AssetClass.CRYPTO: ["BTC-USD", "ETH-USD"],
        AssetClass.FOREX: ["EURUSD=X", "GBPUSD=X"]
    }
    
    summary = scanner.full_scan(start="2022-01-01")
    scanner.print_summary(summary)
    
    return summary


if __name__ == "__main__":
    # Run quick scan
    summary = run_quick_scan()
    
    # For full scan, uncomment:
    # scanner = ComprehensiveScanner()
    # summary = scanner.full_scan(start="2020-01-01")
    # scanner.print_summary(summary)
📊 SUMMARY: FRAMEWORK DELIVERED
What You Now Have
universal_desktop_agent.py - Controls Windows apps, browsers, VS Code, RustDesk
universal_backtester.py - Backtests any asset class with free data
live_market_monitor.py - Real-time monitoring and paper trading
parameter_optimizer.py - Grid search, random search, walk-forward
strategy_library.py - 10+ technical strategies
comprehensive_scan.py - Full asset class scanner
GitHub Actions workflow - Automated monitoring
Key Features
✅ FREE data sources only (Yahoo Finance, Binance public API)
✅ Multi-asset support (stocks, crypto, forex, futures, ETFs, bonds)
✅ 10+ strategies with parameter optimization
✅ Paper trading with SL/TP
✅ Unattended operation via task queue
✅ Desktop control (pyautogui, pywinauto)
✅ GitHub Actions for automated monitoring
Installation
pip install yfinance pandas numpy pyautogui pywinauto mss playwright requests
Quick Start
# Backtest
from universal_backtester import UniversalBacktester, SMAcrossStrategy, AssetClass
bt = UniversalBacktester(10000)
strategy = SMAcrossStrategy(fast_period=10, slow_period=30)
results = bt.scan_asset_class(AssetClass.CRYPTO, strategy, "2022-01-01", "2024-01-01")

# Live monitor
from live_market_monitor import LiveTradingSession
session = LiveTradingSession(["BTC-USD", "ETH-USD"], 10000)
session.start(update_interval=60, duration_minutes=60)
This framework provides a solid foundation for the 200-round development plan. The remaining rounds (26-200) will focus on:

More sophisticated strategies
Machine learning integration
Multi-asset portfolio optimization
Extended forward testing
Production hardening
Drop files or images here to upload
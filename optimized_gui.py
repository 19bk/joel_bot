import random
from PyQt5.QtWidgets import QApplication, QWidget, QHBoxLayout, QVBoxLayout, QPushButton, QTextEdit, QLabel
from pybit.unified_trading import HTTP
import ccxt
from time import sleep
import sys
from PyQt5.QtCore import pyqtSignal, QThread, QDateTime, QObject
from PyQt5.QtCore import QTimer

symbol='SOLUSDT'
leverage="10"

class PnlThread(QThread):
    pnl_updated = pyqtSignal(float, float,float, str, str)  # Add a signal for error handling

    def __init__(self, session, symbol):
        super().__init__()
        
        self.session = session
        self.symbol = symbol

    def run(self):
        while True:
            try:
                data = self.session.get_positions(category="linear", symbol=self.symbol)
                # print(data)
                pnl_value = data['result']['list'][0]['unrealisedPnl']
                actual_pnl_value = 0
                if pnl_value:
                    pnl = round(float(pnl_value), 2)
                else:
                    pnl = 0.0

                if actual_pnl_value:
                    actual_pnl_value = round(float(actual_pnl_value), 2)
                else:
                    actual_pnl_value = 0.0

                balance = self.session.get_wallet_balance(accountType="UNIFIED", coin="USDT")
                account_balance = round(float(balance['result']['list'][0]['coin'][0]['equity']), 2)
                loc_side = data['result']['list'][0]['side']
                self.pnl_updated.emit(pnl, actual_pnl_value, account_balance, loc_side, None)  # Emit the updated values
            except Exception as e:
                # print(e)
                self.pnl_updated.emit(0.0, 0.0,0.0, "", str(e))  # Emit an error signal

            self.msleep(50)  # Adjust the sleep interval

class MyApp(QWidget):
    pnl_updated = pyqtSignal(float, float, str)

    def __init__(self, key, secret, testnet=False):
        super().__init__()
        self.initUI()
        self.session = self.init_session(key, secret, testnet)
        self.symbol = symbol
        self.leverage = leverage
        self.pnl_thread = None  # Initialize the thread reference
        self.position_closed = False


    def start_pnl_thread(self):
        self.pnl_thread = PnlThread( self.session, self.symbol)
        self.pnl_thread.pnl_updated.connect(self.update_pnl_and_balance_ui)
        self.pnl_thread.start()
    
    def delayed_order(self, chosen_side):
        if chosen_side == "Sell":
            self.sell_clicked()
        else:
            self.buy_clicked()

    def update_pnl_and_balance_ui(self, pnl, realized_pnl, balance, emitted_side, error_message):
        # Avoid locking the mutex here
        side_color = 'green' if emitted_side == "Buy" else 'red'
        pnl_color = 'green' if pnl >= 0.0 else 'red'
        true_pnl_color = 'green' if realized_pnl >= 0.0 else 'red'
        self.pos_side.setText(f"<font color='{side_color}'><b>Side:</b> {emitted_side}</font>")
        self.pnl_label.setText(f"<font color='{pnl_color}'><b>PNL:</b> {pnl}</font>")
        # self.true_pnl_label.setText(f"<font color='{true_pnl_color}'><b>Actual PNL:</b> {realized_pnl}</font>")
        self.balance_label.setText(f"Balance: {balance}")
        if error_message:
            # self.textbox.append(f"update_pnl_and_balance_ui Error: {error_message} /n")
            pass
    def init_session(self, key, secret, testnet):
        # Initialize the trading session with the provided API key, secret, and testnet flag
        try:
            return HTTP(api_key=key, api_secret=secret, testnet=testnet)
        except Exception as e:
            print(f"here {e}")

 

    def initUI(self):
        # Initialize the user interface (UI) layout
        layout = QVBoxLayout()
        button_layout = QHBoxLayout()
        pnl_balance_layout = QVBoxLayout()
        buttons = [("Buy", self.buy_clicked), ("Sell", self.sell_clicked)]
        self.textbox = QTextEdit(self)
        self.textbox.setReadOnly(True)

        # Create labels for PNL and account balance
        self.pos_side = QLabel(self)
        self.pnl_label = QLabel(self)
        # self.true_pnl_label = QLabel(self)
        self.balance_label = QLabel(self)
        
        pnl_balance_layout.addWidget(self.pos_side)
        pnl_balance_layout.addWidget(self.pnl_label)
        pnl_balance_layout.addWidget(self.balance_label)

        for name, action in buttons:
            btn = QPushButton(name, self)
            btn.clicked.connect(action)
            button_layout.addWidget(btn)

        # Create and add the Close Position button
        close_position_btn = QPushButton("Close Position", self)
        close_position_btn.clicked.connect(self.close_position_clicked)

        layout.addLayout(button_layout)
        layout.addWidget(self.textbox)
        layout.addLayout(pnl_balance_layout)
        layout.addWidget(close_position_btn)  # Add the button to the layout

        self.setLayout(layout)
        self.setWindowTitle('Auto Trading App')
        self.show()
    
    def buy_clicked(self):
        self.position_closed = False
        self.clicked("Buy")
        

    def sell_clicked(self):
        self.position_closed = False
        self.clicked("Sell")

    def clicked(self, side):
        timestamp = QDateTime.currentDateTime().toString("yyyy-MMM-dd hh:mm:ss ")
        if side == "Close":
            self.textbox.append("<font face='Roboto' color='#FFAA00'>{1} <b>| {0} </b></font>".format(side, timestamp))
            return
        if side == "NO_CLOSE_POS":
            self.textbox.append("<font face='Roboto' color='turquoise'>{1} <b>| {0} </b></font>".format("No position to close ", timestamp))
            print("No position to close")
            return
        ticker_price = self.get_ticker_price()
        available_balance = self.get_available_balance()
        order_quantity = self.calculate_order_quantity(available_balance, ticker_price, leverage)
        # print(order_quantity)
        self.set_leverage()
        self.place_order(order_quantity, side)
        my_entry = self.get_entry_price()
        position_qty = self.get_position_quantity()
        print(position_qty)
        self.set_take_profit_stop_loss(position_qty, my_entry, side)

        if side == "Buy":
            self.textbox.append("<font face='Roboto' color='green'>{1} <b>| {0} </b></font>".format(side, timestamp))
        elif side == "Sell":
            self.textbox.append("<font face='Roboto' color='red'>{1} <b>| {0} </b></font>".format(side, timestamp))
        
    def get_max_leverage(self):
        max_lev_data = self.session.get_risk_limit(
                                                category="linear",
                                                symbol=symbol,
                                            )
        return max_lev_data
           
    def close_position_clicked(self):
        # print("close clicked /n")
        self.position_closed = True
        data = self.session.get_positions(category="linear",symbol=symbol)
        Qty = data['result']['list'][0]['size']
        position_side = data['result']['list'][0]['side']
        if position_side != '':
            self.session.place_order(category="linear", symbol=symbol, side=("Sell" if position_side == "Buy" else "Buy"),
                                                orderType="Market", qty=str(Qty), reduceOnly=True,
                                                timeInForce="PostOnly", positionIdx="0")
            self.clicked("Close")
            print("Position Closed")
        else:
            self.clicked("NO_CLOSE_POS")
            # self.textbox.append(f"No position to close: {position_side} ")

    def getSide(self, side):
        if side == "Buy":
            self.pos_side.setText(f"<font color='green'><b>Side:</b> {side}</font>")
        else:
            self.pos_side.setText(f"<font color='red'><b>Side:</b> {side}</font>")
            
    def get_ticker_price(self):
        # Get the current ticker price 
        ticker_price = self.session.get_tickers(category="linear", symbol=symbol)
        # print(ticker_price)
        return float(ticker_price['result']['list'][0]['markPrice'])  # Change 'lastPrice' to 'markPrice'

    def get_available_balance(self):
        # Get the available balance in the account
        balance = self.session.get_coins_balance(accountType="UNIFIED", coin="USDT")
        return float(balance['result']['balance'][0]['transferBalance'])
    
    def calculate_decimal_quantity(self, num):
        # Take the integer part of the number
        integer_part = int(num)
        
        # Get the number of digits of the integer part
        digit_count = len(str(integer_part))
        
        if digit_count == 5:
            return 3
        elif 2 <= digit_count <= 4:
            return 2
        elif integer_part == 0:
            return 0
        elif digit_count == 1:
            return 1

    def calculate_order_quantity(self, available_balance, ticker_price, leverage):
        # Calculate the order quantity based on available balance, ticker price, and leverage
        decimal_qty = self.calculate_decimal_quantity(ticker_price)
        # print(f"available balance {available_balance}")
        # print(f"ticker price {ticker_price}")
        # print(f"leverage {leverage}")
        calculated_order_quantity_ = ((available_balance * int(leverage)) / ticker_price) * .9
        # print(f"calc order qty {calculated_order_quantity_}")
        calculated_order_quantity = round(calculated_order_quantity_, decimal_qty)
        # print(f"rounded calc ord qty {(calculated_order_quantity)}")
        return calculated_order_quantity
    
    def set_leverage(self):
        # lev = self.get_max_leverage()
        # print(lev)
        # Set the leverage for trading
        try:
            self.session.set_leverage(category="linear", symbol=symbol, buyLeverage=leverage, sellLeverage=leverage)
        except Exception as e:
            # print(f"set leverage {e}")
            pass

    def place_order(self, order_quantity, side):
        # Place a market order with the specified order quantity and side
        # print(type(self.calculate_order_quantity()))
        try:
            self.set_margin_mode()
            my_order = self.session.place_order(category="linear", symbol=symbol, side=str(side), orderType="Market",
                                                qty=str(order_quantity))
            return my_order['result']['orderId']
        except Exception as e:
            # self.textbox.append(f"place_order Failed: {e} /n")
            print(e)
            return None

    def get_entry_price(self):
        # Get the entry price of the current position
        try:
            data = self.session.get_positions(category="linear",symbol=self.symbol,)
            entryPrice = data['result']['list'][0]['avgPrice']
            return entryPrice
        except Exception as e:
            print(e)
            return None

    def get_position_quantity(self):
        # Get the quantity of the current position
        try:
            data = self.session.get_positions(category="linear",symbol=self.symbol,)
            Qty = data['result']['list'][0]['size']
            # print(Qty)
            return Qty
        except Exception as e:
            print(e)
            return None
        
    def set_margin_mode(self):
        return self.session.set_margin_mode(
        setMarginMode="ISOLATED_MARGIN",)

    def set_take_profit_stop_loss(self, position_qty, my_entry, side):
        # Set the take profit and stop loss levels for the current position
        self.myTakeProfit = float(my_entry) * (1.015 if side == "Buy" else 0.985)
        # print(f"tp {self.myTakeProfit}")
        self.myStopLoss = float(my_entry) * (0.990 if side == "Buy" else 1.010)
        # print(f"sl {self.myStopLoss}")
        try:
            # Set the trading stop (stop loss) level
            self.session.set_trading_stop(category="linear", symbol=symbol, stopLoss=str(self.myStopLoss), positionIdx=0)
        except Exception as e:
            print(f"set_trading_stop_ loss :: {e}")
        try:
            # Place a limit order for take profit
            self.session.place_order(category="linear", symbol=symbol, side=("Sell" if side == "Buy" else "Buy"),
                                     orderType="Limit", qty=str(position_qty), price=str(self.myTakeProfit), reduceOnly=True,
                                     timeInForce="PostOnly")
            print(f"{side} position placed")
        except Exception as e:
            print(f"set_take_profit :: {e}")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = MyApp("LUTr5ux8UK85oMM5Tj", "tSbq88myGBidovLvlIxAbDlbVpmRgdyYklBv")
    ex.start_pnl_thread()
    sys.exit(app.exec_())
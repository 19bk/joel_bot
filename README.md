
# Auto Trading App ReadMe

## Overview
This Python application automates trading on the ByBit exchange, leveraging the PyQt5 library for the user interface and the PyBit library for API communication. It facilitates executing buy and sell orders, monitoring positions, and setting stop-loss and take-profit levels.

## Requirements
- Python 3.x
- PyQt5
- pybit
- ccxt

Install the required libraries using pip:
```bash
pip install PyQt5 pybit ccxt
```

## Usage
### API Key Configuration
Before running the application, configure your API key and secret:
```python
key = "YOUR_API_KEY"
secret = "YOUR_API_SECRET"
```

### Symbol and Leverage Configuration
Set the trading symbol and leverage in the code:
```python
symbol = 'SOLUSDT'
leverage = "10"
```

### Running the Application
Execute the script to launch the user interface. It allows you to:
- Buy: Execute a buy order.
- Sell: Execute a sell order.
- Close Position: Close the current position.
- Monitor real-time PNL, position side, and account balance.

### Error Handling
The application handles API request errors and displays issues in the user interface.

### Logging
Trading actions and error messages are logged in the UI's text box.

## Features
- Automated market order trading.
- Real-time PNL monitoring.
- Configurable stop-loss and take-profit.
- User-friendly GUI.

## Disclaimer
This application is for educational purposes and should be used with caution in real trading. Understand trading and risk management thoroughly before use. The developer is not liable for any financial losses. Use at your own risk and test in a simulated environment first.

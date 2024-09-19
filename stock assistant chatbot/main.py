import json
import openai
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
import yfinance as yf


openai.api_key = open('api_key', 'r').read()

def get_stock_price(ticker):
    return str(yf.Ticker(ticker).history(period='1y').iloc[-1]['Close'])

def calculate_SMA(ticker, window):
    data = yf.Ticker(ticker).history(period='1y').Close
    return str(data.rolling(window=window).mean().iloc[-1])

def calculate_EMA(ticker, window):
    data = yf.Ticker(ticker).history(period='1y').Close
    return str(data.ewm(span=window, adjust=False).mean().iloc[-1])

def calculate_RSI(ticker):
    data = yf.Ticker(ticker).history(period='1y').Close
    delta = data.diff()
    up = delta.clip(lower=0)
    down = -1 * delta.clip(upper=0)
    ema_up = up.ewm(com=14 - 1, adjust=False).mean()
    ema_down = down.ewm(com=14 - 1, adjust=False).mean()
    rs = ema_up / ema_down
    return str(100 - (100 / (1 + rs)).iloc[-1])

def calculate_MACD(ticker):
    data = yf.Ticker(ticker).history(period='1y').Close
    short_EMA = data.ewm(span=12, adjust=False).mean()
    long_EMA = data.ewm(span=26, adjust=False).mean()
    MACD = short_EMA - long_EMA
    signal = MACD.ewm(span=9, adjust=False).mean()
    MACD_histogram = MACD - signal
    return f'{MACD[-1]}, {signal[-1]}, {MACD_histogram[-1]}'

def plot_stock_price(ticker):
    data = yf.Ticker(ticker).history(period='1y').Close
    plt.figure(figsize=(10, 5))
    plt.plot(data.index, data.Close)
    plt.title(f'{ticker} Stock Price Over Last Year')
    plt.xlabel('Date')
    plt.ylabel('Stock Price')
    plt.grid(True)
    plt.savefig('stock.png')
    plt.Close()

functions = [
    {
        "name": "get_stock_price",
        "description": "Get the stock price of a given ticker", 
        "parameters":{
            'type' : 'object',
            "properties": {
                "ticker": {
                    "type": "string",
                    "description": "The ticker of the stock to get the price for "
                }
            },
            "required": ["ticker"]
        }
    },
    {
        "name": "calculate_SMA",
        "description": "Calculate the Simple Moving Average (SMA) of a given ticker",
        "parameters":{
            'type' : 'object',
            "properties": {
                "ticker": {
                    "type": "string",
                    "description": "The ticker of the stock to calculate the SMA for "
              },
            "window":{
                "type": "integer",
                "description": "The window size for the SMA calculation"
            }
        },
        "required": ["ticker", "window"],
    },

},
    {
        "name": "calculate_EMA",
        "description": "Calculate the Exponential Moving Average (EMA) of a given ticker",
        "parameters":{
            'type' : 'object',
            "properties": {
                "ticker": {
                    "type": "string",
                    "description": "The ticker of the stock to calculate the EMA for "

                
            },
            "window":{
                "type": "integer",
                "description": "The window size for the EMA calculation"
            }
            },
            "required": ["ticker", "window"],
        },
    },
    {
        "name": "calculate_RSI",
        "description": "Calculate the Relative Strength Index (RSI) of a given ticker",
        "parameters":{
            'type' : 'object',
            "properties": {

                "ticker": {
                    "type": "string",
                    "description": "The ticker of the stock to calculate the RSI for "
                },

                },
            
            "required": ["ticker"],
        },
    },
    {
        "name": "calculate_MACD",
        "description": "Calculate the Moving Average Convergence Divergence (MACD) of a given ticker",
        "parameters":{
            'type' : 'object',
            "properties": {
                "ticker": {
                    "type": "string",
                    "description": "The ticker of the stock to calculate the MACD for "
                },
                
            },
            "required": ["ticker"],
        },
    },
    {
        "name": "plot_stock_price",
        "description": "Plot the stock price of a given ticker",
        "parameters":{
            'type' : 'object',
            "properties": {
                "ticker": {
                    "type": "string",
                    "description": "The ticker of the stock to plot the price for "
                },
            },
            "required": ["ticker"],
        },
    },
]


available_functions ={
    "get_stock_price": get_stock_price,
    "calculate_SMA": calculate_SMA,
    "calculate_EMA": calculate_EMA,
    "calculate_RSI": calculate_RSI,
    "calculate_MACD": calculate_MACD,
    "plot_stock_price": plot_stock_price
}

if 'messages' not in st.session_state:
    st.session_state.messages = []

st.title('Stock Analysis App')
user_input = st.text_input('Enter a command')
if user_input:
    try:
        st.session_state['messages'].append({"role": "user", "content": user_input})

        response = openai.ChatCompletion.create(
            model = "gpt-3.5-turbo",
            messages = st.session_state['messages'],
            functions=functions,
            function_call="auto"
        )

        response_message = response.choices[0].message

        if response_message.get('function_call'):
            function_name = response_message['function_call']['name']
            function_args = json.load(response_message['function_call']['arguments'])

            if function_name in ['get_stock_price', 'calculate_SMA', 'calculate_EMA', 'calculate_RSI', 'calculate_MACD', 'plot_stock_price']:
                args_dict = {'ticker': function_args.get('ticker')}
            elif function_name in ['calculate_SMA', 'calculate_EMA']:
                args_dict = {'ticker': function_args.get('ticker'), 'window': function_args.get('window')}


            function_to_call = available_functions[function_name]
            function_response = function_to_call(**args_dict) 

            if function_name == 'plot_stock_price':
                st.image('stock.png')
            else:
                st.session_state['messages'].append(response_message)
                st.session_state['messages'].append(
                    {
                        "role": "function",
                        'name': function_name,
                        'content': function_response
                    }
                )
                second_response = openai.ChatCompletion.create(
                    model = "gpt-3.5-turbo",
                    messages = st.session_state['messages']
                   
                )
                st.text(second_response['choices'][0]['message']['content'])
                st.session_state['messages'].append({'role':'assistant','content': second_response['choices'][0]['message']['content']})
        else:
            st.text(response_message['content'])
            st.session_state['messages'].append({'role':'assistant','content': response_message['content']})

    except Exception as e:
        st.text('Error occurred,'+ str(e))

    # try:
    # # your API call
    # except openai.error.RateLimitError as e:
    #     st.error(f"Quota exceeded: {e}")

            
                













# LIVETRADE - Kraken Limit Order Bot

A simple trading bot for placing limit orders on Kraken cryptocurrency exchange.

## Overview

This bot is designed to automatically place limit orders on Kraken based on predefined price targets. It uses the pykrakenapi library for exchange interactions.

## Prerequisites

- Python 3.8+
- Kraken account with API keys
- Sufficient balance in your Kraken account

## Installation

1.Clone the repository

```bash
git clone https://github.com/Rovis91/LiveTrade
cd LIVETRADE
```

2.Create and activate virtual environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3.Install dependencies

```bash
pip install -r requirements.txt
```

4.Configure environment variables

- Copy `.env.example` to `.env`
- Add your Kraken API credentials

## Configuration

The bot uses two types of configuration:

- `.env` file for API credentials
- JSON configuration files in `config/` for trading parameters

## Features

- Limit order placement
- Balance verification
- Order tracking
- Basic error handling
- Logging system

## Safety Features

- Input validation
- Balance checks
- Order validation before placement
- Rate limiting compliance

## Logging

Logs are stored in the `logs/` directory with:

- Transaction history
- Error logs
- System status

## Contributing

1. Fork the repository
2. Create your feature branch
3. Submit a pull request

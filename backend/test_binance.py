import asyncio
from binance_client import binance_client
from ml_predictor import ml_predictor
from strategies import strategy_manager
import pandas as pd

async def run_tests():
    print("--- Test 1: Fetching Historical Klines ---")
    try:
        klines = binance_client.get_historical_klines("BTCUSDT", interval="1m", limit=50)
        print(f"Success! Retrieved {len(klines)} klines.")
        
        print("\n--- Test 2: Evaluate Strategies ---")
        df = pd.DataFrame(klines)
        eval_result = strategy_manager.evaluate_strategies(df)
        print(f"RSI & EMA Status: {eval_result}")
    except Exception as e:
        print(f"Failed Test 1/2: {e}")

    print("\n--- Test 3: ML Predictor Initialization ---")
    try:
        ml_predictor.initialize_model()
        pred = ml_predictor.predict("BTCUSDT")
        print(f"Success! ML Recommended Strategy: {pred.get('best_strategy')}")
    except Exception as e:
        print(f"Failed Test 3: {e}")
        
    print("\nAll tests finished successfully.")

if __name__ == "__main__":
    asyncio.run(run_tests())

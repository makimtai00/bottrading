import { useEffect, useState, useRef } from 'react'
import { Activity, Zap, TrendingUp, BarChart2 } from 'lucide-react'
import TradingChart from './components/TradingChart'
import StrategyPanel from './components/StrategyPanel'
import OrderPanel from './components/OrderPanel'

const SYMBOLS = [
    "BTCUSDT", "ETHUSDT",
    "PNUTUSDT", "MANAUSDT", "KAITOUSDT", "NEARUSDT", "GMTUSDT", "TONUSDT", "GOATUSDT",
    "PONKEUSDT", "SAFEUSDT", "AVAUSDT", "TOKENUSDT", "MOCAUSDT", "PEOPLEUSDT", "SOLUSDT",
    "SUIUSDT", "DOGEUSDT", "ENAUSDT", "MOVEUSDT", "ADAUSDT", "TURBOUSDT", "NEIROUSDT",
    "AVAXUSDT", "DOTUSDT", "XRPUSDT", "NEIROETHUSDT", "LINKUSDT", "XLMUSDT", "ZECUSDT",
    "ATOMUSDT", "BATUSDT", "NEOUSDT", "QTUMUSDT"
]

export default function App() {
    const [symbol, setSymbol] = useState(SYMBOLS[0])
    const [interval, setInterval] = useState('5m')

    return (
        <div className="min-h-screen flex flex-col">
            {/* Header */}
            <header className="bg-dark-800 border-b border-dark-700 p-4 shadow-md">
                <div className="max-w-7xl mx-auto flex items-center justify-between">
                    <div className="flex items-center gap-3">
                        <div className="bg-brand-blue/20 p-2 rounded-lg">
                            <Activity className="text-brand-blue w-6 h-6" />
                        </div>
                        <h1 className="text-xl font-bold tracking-tight">AI Scalping Bot</h1>
                    </div>

                    <div className="flex gap-4 items-center">
                        <div className="flex flex-col md:flex-row gap-2 md:items-center">
                            <span className="text-sm text-gray-400 hidden md:block">Timeframe</span>
                            <select
                                className="bg-dark-700 border border-dark-600 rounded-md px-3 py-1.5 focus:outline-none focus:ring-2 focus:ring-brand-blue"
                                value={interval}
                                onChange={(e) => setInterval(e.target.value)}
                            >
                                <option value="5m">5 Minutes</option>
                                <option value="15m">15 Minutes</option>
                            </select>
                        </div>
                        <div className="flex flex-col md:flex-row gap-2 md:items-center">
                            <span className="text-sm text-gray-400 hidden md:block">Trading Pair</span>
                            <select
                                className="bg-dark-800 border-dark-600 text-gray-200 text-sm rounded-lg focus:ring-brand-blue focus:border-brand-blue block p-2"
                                value={symbol}
                                onChange={(e) => setSymbol(e.target.value)}
                            >
                                {SYMBOLS.map(sym => (
                                    <option key={sym} value={sym}>{sym}</option>
                                ))}
                            </select>
                        </div>
                    </div>
                </div>
            </header>

            {/* Main Content */}
            <main className="flex-1 max-w-7xl w-full mx-auto p-4 md:p-6 grid grid-cols-1 lg:grid-cols-3 gap-6">

                {/* Left Col: Chart */}
                <div className="lg:col-span-2 flex flex-col gap-6">
                    <div className="bg-dark-800 rounded-xl border border-dark-700 overflow-hidden shadow-lg flex flex-col">
                        <div className="p-4 border-b border-dark-700 flex justify-between items-center">
                            <h2 className="font-semibold flex items-center gap-2">
                                <BarChart2 className="w-5 h-5 text-brand-green" />
                                Live Chart ({interval})
                            </h2>
                            <div className="flex gap-2">
                                <span className="flex h-2 w-2 relative mt-1.5">
                                    <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-brand-green opacity-75"></span>
                                    <span className="relative inline-flex rounded-full h-2 w-2 bg-brand-green"></span>
                                </span>
                                <span className="text-xs text-gray-400">WebSocket Connected</span>
                            </div>
                        </div>
                        <div className="h-[450px] w-full p-2 relative">
                            <TradingChart symbol={symbol} interval={interval} />
                        </div>
                    </div>
                </div>

                {/* Right Col: ML Insights & Auto Orders */}
                <div className="flex flex-col gap-6">
                    <StrategyPanel symbol={symbol} interval={interval} />
                    <OrderPanel />
                </div>

            </main>
        </div>
    )
}


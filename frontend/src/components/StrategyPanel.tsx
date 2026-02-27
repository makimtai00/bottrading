import { useState, useEffect } from 'react'
import { Zap, Cpu, Target, ShieldAlert, Crosshair } from 'lucide-react'

interface Prediction {
    strategy: string
    win_probability: number
    is_recommended: boolean
}

interface TradeSetup {
    direction: string
    entry_price: number
    take_profit_price: number
    stop_loss_price: number
    estimated_win_rate: number
}

interface SMCState {
    bos_bullish: boolean
    bos_bearish: boolean
    fvg_bullish: boolean
    fvg_bearish: boolean
    in_ob_bullish: boolean
    in_ob_bearish: boolean
}

interface MLData {
    timestamp: number
    symbol: string
    interval: string
    btc_global_trend: string
    best_strategy: string
    trade_setup: TradeSetup
    all_predictions: Prediction[]
    smc_state?: SMCState
}

interface Props {
    symbol: string
    interval: string
}

export default function StrategyPanel({ symbol, interval }: Props) {
    const [data, setData] = useState<MLData | null>(null)
    const [loading, setLoading] = useState(true)

    useEffect(() => {
        let fetchTimer: NodeJS.Timeout

        const fetchMLData = async () => {
            try {
                const res = await fetch(`http://localhost:8000/api/v1/ml/predict/${symbol}?interval=${interval}`)
                if (res.ok) {
                    const json = await res.json()
                    setData(json.prediction)
                }
            } catch (error) {
                console.error("Lỗi tải dự đoán AI:", error)
            } finally {
                setLoading(false)
            }
        }

        fetchMLData()
        // Tự động làm mới gợi ý AI sau mỗi 5 giây
        fetchTimer = setInterval(fetchMLData, 5000)

        return () => clearInterval(fetchTimer)
    }, [symbol, interval])

    return (
        <div className="bg-dark-800 rounded-xl border border-dark-700 p-5 shadow-lg flex flex-col gap-4">
            <div className="flex justify-between flex-wrap gap-2 items-center border-b border-dark-700 pb-3">
                <h2 className="font-semibold flex items-center gap-2">
                    <Cpu className="text-brand-blue w-5 h-5" />
                    AI Strategy Insights
                </h2>
                {loading ? (
                    <span className="text-xs text-gray-400 animate-pulse">Analyzing market...</span>
                ) : (
                    <span className="text-xs bg-dark-700 px-2 py-1 rounded text-gray-300">Live AI</span>
                )}
            </div>

            <div className="flex flex-col gap-4">
                {data ? (
                    <>
                        {/* BTC Trend Filter Indicator */}
                        <div className="bg-dark-900 border border-dark-700 rounded-lg p-3 flex justify-between items-center">
                            <span className="text-sm text-gray-400">BTC Overall Trend</span>
                            <span className={`text-sm font-semibold ${data.btc_global_trend && data.btc_global_trend.includes('Bullish') ? 'text-brand-green' : data.btc_global_trend && data.btc_global_trend.includes('Bearish') ? 'text-brand-red' : 'text-gray-300'}`}>
                                {data.btc_global_trend || 'Analyzing...'}
                            </span>
                        </div>

                        {/* SMC State Indicators */}
                        {data.smc_state && (
                            <div className="bg-dark-900 border border-dark-700 rounded-lg p-3 flex flex-col gap-2">
                                <span className="text-sm font-medium text-gray-400 mb-1 border-b border-dark-700 pb-1">Smart Money Concepts</span>
                                <div className="grid grid-cols-2 gap-2 text-xs">
                                    <div className="flex justify-between items-center bg-dark-800 p-2 rounded border border-dark-700/50">
                                        <span className="text-gray-500">Structure</span>
                                        <span className={`font-semibold ${data.smc_state.bos_bullish ? 'text-brand-green' : data.smc_state.bos_bearish ? 'text-brand-red' : 'text-gray-500'}`}>
                                            {data.smc_state.bos_bullish ? 'BOS Bullish' : data.smc_state.bos_bearish ? 'BOS Bearish' : 'Sideway'}
                                        </span>
                                    </div>
                                    <div className="flex justify-between items-center bg-dark-800 p-2 rounded border border-dark-700/50">
                                        <span className="text-gray-500">Imbalance</span>
                                        <span className={`font-semibold ${data.smc_state.fvg_bullish ? 'text-brand-green' : data.smc_state.fvg_bearish ? 'text-brand-red' : 'text-gray-500'}`}>
                                            {data.smc_state.fvg_bullish ? 'Bullish FVG' : data.smc_state.fvg_bearish ? 'Bearish FVG' : 'Balanced'}
                                        </span>
                                    </div>
                                    <div className="flex justify-between items-center bg-dark-800 p-2 rounded border border-dark-700/50 col-span-2">
                                        <span className="text-gray-500">Order Block Mitigation</span>
                                        <span className={`font-semibold px-2 py-0.5 rounded ${data.smc_state.in_ob_bullish ? 'bg-brand-green/20 text-brand-green' : data.smc_state.in_ob_bearish ? 'bg-brand-red/20 text-brand-red' : 'text-gray-500'}`}>
                                            {data.smc_state.in_ob_bullish ? 'In Demand OB (Discount)' : data.smc_state.in_ob_bearish ? 'In Supply OB (Premium)' : 'None'}
                                        </span>
                                    </div>
                                </div>
                            </div>
                        )}

                        <div className="bg-dark-900 border border-brand-green/30 rounded-lg p-4 flex flex-col gap-1 items-center justify-center relative overflow-hidden">
                            <div className="absolute top-0 right-0 w-16 h-16 bg-brand-green/10 rounded-full blur-2xl"></div>
                            <span className="text-sm text-gray-400">Recommended Strategy ({data.interval})</span>
                            <div className="text-2xl font-bold text-brand-green flex items-center gap-2">
                                <Zap className="w-5 h-5" />
                                {data.best_strategy}
                            </div>
                            <span className="text-xs text-gray-500 mt-1">Updates every 5 seconds</span>
                        </div>

                        {/* Trade Setup Panel */}
                        {data.trade_setup && (
                            <div className="bg-dark-800 border border-dark-600 rounded-lg p-4 flex flex-col gap-3">
                                <div className="flex justify-between items-center border-b border-dark-700 pb-2">
                                    <h3 className="text-sm font-semibold flex items-center gap-2">
                                        <Crosshair className="w-4 h-4 text-brand-blue" />
                                        AI Trade Setup
                                    </h3>
                                    <span className={`text-xs font-bold px-2 py-1 rounded ${data.trade_setup.direction.includes('LONG') ? 'bg-brand-green/20 text-brand-green' : 'bg-brand-red/20 text-brand-red'}`}>
                                        {data.trade_setup.direction}
                                    </span>
                                </div>
                                <div className="grid grid-cols-3 gap-2 text-center mt-2">
                                    <div className="flex flex-col bg-dark-900 p-2 rounded border border-dark-700">
                                        <span className="text-xs text-gray-400 uppercase">Entry</span>
                                        <span className="text-sm font-mono text-gray-200 mt-1">${data.trade_setup.entry_price}</span>
                                    </div>
                                    <div className="flex flex-col bg-dark-900 p-2 rounded border border-brand-green/30">
                                        <span className="text-xs text-brand-green uppercase flex justify-center gap-1 items-center"><Target className="w-3 h-3" /> TP</span>
                                        <span className="text-sm font-mono text-brand-green mt-1">${data.trade_setup.take_profit_price}</span>
                                    </div>
                                    <div className="flex flex-col bg-dark-900 p-2 rounded border border-brand-red/30">
                                        <span className="text-xs text-brand-red uppercase flex justify-center gap-1 items-center"><ShieldAlert className="w-3 h-3" /> SL</span>
                                        <span className="text-sm font-mono text-brand-red mt-1">${data.trade_setup.stop_loss_price}</span>
                                    </div>
                                </div>
                            </div>
                        )}

                        <div className="flex flex-col gap-2 mt-2">
                            <h3 className="text-sm font-medium text-gray-300 mb-1">Win Probability Estimations</h3>
                            {data.all_predictions.map((p, index) => (
                                <div key={index} className="flex flex-col gap-1">
                                    <div className="flex justify-between items-center text-sm">
                                        <span className="text-gray-400">{p.strategy.replace('_', ' ')}</span>
                                        <span className={`font-mono ${p.is_recommended ? 'text-brand-green' : 'text-gray-300'}`}>
                                            {p.win_probability}%
                                        </span>
                                    </div>
                                    <div className="h-1.5 w-full bg-dark-900 rounded-full overflow-hidden">
                                        <div
                                            className={`h-full rounded-full transition-all duration-500 ${p.is_recommended ? 'bg-brand-green' : 'bg-dark-600'}`}
                                            style={{ width: `${p.win_probability}%` }}
                                        ></div>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </>
                ) : (
                    <div className="h-48 flex items-center justify-center text-gray-500 text-sm">
                        Failed to load ML models
                    </div>
                )}
            </div>
        </div>
    )
}

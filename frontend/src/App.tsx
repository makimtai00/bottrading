import { useEffect, useState } from 'react'
import { Activity, BarChart2, Loader2 } from 'lucide-react'
import Select from 'react-select'
import TradingChart from './components/TradingChart'
import StrategyPanel from './components/StrategyPanel'
import OrderPanel from './components/OrderPanel'

export default function App() {
    const [symbol, setSymbol] = useState("BTCUSDT")
    const [symbolsData, setSymbolsData] = useState<{ value: string, label: string }[]>([])
    const [interval, setInterval] = useState('5m')
    const [loadingSymbols, setLoadingSymbols] = useState(true)

    useEffect(() => {
        // Fetch dynamic list of USDT futures when the app loads
        const fetchSymbols = async () => {
            try {
                const res = await fetch("http://localhost:8000/api/v1/symbols")
                if (res.ok) {
                    const json = await res.json()
                    if (json.data && Array.isArray(json.data)) {
                        // Vừa set data cho react-select vừa chứa danh sách symbol
                        const formattedSymbols = json.data.map((sym: string) => ({
                            value: sym,
                            label: sym
                        }))
                        setSymbolsData(formattedSymbols)
                        // Giữ BTCUSDT làm mặc định nếu có trong list
                        if (!json.data.includes("BTCUSDT") && json.data.length > 0) {
                            setSymbol(json.data[0])
                        }
                    }
                }
            } catch (error) {
                console.error("Lỗi lấy danh sách Symbol:", error)
            } finally {
                setLoadingSymbols(false)
            }
        }

        fetchSymbols()
    }, [])

    // Custom styles for react-select to match the dark theme
    const selectStyles = {
        control: (provided: any, state: any) => ({
            ...provided,
            backgroundColor: '#1E2329', // bg-dark-800
            borderColor: state.isFocused ? '#3B82F6' : '#2B3139', // bg-dark-600
            color: '#EAECEF',
            minHeight: '38px',
            boxShadow: state.isFocused ? '0 0 0 1px #3B82F6' : 'none',
            '&:hover': {
                borderColor: '#3B82F6'
            },
            width: '200px'
        }),
        menu: (provided: any) => ({
            ...provided,
            backgroundColor: '#1E2329',
            border: '1px solid #2B3139',
            zIndex: 50
        }),
        option: (provided: any, state: any) => ({
            ...provided,
            backgroundColor: state.isSelected ? '#3B82F6' : state.isFocused ? '#2B3139' : '#1E2329',
            color: '#EAECEF',
            cursor: 'pointer',
            '&:active': {
                backgroundColor: '#3B82F6'
            }
        }),
        singleValue: (provided: any) => ({
            ...provided,
            color: '#EAECEF'
        }),
        input: (provided: any) => ({
            ...provided,
            color: '#EAECEF'
        })
    }

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
                        <div className="flex flex-col md:flex-row gap-2 md:items-center relative z-50">
                            <span className="text-sm text-gray-400 hidden md:block">Trading Pair</span>
                            {loadingSymbols ? (
                                <div className="flex items-center gap-2 text-sm text-gray-400 px-3 py-1.5 border border-dark-600 rounded-md">
                                    <Loader2 className="w-4 h-4 animate-spin" /> Fetching...
                                </div>
                            ) : (
                                <Select
                                    className="react-select-container text-sm"
                                    classNamePrefix="react-select"
                                    options={symbolsData}
                                    value={symbolsData.find(s => s.value === symbol)}
                                    onChange={(selectedOption: any) => {
                                        if (selectedOption) setSymbol(selectedOption.value)
                                    }}
                                    styles={selectStyles}
                                    isSearchable={true}
                                />
                            )}
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


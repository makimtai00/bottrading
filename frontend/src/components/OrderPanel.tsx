import { useState, useEffect } from 'react'
import { Activity, Clock, LogOut, CheckCircle, XCircle, Timer } from 'lucide-react'

interface OpenOrder {
    id: string
    symbol: string
    direction: string
    entry_price: number
    take_profit_price: number
    stop_loss_price: number
    estimated_win_rate: number
    open_time: number
    status: string
    pnl: number
}

interface ClosedOrder extends OpenOrder {
    close_reason: string
    close_price: number
    final_pnl: number
    close_time: number
}

export default function OrderPanel() {
    const [activeTab, setActiveTab] = useState<'pending' | 'open' | 'closed'>('pending')
    const [pendingOrders, setPendingOrders] = useState<OpenOrder[]>([])
    const [openOrders, setOpenOrders] = useState<OpenOrder[]>([])
    const [closedOrders, setClosedOrders] = useState<ClosedOrder[]>([])

    const fetchOrders = async () => {
        try {
            const [pendingRes, openRes, closedRes] = await Promise.all([
                fetch('http://localhost:8000/api/v1/orders/pending'),
                fetch('http://localhost:8000/api/v1/orders/open'),
                fetch('http://localhost:8000/api/v1/orders/closed')
            ])

            if (pendingRes.ok) {
                const pendingData = await pendingRes.json()
                setPendingOrders(pendingData.data || [])
            }
            if (openRes.ok) {
                const openData = await openRes.json()
                setOpenOrders(openData.data || [])
            }
            if (closedRes.ok) {
                const closedData = await closedRes.json()
                setClosedOrders(closedData.data || [])
            }
        } catch (error) {
            console.error("Lỗi lấy dữ liệu Lệnh:", error)
        }
    }

    useEffect(() => {
        fetchOrders()
        const timer = setInterval(fetchOrders, 3000) // Cập nhật PNL ảo mỗi 3 giây
        return () => clearInterval(timer)
    }, [])

    const formatTime = (ts: number) => {
        return new Date(ts * 1000).toLocaleTimeString()
    }

    return (
        <div className="bg-dark-800 rounded-xl border border-dark-700 shadow-lg flex flex-col h-[400px]">
            {/* Tabs Header */}
            <div className="flex border-b border-dark-700">
                <button
                    onClick={() => setActiveTab('pending')}
                    className={`flex-1 py-3 px-2 text-sm font-semibold flex items-center justify-center gap-1.5 transition-colors ${activeTab === 'pending' ? 'text-brand-blue border-b-2 border-brand-blue bg-dark-700/50' : 'text-gray-400 hover:text-gray-200'
                        }`}
                >
                    <Timer className="w-4 h-4" />
                    Pending ({pendingOrders.length})
                </button>
                <button
                    onClick={() => setActiveTab('open')}
                    className={`flex-1 py-3 px-2 text-sm font-semibold flex items-center justify-center gap-1.5 transition-colors ${activeTab === 'open' ? 'text-brand-blue border-b-2 border-brand-blue bg-dark-700/50' : 'text-gray-400 hover:text-gray-200'
                        }`}
                >
                    <Activity className="w-4 h-4" />
                    Active ({openOrders.length})
                </button>
                <button
                    onClick={() => setActiveTab('closed')}
                    className={`flex-1 py-3 px-2 text-sm font-semibold flex items-center justify-center gap-1.5 transition-colors ${activeTab === 'closed' ? 'text-brand-blue border-b-2 border-brand-blue bg-dark-700/50' : 'text-gray-400 hover:text-gray-200'
                        }`}
                >
                    <Clock className="w-4 h-4" />
                    History ({closedOrders.length})
                </button>
            </div>

            {/* List */}
            <div className="flex-1 overflow-y-auto p-2">
                {activeTab === 'pending' ? (
                    pendingOrders.length > 0 ? (
                        <div className="flex flex-col gap-2">
                            {pendingOrders.map(order => (
                                <div key={order.id} className="bg-dark-900 border border-dark-700 rounded-lg p-3 flex justify-between items-center opacity-80">
                                    <div className="flex flex-col gap-1">
                                        <div className="flex items-center gap-2">
                                            <span className="font-bold text-gray-200">{order.symbol}</span>
                                            <span className={`text-xs px-2 py-0.5 rounded font-mono ${order.direction.includes('LONG') ? 'bg-brand-green/20 text-brand-green' : 'bg-brand-red/20 text-brand-red'}`}>
                                                LIMIT {order.direction}
                                            </span>
                                        </div>
                                        <div className="text-xs text-brand-blue font-mono mt-1">
                                            Wait Entry: {order.entry_price}
                                        </div>
                                        <div className="text-xs text-gray-500 font-mono mt-0.5">
                                            TP: {order.take_profit_price} / SL: {order.stop_loss_price}
                                        </div>
                                    </div>
                                    <div className="flex flex-col items-end">
                                        <span className="text-xs text-brand-blue animate-pulse flex items-center gap-1">
                                            <Timer className="w-3 h-3" /> Waiting...
                                        </span>
                                        <span className="text-xs text-gray-500 mt-1">{formatTime(order.open_time)}</span>
                                    </div>
                                </div>
                            ))}
                        </div>
                    ) : (
                        <div className="h-full flex flex-col items-center justify-center text-gray-500 text-sm gap-2">
                            <Timer className="w-8 h-8 opacity-50" />
                            Listening for AI Limit Signals...
                        </div>
                    )
                ) : activeTab === 'open' ? (
                    openOrders.length > 0 ? (
                        <div className="flex flex-col gap-2">
                            {openOrders.map(order => (
                                <div key={order.id} className="bg-dark-900 border border-dark-700 rounded-lg p-3 flex justify-between items-center">
                                    <div className="flex flex-col gap-1">
                                        <div className="flex items-center gap-2">
                                            <span className="font-bold text-gray-200">{order.symbol}</span>
                                            <span className={`text-xs px-2 py-0.5 rounded font-mono ${order.direction.includes('LONG') ? 'bg-brand-green/20 text-brand-green' : 'bg-brand-red/20 text-brand-red'}`}>
                                                {order.direction}
                                            </span>
                                        </div>
                                        <div className="text-xs text-gray-400 font-mono">
                                            Entry: {order.entry_price} → TP: <span className="text-brand-green">{order.take_profit_price}</span> / SL: <span className="text-brand-red">{order.stop_loss_price}</span>
                                        </div>
                                    </div>
                                    <div className="flex flex-col items-end">
                                        <span className={`font-mono text-lg font-bold ${order.pnl >= 0 ? 'text-brand-green' : 'text-brand-red'}`}>
                                            {order.pnl >= 0 ? '+' : ''}{order.pnl}%
                                        </span>
                                        <span className="text-xs text-gray-500">{formatTime(order.open_time)}</span>
                                    </div>
                                </div>
                            ))}
                        </div>
                    ) : (
                        <div className="h-full flex flex-col items-center justify-center text-gray-500 text-sm gap-2">
                            <Activity className="w-8 h-8 opacity-50" />
                            No Active Orders
                        </div>
                    )
                ) : (
                    closedOrders.length > 0 ? (
                        <div className="flex flex-col gap-2">
                            {closedOrders.map(order => (
                                <div key={order.id} className={`bg-dark-900 border rounded-lg p-3 flex justify-between items-center ${order.final_pnl >= 0 ? 'border-brand-green/30' : 'border-brand-red/30'}`}>
                                    <div className="flex flex-col gap-1">
                                        <div className="flex items-center gap-2">
                                            {order.final_pnl >= 0 ? <CheckCircle className="w-4 h-4 text-brand-green" /> : <XCircle className="w-4 h-4 text-brand-red" />}
                                            <span className="font-bold text-gray-200">{order.symbol}</span>
                                            <span className="text-xs text-gray-400">({order.close_reason})</span>
                                        </div>
                                        <div className="text-xs text-gray-400 font-mono">
                                            Entry: {order.entry_price} → TP: <span className="text-brand-green">{order.take_profit_price}</span> / SL: <span className="text-brand-red">{order.stop_loss_price}</span>
                                            <br />
                                            Closed at: {order.close_price}
                                        </div>
                                    </div>
                                    <div className="flex flex-col items-end">
                                        <span className={`font-mono text-lg font-bold ${order.final_pnl >= 0 ? 'text-brand-green' : 'text-brand-red'}`}>
                                            {order.final_pnl >= 0 ? '+' : ''}{order.final_pnl}%
                                        </span>
                                        <span className="text-xs text-gray-500">{formatTime(order.close_time)}</span>
                                    </div>
                                </div>
                            ))}
                        </div>
                    ) : (
                        <div className="h-full flex flex-col items-center justify-center text-gray-500 text-sm gap-2">
                            <LogOut className="w-8 h-8 opacity-50" />
                            No closed trades yet
                        </div>
                    )
                )}
            </div>
        </div>
    )
}

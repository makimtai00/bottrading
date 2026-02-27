import { useEffect, useRef } from 'react';
import { createChart, ColorType, IChartApi, ISeriesApi, CandlestickData, Time } from 'lightweight-charts';

interface Props {
    symbol: string;
    interval: string;
}

export default function TradingChart({ symbol, interval }: Props) {
    const chartContainerRef = useRef<HTMLDivElement>(null);
    const chartRef = useRef<IChartApi | null>(null);
    const seriesRef = useRef<ISeriesApi<"Candlestick"> | null>(null);

    useEffect(() => {
        if (!chartContainerRef.current) return;

        const chart = createChart(chartContainerRef.current, {
            layout: {
                background: { type: ColorType.Solid, color: 'transparent' },
                textColor: '#9ca3af',
            },
            grid: {
                vertLines: { color: '#374151' },
                horzLines: { color: '#374151' },
            },
            width: chartContainerRef.current.clientWidth,
            height: chartContainerRef.current.clientHeight,
            timeScale: {
                timeVisible: true,
                secondsVisible: false,
            }
        });

        const candlestickSeries = chart.addCandlestickSeries({
            upColor: '#10b981',
            downColor: '#ef4444',
            borderVisible: false,
            wickUpColor: '#10b981',
            wickDownColor: '#ef4444'
        });

        chartRef.current = chart;
        seriesRef.current = candlestickSeries;

        // Xử lý Resize
        const handleResize = () => {
            if (chartContainerRef.current && chart) {
                chart.applyOptions({
                    width: chartContainerRef.current.clientWidth,
                    height: chartContainerRef.current.clientHeight
                });
            }
        };
        window.addEventListener('resize', handleResize);

        // Fetch Historical Data
        const fetchData = async () => {
            try {
                const res = await fetch(`http://localhost:8000/api/v1/klines/${symbol}?interval=${interval}&limit=200`);
                if (res.ok) {
                    const json = await res.json();
                    if (json.data && seriesRef.current) {
                        // Dữ liệu lightweight-charts yêu cầu sort tăng dần và ko có duplicate time
                        const formatted = json.data.map((d: any) => ({
                            time: d.time as Time,
                            open: d.open,
                            high: d.high,
                            low: d.low,
                            close: d.close
                        }));
                        seriesRef.current.setData(formatted);
                    }
                }
            } catch (error) {
                console.error("Lỗi tải nến quá khứ:", error);
            }
        };

        fetchData();

        // WebSocket Connection for Live Candles
        const ws = new WebSocket('ws://localhost:8000/ws/market_data');
        ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            // Lọc dữ liệu theo symbol và interval
            if (data.type === 'kline' && data.symbol.toUpperCase() === symbol.toUpperCase() && data.interval === interval) {
                if (seriesRef.current) {
                    seriesRef.current.update({
                        time: data.time as Time,
                        open: data.open,
                        high: data.high,
                        low: data.low,
                        close: data.close
                    });
                }
            }
        };

        return () => {
            window.removeEventListener('resize', handleResize);
            ws.close();
            chart.remove();
        };

    }, [symbol, interval]);

    return (
        <div className="w-full h-full" ref={chartContainerRef}></div>
    );
}

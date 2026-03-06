'use client'
import { useState, useEffect } from 'react'
import Header from '@/components/layout/Header'

export default function ExchangePage() {
    const [data, setData] = useState(null)
    const [history, setHistory] = useState([])
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState(null)

    const fetchData = async () => {
        try {
            const [rateRes, histRes] = await Promise.all([
                fetch('/api/exchange'),
                fetch('/api/exchange/history')
            ])
            const rateData = await rateRes.json()
            const histData = await histRes.json()
            setData(rateData)
            setHistory(histData.history || [])
            setError(null)
        } catch (e) {
            setError('환율 정보를 불러올 수 없습니다.')
        } finally {
            setLoading(false)
        }
    }

    useEffect(() => {
        fetchData()
        const interval = setInterval(fetchData, 60000) // 1분마다 UI 갱신
        return () => clearInterval(interval)
    }, [])

    // 간단한 텍스트 차트
    const renderChart = () => {
        if (history.length < 2) return null
        const rates = history.map(h => h.rate)
        const min = Math.min(...rates)
        const max = Math.max(...rates)
        const range = max - min || 1

        return (
            <div className="mt-8 bg-white rounded-xl shadow-sm p-6">
                <h2 className="text-lg font-semibold text-gray-700 mb-4">📈 환율 추이</h2>
                <div className="flex items-end gap-1 h-40">
                    {history.slice(-48).map((h, i) => {
                        const height = ((h.rate - min) / range) * 100 + 10
                        const time = new Date(h.time)
                        const label = `${time.getMonth()+1}/${time.getDate()} ${time.getHours()}시`
                        return (
                            <div key={i} className="flex-1 flex flex-col items-center group relative">
                                <div className="absolute -top-8 bg-gray-800 text-white text-xs px-2 py-1 rounded opacity-0 group-hover:opacity-100 whitespace-nowrap z-10">
                                    {h.rate.toLocaleString('ko-KR', { maximumFractionDigits: 2 })}원<br/>{label}
                                </div>
                                <div
                                    className="w-full bg-blue-400 hover:bg-blue-600 rounded-t transition-colors cursor-pointer"
                                    style={{ height: `${height}%` }}
                                />
                            </div>
                        )
                    })}
                </div>
                <div className="flex justify-between text-xs text-gray-400 mt-2">
                    <span>최저 {min.toLocaleString('ko-KR', { maximumFractionDigits: 2 })}원</span>
                    <span>최고 {max.toLocaleString('ko-KR', { maximumFractionDigits: 2 })}원</span>
                </div>
            </div>
        )
    }

    return (
        <div className="min-h-screen bg-gray-50">
            <Header />
            <main className="max-w-3xl mx-auto px-4 py-10">
                <h1 className="text-3xl font-bold text-gray-800 mb-8">💱 환율 정보</h1>

                {loading ? (
                    <div className="text-center py-20 text-gray-400">
                        <p className="text-xl">환율 정보를 불러오는 중...</p>
                    </div>
                ) : error ? (
                    <div className="text-center py-20 text-red-400">
                        <p className="text-xl">{error}</p>
                    </div>
                ) : data ? (
                    <>
                        {/* 메인 환율 카드 */}
                        <div className="bg-white rounded-xl shadow-sm p-8">
                            <div className="flex items-center justify-between">
                                <div>
                                    <p className="text-sm text-gray-400 mb-1">미국 달러 (USD) → 한국 원 (KRW)</p>
                                    <div className="flex items-baseline gap-2">
                                        <span className="text-5xl font-bold text-gray-800">
                                            {data.rate?.toLocaleString('ko-KR', { maximumFractionDigits: 2 })}
                                        </span>
                                        <span className="text-xl text-gray-500">원</span>
                                    </div>
                                    <p className="text-sm text-gray-400 mt-2">1 USD 기준</p>
                                </div>
                                <div className="text-right">
                                    <div className="text-6xl">🇺🇸</div>
                                    <p className="text-xs text-gray-400 mt-2">→ 🇰🇷</p>
                                </div>
                            </div>
                            <div className="border-t mt-6 pt-4 flex justify-between text-sm text-gray-400">
                                <span>갱신: {data.updatedAtKR}</span>
                                <span>출처: {data.source}</span>
                            </div>
                        </div>

                        {/* 환율 계산기 */}
                        <Calculator rate={data.rate} />

                        {/* 차트 */}
                        {renderChart()}
                    </>
                ) : null}
            </main>
        </div>
    )
}

function Calculator({ rate }) {
    const [usd, setUsd] = useState('1')
    const krw = (parseFloat(usd) || 0) * rate

    return (
        <div className="mt-6 bg-white rounded-xl shadow-sm p-6">
            <h2 className="text-lg font-semibold text-gray-700 mb-4">🧮 환율 계산기</h2>
            <div className="flex items-center gap-4">
                <div className="flex-1">
                    <label className="text-sm text-gray-500">USD</label>
                    <input
                        type="number"
                        value={usd}
                        onChange={(e) => setUsd(e.target.value)}
                        className="w-full mt-1 p-3 border rounded-lg text-lg focus:outline-none focus:ring-2 focus:ring-blue-400"
                        min="0"
                        step="0.01"
                    />
                </div>
                <span className="text-2xl text-gray-400 pt-5">=</span>
                <div className="flex-1">
                    <label className="text-sm text-gray-500">KRW</label>
                    <div className="w-full mt-1 p-3 bg-gray-50 border rounded-lg text-lg font-semibold text-gray-700">
                        {krw.toLocaleString('ko-KR', { maximumFractionDigits: 0 })} 원
                    </div>
                </div>
            </div>
        </div>
    )
}
